# GoalKick

An iOS app that measures goalkeeper kicking performance from video captured on the device.

Point the camera at a goal kick, record at high frame rate, and get ball **velocity**, **launch angle**, and **theoretical carry distance / max height** — using nothing but the known physical size of the ball for scale.

## Status

Early development. Capture works; measurement does not exist yet.

| Area | State |
|---|---|
| High frame rate capture | Working, verified on device |
| Recording and saving to Photos | Working, verified on device |
| Video review and frame stepping | Written, not yet tested |
| Ball tracking | Not started |
| Metrics | Not started |

`project_notes.md` in this repository is the single source of truth for decisions, current state, and open questions. Read it before changing anything.

## Requirements

- Xcode 26 with the iOS 26 SDK
- **A physical iPhone.** The Simulator has no camera, exposes no real capture formats, and cannot validate any capture work.
- An Apple ID for code signing. A free Personal Team is sufficient; builds signed that way stop launching after 7 days and must be re-run from Xcode.

## Running it

1. Open `GoalKick.xcodeproj`.
2. Under the `GoalKick` target, go to Signing & Capabilities and select your team. Change the bundle identifier if `com.rocket.GoalKick` is taken.
3. Select your iPhone as the run destination and press Run.
4. Grant camera access on first launch, and Photos access on the first save.

## How it works

**Capture.** Two configurations are selectable: 1080p at 240 fps, and 4K at 120 fps. The chosen format is pinned with `activeVideoMinFrameDuration` and `activeVideoMaxFrameDuration` set to the same value, so the camera cannot quietly drop the frame rate in poor light — that would corrupt every downstream measurement without any visible symptom.

**Video stabilization is deliberately disabled.** Stabilization warps image geometry frame by frame to smooth handheld shake. Excellent for home video, fatal here: it would move the ball within the image for reasons unrelated to the ball moving.

**Verification.** After each recording the app reads the finished file back with `AVURLAsset` and reports its actual resolution, frame rate, duration, and frame count. What the camera was asked for and what landed on disk are separate claims, and only the second one matters.

**Scale calibration.** Real-world distance is recovered from the ball's apparent pixel diameter, which requires the camera's focal length in pixels. Two routes exist:

- The per-frame **intrinsic matrix**, which gives true focal length under current focus. Measured across all 70 formats on the test device: 66 support it, and the 4 that do not are exactly the four 240 fps formats. Intrinsics and 240 fps are mutually exclusive.
- **Field of view**, published for every format including the 240 fps ones, giving `fx = (imageWidth / 2) / tan(fieldOfView / 2)`. Nominal rather than measured, but a goal kick is filmed at 20–40 m where the lens sits at effectively infinite focus.

**Frame rates are not what they claim.** Recorded files report 239.9 and 119.9 fps — the NTSC-derived rates of 240 ÷ 1.001 and 120 ÷ 1.001. `nominalFrameRate` is a label, not a measurement, so Δt must always come from each frame's presentation timestamp.

## Project layout

- `ContentView.swift` — tab bar container
- `RecordView.swift` — capture screen: live preview, configuration picker, record button
- `Recorder.swift` — capture session, format selection, recording, file verification, Photos save
- `ReviewView.swift` — playback with pause, 1/2 and 1/4 speed, and frame-accurate stepping
- `project_notes.md` — decisions, current state, open questions

## Terminology

The person using the app is the **coach**. The goalkeeper being measured is the **kicker**.

## Tech stack

Native Swift and SwiftUI, with AVFoundation for capture and playback, Vision for tracking (planned), and PhotoKit for saving. No third-party dependencies.

Native was not a preference. Deliverable 1 depends on 240 fps capture, camera intrinsics, frame-accurate playback stepping, and per-frame presentation timestamps — none of which are reachable from a web or cross-platform stack.
