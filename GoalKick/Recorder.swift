//
//  Recorder.swift
//  GoalKick
//
//  High frame rate capture: format selection, recording, and file verification.
//  Clips are written to the app's own storage. Nothing is written to Photos.
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

// MARK: - Ball size

/// The ball's physical diameter is the only real-world measurement the app is
/// given. Together with the focal length in pixels it is what turns an apparent
/// diameter on screen into a distance in metres — so a clip recorded without it
/// cannot be measured at all, at any later date.
///
/// That is why it is recorded per clip at capture time rather than kept as a
/// global setting: a setting describes the app's state now, not the state when
/// a particular clip was filmed.
enum BallSize: String, CaseIterable, Identifiable, Sendable {
    case size3 = "Size 3"
    case size4 = "Size 4"
    case size5 = "Size 5"

    // As with CaptureConfig, these are pure value computations read from the
    // capture queue, so they are explicitly nonisolated to opt out of the
    // project's MainActor default isolation.

    nonisolated var id: String { rawValue }

    /// Diameter in millimetres, taken from the midpoint of each size's official
    /// circumference range: d = circumference / π.
    ///
    /// - Size 3: 58–61 cm → 59.5 cm
    /// - Size 4: 63.5–66 cm → 64.75 cm
    /// - Size 5: 68–70 cm → 69.0 cm
    ///
    /// These are nominal. A ball's real diameter varies with inflation
    /// pressure and wear, which puts a floor on achievable accuracy that no
    /// amount of tracking precision can lift.
    nonisolated var diameterMillimetres: Double {
        switch self {
        case .size3: return 189.4
        case .size4: return 206.1
        case .size5: return 219.6
        }
    }

    /// The form the metric maths actually consumes.
    nonisolated var diameterMetres: Double {
        diameterMillimetres / 1000
    }

    /// Filename-safe token, so a clip's ball size is visible on disk and in
    /// the Files app without opening the video.
    nonisolated var fileToken: String {
        switch self {
        case .size3: return "sz3"
        case .size4: return "sz4"
        case .size5: return "sz5"
        }
    }

    nonisolated static func from(fileToken token: String) -> BallSize? {
        allCases.first { $0.fileToken == token }
    }

    /// Recovers the ball size from a clip filename written by `newClipURL`.
    ///
    /// Any component is matched rather than a fixed position, so a clip
    /// recorded before ball size existed simply yields nil instead of
    /// mis-parsing, and adding further tokens later cannot break this.
    nonisolated static func from(filename: String) -> BallSize? {
        let stem = (filename as NSString).deletingPathExtension
        for component in stem.split(separator: "-") {
            if let match = from(fileToken: String(component)) {
                return match
            }
        }
        return nil
    }
}

// MARK: - Clip metadata

/// Identifiers for the movie-level metadata written into each recording.
///
/// The filename carries the ball size too, but this is the authoritative copy:
/// the two can only disagree if a file is renamed, and renaming damages the
/// filename while leaving what is inside the file untouched.
///
/// `mdta` is the QuickTime metadata keyspace, which permits reverse-DNS keys of
/// our own. It is the only keyspace that does, and .mov files support it.
enum ClipMetadata {
    // Computed and explicitly nonisolated, not stored. A `static let` here
    // would inherit the project's MainActor default isolation and could not
    // be read from the capture queue, which is exactly where it is needed.
    // Same reason CaptureConfig's properties are marked nonisolated above.

    nonisolated static var ballSizeIdentifier: AVMetadataIdentifier {
        AVMetadataIdentifier("mdta/com.rocket.GoalKick.ballSize")
    }

    nonisolated static var ballDiameterIdentifier: AVMetadataIdentifier {
        AVMetadataIdentifier("mdta/com.rocket.GoalKick.ballDiameterMillimetres")
    }

    /// Movie-level metadata describing the ball, to be handed to the movie
    /// output *before* recording starts. Set afterwards it has no effect.
    ///
    /// The diameter is written alongside the size name so that analysis code
    /// never has to know what "Size 4" means in millimetres — the number it
    /// needs is in the file.
    nonisolated static func items(for ballSize: BallSize) -> [AVMetadataItem] {
        let name = AVMutableMetadataItem()
        name.identifier = ballSizeIdentifier
        name.dataType = kCMMetadataBaseDataType_UTF8 as String
        name.value = ballSize.rawValue as NSString

        let diameter = AVMutableMetadataItem()
        diameter.identifier = ballDiameterIdentifier
        diameter.dataType = kCMMetadataBaseDataType_UTF8 as String
        diameter.value = String(ballSize.diameterMillimetres) as NSString

        return [name, diameter]
    }

    /// Reads the ball diameter back out of a recorded clip.
    ///
    /// Async because loading metadata means reading the file. This is the call
    /// analysis should use; the filename token is for display and for quick
    /// inspection from outside the app.
    nonisolated static func ballDiameterMillimetres(in url: URL) async -> Double? {
        let asset = AVURLAsset(url: url)
        guard let metadata = try? await asset.load(.metadata) else { return nil }
        let matches = AVMetadataItem.metadataItems(from: metadata,
                                                   filteredByIdentifier: ballDiameterIdentifier)
        guard let item = matches.first,
              let text = try? await item.load(.stringValue) else { return nil }
        return Double(text)
    }
}

// MARK: - Local clip storage

/// A recording held in the app's own Documents directory.
struct Clip: Identifiable, Hashable {
    let url: URL
    let created: Date
    let sizeBytes: Int64
    /// Parsed from the filename, so the clip list stays synchronous. Nil for
    /// clips recorded before ball size was captured — those are not
    /// measurable, and showing that plainly is the point.
    let ballSize: BallSize?

    var id: URL { url }
    var name: String { url.lastPathComponent }

    var sizeDescription: String {
        ByteCountFormatter.string(fromByteCount: sizeBytes, countStyle: .file)
    }

    var ballDescription: String {
        ballSize?.rawValue ?? "Ball size unknown"
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

    static func newClipURL(for config: CaptureConfig, ballSize: BallSize) -> URL {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd-HHmmss"
        let stamp = formatter.string(from: Date())
        return directory
            .appendingPathComponent("GoalKick-\(stamp)-\(config.fileToken)-\(ballSize.fileToken)")
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
                            sizeBytes: Int64(values?.fileSize ?? 0),
                            ballSize: BallSize.from(filename: url.lastPathComponent))
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
    /// Likewise for the ball size. Same rule, same reason.
    nonisolated(unsafe) private var activeBallSize: BallSize = .size4

    /// Tracks how the device is held so recordings come out the right way up.
    /// Without this the capture connection stays at its portrait default no
    /// matter how the phone is turned — the UI rotates, the pixels do not.
    nonisolated(unsafe) private var rotationCoordinator: AVCaptureDevice.RotationCoordinator?
    nonisolated(unsafe) private var rotationObservation: NSKeyValueObservation?
    nonisolated(unsafe) private weak var previewLayer: AVCaptureVideoPreviewLayer?

    nonisolated private let sessionQueue = DispatchQueue(label: "com.rocket.GoalKick.session")

    // Main actor state, for the UI only.
    @Published var config: CaptureConfig = .highSpeed1080p
    @Published var ballSize: BallSize = .size4
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

    /// Ball size changes nothing about the capture session — it is written to
    /// the filename and the movie metadata when recording starts — so unlike
    /// `select(_:)` this only moves the value onto the capture queue.
    nonisolated func select(ballSize newBallSize: BallSize) {
        DispatchQueue.main.async {
            self.ballSize = newBallSize
        }
        sessionQueue.async {
            self.activeBallSize = newBallSize
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
                // The ball size is written twice, on purpose. The metadata is
                // authoritative; the filename token mirrors it so the size is
                // legible in the Files app and to analysis code on the Mac
                // without opening the video. Both travel with the file over
                // AirDrop, which a sidecar file would not.
                //
                // Metadata must be assigned before startRecording — set after,
                // it is silently ignored.
                self.movieOutput.metadata = ClipMetadata.items(for: self.activeBallSize)

                // Recorded straight into the app's own storage. This file is
                // the only copy, and the only one with true frame timing.
                let url = ClipStore.newClipURL(for: self.activeConfig,
                                               ballSize: self.activeBallSize)
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

            // Read the ball back out of the finished file rather than trusting
            // that the write worked. A clip whose ball size failed to record
            // is not measurable, and that should be visible now, not at
            // analysis time weeks later.
            let ball: String
            if let diameter = await ClipMetadata.ballDiameterMillimetres(in: url) {
                ball = String(format: " · ball %.1f mm", diameter)
            } else {
                ball = " · BALL SIZE MISSING"
            }

            return String(format: "FILE: %.0f × %.0f · %.1f fps · %.2f s · ~%d frames%@",
                          size.width, size.height, rate, seconds, frames, ball)
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
