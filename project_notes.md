# Goalkeeper Training App

## Purpose of the project_notes.md file

This project_notes.md file serves as the single source of truth for this project. It should be deferred to whenever you are making decisions.

This document should be kept up to date at all times so that a new conversation can be started with any LLM and have the complete background for the project, the current state, and next steps. It should include final decisions that have been made as well as open questions.

It records **current state only**. Decisions that were later reversed are removed rather than preserved as history; what survives is the decision now in force and the reasoning that still applies.

## LLM Start Here

- If you are an LLM, then this document should provide you with all previous decisions that have been made and also give you all necessary background information.
- Your function is to provide technical guidance.
- If anything we are working on violates United States laws or laws that are applicable in the State of Texas, please bring them to my attention. We will not violate any laws that apply in those jurisdictions.
- You will only do the things asked of you, you will not exceed them or fail to do them.
- Do any requests one step at a time and wait for confirmation before moving on.
- **When you need me to choose between options, present them as a clickable multiple-choice prompt rather than as a question in prose.** In Claude Code this is the `AskUserQuestion` tool. Seeing the options laid out side by side with what each one means is what makes the decision legible — a paragraph asking me to "confirm X and Y" often does not make clear what I am actually being asked or what turns on it. State a recommendation in the option label where you have one.
  - **This applies every single time, without exception.** It is not reserved for large or architectural decisions.
  - **It explicitly includes permission requests** — asking to edit `project_notes.md`, asking to change project configuration, asking whether to proceed to the next step. Those are choices and they go in the tool, not in prose.
  - **It applies even when the answer seems obviously yes,** and even when you are asking about two or three things at once. Multiple pending questions means multiple questions in the prompt, not a numbered list in the message body.
  - **Never end a message with a prose question asking me to approve, confirm, or choose.** If you find yourself writing "Would you like me to..." or "Two things I'd like your permission for," stop and use the tool instead.
- When asked to write any code (e.g. markdown, swift, html, python, java, etc.) write whatever fully in that language. Do not write part of it and expect the user to convert any part.
- Do not offer additional steps without being asked.
- Never execute code. I will always execute code myself.

### My Experience Level — calibrate your instructions to this

I am an experienced developer, but my background is **Python**. **I have never written Swift and I have never built an iOS app.** Assume no prior knowledge of Swift syntax, Xcode, Apple's frameworks, or iOS platform conventions.

What this means for how you should write to me:

- **Be very detailed.** Do not skip steps and do not assume I know where something lives.
- **Xcode is a GUI and I do not know my way around it.** Give click-by-click navigation — which menu, which sidebar, which tab, which keyboard shortcut. Never say "set that in Build Settings" without telling me how to get to Build Settings.
- **Explain Swift idioms the first time they appear** in code you give me — optionals and unwrapping, `guard`, value vs. reference types, protocols, closures, property wrappers, `async`/`await`, error handling. A Python developer will not guess these.
- **Explain Apple framework concepts and why they exist**, not just which API to call. The mental model matters more than the method name.
- **Do not explain general programming.** I know data structures, concurrency concepts, version control, debugging, and how to read a stack trace. The gap is Swift, Xcode, and Apple's platform — not programming itself. Explaining what a for-loop does wastes both our time.
- **When something fails, tell me how to find the actual error message**, not just the fix you assume applies. I do not yet know where Xcode hides its errors.

### Code Delivery Rule — read this before writing any code

The rule differs by file type.

**Swift source files inside the Xcode project: edit them directly.** You do not need to ask each time. Write the change, then explain in chat what you changed and why. This applies to `.swift` files under `GoalKick/`. Rationale: source files grow long, and most changes touch a few lines in the middle of an existing file. Reprinting whole files into chat for me to re-paste is slow and is where copy-paste errors come from. Git history and undo are the backstop.

**`project_notes.md`: never edit without my explicit permission, given in chat, for that specific edit.**

- **Explicit permission means I say so directly** — for example, "update Current State," "add that to the file." Nothing else counts.
- **Asking for permission is not receiving it.** Do not ask and then proceed. Do not treat silence, a follow-up question, or a general approval of an approach as consent.
- **These are NOT permission:** me asking "what is the next step?", me describing a problem, me approving a design or an approach, me saying a plan sounds good, or me having granted permission for an earlier, different edit. Permission is per-edit and does not carry forward.
- If you believe an edit to this file is genuinely necessary, state why and stop. Wait for me to say yes.

**Any other file — new files of any kind, project configuration, build settings: ask first.** Creating files is not covered by the Swift editing permission above.

**Whatever the destination, deliver code complete and in full.** Never partial, never with placeholders for me to fill in.

## Project Goal

The project goal is to create an iOS training app for goalkeepers. We will begin with one deliverable, but add more as we go. I want to iterate product improvements and features. But success is completing each deliverable as we go.

### Deliverable 1

Build an iOS app that measures, from video captured by the device, a soccer ball's **velocity**, **launch angle**, and **theoretical carry distance / max height**.

End state: process a single video containing a goal kick and produce goalkeeper performance metrics. You will only know the size of the ball as input. We will use standard soccer ball sizes — for example, Size 4.

For ease of use, the user of the app is called the **coach** and the goalkeeper is called the **kicker**. The coach should be able to show the kicker the video as well as the statistics.

The coach should be able to do the following with the video:
- Pause at any time
- Slow playback to the following speeds:
  - 1/2
  - 1/4
- Step through the video frame by frame using advance and reverse buttons

**Clips are stored inside the app, in its own Documents directory. Nothing is written to Photos.** What is stored is the raw capture — not a version with tracking or metrics rendered onto it. Exporting to Photos is out of scope for now.

The reason is not preference. Saving a 240 fps clip to Photos makes iOS classify it as slow motion, and reading it back returns a retimed 30 fps file — every frame present, but timestamps 8× too far apart. Photos was never a safe store for measurement footage, so the app owns its own.

For Deliverable 1, success is being able to review the video and get metrics.

## Tech Stack

The app is built as a **native iOS app in Swift**. This is decided. The requirements in Deliverable 1 depend on platform capabilities that only native access provides: high-frame-rate capture (120–240 fps), camera optics data for scale calibration, frame-accurate playback stepping, and per-frame presentation timestamps. A web or cross-platform stack cannot meet them.

| Layer | Choice |
|---|---|
| Language | Swift 5 language mode (`SWIFT_VERSION = 5.0`), with `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` — the Xcode 26 default. Deliberately **not** Swift 6 strict concurrency. See the note below. |
| UI | SwiftUI, with `UIViewRepresentable` wrappers for camera preview and `AVPlayerLayer` |
| Capture | AVFoundation — `AVCaptureSession`, high-speed format selection, video stabilization forced off (it warps geometry and would corrupt measurement) |
| Ball tracking | Vision (`VNTrackObjectRequest`) first; a Core ML detector if Vision's tracker proves insufficient |
| Numerics | Accelerate / vImage; Metal only if profiling demands it |
| Playback | `AVPlayer`, driven by setting `rate` directly for slow and reverse playback, and `AVPlayerItem.step(byCount:)` for frame stepping |
| Camera attitude | CoreMotion, to correct launch angle for camera tilt |
| Storage | The app's own `Documents/Clips/`, managed by `ClipStore`. The only copy, and the only source with true timing. Nothing is written to Photos. |
| Dependencies | None third-party |

**Scale calibration:** the known ball diameter plus the camera's **focal length in pixels** is how real-world distance is recovered from apparent pixel size. Focal length is the hard requirement; the intrinsic matrix is only one of two ways to obtain it.

- **Intrinsic matrix** — delivered per frame, gives true focal length under current focus plus the optical center. Better, but unavailable at 240 fps on the test device.
- **Field of view** — `AVCaptureDevice.Format.videoFieldOfView` is published for every format, including the 240 fps ones. Focal length follows as `fx = (imageWidth / 2) / tan(fieldOfView / 2)`. Nominal rather than measured, but a goal kick is filmed at 20–40 m where the lens is effectively at infinity focus, so the nominal value is accurate.

**Known technical risk:** motion blur on a fast-moving ball at high frame rates may defeat Vision's built-in tracker and force a trained Core ML detector. The stack above supports either path.

**On Swift 6:** the decision to stay in Swift 5 mode stands, and was reconsidered deliberately after capture was working rather than allowed to lapse. Strict concurrency turns data-race issues into hard compile errors, and the next phase — passing `CMSampleBuffer` and `CVPixelBuffer` to Vision — is the worst area for that friction, since neither type is `Sendable` and the annotations are Apple's to fix, not ours. `SWIFT_VERSION` is a single build setting, so migrating later costs the same work on a more settled design. Revisit once tracking works.

## Current State

### What does NOT exist yet

**There is no measurement code of any kind.** No ball detection, no tracking, no velocity, no launch angle, no carry distance, no max height. Deliverable 1's actual metrics are entirely unstarted, and their feasibility has not been demonstrated.

What exists is everything *around* the measurement: a way to capture footage good enough to measure from, and a way to look at it frame by frame. Both are verified on hardware. Neither computes anything.

### Environment

- **Mac:** macOS 26, Xcode 26 from the Mac App Store, iOS 26 platform installed, command line tools pointed at Xcode.
- **Test device:** "Rocket's iPhone," paired over cable, Developer Mode enabled, developer certificate trusted.
- **Signing:** free Apple ID under a Personal Team (Robert Williams), automatic signing. Not enrolled in the paid Apple Developer Program.

Build, sign, install, and launch on the physical device are all confirmed working. Getting code onto the phone is a solved problem.

### Project

- **Location:** `/Users/rocket/Github/gk/GoalKick/`
- **Bundle identifier:** `com.rocket.GoalKick`
- **Targets:** `GoalKick`, `GoalKickTests`, `GoalKickUITests`
- **Configured as:** SwiftUI interface, Storage None, CloudKit off
- **Version control:** Git at the project root, pushed to `https://github.com/rgw3/gk` (private, remote `origin`, branch `main`). `.gitignore` covers Xcode noise; `xcuserdata` is untracked.
- **`project_notes.md` lives inside the project folder**, so the source of truth is versioned alongside the code.
- **`README.md`** exists at the project root as a public-facing overview. It restates parts of this file for a reader arriving from GitHub; **this file is authoritative** where the two differ.

| File | Contents |
|---|---|
| `ContentView.swift` | Tab bar container only |
| `RecordView.swift` | Capture screen: live preview, configuration picker, record button |
| `Recorder.swift` | `CaptureConfig`, `ClipStore`, capture session, format selection, orientation, recording, file verification |
| `ReviewView.swift` | Playback controller, transport, scrubbing, looping, frame stepping, clip browser |

**App icon:** a placeholder in `Assets.xcassets/AppIcon.appiconset/`, cropped from an illustration to the ball. Only the Any Appearance slot is filled; iOS derives dark and tinted. To be revisited.

### Camera capability, measured on the test device

The back camera exposes **70 formats**. Every one was applied in turn, with video stabilization explicitly disabled, and its connection queried for intrinsic matrix support. Those relevant to measurement:

| Resolution | Max fps | Intrinsics | fx from FOV |
|---|---|---|---|
| 1920 × 1080 | 240 | no | ≈ 1,260 px |
| 1280 × 720 | 240 | no | ≈ 840 px |
| 4224 × 2240 | 120 | yes | ≈ 2,773 px |
| 3840 × 2160 | 120 | yes | ≈ 2,520 px |
| 1920 × 1080 | 120 | yes | ≈ 1,260 px |

**66 of 70 formats support intrinsic matrix delivery, and the 4 that do not are exactly the four 240 fps formats.** Intrinsics and 240 fps are mutually exclusive on this device. Stabilization was ruled out as the cause — it was off during the scan.

Field of view is 74.6° for both 1080p formats, so `fx ≈ 1,260 px` either way. The 240 fps format is not optically different; it simply will not report its matrix.

Formats that look duplicated when listed by dimensions and frame rate alone are genuinely distinct — they differ in pixel format, binning, HDR support, or field of view.

Note that a format *supporting* 240 fps is not the same as a session *running* at 240 fps. That requires setting `activeVideoMinFrameDuration` explicitly.

### Capture

Both configurations record and read back correctly, verified from the finished files rather than from what the camera was asked for:

| Selected | File contents |
|---|---|
| 1080p · 240 | 1920 × 1080 · 239.9 fps · 5.67 s · ~1361 frames |
| 4K · 120 | 3840 × 2160 · 119.9 fps · 6.56 s · ~787 frames |

Frame counts corroborate the rates in both cases, so the format survives recording and is not silently overridden.

**Reported rates are 239.9 and 119.9, not 240 and 120** — the NTSC-derived rates of 240 ÷ 1.001 and 120 ÷ 1.001. The 0.1% difference is negligible in itself, but it establishes that `nominalFrameRate` is a label rather than a measurement. **Δt must come from each frame's presentation timestamp, never from `1 / nominalFrameRate`.**

**Recording follows device orientation.** `AVCaptureDevice.RotationCoordinator` supplies `videoRotationAngleForHorizonLevelCapture`, applied to both the movie output connection and the preview layer. Without it the capture connection stays at its portrait default however the phone is held — the UI rotates and the pixels do not. Three details that each caused or would have caused a bug:

- The observation uses `.initial`, so the current orientation applies at launch rather than only after the first rotation.
- Rotation is not changed while recording, which would otherwise split orientation across one file.
- Rotation is re-applied after every format change, because switching configuration rebuilds the connection and silently resets it to portrait.

**Consequence for analysis:** clips carry a `preferredTransform` describing their rotation. The tracking code must apply it before treating pixel coordinates as physical. Getting this wrong would swap the trajectory's axes and turn launch angle into its complement.

**Concurrency.** Capture state (`session`, `movieOutput`, `device`, `activeConfig`) is confined to `sessionQueue` and marked `nonisolated(unsafe)`; published UI state is main-actor and written only through the `set(...)` helpers. `Recorder` is `@unchecked Sendable` — a promise backed by that queue confinement rather than a compiler-checked guarantee. This replaced a real data race where the capture path read main-actor state from a background queue.

### Storage

**Photos retimes high-frame-rate clips and cannot be used as a source of truth.** Saving a 240 fps clip to Photos makes iOS classify it as slow motion, and reading it back returns a **30 fps** file — exactly 240 ÷ 8, duration stretched 8×. Measured: a 768-frame clip came back as 768 frames at 30 fps over 23.6 s.

**Every frame survives the round trip; only the timestamps lie.** Nothing is lost, but Δt would read 1/30 s instead of 1/240 s, making every velocity 8× too slow with no visible symptom.

**Therefore the app owns its clips outright.** Recordings are written directly to `Documents/Clips/`, managed by `ClipStore`. **Nothing is written to Photos at all.** The review screen reads only from that directory — the Photos picker was removed rather than left available, because an input path that silently returns 8×-wrong timing is not something to leave next to a "choose clip" button.

Clips are deleted from the clip list, by swiping a row or via the Edit button. Nothing else prunes the directory, and 4K/120 runs roughly 6 MB per second, so this matters.

`NSPhotoLibraryAddUsageDescription` remains in the target's Info settings but is unused and inert, since the app no longer requests Photos access.

The app library is not visible in the Files app; `Documents` is private unless the project opts into file sharing.

### Review

All verified on the device:

- Playback and pause at 1×, 1/2, 1/4, and 1/8
- Frame-accurate stepping — `AVPlayerItem.step(byCount:)` advances exactly one frame per tap
- Restart, returning to frame 0 and staying paused
- A scrub bar for coarse positioning, with the step buttons for fine adjustment
- Section looping: mark In and Out, then repeat that stretch continuously. Marking Out before In swaps them rather than refusing.
- Continuous reverse playback at the selected speed. `canPlayReverse` is true for these clips, so the encoding supports backwards decode and no codec change is needed.
- Controls overlay the video and auto-hide after 3 seconds, so the picture fills the screen in both orientations. They never auto-hide when no clip is loaded, or the "Choose clip" button would vanish with no way back.

**1/8 is the rate at which a 240 fps clip shows every frame.** 240 ÷ 8 = 30 frames displayed per second. At 1× the display physically cannot show all 240, so frames are dropped and the reviewer is not seeing everything that was recorded. The equivalent for 4K/120 is 1/4. Slower than that repeats frames rather than revealing new ones.

**Seeking uses two modes, deliberately.** While the scrubber is dragged, seeks use infinite tolerance — "any nearby keyframe will do" — the cheapest seek available. On release, a zero-tolerance seek snaps to the exact frame. Restart does the same. One mode alone cannot give both a responsive drag and a frame-accurate resting position.

**Seeks are coalesced: at most one in flight, and only the newest target is kept.** A drag emits values far faster than AVPlayer can service them, and queueing every one makes the picture fall progressively behind the finger. Intermediate positions are dropped on purpose.

### Standing constraints from the free-tier account

- Builds signed under a Personal Team **stop launching after 7 days** and must be re-run from Xcode. Expected behavior, not a bug.
- TestFlight and App Store distribution are unavailable without the paid program ($99/year).
- A Personal Team is capped at **10 App IDs per 7-day period**, so bundle identifiers should be chosen deliberately rather than by trial and error.

## Next Steps

**Step 1 — Capture spike. COMPLETE.** High-speed capture, recording, and storage in the app's own library all work and are verified on the device. The one criterion that resolved differently: the step originally required confirming intrinsic matrix delivery. Intrinsics are unavailable at 240 fps, but the underlying requirement — obtaining focal length — is satisfied through field of view instead. The requirement was met; the originally stated mechanism was too narrow.

**Step 2 — Video review screen. COMPLETE.** Every playback control Deliverable 1 asks for — pause, 1/2 and 1/4 speed, frame-by-frame stepping — is verified on the device, along with 1/8 speed, restart, scrubbing, section looping, and reverse playback beyond the requirement.

**Step 3 — Ball tracking spike.** Detect and track the ball across frames of a real goal kick, and report its pixel position and apparent diameter per frame. Start with Vision's `VNTrackObjectRequest`; fall back to a trained Core ML detector if motion blur defeats it.

Done when a real goal kick clip yields a per-frame table of ball centre and diameter in pixels, covering the flight from contact to apex or beyond.

This is the largest remaining unknown in the project. Nothing about velocity, launch angle, or carry distance can be computed until it works, and it is the one part whose feasibility has not been demonstrated at all.

**Blocked on footage.** Step 3 cannot start without real goal kick clips. **Film several kicks with the app, and where possible film the same kick in both capture configurations** — that comparison is what settles the open question below.

Note that capture work cannot be validated in the iOS Simulator, which has no camera and exposes no real capture formats. Playback work can be.

## Open Questions

**Which capture configuration gives better metric accuracy: 1080p at 240 fps, or 4K at 120 fps?**

- **1080p at 240 fps** — roughly 12.5 cm of ball travel between frames at 30 m/s. Twice the trajectory samples, and the shorter per-frame exposure means less motion blur, which matters because blur inflates the apparent ball diameter and degrades the centroid. Calibrated from field of view; no intrinsic matrix available.
- **4K at 120 fps** — roughly 25 cm between frames, but four times the pixels across the ball, so a more precise diameter estimate, which propagates into distance and therefore into every metric. Intrinsic matrix available.

**Settle this by filming the same goal kick both ways once tracking exists**, not from first principles. The recorder offers both configurations so that comparison is possible.

**Related and unresolved:** the intrinsic matrix is delivered per frame to a live capture session and is **not stored in a recorded movie file**. Since Deliverable 1 analyses a saved video, using intrinsics at analysis time would require capturing them alongside the recording and storing them in a sidecar. If we do not do that, the practical calibration route is field of view for both configurations — which would substantially collapse the advantage of 4K/120 above.

## End of Document
