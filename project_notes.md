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
- Pinch to zoom into the picture, and pan around while zoomed
- Draw yellow lines over the video with a finger, Apple Pencil or stylus, which stay in place while the clip plays. A button to turn drawing on and off, and a button to clear.

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
| Ball tracking | **A pre-trained COCO object detector, not Vision's tracker.** `yolo11n` finds footballs through its "sports ball" class with no training data and no colour assumptions. `VNTrackObjectRequest` was never tried: a tracker follows an appearance you hand it, so it needs seeding and inherits whatever colour that seed had, while a detector generalises across ball colours for free. The hard part is not detection but **choosing which football is the one being measured** — a pitch in use has several — and that rule is in *Analysis pipeline*. In the app this becomes the model exported to Core ML and run through `VNCoreMLRequest`. |
| Camera-shake correction | Frame-to-frame background registration. OpenCV optical flow on the Mac; `VNTranslationalImageRegistrationRequest` / `VNHomographicImageRegistrationRequest` in the app |
| Numerics | Accelerate / vImage; Metal only if profiling demands it |
| Playback | `AVPlayer`, driven by setting `rate` directly for slow and reverse playback, and `AVPlayerItem.step(byCount:)` for frame stepping |
| Camera attitude | CoreMotion, to correct launch angle for camera tilt |
| Storage | The app's own `Documents/Clips/`, managed by `ClipStore`. The only copy, and the only source with true timing. Nothing is written to Photos. Exposed in the Files app via `UIFileSharingEnabled` so clips can be AirDropped to the iPad or the Mac. |
| Dependencies | None third-party |

**Scale calibration:** the known ball diameter plus the camera's **focal length in pixels** is how real-world distance is recovered from apparent pixel size. Focal length is the hard requirement; the intrinsic matrix is only one of two ways to obtain it.

- **Intrinsic matrix** — delivered per frame, gives true focal length under current focus plus the optical center. Better, but unavailable at 240 fps on the iPhone, and delivered only to a live capture session rather than stored in the recorded file.
- **Field of view** — `AVCaptureDevice.Format.videoFieldOfView` is published for every format, including the 240 fps ones. Focal length follows as `fx = (imageWidth / 2) / tan(fieldOfView / 2)`. Nominal rather than measured, but a goal kick is filmed at 20–40 m where the lens is effectively at infinity focus, so the nominal value is accurate.

### Porting risks — audited 2026-08-24

**Everything in Deliverable 1 must run in Swift on an iPhone or iPad.** The Mac pipeline is a spike, so what matters is not whether it works but whether it survives the move. Audited against the code as it actually stands:

**The physics ports cleanly.** `compute_metrics.py` uses no OpenCV at all — it is pure numpy, and every call has an Accelerate equivalent: `polyfit` and `linalg.lstsq` map to LAPACK `dgels`, and `median`, `std`, `mean` and `dot` to vDSP. The RK4 integration, the Gauss-Newton drag fit with its numerical Jacobian, and the landing detection are plain arithmetic on arrays — perhaps 150 lines of Swift, running in milliseconds on a hundred samples. Nothing here is a risk.

**The app will be better than the Mac in one respect.** `compute_metrics.py` hardcodes `fx` as 1260 or 2520 from an assumed 74.6° field of view. The app has `AVCaptureDevice.Format.videoFieldOfView` at capture time and can write the true value into each clip, exactly as it already does for ball size. That removes an assumption rather than porting one.

**Native-resolution inference was the largest risk. It is solved, by cropping.** `--imgsz` defaults to the clip's own width — 3840 for 4K — because diameter precision is what every distance rests on. On a phone that is 36× the pixels a Core ML YOLO export normally takes, and it was the least device-friendly thing in the pipeline.

The way out is not a bigger model input but a smaller picture. Measured 2026-08-24 on a 4K clip, comparing the full frame downscaled against a **640 px crop at native resolution** centred where the ball is predicted to be:

| Frame | True diameter | full @1280 | full @3840 | **crop 640 @native** |
|---|---|---|---|---|
| at rest | 57.2 px | +0.6% | −0.1% | **+1.9%** |
| early flight | 52.4 px | +6.0% | +0.1% | **+3.3%** |
| mid flight | 37.7 px | **not found** | +0.0% | **−0.2%** |
| late flight | 30.4 px | **+32.9%** | −1.6% | **−0.2%** |

The crop matches full-frame 3840 accuracy while the model sees only 640 px — **1/36th the compute**. The ball keeps every pixel it had; only empty grass is discarded.

**Note what the middle column says, because it is the trap.** Full-frame 1280 is what a naive port would reach for, and it does not merely degrade — it loses the ball mid-flight and reads 33% high late. That failure would surface as bad physics, not as a resolution problem, and would be very hard to attribute.

**The detection floor is measured.** At 640 the detector finds nothing at all on a 4K frame, because a 6× downscale turns a 57 px ball into 9.5 px. 960 is the minimum that finds it; confidence only firms up above 2560. So the architecture to port is: acquire once on a full frame at 1280–2560, then track in 640 crops at native resolution.

**The export changes nothing, which was not a foregone conclusion.** The same frames through `yolo11n.pt` and `yolo11n.mlpackage` give **0.00% difference** in box diameter and identical confidences to two decimals. That means the diameter bias under *The gravity discrepancy* is a property of the architecture rather than the runtime, and characterising it on the Mac is not wasted. The distance gate's 1.3 factor and the 1.6 diameter tolerance likewise carry over.

**The Neural Engine is still untested, and it is the thing that ships.** Ultralytics runs Core ML on the Mac's CPU or GPU. The ANE may use float16, which could move box coordinates. The comparison in `tools/export_coreml.py compare` has to be repeated on a device before any of the above is settled.

**Registration is unverified.** The Mac uses Shi-Tomasi features, Lucas-Kanade optical flow and a RANSAC affine estimate. `VNTranslationalImageRegistrationRequest` is a *different algorithm*, not a reimplementation. Drift of 250–390 px is currently being corrected on real clips, so this matters; equivalent in intent, unproven in effect.

**Camera distance is now a required per-clip input.** The acquisition gate needs the distance the coach paced out. That means a control on the Record screen beside the ball size picker, captured per clip for the same reason ball size is — it describes the clip, not the app. This requirement did not exist before 2026-08-24 and nothing in the app provides it.

**Coaches cannot pass flags.** Defaults carried 9 of 11 clips on the 2026-08-22 set, which is respectable, but two failed and the app has no way to say so intelligibly. Whatever ships must either work on defaults or explain itself.

**Known technical risk, partially measured:** motion blur on a fast-moving ball may defeat Vision's built-in tracker and force a trained Core ML detector. First footage (2026-08-21, bright sun, ball at ~13 m/s) shows **no meaningful blur** — panel detail is legible on a ball ~70 px across at 240 fps. This retires the risk at that speed and in that light only. A real goal kick at ~30 m/s smears roughly 2.3× further per exposure, and overcast light lengthens exposure further, so the risk stands for the footage that actually matters.

**On Swift 6:** the decision to stay in Swift 5 mode stands, and was reconsidered deliberately after capture was working rather than allowed to lapse. Strict concurrency turns data-race issues into hard compile errors, and the next phase — passing `CMSampleBuffer` and `CVPixelBuffer` to Vision — is the worst area for that friction, since neither type is `Sendable` and the annotations are Apple's to fix, not ours. `SWIFT_VERSION` is a single build setting, so migrating later costs the same work on a more settled design. Revisit once tracking works.

## Measurement Approach

**Only launch conditions are measured. Everything else is computed.**

Deliverable 1 asks for velocity, launch angle, and *theoretical* carry distance and max height. Theoretical means derived from launch conditions rather than observed, so the ball never has to be filmed landing. Velocity and launch angle are fully determined within the first fraction of a second after contact; carry and apex follow from the flight model.

This resolves what would otherwise be an impossible framing problem. Covering a 40 m flight requires standing ~27 m back, where a Size 4 ball is under 10 px wide at 1080p (see *Pixels on the ball*). Filming only the launch allows standing 5–12 m away, where the ball is 26–52 px and the diameter estimate is sound.

It also means footage that ends early — a ball struck into a close net — still yields all four metrics.

**Filming guardrails.** These are constraints on the coach, not on the software, and they are what make the measurement tractable:

| Guardrail | Why |
|---|---|
| Held steady, no deliberate pan | Handheld is the expected case — coaches will not carry tripods, and requiring one would make the app unusable. Over a ~0.15 s measurement window a steady hand drifts only a few pixels, worth roughly 1–3% on speed, and residual shake is removed in analysis by registering each frame against the background. **Panning is different in kind** and must be avoided: following the ball keeps it near frame centre while the whole background sweeps past, a far larger correction. Never pan; let the ball leave the frame rather than chase it. A tripod or any rest improves accuracy and should be used when available, but is not required. |
| 5–12 m from the ball | Sets a floor on pixels across the ball: ~52 px at 5 m, ~26 px at 10 m at 1080p. Accuracy becomes a known quantity rather than a lottery. |
| Within ±15° of perpendicular to the kick | Off-axis foreshortening under-reads velocity by roughly `cos φ` — 3.4% at 15°, 13% at 30°. |
| Ball stationary and in frame before the kick | The most accurate diameter measurement available is the ball at rest: sharp, unblurred, measurable over many frames. Scale is fixed there, once, rather than fought for mid-flight. It also makes contact detectable automatically — contact is the first frame the ball moves. |
| No other footballs in shot, or none nearer than the one being kicked | Learned on 2026-08-22, where a bag of spares on the touchline and a game on the next pitch cost nine clips out of eleven. The detector cannot know which football matters; the *nearest* one is the measurement ball, and the acquisition rule depends on that staying true. A spare ball rolled closer to the camera than the one being struck would break it. |

**Whether the landing must be in frame depends on what the clip is for, and the two answers conflict.** This is worth stating plainly because `shot-list.txt` and this table appear to disagree, and neither is wrong.

- **For measuring a kick**, only launch conditions matter. Carry and apex are computed from them, so the ball never has to be filmed landing, and the coach should stand as close as the guardrails allow — closer means more pixels on the ball, and diameter precision is the weakest link in the chain.
- **For validating the pipeline**, the landing must be in shot. Computed carry can only be checked against a paced distance if the footage shows where the ball actually came down, and the bounce is also what tells the software where free flight ended.

The 2026-08-22 session was filmed for the first purpose and used for the second, which is why seven clips of eleven can never be checked against their paced landings — the ball had left the frame. `shot-list.txt` item 14 now requires the landing in shot, because that sheet exists to produce *validation* footage. Once the pipeline is trusted, ordinary use goes back to standing close.

**Free flight ends at the bounce, and the fit has to stop there.** Not a filming guardrail but the same class of mistake: a window containing something other than free flight. A parabola fitted across a flight and its bounces is nearly a straight line and reports gravity near zero. `compute_metrics.py` now finds the landing and cuts there — see *The gravity discrepancy*.

None of the filming guardrails is built. The app offers no framing guidance and performs no compliance check.

**On-device constraints.** Analysis runs on an iPhone or iPad, after capture rather than live, so throughput is not critical — but two things are:

- **The detector must export to Core ML and fit on the Neural Engine.** The Mac-side spike is restricted to `yolo11n` (~6 MB) and `yolo11s` (~19 MB) for that reason. Proving the concept with a model that cannot ship would prove nothing.
- **Camera-shake compensation ports cleanly.** Frame-to-frame registration against the background has native equivalents in `VNTranslationalImageRegistrationRequest` and `VNHomographicImageRegistrationRequest`, so this technique survives the move to the app with no third-party dependency. It complements the decision to disable hardware video stabilisation at capture: the camera's own stabiliser applies a *non-rigid* warp that corrupts geometry, while a *rigid* registration applied in analysis removes shake without distorting. Off in the camera, corrected in software.
- **Diameter refinement was dropped rather than ported.** An earlier spike refined ball diameter with OpenCV's `HoughCircles`, which has no Apple equivalent. Measured against real footage it inflated diameter by ~45% while the raw detector box held steady to a few pixels, so it was removed. Nothing in the current pipeline depends on an OpenCV routine without a Vision or Accelerate counterpart.

## Current State

### What does NOT exist yet

**There is no measurement code in the app.** Detection, tracking and metrics exist only as Python on the Mac (see *Analysis pipeline*). The iOS app still captures, stores and reviews; it computes nothing, and no Swift has been written for any of it.

**A Core ML model does exist** — `yolo11n.mlpackage` at the repo root, exported 2026-08-24 and verified to reproduce the PyTorch boxes exactly. It has never been loaded by the app, and it has never run on the Neural Engine.

**The metrics are half-validated.** The reconstruction is confirmed: on every clip whose track reaches the ground, observed displacement matches a paced landing to within 3–10%. The flight fit is not: gravity averages 8.3 against 9.81, from a known cause — a progressive bias in the detector's flight diameters, detailed under *The gravity discrepancy*. **No figure should be shown to a coach yet**, but the open question is now a specific measurable defect rather than a mystery.

**No filming guardrail is enforced or checked.** The app gives the coach no framing guidance and does not verify afterwards whether the shot was square, steady, or at a sensible distance — despite those being what makes the measurement work at all. The measurements needed for the check already exist in the Mac pipeline; nothing surfaces them.

**Annotations are not saved.** Telestration strokes live only in memory and are lost when the clip changes or the app quits. There is no undo, one colour, one thickness.

**The test targets remain empty.** No test has been written for either the Swift app or the Python tools.

**No synthetic validation exists.** The pipeline has now been checked against *real* data with a known answer — the eleven paced landings of 2026-08-22 — but never against a generated trajectory whose launch conditions are known exactly. Real footage confirms the answer without isolating which stage is wrong when it is not; synthetic data would. See *Next Steps → Step 5*.

### What is done

Each of these is verified on hardware, not merely written. Details are in the sections below.

| Milestone | Outcome |
|---|---|
| **Capture spike** | High-speed capture, recording, and storage in the app's own library. The step originally required confirming intrinsic matrix delivery; intrinsics turned out to be unavailable at 240 fps, but the underlying requirement — obtaining focal length — is met through field of view. |
| **Video review screen** | Every playback control Deliverable 1 asks for, plus 1/8 speed, restart, scrubbing, section looping, and reverse playback beyond the requirement. |
| **Clip transfer off the device** | File sharing exposes `Documents/` in the Files app and in Finder over the cable, which is the reliable route and is verified. AirDrop is *not* reliable — see *Getting clips off the device*. The Import and share buttons and the document-type declaration are **built but not yet exercised on device.** |
| **iPad as the review device** | No port was needed. The app was already universal and the review screen required no layout changes. |
| **Ball size capture** | A `BallSize` picker on the Record screen, written into every clip twice: as a filename token and as `mdta` metadata inside the movie. Both survive AirDrop, which a sidecar file would not. Builds and runs on device; **the metadata round-trip has not been confirmed from a real recording.** |
| **Pinch to zoom in Review** | Up to 8×, with pan, double-tap to zoom to a tapped point, and a persistent badge that resets. Built on `UIScrollView`. Verified on device. |
| **Telestration** | Yellow strokes over the video that hold position while the clip plays, with on/off and clear buttons. Strokes are stored normalised to the picture, so they track the video through zoom, pan and rotation. Verified on device. |
| **First footage** | Ten clips, 2026-08-21. Five at 1080p/240, five at 4K/120. Documented under *Open Questions → How should a goal kick be filmed?* |
| **Step 3 — ball tracking** | Done, on the Mac. A stock `yolo11n` finds the ball across the flight with no training data. Acquisition takes the largest candidate rather than the most confident, gated on the distance the coach paced out, which is what stops it locking onto other people's footballs elsewhere on the pitch; `--max-gap` is 30 frames so the blur blackout off the boot does not end the track. Ten of eleven 2026-08-22 clips track correctly. |
| **Step 4 — metrics** | Written, on the Mac. Produces speed, launch angle, carry and apex, with both flight models side by side, cuts the fit at the bounce automatically, and fits launch conditions against the drag ODE rather than a parabola. Nine of eleven clips produce sound numbers. |
| **Ground truth** | Eleven kicks filmed 2026-08-22 with paced landing distances, camera at 10 yards, cones at a measured 5 yards. The first data in the project's history against which a computed carry can be checked at all. |
| **Reconstruction validated** | On every clip whose track reaches the ground, observed displacement matches the paced landing to within **3–10%**. Focal length from field of view, ball diameter as scale, per-frame depth and 3D geometry confirmed against a distance measured on the pitch rather than against themselves. |
| **Portability audited** | 2026-08-24. The maths ports to Accelerate with no OpenCV dependency. Recorded under *Porting risks*. |
| **Core ML export** | `yolo11n.mlpackage` at the repo root, reproducing the PyTorch boxes to 0.00%. Built with a pinned Python 3.9 environment. **Never run on the Neural Engine**, which is the runtime that ships. |
| **Crop architecture proven** | A 640 px crop at native resolution matches full-frame 3840 accuracy at 1/36th the compute. This resolves the largest porting risk and is what gets ported. |

### Environment

- **Mac:** macOS 26, Xcode 26 from the Mac App Store, iOS 26 platform installed, command line tools pointed at Xcode.
- **Test devices:** two, with different jobs.
  - **"Rocket's iPhone"** — the **capture** device. Paired over cable, Developer Mode enabled, developer certificate trusted.
  - **iPad Air 11" (Wi-Fi only)** — the **review** device, verified working. Capture is not attempted on it; see the Review section.
- **Signing:** free Apple ID under a Personal Team (Robert Williams), automatic signing. Not enrolled in the paid Apple Developer Program.

Build, sign, install, and launch are confirmed working on both devices. Getting code onto hardware is a solved problem. Note the 7-day Personal Team expiry now applies to two devices rather than one.

### Project

- **Location:** `/Users/rocket/Github/gk/GoalKick/`
- **Bundle identifier:** `com.rocket.GoalKick`
- **Targets:** `GoalKick`, `GoalKickTests`, `GoalKickUITests`. **The two test targets are untouched Xcode template stubs** — no test has been written for this project. Whether to start is undecided; nothing in the build depends on them.
- **Deployment target:** iOS 26.5 (`IPHONEOS_DEPLOYMENT_TARGET = 26.5`). Any API is fair game; nothing needs availability guards.
- **Configured as:** SwiftUI interface, Storage None, CloudKit off
- **Device family:** `TARGETED_DEVICE_FAMILY = "1,2"` — iPhone and iPad. The app has always been universal; running on iPad needs no port. All four iPad orientations are already permitted.
- **Version control:** Git at the project root, pushed to `https://github.com/rgw3/gk` (private, remote `origin`, branch `main`). `.gitignore` covers Xcode noise; `xcuserdata` is untracked.
- **`project_notes.md` lives inside the project folder**, so the source of truth is versioned alongside the code.
- **`README.md`** exists at the project root as a public-facing overview. It restates parts of this file for a reader arriving from GitHub; **this file is authoritative** where the two differ.

| File | Contents |
|---|---|
| `ContentView.swift` | Tab bar container — **Record** and **Review** — and the `onOpenURL` landing point for clips sent to the app from outside it |
| `RecordView.swift` | Capture screen: live preview, configuration picker, ball size picker, record button |
| `Recorder.swift` | `CaptureConfig`, `BallSize`, `ClipMetadata`, `ClipStore`, capture session, format selection, orientation, recording, file verification |
| `ReviewView.swift` | `ReviewPlayer` (transport, scrubbing, looping, frame stepping), `DrawingCanvasView`, `ZoomingScrollView`, `ZoomableVideoView`, clip browser, review screen |
| `Info.plist` | Only the Info keys the `INFOPLIST_KEY_*` allowlist cannot express — `UIFileSharingEnabled` and `CFBundleDocumentTypes`. Everything else is still generated by `GENERATE_INFOPLIST_FILE` and merged at build time. Do not duplicate generated keys here. |

**The project uses Xcode 16+ synchronized folders** (`PBXFileSystemSynchronizedRootGroup`), so files added to `GoalKick/` join the target automatically with no project-file surgery. `Info.plist` is the one deliberate exception: it carries a `membershipExceptions` entry excluding it from the target, because otherwise the folder copies it into the bundle as a resource while `ProcessInfoPlistFile` generates one at the same path, and the build fails with **"Multiple commands produce … GoalKick.app/Info"**. That exception is what Xcode itself writes when target membership is unticked in the File Inspector.

**App icon:** a placeholder in `Assets.xcassets/AppIcon.appiconset/`, cropped from an illustration to the ball. Only the Any Appearance slot is filled; iOS derives dark and tinted. To be revisited.

### Analysis pipeline (Mac-side, Python)

Measurement is being developed in Python on the Mac before anything is ported to Swift. The reason is deliberate: the feasibility question — can the ball be found at all — is separable from learning Swift, and iterating on the Mac takes seconds where a device rebuild takes a minute and expires after 7 days.

**These files live at the repo root, outside `GoalKick/`**, because the project uses synchronized folders and anything inside `GoalKick/` is swept into the app target automatically.

| File | Contents |
|---|---|
| `tools/extract_frames.py` | `probe` (verify real frame timing against nominal), `sheet` (contact sheet to locate the kick), `extract` (frames as PNGs) |
| `tools/detect_ball.py` | YOLO detection, background registration, continuity gating; writes the per-frame CSV |
| `tools/compute_metrics.py` | Reads that CSV; 3D reconstruction, trajectory fit, landing detection, both flight models |
| `tools/validate.py` | Checks the pipeline against ground truth: `carry` (observed displacement vs paced landing), `height` (camera height, independent of `fx`), `tilt` (principal-point sweep, kept as a negative result) |
| `tools/export_coreml.py` | Converts the detector to Core ML, checks the export against the weights, and reproduces the crop-vs-full-frame measurement. **Runs under `.venv-export`, not `.venv`** |
| `tools/sessions/*.csv` | Ground truth per filming session: which file is which kick, the paced landing, the paced camera distance, and whether the track reaches the ground |
| `tools/requirements.txt` | `opencv-python`, `numpy`, `ultralytics` — the analysis environment |
| `tools/requirements-export.txt` | Pinned `torch`, `coremltools`, `ultralytics` — the export environment |

**The kick-to-file mapping lives in `tools/sessions/2026-08-22.csv`, not in this document.** Landing distances quoted here by kick number are meaningless without it, and prose is the wrong place for a lookup table that code also has to read. `validate.py` reads it directly, so the numbers in this file and the numbers the tools produce cannot drift apart.

> ⚠️ **The clips are not in this repository.** Eleven files, about 1.3 GB, at `~/Desktop/clips/`. Nothing under `tools/` can be reproduced without them — every command in *Next Steps → Step 5* will fail with no useful explanation if they are missing or moved. They are the only copy and they are not backed up anywhere the repository knows about.

**The CSV is the interface between detection and physics**, so the arithmetic can be re-run in a second without paying for the model again.

**Acquisition takes the largest candidate, not the most confident.** The ball being measured is the one the coach stood 10 yards from, so it is the nearest object in shot and therefore the biggest. Everything else a pitch offers is further away and smaller.

This is the whole acquisition rule rather than a tie-breaker, and it was learned expensively. Taking the detector's own ranking picked a football roughly 25 m away in **nine clips out of eleven** on 2026-08-22, because the pitch had a bag of spare balls on the touchline and another age group playing two pitches over. A distant ball sitting still is crisper than a near one and scores higher for it. The size gate then locked around that wrong ball and rejected the real one for the rest of the clip, producing tracks that looked immaculate — 100% detection, tidy diameter statistics — and measured nothing.

**The signature to watch for is implied range.** A Size 4 ball at 9.1 m is 28 px at 1080p and 57 px at 4K. The nine bad tracks measured 17–24 px and implied ranges of 20–31 m. Any run whose implied range disagrees with where the camera actually stood is tracking the wrong object, whatever its confidence.

**Raising `--confidence` does not help here**, because the distractors are genuine footballs detected at 0.9+. Size is the discriminator, not confidence.

**`--max-gap` defaults to 30 frames, not 10.** The ball is genuinely unfindable for a moment as it leaves the boot: blurred, partly behind the kicker's leg, and accelerating hardest. Measured at 4K/120 that blackout ran twelve frames, and a limit of 10 ended the track inside it — discarding the whole flight to save a tenth of a second. Raising it beyond 30 buys nothing: at 90 the termination frames move out and every longest-unbroken segment stays identical, because by then the ball has left the frame.

**`--camera-distance` gates acquisition on the distance the coach paced out.** Expected diameter follows from `fx · D / Z`, and a candidate more than a factor off that is a different ball whichever way it is wrong. Largest-candidate alone fixed seven clips and broke two in the other direction, latching onto a spare ball lying *nearer* the camera than the one being struck.

Tolerance is **1.3**, not 1.5. At 1.5 a spare ball 6.8 m away measured 76.8 px against an expected 56.8 — inside a 38–85 px window, so the gate approved it. 1.3 excludes it while every correctly acquired clip sits between 55.7 and 57.9 px, and it still tolerates about 30% error in pacing.

The gate applies **only at acquisition**. The ball recedes from 9 m to 24 m during one measured flight, so enforcing it throughout would throw the flight away; the continuity and size-ratio checks carry the track once it is locked.

**`compute_metrics.py` cuts the fit at the landing and fits against drag.** `find_landing()` finds the reversal in vertical image position after the apex, working purely in image space so it needs no scale, focal length or depth. `fit_launch_with_drag()` integrates the drag ODE from a trial launch state and refines by Gauss-Newton with a numerical Jacobian — seven free parameters, gravity among them, because pinning gravity at 9.81 would trade away the only independent check the pipeline has. The drag-free parabola is still computed and printed alongside.

**`--contact-threshold` defaults to 0.3 of peak speed, not 0.15.** A ball resting on grass is not motionless in the image: handheld drift ran 250–390 px across the 2026-08-22 clips, and what registration leaves behind clears a 15% bar for three frames. Two clips fired contact while the ball still sat there and fitted 400–550 frames of a stationary ball. 0.3 and 0.5 select the same contact frame on both, so this is a plateau rather than a tuned value.

**`--imgsz` defaults to the clip's own width**, so nothing is thrown away before the detector sees it. This is not a minor setting: the model resizes each frame before looking at it, and a downscale degrades the ball's apparent diameter, which is what every distance in the pipeline rests on. Measured on one 4K clip, going from 0.33× to 0.50× cut range scatter from 200 mm to 118 mm.

**The floor is measured**, on a 4K frame with the ball at a known 57.2 px:

| `--imgsz` | Result |
|---|---|
| 640 | ball not found at all — a 6× downscale leaves it 9.5 px |
| 960 | found, confidence 0.43 |
| 1280 | found at rest, **lost mid-flight, 33% high late** |
| 1920 | accurate, confidence 0.71 |
| 3840 | accurate to 1.6% throughout, confidence 0.82–0.94 |

`--imgsz 1920` remains the quicker, coarser option for the Mac. **Do not reach for 1280 to save time** — it fails in exactly the frames that matter and the symptom looks like bad physics rather than a bad setting.

**On the device this changes shape entirely.** A 640 px crop at native resolution matches full-frame 3840 accuracy at 1/36th the compute — see *Porting risks*. The Mac pipeline does not yet do this, and adopting it here would make the Mac faster too.

**There are two Python environments, deliberately, and they are allowed to disagree.**

- **`tools/.venv`** — Python 3.14, torch 2.13, OpenCV. The analysis environment, used constantly, chosen for speed on this Mac. Wheels resolved on 3.14 without needing an older interpreter.
- **`tools/.venv-export`** — Python 3.9 from `/usr/bin/python3`, with torch 2.7.1 and coremltools 9.0 pinned. Runs once per model version and does not care about speed. Both are gitignored; `tools/requirements-export.txt` carries the versions and the reasoning.

The split is not tidiness. coremltools converts from TorchScript and is pinned to torch versions it has tested; on torch 2.13 it fails with a cascade of frontend errors, each patch revealing the next. **Hand-patching a model converter is a bad trade when the whole point is measuring bounding boxes to a few percent** — it can export cleanly and compute something subtly different. Under the pinned environment the export succeeded first time with no patches. Forcing one environment to do both jobs is what created the problem; separating them means the fast path never has to be downgraded to keep the export working.

**Nothing here ships.** It is a spike whose findings port to Vision, Core ML and Accelerate. Two constraints keep it portable: the detector is restricted to `yolo11n` and `yolo11s` so it will fit on the Neural Engine, and no technique is used that lacks an Apple equivalent — which is why an OpenCV `HoughCircles` diameter refinement was removed rather than kept.

**Clips reach the Mac over the cable, not AirDrop.** Finder → the iPhone under *Locations* → the **Files** tab → *GoalKick → Clips* → drag out. This is byte-for-byte and needs no device discovery; AirDrop failed to find the Mac in practice.

### Camera capability, measured on the iPhone

The iPhone's back camera exposes **70 formats**. Every one was applied in turn, with video stabilization explicitly disabled, and its connection queried for intrinsic matrix support. Those relevant to measurement:

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

**The app owns its clips outright.** Recordings are written directly to `Documents/Clips/`, managed by `ClipStore`. **Nothing is written to Photos.** The review screen reads only from that directory.

The reason was a measured failure: saving a **240 fps** clip to Photos made iOS classify it as slow motion, and reading it back returned a **30 fps** file — exactly 240 ÷ 8, duration stretched 8×. A 768-frame clip came back as 768 frames at 30 fps over 23.6 s. Every frame survived; only the timestamps lied. Δt would read 1/30 s instead of 1/240 s, making every velocity 8× too slow with no visible symptom. An input path that silently returns 8×-wrong timing is not something to leave next to a "choose clip" button, so the Photos picker was removed rather than left available.

> ⚠️ **This decision is under review, with evidence on both sides.** See *Should Photos be reconsidered as the store?* under Open Questions. A 4K/120 clip has since round-tripped through Photos with its timing intact. The decision above stands until the 240 fps case is retested, but it is no longer settled.

Clips are deleted from the clip list, by swiping a row or via the Edit button. Nothing else prunes the directory, and 4K/120 runs roughly 6 MB per second, so this matters.

**Clips can be brought in and sent out from the clip browser.** An **Import** button opens the system file picker and copies any `.mov` into the library; a **share** button on each row sends the file itself. Import keeps the original filename, because it carries the capture configuration and ball size tokens, and a clip renamed to a fresh timestamp would lose the only record of its ball size visible without opening the file. Collisions get a numeric suffix rather than overwriting. Files are copied, never moved — the source may belong to another app or a file provider.

The app also declares `CFBundleDocumentTypes` for movies, so it appears in a share sheet as a destination and `onOpenURL` in `ContentView` imports what arrives. `Documents/Inbox` is cleaned up afterwards, since iOS leaves a copy there and that directory is visible in Files.

**The app declares no Photos usage descriptions.** `NSPhotoLibraryAddUsageDescription` was removed once Photos was abandoned — it was unreachable, and its text claimed the app saved kicks to Photos, which is the opposite of what the app does. If Photos export is ever brought back into scope, the key comes back with it.

### Getting clips off the device

**The app opts into file sharing, so `Documents/` is visible in the Files app** under *On My iPhone → GoalKick*, with `Clips` inside it. This is the supported way to move a recording to another device or to the Mac.

**The reliable route is the cable, not AirDrop.** Finder → the device under *Locations* → the **Files** tab → *GoalKick → Clips* → drag the `.mov` out. Byte for byte, no discovery to fail, and it works for the iPad as well as the iPhone. This is the route to use.

**AirDrop does not behave as this document previously claimed.** It said the receiving device would offer *Save to Files*. **It does not.** iOS routes an AirDropped video to **Photos** on its own, without asking — which is exactly the destination that retimes high-frame-rate footage. Declaring `CFBundleDocumentTypes` does not change this: it makes the app *able* to receive a movie, but for media types iOS never presents the choice.

Two consequences:

- **Do not rely on AirDrop for measurement footage.** Use the cable. If a clip does arrive via AirDrop, check where it landed before trusting it.
- **The Import button exists because of this.** Reaching out to fetch a file from wherever iOS put it works; waiting to be handed one does not.

**A trap that cost an evening:** an app's Documents folder only appears in the Files app once it is non-empty. On a device where GoalKick had never recorded anything — the iPad — there was no GoalKick folder in Files at all, so there was nowhere to save an incoming clip to. Import now creates the directory itself, so a fresh install works with no setup.

AirDrop needs no network — it discovers over Bluetooth LE then transfers over direct peer-to-peer Wi-Fi, so it would work on a pitch with no coverage. That property is why an iCloud-shared library was rejected independently of cost: iCloud would fail exactly where the app is used. **iCloud Drive is unavailable anyway**: an app's own iCloud container needs a paid Apple Developer Program membership, and this project is on a free Personal Team.

Enabling this required a real `Info.plist`, because **`INFOPLIST_KEY_UIFileSharingEnabled` does not work.** Xcode's `INFOPLIST_KEY_*` build-setting mechanism only recognises an allowlist of 95 key names; `UIFileSharingEnabled` is not among them, and an unrecognised key is **silently ignored** — no error, no warning, the setting simply never reaches the app. `LSSupportsOpeningDocumentsInPlace` *is* on the allowlist and remains a build setting.

**To verify what the app actually shipped, read the built plist, not the project settings:**

```
plutil -extract UIFileSharingEnabled raw "$(find ~/Library/Developer/Xcode/DerivedData -path "*Build/Products/Debug-iphoneos/GoalKick.app/Info.plist" | head -1)"
```

An app's Documents folder only appears in Files once it is non-empty, so at least one clip must exist before the folder shows up.

### Review

All verified on the device:

- Playback and pause at 1×, 1/2, 1/4, and 1/8
- Frame-accurate stepping — `AVPlayerItem.step(byCount:)` advances exactly one frame per tap
- Restart, returning to frame 0 and staying paused
- A scrub bar for coarse positioning, with the step buttons for fine adjustment
- Section looping: mark In and Out, then repeat that stretch continuously. Marking Out before In swaps them rather than refusing.
- Continuous reverse playback at the selected speed. `canPlayReverse` is true for these clips, so the encoding supports backwards decode and no codec change is needed.
- Controls overlay the video and auto-hide after 3 seconds, so the picture fills the screen in both orientations. They never auto-hide when no clip is loaded, or the "Choose clip" button would vanish with no way back.

**Pinch to zoom, up to 8×, with pan.** Double-tap zooms to 3× centred on the tapped point rather than on the middle of the screen, because the coach is pointing at the ball. Zoom holds across frame stepping, speed changes and scrubbing — that combination is the point of the feature — and resets on rotation and on loading a new clip.

Built on `UIScrollView` rather than SwiftUI's `MagnifyGesture` and `DragGesture`. Zooming is more than a scale factor: the pan must stay inside the content, the gestures must compose without fighting, and letting go should settle rather than stop dead. UIKit has done all of that for years, and reimplementing it in gesture callbacks means reimplementing its edge cases too.

The subview sizing lives in `layoutSubviews`, not `updateUIView`, because SwiftUI runs `updateUIView` on *state* changes — which is not necessarily after it has decided how big the view is. On first appearance the bounds can still be zero.

**Telestration: yellow strokes that hold position while the clip plays.** A permanently visible two-button cluster at top-left toggles drawing and clears. It is deliberately not in the auto-hiding panel: drawing is a mode, and a mode the coach cannot see they are in is a trap — they would drag the video, nothing would happen, and there would be no clue why. While drawing is on, pan, pinch and tap-to-toggle-controls are all disabled, so a one-finger drag is unambiguously a line.

**Strokes are stored as fractions of the video picture, not as screen coordinates.** A point is kept as (0.5, 0.5) meaning the middle of the picture, whatever the zoom, the orientation, or the size of the letterbox bars. Screen coordinates would have been less code and quietly wrong: a circle drawn around the plant foot would slide off it the moment the coach zoomed, and turning the phone would scatter every line. Line width is normalised the same way, so a stroke drawn at 3× does not become a fat band at 1×. The canvas is a subview of the zooming view, so the scroll view's transform carries the strokes along with the picture for free.

Coalesced touches are read on every move. Apple Pencil reports far faster than the screen refreshes, and ignoring the in-between samples turns a smooth arc into visible straight segments.

**Both features are presentation only.** Measurement reads the stored pixels; neither zoom nor annotation changes any number.

**1/8 is the rate at which a 240 fps clip shows every frame.** 240 ÷ 8 = 30 frames displayed per second. At 1× the display physically cannot show all 240, so frames are dropped and the reviewer is not seeing everything that was recorded. The equivalent for 4K/120 is 1/4. Slower than that repeats frames rather than revealing new ones.

**Seeking uses two modes, deliberately.** While the scrubber is dragged, seeks use infinite tolerance — "any nearby keyframe will do" — the cheapest seek available. On release, a zero-tolerance seek snaps to the exact frame. Restart does the same. One mode alone cannot give both a responsive drag and a frame-accurate resting position.

**Seeks are coalesced: at most one in flight, and only the newest target is kept.** A drag emits values far faster than AVPlayer can service them, and queueing every one makes the picture fall progressively behind the finger. Intermediate positions are dropped on purpose.

**Review happens on the iPad Air 11".** A 6" phone is too small to show a kicker their own technique. The app is universal (`TARGETED_DEVICE_FAMILY = "1,2"`) and needed no port and no layout changes — SwiftUI adapted the clip browser sheet by itself. Clips reach the iPad through the AirDrop path described under *Getting clips off the device*.

**Capture stays on the iPhone.** No iPad is expected to offer 1080p/240 or 4K/120, so `applyFormat` would find no matching format and set the status to "No format matching …" — it fails visibly rather than crashing, but the footage would not be measurable. **This has not been confirmed on the iPad**, and the 70-format scan used during the capture spike is no longer in the codebase. It does not need confirming unless capture on iPad is ever wanted.

Playback work can be validated in the iOS Simulator; capture work cannot, because the Simulator has no camera and exposes no real capture formats.

### Standing constraints from the free-tier account

- Builds signed under a Personal Team **stop launching after 7 days** and must be re-run from Xcode. Expected behavior, not a bug.
- TestFlight and App Store distribution are unavailable without the paid program ($99/year).
- A Personal Team is capped at **10 App IDs per 7-day period**, so bundle identifiers should be chosen deliberately rather than by trial and error.

## Next Steps

Completed work is recorded under *Current State → What is done*. This section holds only what has not been done.

Steps 3 and 4 are written and running on the Mac. What follows is what remains.

**Step 5 — Establish measurement accuracy.** Mostly done, and what remains has been deliberately deferred behind Step 7. Ten of eleven 2026-08-22 clips track the right ball and nine produce sound metrics, against two and zero before 2026-08-24.

**What was achieved.** On every clip whose track reaches the ground, observed displacement matches the paced landing to within 3–10%. That is the first end-to-end validation this project has had: focal length from field of view, ball diameter as scale, per-frame depth and 3D geometry, all confirmed against a distance measured on the pitch rather than against themselves.

**What remains.** Fitted gravity still averages 8.3 rather than 9.81, and the cause is a progressive bias in the detector's flight diameters — see *The gravity discrepancy*. Correcting that bias is the outstanding work.

**Step 7 was moved ahead of this, on a premise the export has since disproven.** The worry was that the bias belongs to the PyTorch model's boxes and that Core ML export would change them, so measuring it first would mean measuring it twice. Measured 2026-08-24, the export reproduces the boxes to **0.00%** — so the bias would have transferred and the reordering was not necessary for that reason.

It was worth doing anyway, and by some distance. Exporting first is what surfaced the crop architecture, which resolved the largest porting risk on the books and revealed that full-frame 1280 — the obvious on-device compromise — silently loses the ball mid-flight. Neither would have been found by finishing the accuracy work first. **The decision was right; the stated reason was wrong.**

Two things worth doing whenever this resumes:

1. **A synthetic validation harness.** Every debugging session so far has lacked a known answer. Generating a ballistic trajectory with chosen parameters, projecting it through the pinhole model, and feeding it to `compute_metrics.py` would establish whether the maths is right independently of any footage — and would turn the noise tolerance and the ±15° guardrail from arguments into measured curves. It would also compare 1080p against 4K on the *same* kick, which no single-phone filming session can do. It would have caught the landing-window bug in an afternoon.
2. **Two clips still fail and are not understood.** Kick 7 acquires for a single frame and collapses; kick 10 detects correctly but its track only starts near the end of the clip. Neither is diagnosed.

**Before anything else, check the prerequisites.** The eleven clips must be at `~/Desktop/clips/`, and both virtual environments must exist — `tools/.venv` from `tools/requirements.txt`, and `tools/.venv-export` from `tools/requirements-export.txt`. Both are gitignored and neither survives a fresh clone. Each requirements file carries its own build instructions.

**Then validate against ground truth**, which is the fastest way to see whether anything has regressed:

```
./tools/.venv/bin/python tools/validate.py carry
./tools/.venv/bin/python tools/validate.py height
```

`carry` should report four clips between −3% and −10%; `height` should read about 1.09 m across three. Different numbers mean something changed.

**Reproducing the current results.** Detection, then metrics; the 4K clips need their dimensions passed:

```
for f in $(ls -1 ~/Desktop/clips/*.mov | sort); do ./tools/.venv/bin/python tools/detect_ball.py "$f" --camera-distance 9.14; done

for c in tools/frames/*-track.csv; do case "$c" in *1080p240*) W=1920; H=1080;; *) W=3840; H=2160;; esac; ./tools/.venv/bin/python tools/compute_metrics.py "$c" --width $W --height $H --ball-size 4; done
```

**Check implied range before believing any metric.** If a clip reports the ball 20–31 m away when the camera stood at 9.1 m, it has locked onto someone else's football — see *Analysis pipeline*.

**Seven clips can never be checked against their paced landings, and no amount of processing will change that.** Their tracks end before the ball lands; raising `--max-gap` to 90 pushed out the termination frames while leaving every longest-unbroken segment unchanged, because the ball had left the picture. The footage does not contain the answer.

The cause is that the session was filmed to measure kicks and then used to validate the pipeline, which want opposite framing — see *Measurement Approach*. `shot-list.txt` item 14 now requires the landing in shot for validation footage.

**Step 6 — Verify on hardware what is written but untested.** Two things, both quick:

- **The ball size metadata.** The picker builds and runs, but no recording has been checked. Record a clip and confirm the status panel reads `· ball 206.1 mm` rather than `BALL SIZE MISSING`. That is the half of the two-copy scheme that cannot be checked by looking at filenames in Files.
- **Import and share in the clip browser.** Built in response to the AirDrop trouble and never exercised. Import a `.mov` from Files, and share one out.

**Step 6b — Measure what Photos does to 240 fps.** Run a 1080p/240 clip through Photos by the same route the 4K/120 clip survived, and probe it.

The store question no longer depends on this — `Documents/Clips/` stays on its own merits, for the reasons under *Should Photos be reconsidered as the store?*. The test is still worth running, but the reason has changed: it tells us what an **import probe** will encounter when a coach brings in a clip that has passed through Photos. That probe has to exist anyway for external footage, and this is the case it most needs to catch.

**Step 7 — Port the pipeline to the app. This now comes before the rest of Step 5.** Export the detector to Core ML, drive it through `VNCoreMLRequest`, replace OpenCV registration with the Vision equivalents, and reimplement the trajectory fit in Swift.

**The ordering was reversed on 2026-08-24.** This step previously read "not to be started before Step 5; porting a pipeline whose accuracy is unknown would only make its errors harder to find." That was right while the unknown was the *physics*; the physics is now validated against paced landings. The reason recorded at the time — that Core ML export would change the boxes — turned out to be false, but the reordering paid for itself anyway. See *Step 5*.

**Done on 2026-08-24:**

- `yolo11n` exported to Core ML as `yolo11n.mlpackage`, verified to reproduce PyTorch boxes to 0.00%.
- The crop architecture measured and validated — 640 px at native resolution matches full-frame 3840. This is what gets ported, not the Mac's full-frame approach.
- A pinned export environment built so the conversion is reproducible.

**Remaining, cheapest and most decisive first:**

1. **Run the exported model on the Neural Engine and repeat the box comparison.** Everything above was measured on the Mac's CPU or GPU. The ANE may use float16 and is what ships. Until this is done the export is validated only as a conversion, not as a runtime.
2. **Port the tracker with crop-based inference**, driven through `VNCoreMLRequest`. Acquire once on a full frame, then track in 640 crops.
3. **Correct the diameter bias**, which can now be done on either side since the boxes match.
4. **Port the maths.** Low risk: `compute_metrics.py` is pure numpy and every call has an Accelerate equivalent.
5. **Replace registration with Vision** and check it against the OpenCV results on the same clips, since it is a different algorithm rather than a reimplementation.
6. **Add a camera distance control to the Record screen.** The acquisition gate needs the distance the coach paced out, captured per clip beside the ball size for the same reason — it describes the clip, not the app.


**Step 8 — Filming guardrails in the app.** Framing guidance before the kick, and a compliance check afterwards. The check is cheap and concrete: the ball's diameter trend across the flight measures how far off perpendicular the shot was, and background registration already measures camera movement. Both numbers exist in the Mac pipeline; nothing surfaces them to the coach.

**Step 9 — A results screen.** Nothing in the app displays a metric. Whatever it shows must label carry and apex as theoretical, and should surface the quality signals — off-square angle, camera drift, fitted gravity — rather than presenting a bare number as though it were certain.

### Optional, not scheduled

Both clip-transfer refinements once listed here — a `ShareLink` in the clip browser, and `CFBundleDocumentTypes` plus `onOpenURL` — **have been built**, along with an Import button that was not anticipated. They moved out of this section the moment the Files detour became irritating in real use, which is what this section said should trigger them. See *Getting clips off the device*.

**Telestration colour picker.** Today every stroke is yellow. Add a picker so the coach can change colour mid-session — one mark for the plant foot, another for the ball's path, without them reading as the same annotation.

**The palette is chosen for contrast against turf, not for familiarity:** yellow, white, cyan, magenta. Green and blue were requested and rejected on the pitch test — green vanishes against grass, which is the only background this app ever has, and blue is weak in low light and against dark kit. Red was rejected too: it collides with the training cones already in frame. The colours that survive are the ones no football pitch contains.

Two consequences to settle before this is built, both of which reach further than the feature itself:

- **A stroke must carry its own colour.** Strokes are currently normalised to the picture with a single implicit colour. Adding a per-stroke colour field changes the stroke model, and the same model is what *Annotations are not saved* will have to persist. Settle the field first; migrating a saved format afterwards costs more.
- **The picker belongs in the always-visible cluster.** Colour is a mode in the same way drawing is, and the current colour must be legible at a glance or the coach draws the wrong one. That puts it alongside the drawing toggle and clear button rather than in the auto-hiding panel — a corner already competing with the zoom badge. The layout question is real and is the reason this is not a one-line change.

**Move configuration off the Record screen.** The capture screen carries a live preview, a configuration picker, a ball size picker and a record button, and it is too crowded. To be revisited once the measurement mechanics are settled — the UI is not what is being proven right now.

The constraint that shapes any redesign: **ball size is not a setting and cannot be moved to a preferences page.** It is per-clip data captured at record time, for the reason recorded under *How does the app learn the ball's size?* — a setting describes the app's state now, not the state when a clip was filmed. Capture configuration is the same. Both must stay verifiable at the moment of capture.

The pattern that fits is the one Apple's Camera app uses for `4K • 60`, and that Halide and Kino use over the viewfinder: **a single always-visible status line — `1080p·240 · Size 4` — that expands into a sheet on tap.** Genuine app preferences go behind a gear; preview and record button get the rest of the screen. Filmic Pro's dense bar of expandable pods is the counter-example to avoid.

That status line is a correctness feature, not tidiness. A clip whose ball size is unknown is not measurable at all, and `BALL SIZE MISSING` is a failure that has to be caught before the kick, not after.

**A clip info panel in Review, and footage the app did not record.** A coach may be sent video from a source outside the app — a GoPro on the far post, a clip emailed from another parent. Review should show what a clip actually is, and the app should be able to measure footage it did not capture.

**Do not ask the user for what the file already knows.** Resolution, duration and rotation come from `AVAsset`; real frame timing comes from walking sample presentation timestamps with `AVAssetReader`, which is what `tools/extract_frames.py probe` does on the Mac. `nominalFrameRate` is a label and must not be trusted — see *Capture*. The panel can populate itself.

**The blocker is not metadata, it is focal length.** Every distance in the pipeline comes from `fx`, and `fx` comes from `AVCaptureDevice.Format.videoFieldOfView` — an API that exists only because the app ran the capture session. For a clip from another camera there is no field of view to read, and without it apparent ball size cannot be converted into range. Three routes, in increasing order of interest:

- A lens preset library (GoPro Hero 12 Wide → known FOV). Practical, but a maintenance burden, and a user who picks the wrong mode gets confidently wrong numbers.
- Maker metadata from the file. GoPro writes GPMF telemetry, but this is device-specific and fragile.
- **Calibration from a known reference in the scene.** A measured length in the ground plane — cones at a known spacing, the goal width, the penalty box — solves for scale without knowing the lens at all. It works for any camera ever made, and the 2026-08-22 session already filmed cones at 5 yards for exactly this kind of cross-check.

**Two hazards specific to action cameras:** wide modes carry heavy barrel distortion, and in-camera stabilisation such as GoPro's HyperSmooth applies the same non-rigid warp that this project disables on the iPhone for corrupting geometry. It has to be off at the camera, and the app cannot enforce that — only warn.

**Other kicks: passing, goalkeeper punts, drop kicks, goal kicks from the ground.** Deliberately out of scope until the goal kick works end to end.

Most of the pipeline is kick-agnostic — it measures a ball's launch conditions and does not care what produced them. What changes per kick type is the filming guardrail, the expected speed and angle ranges, and therefore the sanity checks. One case does not fit the model at all: **a ground pass may have no ballistic phase**, so carry and apex are meaningless for it and a rolling ball needs different physics entirely.

## Open Questions

**Which capture configuration gives better metric accuracy: 1080p at 240 fps, or 4K at 120 fps?**

- **1080p at 240 fps** — roughly 12.5 cm of ball travel between frames at 30 m/s. Twice the trajectory samples, and the shorter per-frame exposure means less motion blur, which matters because blur inflates the apparent ball diameter and degrades the centroid. Calibrated from field of view; no intrinsic matrix available.
- **4K at 120 fps** — roughly 25 cm between frames, but four times the pixels across the ball, so a more precise diameter estimate, which propagates into distance and therefore into every metric.

**Both configurations are currently calibrated from field of view, and 4K/120's intrinsic matrix is not in fact an advantage today.** The camera reports intrinsics only to a live capture session; they are **not stored in the recorded movie file**. Deliverable 1 analyses a saved video, so intrinsics are unavailable at analysis time unless they are captured alongside the recording and written to a sidecar — which has not been built. Until it is, the choice is purely samples-and-blur versus pixels-on-ball.

**This cannot be settled by filming the same kick both ways.** One phone runs one format at a time, so a single kick cannot be recorded at 1080p/240 and 4K/120 simultaneously. Comparing configurations means comparing sets of kicks in aggregate, or using two devices. The 2026-08-21 session produced five of each; the 2026-08-22 session came out **3 × 1080p and 8 × 4K**, which is a thin and lopsided basis for the comparison even though it is good data for the physics. A future session wanting to settle this should hold the split even and record which is which deliberately.

**The pipeline now measures the thing that decides this.** `compute_metrics.py` reports range scatter about the fitted trend and fitted gravity, both of which degrade with depth noise. Running the same analysis across the 1080p and 4K sets answers the question empirically rather than by argument.

**One comparison has been run and it was not valid.** At `--imgsz 1280`, 1080p showed 3.7% relative diameter scatter against 4K's 4.4%, suggesting 4K was no better. But that setting downscales a 1920-wide frame by 0.67× and a 3840-wide frame by 0.33× — 4K was handicapped by twice as much. A fair test needs both at native resolution, which is now the default. **The question remains open.**

**Pixels on the ball, and why filming distance dominates accuracy**

Range is recovered from apparent diameter: `Z = fx × D / d`. Run backwards, that gives the ball's pixel width at a given range for a Size 4 ball (D = 206 mm):

| Range | 1080p (fx ≈ 1260) | 4K (fx ≈ 2520) |
|---|---|---|
| 3.7 m *(first footage)* | 70 px | 140 px |
| 10 m | 26 px | 52 px |
| 20 m | 13 px | 26 px |
| 27 m | 9.6 px | 19 px |
| 40 m | 6.5 px | 13 px |

Relative range error tracks relative diameter error one for one. Half a pixel of error on a 70 px ball is 0.7%; the same half pixel on a 9.6 px ball is 5%, and it propagates into every metric.

**The geometry traps you.** With a 74.6° field of view, framing a 40 m flight means standing about 26–27 m back. At that range the ball is under 10 px at 1080p. Whole flight in frame and a well-resolved ball are in direct conflict, and no technique resolves it — only a longer lens or a second camera would.

**This is evidence for 4K/120** in the open question above. At realistic goal-kick range it roughly doubles the pixels across the ball, and the diameter estimate is the weakest link in the chain.

**A constant-range assumption was tried and abandoned.** The reasoning was that for a side-on shot the ball stays at roughly constant range, so diameter could be averaged once to fix the scale and the flight treated as flat. Measured against real footage that failed silently and badly. The ball was travelling ~11–15° toward the camera, its apparent size grew across the flight, and the steadily inflating scale cancelled gravity's curvature almost exactly — the fit reported gravity as **−0.16 m/s²**, a straight line through what should have been a 48-pixel sag.

**Depth is now computed per frame**, with the range trend smoothed by a straight-line fit before use: over a fifth of a second range changes almost linearly, while measured diameter wobbles a few percent frame to frame, and because both X and Y are multiplied by range that wobble would otherwise contaminate every axis. Moving to 3D raised fitted gravity from −0.16 to 3.49 m/s², which confirmed the diagnosis without resolving the problem.

**What flight model produces carry distance and max height — drag-free, or with air resistance?**

**Decided: both, computed and shown side by side.** The gap between them is itself the honest answer — it shows how much of the figure is physics and how much is assumption. Implemented in `compute_metrics.py`: a closed-form parabola, and RK4 integration with quadratic drag at Cd 0.25, mass by ball size, air density 1.225 kg/m³. On the first footage at ~13 m/s the two differ by about 12% in carry; at goal-kick speeds the gap widens sharply.

**Two limitations are recorded in the code and must reach the UI.** The drag coefficient of a football is not constant — it falls through the drag crisis around 10–15 m/s and varies with panelling — and a single value is used. And spin is ignored entirely, so there is no Magnus force: a ball struck with backspin carries further than either model predicts.

The reasoning that led here, kept because it still applies:

The two answers differ enormously. A size 4 or 5 ball leaving the foot at ~30 m/s is deep in a drag-dominated regime; a vacuum parabola can overestimate carry by roughly a factor of two. This is not a refinement, it is the difference between a number that means something and one that does not.

- **Drag-free parabola** — closed form, no parameters beyond launch velocity and angle, and defensible if the figure is presented explicitly as a theoretical maximum rather than a prediction of where the ball would land.
- **With drag** — needs a drag coefficient and a ball mass, and realistically numerical integration rather than a closed form. Closer to reality, but introduces constants the app cannot measure and must assume.

Deliverable 1's wording, "theoretical carry distance," leans toward the first. That has never been confirmed as a decision, and **whichever is chosen must be stated in the UI**, or the coach will read a theoretical maximum as a real distance.

Because carry distance and max height are computed from launch conditions rather than measured (see *Measurement Approach*), the flight model is not a refinement of those metrics — it *is* those metrics. That is why showing both was chosen over picking one.

**What remains open** is what the UI presents. Two numbers with a caveat is honest but may be more than a coach wants mid-session. Whichever is shown, it must be labelled a theoretical maximum, or the coach will read it as where the ball would land.

**How does the app learn the ball's size?** — **Answered.**

A segmented picker of the three standard sizes on the Record screen, captured **per clip at record time**, not as a global setting: a setting describes the app's state now, not the state when a clip was filmed, and a clip whose ball size is unknown later is not measurable at all.

Diameters come from the midpoint of each size's official circumference range — 189.4 mm, 206.1 mm, 219.6 mm for sizes 3, 4 and 5 — and are nominal. A ball's real diameter varies with inflation pressure and wear, which puts a floor on accuracy that no amount of tracking precision can lift.

**The size is written twice, deliberately.** A filename token (`-sz4`) so it is legible in the Files app and to analysis code without opening the video, and `mdta` metadata inside the movie as the authoritative copy. They can only disagree if a file is renamed, and renaming damages the filename while leaving the metadata intact — so the copy that survives the failure mode wins. Both travel with the file over AirDrop, which a sidecar file would not.

Custom diameters in millimetres were considered and rejected as slower to set pitch-side. Revisit if a measured ball is ever wanted.

**Should Photos be reconsidered as the store?**

Raised because moving clips from the iPhone to the iPad is genuinely painful, and Photos would sync them automatically. The transfer problem is real: AirDrop routes videos into Photos without asking, the Files-app folder does not exist until the app has written something, and the cable is the only reliable route.

**The evidence is now mixed, and the original objection is no longer proven for every case.**

| Test | Result |
|---|---|
| **4K/120** — iPhone → AirDrop → iPad Photos → Save to Files → cable → Mac | **119.94 fps, timing intact.** Filename preserved. |
| **1080p/240** — same route | **Not tested.** This is the case that matters. |
| App writes to Photos and reads back via `PHImageManager` | **Not tested.** This is what originally failed. |

240 fps is the aggressive case: iOS treats high-frame-rate video as slow motion and 240 gets the harsher treatment, which is what produced the original 8× error. 120 passing does not imply 240 will.

The second gap is subtler and matters as much. Both tests move a *file* through Photos. The proposal is different — the app **writes** through `PHPhotoLibrary` and later **reads** through `PHImageManager` or `PHAssetResourceManager`. That is a separate code path, and it is the one that failed. A clean 240 result would justify building a small test of the app's own write-and-read path, not switching outright.

**Two further risks, independent of retiming:**

- **iCloud "Optimize Storage"** can replace a local original with a smaller proxy and fetch the real one on demand. On a pitch with no signal that is a clip which cannot be analysed.
- **Photos presents the slow-motion version**, so what the coach sees and what the analysis reads would be different assets. That is a class of bug that hides well.

**A second, stronger argument has since been raised: ingest, not sync.** The original case for Photos was that it would move clips to the iPad automatically. The better case is that a coach may be *sent* footage — emailed a clip filmed on a GoPro or another parent's phone — and needs a way to get it in. See *A clip info panel in Review* under *Optional, not scheduled*.

**How comparable apps resolve this: both, with distinct roles.** Photos and Files are import sources and export destinations; the app keeps its own working store. Hudl Technique, OnForm, Coach's Eye and LumaFusion all accept video from anywhere and then **copy it into an internal library they control**. Import copies, it never references — which is precisely what avoids the two traps identified above, since a copied file cannot be swapped for an iCloud proxy and cannot be silently served as a slow-motion rendition.

Read that way the question largely dissolves, and the answer keeps the current architecture:

- **`Documents/Clips/` stays as the store.** Photos becomes a third *import source*, alongside the Files picker and the share-sheet path already built.
- **The ingest problem is mostly solved already.** A coach emailed a clip can save it to Files and use Import, or share it straight into GoalKick via `CFBundleDocumentTypes`. A Photos picker is incremental convenience rather than an architectural change.
- **Probe presentation timestamps on every import, whatever the source, and warn when timing looks retimed.** This is needed for external footage regardless, so one check covers Photos slow-motion, GoPro clips, and anything that has been through a messaging app. It converts the retiming hazard from a reason to avoid Photos into a thing the app detects.

**On monetization:** restricting input to in-app recording was considered as a way to make the app worth buying, and rejected. The value is in the measurement pipeline, not in owning the capture path; every comparable app monetizes analysis, team management and cloud sharing while accepting footage from anywhere. Locking the input narrows where the app is useful without defending the part that is hard to build. Moot in the near term regardless — App Store distribution needs the paid Developer Program, and this project is on a free Personal Team.

**Decision for now:** `Documents/Clips/` stays as the store, and that is now settled on its merits rather than pending a test. What remains open is only whether Photos is added as an *import source*, and the 240 fps retiming test is still worth running because it tells us what an import probe will encounter.

**How should a goal kick be filmed?**

Still open as a protocol, but the first session is now on record. Camera distance, angle relative to the kick direction, and whether the operator pans or holds the phone fixed all change how hard tracking is and how accurate the result can be.

**First footage, filmed 2026-08-21:** Size 4 ball, teal. Ten clips — five at 1080p/240, then five at 4K/120. Camera **side on and static** (handheld, no deliberate pan; the framing holds across a whole clip). Distance not measured. These clips predate the ball size selector, so they carry no size token and no metadata.

**What was filmed is not a goal kick.** The kicker strikes into a portable net. Measured from the first clip: the ball is **~4.2 m** from the camera, contact is at frame 545, free flight begins around 548 once the ball leaves the boot, and it reaches the net by ~589 — about **0.17 s** of flight. Speed is ~13 m/s at ~25°, against the ~30 m/s this document assumes elsewhere. The kick runs **11° off perpendicular, toward the camera**, right at the guardrail limit.

**All four metrics are still obtainable in principle**, because carry and apex are computed from launch conditions rather than observed — see *Measurement Approach*. An earlier note here claimed the net made them unrecoverable; that was wrong.

The clips are excellent tracker development footage precisely because they are easy: sharp ball, ~60–70 px across, near-static camera, strong colour separation, never against sky. A tracker that fails here fails everywhere. They are **poor physics validation footage**, because the flight is short and not square, which is where the trouble described below begins.

**Also note the format comparison cannot be done as this document proposes.** One phone has one active format at a time, so the same kick cannot be recorded at 1080p/240 and 4K/120 simultaneously. The five-and-five sets are different kicks. Comparing configurations means comparing sets in aggregate, or using two devices.

**Second session, filmed 2026-08-22 — the first footage with ground truth.** Eleven kicks on an open field, ball flying free with no net. Size 4. Camera **10 yards from the ball, side on and handheld**, for all eleven. Red cones laid out at a measured 5 yards apart. This is the session `shot-list.txt` was written for, and it is the dataset the project now runs against.

**Every kick has a paced landing distance**, in capture-timestamp order, which is kick order:

| Kick | Landing | Kick | Landing |
|---|---|---|---|
| 1 | 15 yds | 7 | 17.5 yds |
| 2 | 16.5 yds | 8 | 15 yds |
| 3 | 25 yds | 9 | 15.5 yds |
| 4 | 16 yds | 10 | 17.5 yds |
| 5 | 19 yds | 11 | 12 yds |
| 6 | 9 yds | | |

Kick 11 is the deliberate off-square control the shot list called for — roughly 30° off perpendicular and further back. Measured from the footage it is 56.5° off, so the control is more extreme than intended, which made it a better test than planned.

**The formats came out 3 × 1080p/240 and 8 × 4K/120**, not the planned five and five; kicks 1, 6 and 7 are the 1080p ones. All eleven probe clean — real frame timing matches nominal, rotation 0° in metadata on every clip. Clips live at `~/Desktop/clips/`.

**Two things this session established beyond the metrics.** The scale model checks out: the ball at rest measured 56.8 px against a predicted 56.8 px for a Size 4 at 10 yards through `fx` 2520, which is the first time focal length, ball diameter and a real measured distance have been confirmed to agree. And the cones, laid out at a known spacing, are an independent scale reference in the ground plane — useful in their own right, and the same technique that would let the app measure footage from a camera whose lens it knows nothing about.

**Which file is which kick is recorded in `tools/sessions/2026-08-22.csv`**, along with the paced landings and which clips reach the ground. Everything below is by kick number and needs that file to be usable.

**Results, as of 2026-08-24.** Ten of eleven clips track the right ball; nine produce sound metrics. Kick 7 acquires for a single frame and collapses; kick 10 detects correctly but its track starts near the end of the clip. Neither is diagnosed.

| Kick | Speed | Fitted gravity | Landing captured |
|---|---|---|---|
| 1 | 13.75 m/s | 4.40 — suspect | no |
| 2 | 12.55 m/s | 8.19 | **yes** |
| 3 | 17.35 m/s | 7.42 | no |
| 4 | 13.61 m/s | 8.31 | **yes** |
| 5 | 16.03 m/s | 7.01 | no |
| 6 | 12.85 m/s | **10.48** | **yes** |
| 8 | 14.99 m/s | 6.79 — suspect | no |
| 9 | 15.40 m/s | 7.74 | **yes** |
| 11 | 14.93 m/s | **9.23** | no |

**Only the four clips with a captured landing can be checked against the paced distance**, and all four match to within 3–10%. The rest lose the ball before it lands.

**Two things this session got wrong are worth keeping.** A pitch in normal use has other footballs on it — a bag of spares on the touchline, another age group playing alongside — and they defeated the detector before the acquisition rule was fixed. And the instruction to let the ball fly out of frame, which is right for tracking, means the landing is never seen; validation footage needs a wider frame or more distance. Both are now in `shot-list.txt`.

Camera distance is the dominant accuracy parameter (see *Pixels on the ball* above) and pacing it out, as was done here, should be standard.

**The gravity discrepancy — two causes found, one fixed, one located**

`compute_metrics.py` fits gravity from the data rather than assuming it. Nothing tells the fit that gravity is 9.81; the value falls out of the pixel scale, the frame timestamps and the 3D reconstruction alone. It is the only independent check the pipeline has, and for most of this project's life it did not land.

**The cause is the flight window, and this document previously ruled that out in error.** An earlier version of this section listed the flight window among the eliminated causes, on the grounds that contact detection and boot-phase exclusion had both been corrected. A window has two ends and only the start had been fixed. The fit was still running past the *end* of free flight — through the bounce, the second bounce, and the ball rolling to a stop.

Measured on the 2026-08-22 control kick. Same clip, same detections, only the window changed:

| Fit window | Fitted gravity | Vertical residual | Carry |
|---|---|---|---|
| Contact to end of track — 215 frames, two bounces and the roll | 1.37 m/s² | 222.4 mm | 2.72 m |
| Free flight only — 104 frames, f654 to f757 | **9.66 m/s²** | **3.2 mm** | 10.30 m |

A parabola fitted across a flight *and* its bounces is very nearly a straight line, which is why the estimate collapses toward zero rather than merely degrading. The 222 mm residual was the fit announcing it could not describe the data; nothing was reading it.

**`find_landing()` now cuts the fit at the bounce automatically**, from the reversal in vertical image position after the apex. It works entirely in image space and needs no scale, no focal length and no depth — all of which are noisier than the pixel row the ball sits on. `--last-frame` overrides it, `--keep-after-landing` disables it, and when no landing is found the tool now says so rather than silently fitting to the end of the track.

**The off-square cross-term is real, but it is not what was breaking the estimate.** The mechanism still stands. Writing `u` for the ball's vertical image position relative to the principal point:

```
Y = −u·Z/fx      →      Ÿ = −(ü·Z + 2·u̇·Ż)/fx
```

The quadratic term the fit calls "gravity" has two contributors: real image curvature, and a cross-term between vertical image speed and range rate. The correction is genuine and square filming still removes it.

But the control kick was filmed **56.5° off perpendicular** — nearly four times the guardrail — with `vz` at +10.95 m/s, which is the most adverse geometry in the entire dataset. It fitted gravity to within 1.5% anyway. Whatever the cross-term costs, it is second order next to the window.

**The whole set has since been run, and the window was not the only problem.** Fitted gravity across nine clips now clusters between 6.8 and 10.5, mean about **8.3** — far better than the old 3.5-to-12.3 spread, and still reading systematically low. What follows is what that residual bias turned out to be.

**The vertical axis reads about 22% low while the horizontal validates.** On every clip whose track reaches the ground, observed displacement matches the paced landing to within 3–10%. The vertical does not, and the two share a range and a focal length.

The fit is *internally* consistent, which is why this hid for so long: with `vy` and gravity both scaled down together, flight time `2·vy/g` is unchanged, so the duration agrees with the fit while both disagree with reality.

**Four causes were tested and eliminated, in this order:**

| Suspect | Verdict |
|---|---|
| Motion blur inflating the detector box | **Refuted** — the box *shrinks*, 58.4 → 42.9 px as confidence falls to 0.34 |
| Air resistance biasing a drag-free fit | **Refuted** — fitting against the drag ODE moved gravity only 7.65 → 7.74 |
| Camera tilt / wrong principal point | **Refuted** — gravity is provably invariant to `cy0`, which contributes `cy0·Z/fx`, and `Z` is linear in time, so it can only add a linear term |
| Anchoring range to the resting diameter | **Tried and worse** — see below |

**The cause is a progressive bias in the flight diameters.** Camera height recovered from the ball resting on the ground and again at landing —

```
h = D·(cy₁ − cy₂)/(d₁ − d₂)
```

— needs neither focal length nor principal point, and reads **1.10 m** across three clips against a phone held at about **1.4 m**. Working the geometry backwards on kick 9: the resting diameter is right (56.6 px, matching the paced 9.14 m to under 1%), while the landing diameter is under-read by 6.3% — 37.0 px where the flat-pitch constraint demands 39.5.

So the detector's box degrades as the ball recedes and blurs. **The horizontal survives it because `X` uses `D/d` directly, where a 6% error stays 6%. The vertical goes through the range slope, where the cross-term `2·u̇·Ż/fx` amplifies it.** That is the same cross-term this document has named since the beginning — now with a cause rather than only a magnitude.

**Anchoring the range line to the resting diameter followed obviously and was wrong.** A free fit spreads the flight bias between intercept and slope; anchoring the intercept forces the *slope* to absorb all of it, and the slope is what gravity is most sensitive to. Measured across the set it moved gravity the wrong way on nearly every clip — 8.13 → 6.11, 7.37 → 6.16, 7.01 → 6.25, 9.49 → 8.28 — while improving carry slightly. Kept as `--rest-anchor`, off by default, so the experiment can be repeated rather than re-argued.

**Correcting the diameter bias itself is the remaining work, and it can be done on either side.** The concern was that the bias belongs to *this* detector's bounding boxes and that a Core ML export would change the numerics, so characterising it on the Mac risked measuring it twice. Measured 2026-08-24, the export reproduces the boxes to **0.00%** — the bias is a property of the architecture, not the runtime, and whatever is learned on the Mac transfers.

One caveat survives: that comparison ran on the Mac's CPU or GPU, not the Neural Engine, which may use float16. Until the box comparison is repeated on a device, "the numerics are identical" is proven for the conversion and assumed for the runtime.

**The earlier four-run table has been removed** rather than kept. Every figure in it was produced by fitting past the end of the flight, so the numbers measured the bug and not the footage. The one finding from it that survives on its own evidence is that detector input resolution matters: raising `--imgsz` from 1280 to 1920 on the same 4K clip cut range scatter from 200 mm to 118 mm. `--imgsz` now defaults to the clip's own width.

**That default is load-bearing and may not survive the move to the device.** See *Porting risks* under Tech Stack — native-resolution inference is the least device-friendly thing in the pipeline, and diameter precision is what every distance rests on.

**The c1 anomaly is superseded and needs re-measuring.** It was recorded here that on c1 the ball appeared to accelerate upward across the tracked frames, which free flight forbids, with diameter bias against dark netting as the leading suspect. That clip is a kick into a net and its window very likely included the ball striking it — the same class of error as the bounce, at a different obstacle. Re-run it with the landing cut before treating it as a separate mystery.

**The protocol lives in `shot-list.txt` at the repo root.** Plain text so it opens on a phone in a field. It covers where to stand, how far back, how to frame the ball, and what to shoot. It was followed on 2026-08-22 and revised afterwards from what that session taught. Three items in it carry the most weight:

- **Clear other footballs out of shot.** The one the coach is measuring must be the nearest. This cost nine clips of eleven before the acquisition rule was fixed.
- **Pace out where the ball first lands.** Done for all eleven kicks on 2026-08-22, which finally gives carry distance something to be checked against. Keep doing it every session; it costs nothing but counting.
- **One kick deliberately off perpendicular**, as a control. Shot as kick 11 and it worked as intended — the off-square warning fired at 56.5°. Note the diagnostic did *not* degrade the gravity fit the way this document expected, which is what exposed the real cause.

Keep `shot-list.txt` and this section in step as the protocol changes.

## End of Document
