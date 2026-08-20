# GoalKick

An iOS app that measures goalkeeper kicking performance from video captured on the device.

The intent: point the camera at a goal kick, record at high frame rate, and get ball **velocity**, **launch angle**, and **theoretical carry distance / max height** — using nothing but the known physical size of the ball for scale.

That is the goal, not the current state. See Status.

## Status

Early development. **Everything around the measurement works. The measurement itself does not exist yet.**

| Area | State |
|---|---|
| High frame rate capture | Working, verified on device |
| Clip storage in the app's own library | Working, verified on device |
| Getting clips off the device | Working, verified on device |
| Video review and frame stepping | Working, verified on device |
| Ball tracking | Not started |
| Metrics | Not started |
| Ball size input | Does not exist — see below |
| Flight model for carry distance | Undecided — see below |

**Two of Deliverable 1's inputs are still missing, not merely unimplemented.** The app has no way to be told the ball's size, which scale calibration requires. And no decision has been made on whether carry distance and max height come from a drag-free parabola or a model with air resistance — for a ball leaving the foot at ~30 m/s those differ by roughly a factor of two, so it is not a detail.

`project_notes.md` in this repository is the single source of truth for decisions, current state, and open questions. Read it before changing anything.

## Requirements

- Xcode 26 with the iOS 26 SDK
- **iOS 26.5 or later on the device.** The deployment target is 26.5; earlier iOS 26 releases will not run the build.
- **A physical iPhone.** The Simulator has no camera, exposes no real capture formats, and cannot validate any capture work. Playback work can be validated in the Simulator.
- Optionally an iPad, for review on a larger screen. The app is universal and needs no separate build configuration.
- An Apple ID for code signing. A free Personal Team is sufficient; builds signed that way stop launching after 7 days and must be re-run from Xcode.

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
- **Field of view**, published for every format including the 240 fps ones, giving `fx = (imageWidth / 2) / tan(fieldOfView / 2)`. Nominal rather than measured, but a goal kick is filmed at 20–40 m where the lens sits at effectively infinite focus.

Field of view is the route actually in use, since the intrinsic matrix is delivered only to a live capture session and is not stored in a recorded movie file.

**Frame rates are not what they claim.** Recorded files report 239.9 and 119.9 fps — the NTSC-derived rates of 240 ÷ 1.001 and 120 ÷ 1.001. `nominalFrameRate` is a label, not a measurement, so Δt must always come from each frame's presentation timestamp.

## Storage, and why Photos is not used

**Clips are written to the app's own `Documents/Clips/` directory. Nothing is written to Photos.**

This is not a preference. Saving a 240 fps clip to Photos makes iOS classify it as slow motion, and reading it back returns a **30 fps** file — every frame present, but timestamps 8× too far apart. Δt would read 1/30 s instead of 1/240 s, making every velocity 8× too slow with no visible symptom. Photos is not a safe store for measurement footage, so the app owns its own.

**To get clips off the device,** the app enables file sharing, so `Documents/` appears in the Files app under *On My iPhone → GoalKick*. AirDrop from there copies the file byte for byte and true frame timing survives. On the receiving device, **save to Files, never to Photos.**

Nothing prunes the clip directory except deleting rows in the app, and 4K/120 runs roughly 6 MB per second.

## Review

Playback with pause, 1×, 1/2, 1/4, and 1/8 speed, frame-accurate stepping in both directions, restart, scrubbing, section looping, and continuous reverse playback.

**1/8 is the rate at which a 240 fps clip shows every frame** — 240 ÷ 8 = 30 displayed per second. At 1× the display physically cannot show all 240, so the reviewer is not seeing everything that was recorded. The equivalent for 4K/120 is 1/4.

The app is universal, and review is intended for an iPad, where a coach can show a kicker their own technique on a screen big enough to see it.

## Project layout

- `ContentView.swift` — tab bar container
- `RecordView.swift` — capture screen: live preview, configuration picker, record button
- `Recorder.swift` — `CaptureConfig`, `ClipStore`, capture session, format selection, orientation, recording, file verification
- `ReviewView.swift` — playback controller, transport, scrubbing, looping, frame stepping, clip browser
- `Info.plist` — only the Info keys Xcode's `INFOPLIST_KEY_*` allowlist cannot express; everything else is generated from build settings
- `project_notes.md` — decisions, current state, open questions

## Terminology

The person using the app is the **coach**. The goalkeeper being measured is the **kicker**.

## Tech stack

Native Swift and SwiftUI, with AVFoundation for capture and playback, CoreMotion for camera attitude, and Vision for tracking (planned). No third-party dependencies.

Native was not a preference. Deliverable 1 depends on high frame rate capture, camera optics data for scale calibration, frame-accurate playback stepping, and per-frame presentation timestamps — none of which are reachable from a web or cross-platform stack.
