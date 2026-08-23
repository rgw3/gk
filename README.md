# GoalKick

An iOS app that measures goalkeeper kicking performance from video captured on the device.

The intent: point the camera at a goal kick, record at high frame rate, and get ball **velocity**, **launch angle**, and **theoretical carry distance / max height** — using nothing but the known physical size of the ball for scale.

That is the goal, not the current state. See Status.

## Status

Early development. **The app captures and reviews. The measurement works, but only as Python on a Mac, and its accuracy is not yet established.**

| Area | State |
|---|---|
| High frame rate capture | Working, verified on device |
| Ball size recorded per clip | Working on device; metadata round-trip unconfirmed |
| Clip storage in the app's own library | Working, verified on device |
| Getting clips off the device | Working, verified on device |
| Video review, frame stepping, zoom, telestration | Working, verified on device |
| Importing and sharing clips | Built, not yet verified on device |
| Ball detection and tracking | Working — Mac-side Python only |
| Metrics (velocity, angle, carry, apex) | Written — Mac-side Python only, accuracy unresolved |
| Any measurement inside the app | Not started |

**Ball detection works.** A stock COCO object detector finds the ball in every frame of a real kick, with no training data and no assumptions about its colour. That was the project's largest technical unknown and it is answered.

**The metrics are not yet trustworthy.** The pipeline fits gravity from the data as an independent check — nothing tells it that gravity is 9.81 — and across four runs it has come back between 3.5 and 12.3 m/s². The scatter straddles the true value rather than falling consistently short, so the method appears correct but imprecise. The dominant error is depth, which is recovered from the ball's apparent size; the fix is filming square to the kick, and it has not yet been tried.

`project_notes.md` in this repository is the single source of truth for decisions, current state, and open questions. Read it before changing anything.

## Requirements

- Xcode 26 with the iOS 26 SDK
- **iOS 26.5 or later on the device.** The deployment target is 26.5; earlier iOS 26 releases will not run the build.
- **A physical iPhone.** The Simulator has no camera, exposes no real capture formats, and cannot validate any capture work. Playback work can be validated in the Simulator.
- Optionally an iPad, for review on a larger screen. The app is universal and needs no separate build configuration.
- An Apple ID for code signing. A free Personal Team is sufficient; builds signed that way stop launching after 7 days and must be re-run from Xcode.
- For the analysis pipeline only: Python with `tools/requirements.txt` installed. Not needed to build or run the app.

## Running it

1. Open `GoalKick.xcodeproj`.
2. Under the `GoalKick` target, go to Signing & Capabilities and select your team. Change the bundle identifier if `com.rocket.GoalKick` is taken.
3. Select your iPhone as the run destination and press Run.
4. Grant camera access on first launch.

## How it works

**Capture.** Two configurations are selectable: 1080p at 240 fps, and 4K at 120 fps. The chosen format is pinned with `activeVideoMinFrameDuration` and `activeVideoMaxFrameDuration` set to the same value, so the camera cannot quietly drop the frame rate in poor light — that would corrupt every downstream measurement without any visible symptom.

**Video stabilization is deliberately disabled.** Stabilization warps image geometry frame by frame to smooth handheld shake. Excellent for home video, fatal here: it would move the ball within the image for reasons unrelated to the ball moving.

**Verification.** After each recording the app reads the finished file back with `AVURLAsset` and reports its actual resolution, frame rate, duration, and frame count. What the camera was asked for and what landed on disk are separate claims, and only the second one matters.

**Scale calibration.** Real-world distance is recovered from the ball's apparent pixel diameter, which requires the camera's focal length in pixels. Two routes exist:

- The per-frame **intrinsic matrix**, which gives true focal length under current focus. Measured across all 70 formats on the iPhone's back camera: 66 support it, and the 4 that do not are exactly the four 240 fps formats. Intrinsics and 240 fps are mutually exclusive.
- **Field of view**, published for every format including the 240 fps ones, giving `fx = (imageWidth / 2) / tan(fieldOfView / 2)`. Nominal rather than measured.

Field of view is the route actually in use, since the intrinsic matrix is delivered only to a live capture session and is not stored in a recorded movie file.

**The ball's size is recorded into each clip twice** — as a filename token and as QuickTime metadata inside the movie. Both survive an AirDrop; a sidecar file would not. The metadata is authoritative, because the two can only disagree if someone renames the file, and renaming damages the filename while leaving the metadata intact.

## What gets measured, and what gets computed

Only **launch conditions** are measured. Velocity and launch angle are fully determined in the first fraction of a second after contact. Carry distance and max height are then *computed* from those, which is what "theoretical carry distance" means — the ball never has to be filmed landing.

That distinction resolves what would otherwise be an impossible framing problem. Covering a 40 m flight means standing ~27 m back, where a size 4 ball is under 10 pixels wide at 1080p and the diameter estimate collapses. Filming only the launch allows standing 5–12 m away, where the ball is 26–52 pixels.

Both flight models are computed and shown side by side — a drag-free parabola and RK4 integration with air resistance. The gap between them is the honest answer: it shows how much of the figure is physics and how much is assumption. Spin is ignored, so there is no Magnus force; a ball struck with backspin carries further than either model predicts.

**How a kick must be filmed** matters as much as the code. Camera held steady with no deliberate pan, 5–12 m away, within ±15° of perpendicular to the kick, and the ball stationary in frame beforehand — a ball at rest gives the sharpest diameter measurement available, and it makes contact detectable automatically. None of this is yet enforced or checked by the app.

**Frame rates are not what they claim.** Recorded files report 239.9 and 119.9 fps — the NTSC-derived rates of 240 ÷ 1.001 and 120 ÷ 1.001. `nominalFrameRate` is a label, not a measurement, so Δt must always come from each frame's presentation timestamp.

## Storage, and why Photos is not used

**Clips are written to the app's own `Documents/Clips/` directory. Nothing is written to Photos.**

This is not a preference. Saving a 240 fps clip to Photos makes iOS classify it as slow motion, and reading it back returns a **30 fps** file — every frame present, but timestamps 8× too far apart. Δt would read 1/30 s instead of 1/240 s, making every velocity 8× too slow with no visible symptom. Photos is not a safe store for measurement footage, so the app owns its own.

**The app's own directory stays the store, and that is settled.** The pattern comparable apps use — Hudl Technique, OnForm, LumaFusion — is both, with distinct roles: Photos and Files are import sources and export destinations, while the app keeps a working library it controls. Import copies a file in rather than referencing it, which is what stops an iCloud proxy or a slow-motion rendition being served in place of the original.

**What is still open is whether Photos is added as an import source**, and whether a 240 fps clip survives a round trip through it. `project_notes.md` has the detail.

**To get clips off the device, use the cable.** Finder → the device under *Locations* → the **Files** tab → *GoalKick → Clips* → drag them out. Byte for byte, nothing to discover, works for iPhone and iPad alike.

**AirDrop is not reliable for this.** iOS routes an AirDropped video into Photos on its own without asking, which is the one destination that may retime it. The clip browser has an **Import** button that reaches out and fetches a file from wherever it landed, and a **share** button on each row for sending one out.

Nothing prunes the clip directory except deleting rows in the app, and 4K/120 runs roughly 6 MB per second.

## Review

Playback with pause, 1×, 1/2, 1/4, and 1/8 speed, frame-accurate stepping in both directions, restart, scrubbing, section looping, and continuous reverse playback.

**1/8 is the rate at which a 240 fps clip shows every frame** — 240 ÷ 8 = 30 displayed per second. At 1× the display physically cannot show all 240, so the reviewer is not seeing everything that was recorded. The equivalent for 4K/120 is 1/4.

**Pinch to zoom** up to 8× with pan, and double-tap to zoom to the point you tapped. Zoom holds while stepping frames and changing speed — that combination is the point, since zooming to the plant foot and then stepping through contact is how a coach shows a kicker what actually happened.

**Telestration.** Draw yellow lines over the video with a finger, Apple Pencil or stylus; they hold position while the clip plays. Strokes are stored as fractions of the video picture rather than as screen coordinates, so a circle drawn around the plant foot stays on it through zoom, pan and rotation. Not saved — annotations are lost when the clip changes.

The app is universal, and review is intended for an iPad, where a coach can show a kicker their own technique on a screen big enough to see it.

## Analysis pipeline

Measurement is being developed as Python on the Mac before anything is ported to Swift, because the feasibility question is separable from learning the platform and the iteration loop is seconds rather than a device rebuild.

- `tools/extract_frames.py` — verify real frame timing, locate the kick, dump frames
- `tools/detect_ball.py` — YOLO detection, background registration, continuity gating; writes a per-frame CSV
- `tools/compute_metrics.py` — 3D reconstruction, trajectory fit, both flight models

Nothing here ships. It is a spike whose findings port to Vision, Core ML and Accelerate, and it is constrained accordingly: only detector models small enough for the Neural Engine, and no technique without an Apple equivalent.

## Project layout

- `ContentView.swift` — tab bar container, and the landing point for clips sent to the app from outside it
- `RecordView.swift` — capture screen: live preview, configuration picker, ball size picker, record button
- `Recorder.swift` — `CaptureConfig`, `BallSize`, `ClipMetadata`, `ClipStore`, capture session, format selection, orientation, recording, file verification
- `ReviewView.swift` — playback controller, transport, scrubbing, looping, frame stepping, zoom, telestration, clip browser
- `Info.plist` — only the Info keys Xcode's `INFOPLIST_KEY_*` allowlist cannot express; everything else is generated from build settings
- `tools/` — the Mac-side Python pipeline, deliberately outside `GoalKick/` so Xcode's synchronized folders do not sweep it into the app target
- `shot-list.txt` — the filming protocol, plain text so it opens on a phone in a field
- `project_notes.md` — decisions, current state, open questions

## Terminology

The person using the app is the **coach**. The goalkeeper being measured is the **kicker**.

## Tech stack

Native Swift and SwiftUI, with AVFoundation for capture and playback, CoreMotion for camera attitude, and Vision plus a Core ML detector for tracking. No third-party dependencies in the app.

Ball detection uses a pre-trained COCO model rather than Vision's object tracker. A tracker follows an appearance you hand it, so it needs seeding and inherits whatever that seed looked like; a detector generalises across ball colours for nothing.

Native was not a preference. Deliverable 1 depends on high frame rate capture, camera optics data for scale calibration, frame-accurate playback stepping, and per-frame presentation timestamps — none of which are reachable from a web or cross-platform stack.
