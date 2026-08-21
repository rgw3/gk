//
//  ReviewView.swift
//  GoalKick
//
//  The coach-facing review screen: pause, slow playback, frame stepping.
//
//  Clips come from the app's own library, never from Photos. A 240 fps clip
//  exported back out of Photos arrives retimed to 30 fps — every frame
//  present, but timestamps 8× too far apart.
//

import SwiftUI
import Combine
import AVFoundation
import CoreMedia
import UIKit

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
    /// While the user drags the scrubber, the time observer must not fight
    /// the slider for control of currentTime.
    @Published private(set) var isScrubbing = false
    @Published private(set) var isReversing = false

    // Loop range, in seconds. Both ends must be set for looping to engage.
    @Published private(set) var loopStart: Double?
    @Published private(set) var loopEnd: Double?
    @Published private(set) var isLooping = false

    private var isLoopSeeking = false

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
        clearLoop()
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
        // This is the interval BETWEEN callbacks, not a timestamp precision.
        // Every callback publishes a change and re-renders the view, and the
        // main thread also drives decoding — so asking for a fine interval
        // here starves playback rather than making the readout better.
        // 1/30 s is far more than the readout needs; exact frame positions
        // come from step(_:) setting currentTime directly.
        let interval = CMTime(value: 1, timescale: 30)
        timeObserver = player.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            // The observer was registered with queue: .main, so this closure
            // genuinely runs on the main actor — the compiler just cannot see
            // the connection between that argument and this isolation.
            MainActor.assumeIsolated {
                guard let self, !self.isScrubbing else { return }
                let seconds = time.seconds
                if abs(seconds - self.currentTime) > 0.001 {
                    self.currentTime = seconds
                }
                self.enforceLoopIfNeeded(at: seconds)
            }
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
        if isPlaying && !isReversing {
            pause()
        } else {
            // Setting rate directly is what produces slow playback;
            // play() would always resume at 1.0.
            isReversing = false
            player.rate = Float(speed)
            isPlaying = true
        }
    }

    /// Continuous playback backwards. Not all encodings support it, so the
    /// item is asked before the rate is set.
    func toggleReverse() {
        guard let player, let item = player.currentItem else { return }
        if isPlaying && isReversing {
            pause()
            return
        }
        guard item.canPlayReverse else {
            status = "This clip cannot play in reverse — use frame step"
            return
        }
        isReversing = true
        player.rate = -Float(speed)
        isPlaying = true
    }

    func pause() {
        player?.pause()
        isPlaying = false
        isReversing = false
    }

    func setSpeed(_ newSpeed: Double) {
        speed = newSpeed
        guard let player, isPlaying else { return }
        player.rate = Float(newSpeed) * (isReversing ? -1 : 1)
    }

    // MARK: Looping

    func markIn() {
        loopStart = currentTime
        normalizeLoop()
    }

    func markOut() {
        loopEnd = currentTime
        normalizeLoop()
    }

    func clearLoop() {
        loopStart = nil
        loopEnd = nil
        isLooping = false
    }

    func toggleLoop() {
        guard hasLoopRange else {
            status = "Set both In and Out first"
            return
        }
        isLooping.toggle()
    }

    var hasLoopRange: Bool {
        guard let loopStart, let loopEnd else { return false }
        return loopEnd > loopStart
    }

    /// Marking Out before In is a natural mistake; swap rather than refuse.
    private func normalizeLoop() {
        if let start = loopStart, let end = loopEnd, end < start {
            loopStart = end
            loopEnd = start
        }
    }

    private func enforceLoopIfNeeded(at seconds: Double) {
        guard isLooping, isPlaying, !isLoopSeeking,
              let start = loopStart, let end = loopEnd, end > start else { return }

        if isReversing {
            guard seconds <= start else { return }
            loopJump(to: end)
        } else {
            guard seconds >= end else { return }
            loopJump(to: start)
        }
    }

    private func loopJump(to seconds: Double) {
        guard let player else { return }
        isLoopSeeking = true
        // The rate is captured and restored because a seek can leave the
        // player stopped, which would end the loop after one pass.
        let rate = player.rate
        player.seek(to: CMTime(seconds: seconds, preferredTimescale: 600),
                    toleranceBefore: .zero,
                    toleranceAfter: .zero) { [weak self] _ in
            guard let self else { return }
            Task { @MainActor in
                self.isLoopSeeking = false
                self.currentTime = seconds
                if self.isPlaying {
                    player.rate = rate
                }
            }
        }
    }

    // MARK: Scrubbing

    private var isSeekInFlight = false
    private var pendingSeekTime: Double?

    func beginScrub() {
        pause()
        isScrubbing = true
    }

    /// A drag emits values far faster than AVPlayer can service seeks, so
    /// only one is ever in flight and only the newest target is kept.
    /// Positions the finger passed through in between are dropped — nobody
    /// needs to see them, and queueing them is what makes a scrubber lag.
    func scrub(to seconds: Double) {
        currentTime = seconds
        pendingSeekTime = seconds
        guard !isSeekInFlight else { return }
        issuePendingSeek()
    }

    private func issuePendingSeek() {
        guard let player, let target = pendingSeekTime else {
            isSeekInFlight = false
            return
        }
        pendingSeekTime = nil
        isSeekInFlight = true

        // Infinite tolerance means "any nearby keyframe will do" — the
        // cheapest possible seek, which is what keeps up with a finger.
        player.seek(to: CMTime(seconds: target, preferredTimescale: 600),
                    toleranceBefore: .positiveInfinity,
                    toleranceAfter: .positiveInfinity) { [weak self] _ in
            // Bound here so the nested Task captures an immutable value.
            // Referencing a weakly captured self across a second
            // concurrency boundary is an error in Swift 6.
            guard let self else { return }
            Task { @MainActor in
                self.seekCompleted()
            }
        }
    }

    private func seekCompleted() {
        if pendingSeekTime != nil {
            issuePendingSeek()
        } else {
            isSeekInFlight = false
        }
    }

    /// Exact seek once the drag ends, so the playhead settles on a real
    /// frame rather than wherever the nearest keyframe happened to be.
    func endScrub() {
        guard let player else { return }
        pendingSeekTime = nil
        isSeekInFlight = false
        player.seek(to: CMTime(seconds: currentTime, preferredTimescale: 600),
                    toleranceBefore: .zero,
                    toleranceAfter: .zero)
        isScrubbing = false
    }

    /// Returns to the first frame and stays paused.
    func restart() {
        guard let player else { return }
        pause()
        // Zero tolerance forces an exact seek rather than the nearest
        // keyframe, so this lands on frame 0 and not merely near it.
        player.seek(to: .zero, toleranceBefore: .zero, toleranceAfter: .zero)
        currentTime = 0
    }

    /// Steps exactly one frame. Stepping requires a paused player.
    func step(_ count: Int) {
        guard let player, let item = player.currentItem else { return }
        pause()

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

// MARK: - Clip browser

struct ClipListView: View {
    let onSelect: (Clip) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var clips: [Clip] = []

    var body: some View {
        NavigationStack {
            Group {
                if clips.isEmpty {
                    ContentUnavailableView("No clips yet",
                                           systemImage: "video.slash",
                                           description: Text("Record a goal kick on the Record tab."))
                } else {
                    List {
                        ForEach(clips) { clip in
                            Button {
                                onSelect(clip)
                                dismiss()
                            } label: {
                                VStack(alignment: .leading, spacing: 3) {
                                    Text(clip.name)
                                        .font(.system(.subheadline, design: .monospaced))
                                    Text("\(clip.created.formatted(date: .abbreviated, time: .standard))  ·  \(clip.sizeDescription)")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                    // A clip with no ball size cannot be
                                    // measured, so it is called out rather
                                    // than left looking like the others.
                                    Text(clip.ballDescription)
                                        .font(.caption)
                                        .foregroundStyle(clip.ballSize == nil ? .orange : .secondary)
                                }
                            }
                        }
                        .onDelete { offsets in
                            for index in offsets {
                                ClipStore.delete(clips[index])
                            }
                            clips = ClipStore.clips()
                        }
                    }
                }
            }
            .navigationTitle("Clips")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
                if !clips.isEmpty {
                    ToolbarItem(placement: .primaryAction) {
                        EditButton()
                    }
                }
            }
        }
        .onAppear {
            clips = ClipStore.clips()
        }
    }
}

// MARK: - Screen

struct ReviewView: View {

    @StateObject private var review = ReviewPlayer()
    @State private var showingClips = false
    @State private var controlsVisible = true
    @State private var hideTask: Task<Void, Never>?

    private let speeds: [Double] = [1.0, 0.5, 0.25, 0.125]

    var body: some View {
        ZStack {
            Color.black
                .ignoresSafeArea()

            if let player = review.player {
                PlayerSurface(player: player)
                    .ignoresSafeArea()
            } else {
                emptyState
            }

            VStack {
                Spacer()
                if controlsVisible {
                    controlPanel
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
        // contentShape makes the whole area tappable, including the black
        // bars beside a portrait video.
        .contentShape(Rectangle())
        .onTapGesture {
            if controlsVisible {
                hideTask?.cancel()
                withAnimation(.easeInOut(duration: 0.2)) { controlsVisible = false }
            } else {
                revealControls()
            }
        }
        .sheet(isPresented: $showingClips) {
            ClipListView { clip in
                Task {
                    await review.load(url: clip.url)
                    revealControls()
                }
            }
        }
        .onDisappear {
            hideTask?.cancel()
        }
    }

    // MARK: Auto-hide

    /// Shows the controls and restarts the idle countdown. Called on every
    /// interaction so the panel never vanishes mid-adjustment.
    private func revealControls() {
        withAnimation(.easeInOut(duration: 0.2)) { controlsVisible = true }
        hideTask?.cancel()
        // Keep the panel up when there is no clip, or the Choose clip
        // button would disappear with no obvious way back.
        guard review.player != nil else { return }
        hideTask = Task {
            try? await Task.sleep(for: .seconds(3))
            guard !Task.isCancelled else { return }
            withAnimation(.easeInOut(duration: 0.3)) { controlsVisible = false }
        }
    }

    // MARK: Pieces

    private var emptyState: some View {
        VStack(spacing: 12) {
            Image(systemName: "video.badge.plus")
                .font(.system(size: 44))
                .foregroundStyle(.white.opacity(0.5))
            Text("Choose a clip to review")
                .foregroundStyle(.white.opacity(0.6))
        }
    }

    private var controlPanel: some View {
        VStack(spacing: 10) {
            if review.player != nil {
                readouts
                scrubBar
                transportRow
                speedRow
                loopRow
            } else {
                Text(review.status)
                    .font(.system(.caption, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.8))
            }

            Button {
                revealControls()
                showingClips = true
            } label: {
                Label(review.player == nil ? "Choose clip" : "Choose another clip",
                      systemImage: "list.bullet.rectangle")
                    .font(.subheadline)
            }
            .buttonStyle(.bordered)
            .tint(.white)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 12)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
        .environment(\.colorScheme, .dark)
        .padding(.horizontal, 12)
        .padding(.bottom, 6)
    }

    private var readouts: some View {
        VStack(spacing: 2) {
            Text("frame \(review.frameIndex) of \(review.totalFrames)  ·  \(review.currentTime, specifier: "%.3f") s")
                .font(.system(.caption, design: .monospaced))
                .foregroundStyle(.green)
            Text(review.status)
                .font(.system(.caption2, design: .monospaced))
                .foregroundStyle(.white.opacity(0.65))
            if let start = review.loopStart, let end = review.loopEnd {
                Text("loop \(start, specifier: "%.3f") → \(end, specifier: "%.3f") s")
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundStyle(review.isLooping ? .green : .white.opacity(0.5))
            }
        }
    }

    private var scrubBar: some View {
        Slider(
            value: Binding(
                get: { min(review.currentTime, review.duration) },
                set: { review.scrub(to: $0) }
            ),
            // A zero-width range is invalid, so the duration is floored.
            in: 0...max(review.duration, 0.001),
            onEditingChanged: { editing in
                if editing {
                    review.beginScrub()
                } else {
                    review.endScrub()
                }
                revealControls()
            }
        )
        .tint(.white)
    }

    private var transportRow: some View {
        HStack(spacing: 20) {
            transportButton("backward.end.fill", size: 22) { review.restart() }
            transportButton("backward.frame.fill", size: 24) { review.step(-1) }
            transportButton(review.isPlaying && review.isReversing
                            ? "pause.circle.fill" : "play.circle.fill",
                            size: 34) { review.toggleReverse() }
                .rotation3DEffect(.degrees(review.isPlaying && review.isReversing ? 0 : 180),
                                  axis: (x: 0, y: 1, z: 0))
            transportButton(review.isPlaying && !review.isReversing
                            ? "pause.circle.fill" : "play.circle.fill",
                            size: 42) { review.togglePlay() }
            transportButton("forward.frame.fill", size: 24) { review.step(1) }
        }
        .foregroundStyle(.white)
    }

    private var loopRow: some View {
        HStack(spacing: 8) {
            loopButton("In", active: review.loopStart != nil) { review.markIn() }
            loopButton("Out", active: review.loopEnd != nil) { review.markOut() }
            loopButton(review.isLooping ? "Loop on" : "Loop",
                       active: review.isLooping) { review.toggleLoop() }
            loopButton("Clear", active: false) { review.clearLoop() }
        }
    }

    private func loopButton(_ title: String,
                            active: Bool,
                            action: @escaping () -> Void) -> some View {
        Button {
            action()
            revealControls()
        } label: {
            Text(title)
                .font(.system(.caption, design: .monospaced))
                .frame(maxWidth: .infinity)
                .padding(.vertical, 6)
                .background(active ? .green.opacity(0.85) : .white.opacity(0.15),
                            in: RoundedRectangle(cornerRadius: 8))
                .foregroundStyle(active ? .black : .white)
        }
    }

    private func transportButton(_ symbol: String,
                                 size: CGFloat,
                                 action: @escaping () -> Void) -> some View {
        Button {
            action()
            revealControls()
        } label: {
            Image(systemName: symbol)
                .font(.system(size: size))
        }
    }

    private var speedRow: some View {
        HStack(spacing: 8) {
            ForEach(speeds, id: \.self) { speed in
                Button {
                    review.setSpeed(speed)
                    revealControls()
                } label: {
                    Text(label(for: speed))
                        .font(.system(.footnote, design: .monospaced))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
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
        case 0.125: return "1/8"
        default: return "\(speed)×"
        }
    }
}

#Preview {
    ReviewView()
}
