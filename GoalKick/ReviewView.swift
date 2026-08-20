//
//  ReviewView.swift
//  GoalKick
//
//  The coach-facing review screen: pause, slow playback, frame stepping.
//

import SwiftUI
import Combine
import AVFoundation
import CoreMedia
import UIKit
import PhotosUI
import CoreTransferable
import UniformTypeIdentifiers

// MARK: - Photos transfer

/// PhotosPicker hands back an opaque item; this copies the picked movie
/// into our own temporary file so AVPlayer has a stable URL to work with.
struct PickedMovie: Transferable {
    let url: URL

    static var transferRepresentation: some TransferRepresentation {
        FileRepresentation(contentType: .movie) { movie in
            SentTransferredFile(movie.url)
        } importing: { received in
            let ext = received.file.pathExtension.isEmpty ? "mov" : received.file.pathExtension
            let destination = FileManager.default.temporaryDirectory
                .appendingPathComponent("review-\(UUID().uuidString)")
                .appendingPathExtension(ext)
            try? FileManager.default.removeItem(at: destination)
            try FileManager.default.copyItem(at: received.file, to: destination)
            return PickedMovie(url: destination)
        }
    }
}

// MARK: - Playback controller

@MainActor
final class ReviewPlayer: ObservableObject {

    @Published private(set) var player: AVPlayer?
    @Published private(set) var isPlaying = false
    @Published private(set) var currentTime: Double = 0
    @Published private(set) var duration: Double = 0
    @Published private(set) var frameRate: Double = 0
    @Published var speed: Double = 1.0
    @Published var status: String = "No clip loaded"

    private var timeObserver: Any?

    /// Frame index the playhead currently sits on.
    var frameIndex: Int {
        guard frameRate > 0 else { return 0 }
        return Int((currentTime * frameRate).rounded())
    }

    var totalFrames: Int {
        guard frameRate > 0 else { return 0 }
        return Int((duration * frameRate).rounded())
    }

    func load(url: URL) async {
        teardown()
        status = "Loading…"

        let asset = AVURLAsset(url: url)
        do {
            let tracks = try await asset.loadTracks(withMediaType: .video)
            guard let track = tracks.first else {
                status = "No video track in that file."
                return
            }

            frameRate = Double(try await track.load(.nominalFrameRate))
            duration = CMTimeGetSeconds(try await asset.load(.duration))

            let item = AVPlayerItem(asset: asset)
            let newPlayer = AVPlayer(playerItem: item)
            newPlayer.actionAtItemEnd = .pause
            player = newPlayer

            observeTime(on: newPlayer)

            status = String(format: "%.1f fps · %.2f s · %d frames",
                            frameRate, duration, totalFrames)
        } catch {
            status = "Could not load clip: \(error.localizedDescription)"
        }
    }

    private func observeTime(on player: AVPlayer) {
        // 600 is the conventional timescale for video: it divides evenly by
        // 24, 25, 30, 60, and 120, so common frame rates land on whole values.
        let interval = CMTime(value: 1, timescale: 600)
        timeObserver = player.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            self?.currentTime = time.seconds
        }
    }

    private func teardown() {
        if let timeObserver, let player {
            player.removeTimeObserver(timeObserver)
        }
        timeObserver = nil
        player?.pause()
        player = nil
        isPlaying = false
        currentTime = 0
        duration = 0
        frameRate = 0
    }

    // MARK: Transport

    func togglePlay() {
        guard let player else { return }
        if isPlaying {
            player.pause()
            isPlaying = false
        } else {
            // Setting rate directly is what produces slow playback;
            // play() would always resume at 1.0.
            player.rate = Float(speed)
            isPlaying = true
        }
    }

    func setSpeed(_ newSpeed: Double) {
        speed = newSpeed
        guard let player, isPlaying else { return }
        player.rate = Float(newSpeed)
    }

    /// Steps exactly one frame. Stepping requires a paused player.
    func step(_ count: Int) {
        guard let player, let item = player.currentItem else { return }
        player.pause()
        isPlaying = false

        let canStep = count > 0 ? item.canStepForward : item.canStepBackward
        guard canStep else {
            status = count > 0 ? "At last frame" : "At first frame"
            return
        }

        item.step(byCount: count)
        currentTime = player.currentTime().seconds
    }
}

// MARK: - Player surface

final class PlayerContainerView: UIView {
    override class var layerClass: AnyClass {
        AVPlayerLayer.self
    }

    var playerLayer: AVPlayerLayer {
        layer as! AVPlayerLayer
    }
}

struct PlayerSurface: UIViewRepresentable {
    let player: AVPlayer

    func makeUIView(context: Context) -> PlayerContainerView {
        let view = PlayerContainerView()
        view.playerLayer.player = player
        view.playerLayer.videoGravity = .resizeAspect
        return view
    }

    func updateUIView(_ uiView: PlayerContainerView, context: Context) {
        uiView.playerLayer.player = player
    }
}

// MARK: - Screen

struct ReviewView: View {

    @StateObject private var review = ReviewPlayer()
    @State private var pickedItem: PhotosPickerItem?

    private let speeds: [Double] = [1.0, 0.5, 0.25]

    var body: some View {
        VStack(spacing: 0) {
            videoArea

            controls
                .padding()
                .background(.black)
        }
        .background(.black)
        .onChange(of: pickedItem) { _, newItem in
            guard let newItem else { return }
            Task {
                if let movie = try? await newItem.loadTransferable(type: PickedMovie.self) {
                    await review.load(url: movie.url)
                } else {
                    review.status = "Could not read that item from Photos."
                }
            }
        }
    }

    private var videoArea: some View {
        ZStack {
            Color.black
            if let player = review.player {
                PlayerSurface(player: player)
            } else {
                VStack(spacing: 12) {
                    Image(systemName: "video.badge.plus")
                        .font(.system(size: 44))
                        .foregroundStyle(.white.opacity(0.5))
                    Text("Choose a clip to review")
                        .foregroundStyle(.white.opacity(0.6))
                }
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }

    private var controls: some View {
        VStack(spacing: 14) {
            Text(review.status)
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.white.opacity(0.8))

            if review.player != nil {
                Text("frame \(review.frameIndex) of \(review.totalFrames)   ·   \(review.currentTime, specifier: "%.3f") s")
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(.green)

                transportRow
                speedRow
            }

            PhotosPicker(selection: $pickedItem, matching: .videos) {
                Label(review.player == nil ? "Choose clip" : "Choose another clip",
                      systemImage: "photo.on.rectangle")
            }
            .buttonStyle(.bordered)
            .tint(.white)
        }
    }

    private var transportRow: some View {
        HStack(spacing: 28) {
            Button {
                review.step(-1)
            } label: {
                Image(systemName: "backward.frame.fill")
                    .font(.system(size: 28))
            }

            Button {
                review.togglePlay()
            } label: {
                Image(systemName: review.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                    .font(.system(size: 46))
            }

            Button {
                review.step(1)
            } label: {
                Image(systemName: "forward.frame.fill")
                    .font(.system(size: 28))
            }
        }
        .foregroundStyle(.white)
    }

    private var speedRow: some View {
        HStack(spacing: 10) {
            ForEach(speeds, id: \.self) { speed in
                Button {
                    review.setSpeed(speed)
                } label: {
                    Text(label(for: speed))
                        .font(.system(.subheadline, design: .monospaced))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 8)
                        .background(review.speed == speed ? .white : .white.opacity(0.15),
                                    in: RoundedRectangle(cornerRadius: 8))
                        .foregroundStyle(review.speed == speed ? .black : .white)
                }
            }
        }
    }

    private func label(for speed: Double) -> String {
        switch speed {
        case 1.0: return "1×"
        case 0.5: return "1/2"
        case 0.25: return "1/4"
        default: return "\(speed)×"
        }
    }
}

#Preview {
    ReviewView()
}
