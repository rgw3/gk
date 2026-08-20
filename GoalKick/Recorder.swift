//
//  Recorder.swift
//  GoalKick
//
//  High frame rate capture: format selection, recording, and saving to Photos.
//
//  Threading: published properties are main-actor state for the UI. Everything
//  the capture pipeline touches — session, outputs, device, active config — is
//  owned exclusively by sessionQueue and marked nonisolated(unsafe) to say so
//  explicitly. AVFoundation calls the recording delegate on its own queue, so
//  those methods are nonisolated and hop to main only to publish.
//

import Foundation
import Combine
import AVFoundation
import CoreMedia
import UIKit
import SwiftUI

// MARK: - Capture configuration

/// The two configurations worth comparing, per the open question in
/// project_notes.md: temporal resolution versus spatial resolution.
enum CaptureConfig: String, CaseIterable, Identifiable, Sendable {
    case highSpeed1080p = "1080p · 240"
    case ultraHD120 = "4K · 120"

    // These are pure value computations read from the capture queue, so
    // they are explicitly nonisolated. Without this they inherit the
    // project's MainActor default isolation and cannot be read off-main.

    nonisolated var id: String { rawValue }

    nonisolated var width: Int32 {
        switch self {
        case .highSpeed1080p: return 1920
        case .ultraHD120: return 3840
        }
    }

    nonisolated var height: Int32 {
        switch self {
        case .highSpeed1080p: return 1080
        case .ultraHD120: return 2160
        }
    }

    nonisolated var frameRate: Double {
        switch self {
        case .highSpeed1080p: return 240
        case .ultraHD120: return 120
        }
    }

    /// Filename-safe token so a clip's configuration is visible on disk.
    nonisolated var fileToken: String {
        switch self {
        case .highSpeed1080p: return "1080p240"
        case .ultraHD120: return "4K120"
        }
    }
}

// MARK: - Local clip storage

/// A recording held in the app's own Documents directory.
struct Clip: Identifiable, Hashable {
    let url: URL
    let created: Date
    let sizeBytes: Int64

    var id: URL { url }
    var name: String { url.lastPathComponent }

    var sizeDescription: String {
        ByteCountFormatter.string(fromByteCount: sizeBytes, countStyle: .file)
    }
}

/// Clips live only here. Nothing is written to Photos.
///
/// Photos cannot be used as the source of truth for analysis: saving a
/// 240 fps clip there makes iOS classify it as slow motion, and exporting
/// it back returns a retimed 30 fps file. Every frame survives, but the
/// timestamps are 8× too far apart, which would silently make every
/// velocity 8× too slow. Clips written here are untouched.
enum ClipStore {

    static var directory: URL {
        let documents = FileManager.default.urls(for: .documentDirectory,
                                                 in: .userDomainMask)[0]
        let clips = documents.appendingPathComponent("Clips", isDirectory: true)
        try? FileManager.default.createDirectory(at: clips,
                                                 withIntermediateDirectories: true)
        return clips
    }

    static func newClipURL(for config: CaptureConfig) -> URL {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd-HHmmss"
        let stamp = formatter.string(from: Date())
        return directory
            .appendingPathComponent("GoalKick-\(stamp)-\(config.fileToken)")
            .appendingPathExtension("mov")
    }

    static func clips() -> [Clip] {
        let keys: [URLResourceKey] = [.creationDateKey, .fileSizeKey]
        let contents = (try? FileManager.default.contentsOfDirectory(
            at: directory,
            includingPropertiesForKeys: keys)) ?? []

        return contents
            .filter { $0.pathExtension.lowercased() == "mov" }
            .map { url in
                let values = try? url.resourceValues(forKeys: Set(keys))
                return Clip(url: url,
                            created: values?.creationDate ?? .distantPast,
                            sizeBytes: Int64(values?.fileSize ?? 0))
            }
            .sorted { $0.created > $1.created }
    }

    static func delete(_ clip: Clip) {
        try? FileManager.default.removeItem(at: clip.url)
    }
}

// MARK: - Recorder

/// `@unchecked Sendable` is a promise, not a guarantee the compiler checks:
/// capture state is confined to sessionQueue, published state to the main
/// actor, and the two only meet through the set(...) helpers below.
final class Recorder: NSObject, ObservableObject, @unchecked Sendable {

    // Owned by sessionQueue. The preview layer also reads `session`, which
    // AVFoundation permits from the main thread.
    nonisolated(unsafe) let session = AVCaptureSession()
    nonisolated(unsafe) private let movieOutput = AVCaptureMovieFileOutput()
    nonisolated(unsafe) private var device: AVCaptureDevice?
    /// The session queue's own copy of the active configuration. Never read
    /// `config` (main actor state) from the capture pipeline.
    nonisolated(unsafe) private var activeConfig: CaptureConfig = .highSpeed1080p

    /// Tracks how the device is held so recordings come out the right way up.
    /// Without this the capture connection stays at its portrait default no
    /// matter how the phone is turned — the UI rotates, the pixels do not.
    nonisolated(unsafe) private var rotationCoordinator: AVCaptureDevice.RotationCoordinator?
    nonisolated(unsafe) private var rotationObservation: NSKeyValueObservation?
    nonisolated(unsafe) private weak var previewLayer: AVCaptureVideoPreviewLayer?

    nonisolated private let sessionQueue = DispatchQueue(label: "com.rocket.GoalKick.session")

    // Main actor state, for the UI only.
    @Published var config: CaptureConfig = .highSpeed1080p
    @Published var status: String = "Starting…"
    @Published var detail: String = ""
    /// What the recorded file actually turned out to contain, read back
    /// from the file itself rather than from what we asked the camera for.
    @Published var verification: String = ""
    @Published var isRecording = false
    @Published var isReady = false

    // MARK: Setup

    nonisolated func start() {
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

    nonisolated private func configureSession() {
        guard !session.isRunning else { return }

        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera,
                                                   for: .video,
                                                   position: .back) else {
            set(status: "No back camera found.")
            return
        }
        device = camera

        session.beginConfiguration()
        session.sessionPreset = .inputPriority

        do {
            let input = try AVCaptureDeviceInput(device: camera)
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

        startTrackingRotation(for: camera)
        applyFormat(activeConfig)

        set(isReady: true)
    }

    // MARK: Orientation

    nonisolated private func startTrackingRotation(for camera: AVCaptureDevice) {
        let coordinator = AVCaptureDevice.RotationCoordinator(device: camera,
                                                              previewLayer: previewLayer)
        rotationCoordinator = coordinator

        // .initial fires immediately so the current orientation is applied
        // without waiting for the phone to be turned.
        rotationObservation = coordinator.observe(\.videoRotationAngleForHorizonLevelCapture,
                                                   options: [.initial, .new]) { [weak self] _, _ in
            self?.sessionQueue.async {
                self?.applyRotation()
            }
        }
    }

    nonisolated private func applyRotation() {
        guard let coordinator = rotationCoordinator else { return }
        let angle = coordinator.videoRotationAngleForHorizonLevelCapture

        // Changing rotation mid-recording would split the orientation
        // across one file, so leave it alone until recording stops.
        if !movieOutput.isRecording,
           let connection = movieOutput.connection(with: .video),
           connection.isVideoRotationAngleSupported(angle) {
            connection.videoRotationAngle = angle
        }

        // The preview layer is UI, so its connection is touched on main.
        DispatchQueue.main.async {
            if let previewConnection = self.previewLayer?.connection,
               previewConnection.isVideoRotationAngleSupported(angle) {
                previewConnection.videoRotationAngle = angle
            }
        }
    }

    /// Called by the preview view once its layer exists.
    nonisolated func attachPreviewLayer(_ layer: AVCaptureVideoPreviewLayer) {
        previewLayer = layer
        sessionQueue.async {
            self.applyRotation()
        }
    }

    // MARK: Format selection

    nonisolated func select(_ newConfig: CaptureConfig) {
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

    nonisolated private func applyFormat(_ requested: CaptureConfig) {
        guard let device else { return }
        activeConfig = requested

        let match = device.formats.first { format in
            let dimensions = CMVideoFormatDescriptionGetDimensions(format.formatDescription)
            let maxRate = format.videoSupportedFrameRateRanges.map(\.maxFrameRate).max() ?? 0
            return dimensions.width == requested.width
                && dimensions.height == requested.height
                && maxRate >= requested.frameRate
        }

        guard let format = match else {
            set(status: "No format matching \(requested.rawValue)")
            return
        }

        do {
            try device.lockForConfiguration()
            device.activeFormat = format
            // Pinning min and max stops the camera dropping the rate in
            // poor light, which would silently corrupt every measurement.
            let duration = CMTime(value: 1, timescale: CMTimeScale(requested.frameRate))
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

        // Changing the format rebuilds the connection, which resets its
        // rotation to the portrait default.
        applyRotation()

        let fov = format.videoFieldOfView
        let halfAngle = Double(fov) * .pi / 180 / 2
        let fx = halfAngle > 0 ? (Double(requested.width) / 2) / tan(halfAngle) : 0

        set(status: "Ready — \(requested.rawValue)")
        set(detail: String(format: "%d × %d · %.0f fps · FOV %.1f° · fx ≈ %.0f px",
                           requested.width, requested.height, requested.frameRate, fov, fx))
    }

    // MARK: Recording

    nonisolated func toggleRecording() {
        sessionQueue.async {
            if self.movieOutput.isRecording {
                self.movieOutput.stopRecording()
            } else {
                // Recorded straight into the app's own storage. This file is
                // the master; the Photos copy is a convenience for the coach.
                let url = ClipStore.newClipURL(for: self.activeConfig)
                self.movieOutput.startRecording(to: url, recordingDelegate: self)
            }
        }
    }

    // MARK: Publishing helpers

    nonisolated private func set(status: String) {
        DispatchQueue.main.async { self.status = status }
    }

    nonisolated private func set(detail: String) {
        DispatchQueue.main.async { self.detail = detail }
    }

    nonisolated private func set(verification: String) {
        DispatchQueue.main.async { self.verification = verification }
    }

    nonisolated private func set(isRecording: Bool) {
        DispatchQueue.main.async { self.isRecording = isRecording }
    }

    nonisolated private func set(isReady: Bool) {
        DispatchQueue.main.async { self.isReady = isReady }
    }
}

// MARK: - Recording delegate

/// AVFoundation calls these on its own queue, never the main actor.
extension Recorder: AVCaptureFileOutputRecordingDelegate {

    nonisolated func fileOutput(_ output: AVCaptureFileOutput,
                                didStartRecordingTo fileURL: URL,
                                from connections: [AVCaptureConnection]) {
        set(isRecording: true)
        set(status: "Recording…")
        set(verification: "")
    }

    nonisolated func fileOutput(_ output: AVCaptureFileOutput,
                                didFinishRecordingTo outputFileURL: URL,
                                from connections: [AVCaptureConnection],
                                error: Error?) {
        set(isRecording: false)

        if let error {
            set(status: "Recording failed: \(error.localizedDescription)")
            return
        }

        set(status: "Verifying file…")

        Task {
            let summary = await self.verifyFile(outputFileURL)
            self.set(verification: summary)
            self.set(status: "Saved to app library")
        }
    }

    /// Reads the finished file's real properties. What the camera was asked
    /// for and what landed on disk are different claims, and only this one
    /// matters for measurement.
    nonisolated private func verifyFile(_ url: URL) async -> String {
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
    let recorder: Recorder

    func makeUIView(context: Context) -> PreviewView {
        let view = PreviewView()
        view.videoPreviewLayer.session = recorder.session
        view.videoPreviewLayer.videoGravity = .resizeAspectFill
        recorder.attachPreviewLayer(view.videoPreviewLayer)
        return view
    }

    func updateUIView(_ uiView: PreviewView, context: Context) {}
}
