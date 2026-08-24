# GoalKick

An iOS app that measures goalkeeper kicking performance from video captured on the device.

The intent: point the camera at a goal kick, record at high frame rate, and get ball **velocity**, **launch angle**, and **theoretical carry distance / max height** — using nothing but the known physical size of the ball for scale.

That is the goal, not the current state. See Status.

## Status

Early development. **The app captures and reviews. The measurement works, but only as Python on a Mac — its reconstruction is now validated against distances paced on a pitch, while its flight fit carries a known, located bias.**

| Area | State |
|---|---|
| High frame rate capture | Working, verified on device |
| Ball size recorded per clip | Working on device; metadata round-trip unconfirmed |
| Clip storage in the app's own library | Working, verified on device |
| Getting clips off the device | Working, verified on device |
| Video review, frame stepping, zoom, telestration | Working, verified on device |
| Importing and sharing clips | Built, not yet verified on device |
| Ball detection and tracking | Working on 10 of 11 test clips — Mac-side Python only |
| Metrics (velocity, angle, carry, apex) | Written — Mac-side Python only; reconstruction validated, flight fit biased |
| Core ML export of the detector | Exported and verified against the weights; never run on the Neural Engine |
| Any measurement inside the app | Not started |

**Ball detection works.** A stock COCO object detector finds footballs with no training data and no assumptions about colour. The hard part turned out not to be detection but deciding *which* football matters — a pitch in use has several, and on one session a bag of spares on the touchline was tracked instead of the ball being kicked, in nine clips out of eleven. Acquisition now takes the nearest ball, which is the one the coach stood 10 yards from.

**The reconstruction is validated against reality.** On every clip whose track reaches the ground, the observed displacement matches a distance paced out on the pitch to within **3–10%**. That confirms the whole measurement chain — focal length from field of view, ball diameter as scale, per-frame depth, 3D geometry — against an independent physical measurement rather than against itself.

**The flight fit is not yet right.** The pipeline fits gravity from the data as an independent test — nothing tells it that gravity is 9.81 — and it averages **8.3** across nine clips. The cause is known: the detector's bounding box under-reads the ball's diameter as it recedes and blurs, by about 6% at the landing. The horizontal axis absorbs that harmlessly; the vertical amplifies it through the range slope.

Motion blur inflating the box, air resistance, camera tilt, and anchoring the range to the ball's resting size were each tested and each eliminated. Those negative results are recorded in `project_notes.md` and in the code.

**Nothing should be presented to a coach yet.**

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

Although carry is computed rather than observed, **the fit must still stop where free flight does.** Running it through the bounce and the roll flattens the trajectory into nearly a straight line and reports gravity near zero — that was the pipeline's longest-standing defect. The landing is now found from the reversal in the ball's vertical image position and the fit is cut there.

**How a kick must be filmed** matters as much as the code. Camera held steady with no deliberate pan, 5–12 m away, within ±15° of perpendicular to the kick, and the ball stationary in frame beforehand — a ball at rest gives the sharpest diameter measurement available, and it makes contact detectable automatically. One more rule was learned the hard way: no other footballs in shot, or none nearer than the one being kicked. `shot-list.txt` in this repository is the field version. None of it is yet enforced or checked by the app.

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
- `tools/compute_metrics.py` — 3D reconstruction, trajectory fit, landing detection, both flight models
- `tools/validate.py` — checks the results against ground truth: observed carry against paced landings, camera height as an independent scale check, and a principal-point sweep kept as a negative result
- `tools/export_coreml.py` — Core ML conversion, verification against the original weights, and the crop-versus-full-frame measurement that chose the on-device architecture
- `tools/sessions/*.csv` — which clip is which kick, and how far each one actually landed

The per-frame tracks in `tools/frames/*-track.csv` are committed. The footage they came from is not in this repository, so the tracks are what keeps the physics reproducible.

The CSV is the interface between detection and physics, so the arithmetic can be re-run in a second without paying for the model again.

**A quick way to tell whether a run is real:** check the implied range against where the camera actually stood. A size 4 ball at 9.1 m is 28 pixels at 1080p and 57 at 4K. A track reporting 20–31 m from a camera at 9 m has locked onto a different ball, however confident and however tidy its statistics look.

Nothing here ships. It is a spike whose findings port to Vision, Core ML and Accelerate, and it is constrained accordingly: only detector models small enough for the Neural Engine, and no technique without an Apple equivalent.

**Everything must eventually run in Swift on an iPhone or iPad**, so the spike was audited against that. `compute_metrics.py` uses no OpenCV — it is pure numpy, and every call maps to Accelerate — so the physics is low risk.

The detector looked like the hard part. The pipeline runs inference at the clip's native width because diameter precision drives every distance, and 3840 px is 36× the pixels a Core ML YOLO export normally takes. **Cropping resolves it:** a 640 px window at native resolution, centred where the ball is predicted to be, matches full-frame 3840 accuracy at 1/36th the compute — the ball keeps every pixel it had and only empty grass is discarded. The obvious middle option, full-frame at 1280, is worse than it looks: it loses the ball mid-flight and reads 33% high late, and that failure would present as bad physics rather than a bad setting.

The model is exported and committed as `yolo11n.mlpackage`, reproducing the PyTorch boxes to 0.00%. It has not yet run on the Neural Engine, which is the runtime that will actually ship. `project_notes.md` has the full audit.

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
