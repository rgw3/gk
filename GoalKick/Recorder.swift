//
//  Recorder.swift
//  GoalKick
//
//  High frame rate capture: format selection, recording, and saving to Photos.
//

import Foundation
import Combine
import AVFoundation
import CoreMedia
import UIKit
import SwiftUI
import Photos

// MARK: - Capture configuration

/// The two configurations worth comparing, per the open question in
/// project_notes.md: temporal resolution versus spatial resolution.
enum CaptureConfig: String, CaseIterable, Identifiable {
    case highSpeed1080p = "1080p · 240"
    case ultraHD120 = "4K · 120"

    var id: String { rawValue }

    var width: Int32 {
        switch self {
        case .highSpeed1080p: return 1920
        case .ultraHD120: return 3840
        }
    }

    var height: Int32 {
        switch self {
        case .highSpeed1080p: return 1080
        case .ultraHD120: return 2160
        }
    }

    var frameRate: Double {
        switch self {
        case .highSpeed1080p: return 240
        case .ultraHD120: return 120
        }
    }
}

// MARK: - Recorder

final class Recorder: NSObject, ObservableObject {

    let session = AVCaptureSession()

    @Published var config: CaptureConfig = .highSpeed1080p
    @Published var status: String = "Starting…"
    @Published var detail: String = ""
    /// What the recorded file actually turned out to contain, read back
    /// from the file itself rather than from what we asked the camera for.
    @Published var verification: String = ""
    @Published var isRecording = false
    @Published var isReady = false

    private let sessionQueue = DispatchQueue(label: "com.rocket.GoalKick.session")
    private let movieOutput = AVCaptureMovieFileOutput()
    private var device: AVCaptureDevice?

    // MARK: Setup

    func start() {
        AVCaptureDevice.requestAccess(for: .video) { granted in
            guard granted else {
                self.set(status: "Camera access denied. Enable it in Settings → GoalKick.")
                return
            }
            self.sessionQueue.async {
                self.configureSession()
            }
        }
    }

    private func configureSession() {
        guard !session.isRunning else { return }

        guard let device = AVCaptureDevice.default(.builtInWideAngleCamera,
                                                   for: .video,
                                                   position: .back) else {
            set(status: "No back camera found.")
            return
        }
        self.device = device

        session.beginConfiguration()
        session.sessionPreset = .inputPriority

        do {
            let input = try AVCaptureDeviceInput(device: device)
            guard session.canAddInput(input) else {
                session.commitConfiguration()
                set(status: "Could not add camera input.")
                return
            }
            session.addInput(input)
        } catch {
            session.commitConfiguration()
            set(status: "Could not open camera: \(error.localizedDescription)")
            return
        }

        guard session.canAddOutput(movieOutput) else {
            session.commitConfiguration()
            set(status: "Could not add movie output.")
            return
        }
        session.addOutput(movieOutput)

        session.commitConfiguration()
        session.startRunning()

        applyFormat(config)

        DispatchQueue.main.async {
            self.isReady = true
        }
    }

    // MARK: Format selection

    func select(_ newConfig: CaptureConfig) {
        DispatchQueue.main.async {
            self.config = newConfig
            // The previous file's verification describes the old format.
            // Leaving it on screen makes it look like it describes this one.
            self.verification = ""
        }
        sessionQueue.async {
            self.applyFormat(newConfig)
        }
    }

    private func applyFormat(_ config: CaptureConfig) {
        guard let device else { return }

        let match = device.formats.first { format in
            let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
            let maxRate = format.videoSupportedFrameRateRanges.map(\.maxFrameRate).max() ?? 0
            return dimensions.width == config.width
                && dimensions.height == config.height
                && maxRate >= config.frameRate
        }

        guard let format = match else {
            set(status: "No format matching \(config.rawValue)")
            return
        }

        do {
            try device.lockForConfiguration()
            device.activeFormat = format
            // Pinning min and max stops the camera dropping the rate in
            // poor light, which would silently corrupt every measurement.
            let duration = CMTime(value: 1, timescale: CMTimeScale(config.frameRate))
            device.activeVideoMinFrameDuration = duration
            device.activeVideoMaxFrameDuration = duration
            device.unlockForConfiguration()
        } catch {
            set(status: "Could not apply format: \(error.localizedDescription)")
            return
        }

        // Stabilization warps the image geometry. That is fine for home
        // video and fatal for measurement, so it stays off.
        if let connection = movieOutput.connection(with: .video),
           connection.isVideoStabilizationSupported {
            connection.preferredVideoStabilizationMode = .off
        }

        let fov = format.videoFieldOfView
        let halfAngle = Double(fov) * .pi / 180 / 2
        let fx = halfAngle > 0 ? (Double(config.width) / 2) / tan(halfAngle) : 0

        set(status: "Ready — \(config.rawValue)")
        set(detail: String(format: "%d × %d · %.0f fps · FOV %.1f° · fx ≈ %.0f px",
                           config.width, config.height, config.frameRate, fov, fx))
    }

    // MARK: Recording

    func toggleRecording() {
        sessionQueue.async {
            if self.movieOutput.isRecording {
                self.movieOutput.stopRecording()
            } else {
                let url = FileManager.default.temporaryDirectory
                    .appendingPathComponent(UUID().uuidString)
                    .appendingPathExtension("mov")
                self.movieOutput.startRecording(to: url, recordingDelegate: self)
            }
        }
    }

    // MARK: Helpers

    private func set(status: String) {
        DispatchQueue.main.async { self.status = status }
    }

    private func set(detail: String) {
        DispatchQueue.main.async { self.detail = detail }
    }

    private func set(verification: String) {
        DispatchQueue.main.async { self.verification = verification }
    }
}

// MARK: - Recording delegate

extension Recorder: AVCaptureFileOutputRecordingDelegate {

    func fileOutput(_ output: AVCaptureFileOutput,
                    didStartRecordingTo fileURL: URL,
                    from connections: [AVCaptureConnection]) {
        DispatchQueue.main.async {
            self.isRecording = true
            self.status = "Recording…"
            self.verification = ""
        }
    }

    func fileOutput(_ output: AVCaptureFileOutput,
                    didFinishRecordingTo outputFileURL: URL,
                    from connections: [AVCaptureConnection],
                    error: Error?) {
        DispatchQueue.main.async {
            self.isRecording = false
        }

        if let error {
            set(status: "Recording failed: \(error.localizedDescription)")
            return
        }

        set(status: "Verifying file…")

        Task {
            let summary = await self.verifyFile(outputFileURL)
            self.set(verification: summary)
            self.set(status: "Saving to Photos…")
            self.saveToPhotos(outputFileURL)
        }
    }

    /// Reads the finished file's real properties. What the camera was asked
    /// for and what landed on disk are different claims, and only this one
    /// matters for measurement.
    private func verifyFile(_ url: URL) async -> String {
        let asset = AVURLAsset(url: url)
        do {
            let tracks = try await asset.loadTracks(withMediaType: .video)
            guard let track = tracks.first else {
                return "FILE: no video track"
            }
            let rate = try await track.load(.nominalFrameRate)
            let size = try await track.load(.naturalSize)
            let duration = try await asset.load(.duration)
            let seconds = CMTimeGetSeconds(duration)
            let frames = Int((Double(rate) * seconds).rounded())

            return String(format: "FILE: %.0f × %.0f · %.1f fps · %.2f s · ~%d frames",
                          size.width, size.height, rate, seconds, frames)
        } catch {
            return "FILE: verify failed — \(error.localizedDescription)"
        }
    }

    private func saveToPhotos(_ url: URL) {
        PHPhotoLibrary.requestAuthorization(for: .addOnly) { authorization in
            guard authorization == .authorized || authorization == .limited else {
                self.set(status: "Photos access denied. Enable it in Settings → GoalKick.")
                return
            }

            PHPhotoLibrary.shared().performChanges {
                let request = PHAssetCreationRequest.forAsset()
                request.addResource(with: .video, fileURL: url, options: nil)
            } completionHandler: { success, error in
                if success {
                    self.set(status: "Saved to Photos — \(self.config.rawValue)")
                } else {
                    self.set(status: "Save failed: \(error?.localizedDescription ?? "unknown")")
                }
                try? FileManager.default.removeItem(at: url)
            }
        }
    }
}

// MARK: - Live preview

final class PreviewView: UIView {
    override class var layerClass: AnyClass {
        AVCaptureVideoPreviewLayer.self
    }

    var videoPreviewLayer: AVCaptureVideoPreviewLayer {
        layer as! AVCaptureVideoPreviewLayer
    }
}

struct CameraPreview: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.videoPreviewLayer.session = session
        view.videoPreviewLayer.videoGravity = .resizeAspectFill
        return view
    }

    func updateUIView(_ uiView: PreviewView, context: Context) {}
}
