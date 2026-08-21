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
import UniformTypeIdentifiers

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

/// The video surface, with pinch to zoom and pan while zoomed.
///
/// Built on `UIScrollView` rather than SwiftUI's `MagnifyGesture` and
/// `DragGesture`. Zooming is more than a scale factor: the pan has to stay
/// inside the content, the two gestures have to compose without fighting, a
/// zoomed picture has to stay put while the video steps frame by frame, and
/// letting go should settle rather than stop dead. `UIScrollView` has done all
/// of that since 2007, and reimplementing it in gesture callbacks means
/// reimplementing the edge cases too.
///
/// **Zoom is presentation only.** Measurement reads the stored pixels; nothing
/// here touches them, and a zoomed review changes no number.
///
/// A Swift note, since this pattern recurs: `UIViewRepresentable` is the
/// bridge from UIKit into SwiftUI. `makeUIView` builds the view once,
/// `updateUIView` runs whenever SwiftUI state changes, and the `Coordinator`
/// is where delegate callbacks live — UIKit talks to it, not to the struct,
/// because the struct is a value that SwiftUI recreates constantly.
// MARK: - Telestration

/// Yellow strokes drawn over the video, which stay put while it plays.
///
/// **Strokes are stored normalised to the picture, not to the screen.** A
/// point is kept as a fraction of the video's own rectangle — (0.5, 0.5) is
/// the middle of the picture whatever the zoom, the orientation, or the size
/// of the letterbox bars around it. Screen coordinates would have been less
/// code and wrong: a circle drawn around the plant foot would slide off it the
/// moment the coach zoomed in, and turning the phone would scatter every line.
///
/// Line width is normalised the same way, so a stroke drawn while zoomed in
/// does not become a fat band when zoomed back out. The annotation behaves as
/// though painted onto the video itself.
final class DrawingCanvasView: UIView {

    struct Stroke {
        /// Points as fractions of the picture rectangle, 0...1.
        var points: [CGPoint]
        /// Line width as a fraction of the picture's width.
        var width: CGFloat
    }

    private(set) var strokes: [Stroke] = []
    private var current: Stroke?

    /// Where the picture actually is, letterbox bars excluded.
    var pictureRect: CGRect = .zero {
        didSet { if pictureRect != oldValue { setNeedsDisplay() } }
    }

    /// Current magnification, so a stroke drawn zoomed in comes out the same
    /// apparent thickness as one drawn zoomed out.
    var zoom: CGFloat = 1

    /// Thickness the coach should see, in points, before zoom is accounted for.
    var targetWidth: CGFloat = 4

    var onStrokesChanged: ((Bool) -> Void)?

    private var baseScaleFactor: CGFloat = 0

    override init(frame: CGRect) {
        super.init(frame: frame)
        backgroundColor = .clear
        isOpaque = false
        // One finger, one line. Without this a second finger extends the same
        // stroke from wherever it lands.
        isMultipleTouchEnabled = false
    }

    required init?(coder: NSCoder) {
        fatalError("DrawingCanvasView is created in code, never from a nib")
    }

    // MARK: Drawing

    /// Deliberately silent: this is driven from `updateUIView`, and calling
    /// back into SwiftUI state from inside a view update is what produces
    /// "Modifying state during view update" at runtime. Whoever asked for the
    /// clear already knows there are no strokes left.
    func clear() {
        strokes.removeAll()
        current = nil
        setNeedsDisplay()
    }

    /// Re-renders at the zoomed resolution rather than magnifying an image
    /// drawn for 1×, which is what keeps lines sharp at high zoom.
    func applyZoom(_ newZoom: CGFloat) {
        zoom = newZoom
        if baseScaleFactor == 0 { baseScaleFactor = contentScaleFactor }
        contentScaleFactor = baseScaleFactor * max(1, newZoom)
        setNeedsDisplay()
    }

    override func draw(_ rect: CGRect) {
        guard pictureRect.width > 0, let context = UIGraphicsGetCurrentContext() else { return }

        context.setStrokeColor(UIColor.systemYellow.cgColor)
        context.setFillColor(UIColor.systemYellow.cgColor)
        context.setLineCap(.round)
        context.setLineJoin(.round)

        for stroke in strokes + (current.map { [$0] } ?? []) {
            let width = stroke.width * pictureRect.width
            let points = stroke.points.map(denormalise)

            guard let first = points.first else { continue }

            if points.count == 1 {
                // A tap should leave a mark rather than nothing at all.
                context.fillEllipse(in: CGRect(x: first.x - width / 2,
                                               y: first.y - width / 2,
                                               width: width, height: width))
                continue
            }

            context.setLineWidth(width)
            context.move(to: first)
            for point in points.dropFirst() { context.addLine(to: point) }
            context.strokePath()
        }
    }

    // MARK: Touches

    override func touchesBegan(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first, pictureRect.width > 0 else { return }
        let width = (targetWidth / max(zoom, 0.01)) / pictureRect.width
        current = Stroke(points: [normalise(touch.location(in: self))], width: width)
        setNeedsDisplay()
    }

    override func touchesMoved(_ touches: Set<UITouch>, with event: UIEvent?) {
        guard let touch = touches.first, current != nil else { return }

        // Coalesced touches are the ones the system captured between screen
        // refreshes. Apple Pencil reports far faster than 60 Hz, and ignoring
        // them turns a smooth arc into a chain of visible straight segments.
        let moves = event?.coalescedTouches(for: touch) ?? [touch]
        for move in moves {
            current?.points.append(normalise(move.location(in: self)))
        }
        setNeedsDisplay()
    }

    override func touchesEnded(_ touches: Set<UITouch>, with event: UIEvent?) {
        finishStroke()
    }

    override func touchesCancelled(_ touches: Set<UITouch>, with event: UIEvent?) {
        current = nil
        setNeedsDisplay()
    }

    private func finishStroke() {
        guard let stroke = current else { return }
        strokes.append(stroke)
        current = nil
        setNeedsDisplay()
        onStrokesChanged?(true)
    }

    // MARK: Coordinates

    private func normalise(_ point: CGPoint) -> CGPoint {
        CGPoint(x: (point.x - pictureRect.minX) / pictureRect.width,
                y: (point.y - pictureRect.minY) / pictureRect.height)
    }

    private func denormalise(_ point: CGPoint) -> CGPoint {
        CGPoint(x: pictureRect.minX + point.x * pictureRect.width,
                y: pictureRect.minY + point.y * pictureRect.height)
    }
}

/// A scroll view that keeps the video sized to itself.
///
/// This lives in `layoutSubviews` rather than in `updateUIView` because
/// SwiftUI runs `updateUIView` when *state* changes, which is not necessarily
/// after it has decided how big this view is — on first appearance the bounds
/// can still be zero. `layoutSubviews` runs when the size is real, and again
/// on every rotation.
final class ZoomingScrollView: UIScrollView {
    let videoView = PlayerContainerView()
    /// A subview of videoView, so the scroll view's zoom transform applies to
    /// the strokes as well as to the picture — annotations track the video for
    /// free rather than needing their own transform maintained alongside.
    let canvas = DrawingCanvasView(frame: .zero)
    private var lastSize: CGSize = .zero

    override func layoutSubviews() {
        super.layoutSubviews()

        if bounds.size != .zero, bounds.size != lastSize {
            lastSize = bounds.size

            // Returning to fit on a size change is deliberate. The zooming
            // view's frame is what UIScrollView transforms, so resizing it
            // mid-zoom fights the gesture — and when the phone is turned,
            // landing back at the whole picture is what a coach expects.
            setZoomScale(1, animated: false)
            videoView.frame = CGRect(origin: .zero, size: bounds.size)
            contentSize = bounds.size
            contentInset = .zero
        }

        syncCanvas()
    }

    /// Keeps the canvas over the picture and tells it where the picture is.
    ///
    /// `videoRect` reports zero until the player item has loaded and reported
    /// its dimensions, so this is called from layout and again whenever
    /// SwiftUI updates — whichever happens after the video is ready.
    func syncCanvas() {
        canvas.frame = videoView.bounds
        let rect = videoView.playerLayer.videoRect
        canvas.pictureRect = rect.isEmpty ? videoView.bounds : rect
    }
}

struct ZoomableVideoView: UIViewRepresentable {
    let player: AVPlayer
    /// Bumped by the parent to demand a return to fit. A counter rather than a
    /// boolean so that repeated resets each register, and so the parent never
    /// has to reach in and clear a flag afterwards.
    let resetToken: Int
    @Binding var zoomScale: CGFloat
    let onSingleTap: () -> Void
    /// When on, the canvas takes every touch and the scroll view takes none.
    let isDrawing: Bool
    /// Bumped by the parent to wipe the strokes, same counter trick as reset.
    let clearToken: Int
    let onStrokesChanged: (Bool) -> Void

    func makeUIView(context: Context) -> ZoomingScrollView {
        let scrollView = ZoomingScrollView()
        scrollView.delegate = context.coordinator
        scrollView.minimumZoomScale = 1
        scrollView.maximumZoomScale = 8
        scrollView.showsHorizontalScrollIndicator = false
        scrollView.showsVerticalScrollIndicator = false
        scrollView.backgroundColor = .black
        scrollView.contentInsetAdjustmentBehavior = .never

        let videoView = scrollView.videoView
        videoView.playerLayer.player = player
        videoView.playerLayer.videoGravity = .resizeAspect
        videoView.backgroundColor = .black
        scrollView.addSubview(videoView)
        videoView.addSubview(scrollView.canvas)

        context.coordinator.videoView = videoView
        context.coordinator.scrollView = scrollView

        let doubleTap = UITapGestureRecognizer(
            target: context.coordinator,
            action: #selector(Coordinator.handleDoubleTap(_:)))
        doubleTap.numberOfTapsRequired = 2
        scrollView.addGestureRecognizer(doubleTap)

        let singleTap = UITapGestureRecognizer(
            target: context.coordinator,
            action: #selector(Coordinator.handleSingleTap))
        singleTap.numberOfTapsRequired = 1
        // Without this, the first tap of a double tap toggles the controls on
        // its way to zooming.
        singleTap.require(toFail: doubleTap)
        scrollView.addGestureRecognizer(singleTap)

        context.coordinator.singleTap = singleTap
        context.coordinator.doubleTap = doubleTap

        return scrollView
    }

    func updateUIView(_ scrollView: ZoomingScrollView, context: Context) {
        let coordinator = context.coordinator
        coordinator.onSingleTap = onSingleTap
        coordinator.zoomScale = $zoomScale
        scrollView.videoView.playerLayer.player = player
        scrollView.canvas.onStrokesChanged = onStrokesChanged

        // videoRect is only known once the item has loaded, which is usually
        // after the first layout pass.
        scrollView.syncCanvas()

        // Drawing mode owns the surface outright. Leaving pan or pinch live
        // would make a one-finger drag ambiguous — draw a line, or scroll the
        // picture? — and the tap recognisers would toggle the controls on
        // every dot the coach places.
        scrollView.canvas.isUserInteractionEnabled = isDrawing
        scrollView.isScrollEnabled = !isDrawing
        scrollView.pinchGestureRecognizer?.isEnabled = !isDrawing
        coordinator.singleTap?.isEnabled = !isDrawing
        coordinator.doubleTap?.isEnabled = !isDrawing

        if coordinator.lastClearToken != clearToken {
            coordinator.lastClearToken = clearToken
            scrollView.canvas.clear()
        }

        if coordinator.lastResetToken != resetToken {
            coordinator.lastResetToken = resetToken
            scrollView.setZoomScale(1, animated: true)
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    final class Coordinator: NSObject, UIScrollViewDelegate {
        weak var scrollView: UIScrollView?
        var videoView: PlayerContainerView?
        var onSingleTap: () -> Void = {}
        var zoomScale: Binding<CGFloat>?
        var lastResetToken = 0
        var lastClearToken = 0
        weak var singleTap: UITapGestureRecognizer?
        weak var doubleTap: UITapGestureRecognizer?

        func viewForZooming(in scrollView: UIScrollView) -> UIView? {
            videoView
        }

        func scrollViewDidZoom(_ scrollView: UIScrollView) {
            centreContent(in: scrollView)
            let scale = scrollView.zoomScale
            // Redraw the strokes at the zoomed resolution so they stay sharp
            // rather than being magnified as an image.
            (scrollView as? ZoomingScrollView)?.canvas.applyZoom(scale)
            // Published asynchronously: this fires during UIKit's layout, and
            // writing SwiftUI state from inside a layout pass is what produces
            // "Modifying state during view update" at runtime.
            DispatchQueue.main.async { [weak self] in
                self?.zoomScale?.wrappedValue = scale
            }
        }

        @objc func handleSingleTap() {
            onSingleTap()
        }

        @objc func handleDoubleTap(_ recognizer: UITapGestureRecognizer) {
            guard let scrollView, let videoView else { return }

            if scrollView.zoomScale > scrollView.minimumZoomScale * 1.01 {
                scrollView.setZoomScale(scrollView.minimumZoomScale, animated: true)
                return
            }

            // Zoom in on what was tapped rather than on the middle of the
            // screen — the coach is pointing at the ball, not at the centre.
            let target: CGFloat = 3
            let point = recognizer.location(in: videoView)
            let size = CGSize(width: scrollView.bounds.width / target,
                              height: scrollView.bounds.height / target)
            scrollView.zoom(to: CGRect(x: point.x - size.width / 2,
                                       y: point.y - size.height / 2,
                                       width: size.width,
                                       height: size.height),
                            animated: true)
        }

        /// Keeps the picture centred instead of pinned to the top-left when it
        /// is smaller than the scroll view, which is what it looks like during
        /// a pinch that bounces back.
        private func centreContent(in scrollView: UIScrollView) {
            guard let videoView else { return }
            let horizontal = max(0, (scrollView.bounds.width - videoView.frame.width) / 2)
            let vertical = max(0, (scrollView.bounds.height - videoView.frame.height) / 2)
            scrollView.contentInset = UIEdgeInsets(top: vertical, left: horizontal,
                                                   bottom: vertical, right: horizontal)
        }
    }
}

// MARK: - Clip browser

struct ClipListView: View {
    let onSelect: (Clip) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var clips: [Clip] = []
    @State private var showingImporter = false
    @State private var importError: String?

    var body: some View {
        NavigationStack {
            Group {
                if clips.isEmpty {
                    ContentUnavailableView(
                        "No clips yet",
                        systemImage: "video.slash",
                        description: Text("Record a goal kick on the Record tab, "
                                          + "or use Import to bring one in from Files."))
                } else {
                    List {
                        ForEach(clips) { clip in
                            row(for: clip)
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
                ToolbarItemGroup(placement: .primaryAction) {
                    Button("Import", systemImage: "square.and.arrow.down") {
                        showingImporter = true
                    }
                    if !clips.isEmpty {
                        EditButton()
                    }
                }
            }
        }
        // The reliable way in. iOS decides for itself where an AirDropped
        // movie lands — usually Files, sometimes Photos — and never offers a
        // choice, so waiting to be handed a clip does not work. Reaching out
        // and fetching one does, wherever it ended up.
        .fileImporter(isPresented: $showingImporter,
                      allowedContentTypes: [.quickTimeMovie, .movie],
                      allowsMultipleSelection: true,
                      onCompletion: receive)
        .alert("Could not import",
               isPresented: Binding(get: { importError != nil },
                                    set: { if !$0 { importError = nil } })) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(importError ?? "")
        }
        .onAppear {
            clips = ClipStore.clips()
        }
    }

    private func row(for clip: Clip) -> some View {
        HStack {
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
                    // A clip with no ball size cannot be measured, so it is
                    // called out rather than left looking like the others.
                    Text(clip.ballDescription)
                        .font(.caption)
                        .foregroundStyle(clip.ballSize == nil ? .orange : .secondary)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .contentShape(Rectangle())
            }

            // Sends the file itself, so AirDrop copies it byte for byte and
            // the frame timing survives. Both buttons need an explicit style:
            // inside a List row, the default makes the whole row one tap
            // target and the share button would never be reachable.
            ShareLink(item: clip.url) {
                Image(systemName: "square.and.arrow.up")
                    .font(.body)
            }
        }
        .buttonStyle(.borderless)
    }

    private func receive(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            var failures: [String] = []
            for url in urls {
                do {
                    try ClipStore.importClip(from: url)
                } catch {
                    failures.append("\(url.lastPathComponent): \(error.localizedDescription)")
                }
            }
            clips = ClipStore.clips()
            if !failures.isEmpty {
                importError = failures.joined(separator: "\n")
            }
        case .failure(let error):
            importError = error.localizedDescription
        }
    }
}

// MARK: - Screen

struct ReviewView: View {

    @StateObject private var review = ReviewPlayer()
    @State private var showingClips = false
    @State private var controlsVisible = true
    @State private var hideTask: Task<Void, Never>?
    @State private var zoomScale: CGFloat = 1
    @State private var zoomResetToken = 0
    @State private var isDrawing = false
    @State private var hasStrokes = false
    @State private var clearToken = 0

    private let speeds: [Double] = [1.0, 0.5, 0.25, 0.125]

    var body: some View {
        ZStack {
            Color.black
                .ignoresSafeArea()

            if let player = review.player {
                ZoomableVideoView(player: player,
                                  resetToken: zoomResetToken,
                                  zoomScale: $zoomScale,
                                  onSingleTap: toggleControls,
                                  isDrawing: isDrawing,
                                  clearToken: clearToken,
                                  onStrokesChanged: { hasStrokes = $0 })
                    .ignoresSafeArea()
            } else {
                emptyState
                    // contentShape makes the whole area tappable, including
                    // the black bars beside a portrait video.
                    .contentShape(Rectangle())
                    .onTapGesture(perform: toggleControls)
            }

            // Always on screen, not in the auto-hiding panel. Drawing is a
            // mode, and a mode the coach cannot see they are in is a trap —
            // they would wonder why the video had stopped responding to a
            // drag. The zoom badge is here for the same reason: a magnified
            // picture with the controls hidden looks like footage that was
            // simply filmed close up.
            if review.player != nil {
                VStack {
                    HStack(alignment: .top) {
                        drawingControls
                        Spacer()
                        if zoomScale > 1.01 { zoomBadge }
                    }
                    Spacer()
                }
                .padding(.horizontal, 14)
                .padding(.top, 8)
            }

            VStack {
                Spacer()
                if controlsVisible {
                    controlPanel
                        .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
        .sheet(isPresented: $showingClips) {
            ClipListView { clip in
                Task {
                    await review.load(url: clip.url)
                    // A new clip starts clean. Carrying one clip's zoom into
                    // the next would leave the coach looking at a magnified
                    // corner of footage they have not seen yet, and carrying
                    // its annotations over would be worse — lines drawn on one
                    // kicker's technique, floating over another's.
                    zoomResetToken += 1
                    clearToken += 1
                    hasStrokes = false
                    isDrawing = false
                    revealControls()
                }
            }
        }
        .onDisappear {
            hideTask?.cancel()
        }
    }

    // MARK: Telestration

    /// Drawing toggle, and a clear button that appears once there is
    /// something to clear. Kept deliberately small — they sit permanently
    /// over the picture, and the picture is the point.
    private var drawingControls: some View {
        HStack(spacing: 8) {
            Button {
                withAnimation(.easeInOut(duration: 0.15)) { isDrawing.toggle() }
            } label: {
                roundIcon("scribble.variable", active: isDrawing)
            }
            .accessibilityLabel(isDrawing ? "Stop drawing" : "Draw on the video")

            if hasStrokes {
                Button {
                    clearToken += 1
                    hasStrokes = false
                } label: {
                    roundIcon("trash", active: false)
                }
                .accessibilityLabel("Clear drawing")
                .transition(.scale.combined(with: .opacity))
            }
        }
        .animation(.easeInOut(duration: 0.15), value: hasStrokes)
    }

    private func roundIcon(_ symbol: String, active: Bool) -> some View {
        Image(systemName: symbol)
            .font(.system(size: 14, weight: .semibold))
            .frame(width: 34, height: 34)
            .background(active ? Color.yellow : Color.black.opacity(0.65),
                        in: Circle())
            .foregroundStyle(active ? Color.black : Color.white)
    }

    // MARK: Zoom

    /// Current magnification, and a way back to fit. Tapping it resets.
    private var zoomBadge: some View {
        Button {
            zoomResetToken += 1
        } label: {
            HStack(spacing: 6) {
                Image(systemName: "arrow.down.right.and.arrow.up.left")
                Text(String(format: "%.1f×", zoomScale))
                    .monospacedDigit()
            }
            .font(.caption.weight(.medium))
            .foregroundStyle(.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 8)
            .background(.black.opacity(0.65), in: Capsule())
        }
        .accessibilityLabel("Reset zoom")
    }

    // MARK: Auto-hide

    private func toggleControls() {
        if controlsVisible {
            hideTask?.cancel()
            withAnimation(.easeInOut(duration: 0.2)) { controlsVisible = false }
        } else {
            revealControls()
        }
    }

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
