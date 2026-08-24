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
- **Keep this document current as we go.** Whenever anything is accomplished — a decision made or reversed, code written, a measurement taken, a punch list item finished, an assumption disproven — update `project_notes.md` at that point, not at the end of the session. Record what changed and why, and remove what it superseded rather than leaving both. The reason is cost: batched updates are where the file and the work drift apart, and reconciling them afterwards takes longer than writing them down at the time and is less accurate, because the reasoning has been forgotten by then. See the permission carve-out under *Code Delivery Rule*, which is what makes this possible without asking every time.
  - **Updating the section you are writing in is not enough.** This file states the same fact in several places on purpose — a finding, the status table that summarises it, the file table that lists the code, the risk it retires, the next step that assumed it. A result recorded in one place and left stale in five is worse than not recording it, because the file now contradicts itself and the reader cannot tell which entry is current.
  - **So every time something is recorded, search the file for what else asserted it** — the claim, the file or command it names, the assumption it rests on — and bring those into line in the same pass. Do this as part of the update, not as a review afterwards and never at the end of a session. Half an hour of work has already been enough for a fact written here to go stale elsewhere in this same file.
  - **The most dangerous staleness is a discharged caveat.** A warning that some result is unproven, left in place after it has been proven, does not merely misinform — it suppresses work that is now safe to do. Hunt those specifically.
- **`README.md` is frozen. Do not edit it.** Until I say otherwise, make no changes to `README.md` for any reason — not corrections, not new findings, not bringing it into line with this file. It will get one clean rewrite once the project is finished. Piecemeal updates are what caused the trouble: the two documents drift, they disagree in ways that are not obvious, and a reader cannot tell which one is behind. `project_notes.md` is authoritative in the meantime. Where the README is known to be wrong or behind, add it to *Where README.md disagrees with this file* — that catalogue is what the eventual rewrite will be built from, so it should keep growing while the README itself stays untouched.

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

**`project_notes.md`: never edit without my explicit permission, given in chat, for that specific edit — with one standing exception, below.**

**The standing exception: recording what has actually happened.** Granted 2026-08-24, to make *Keep this document current as we go* workable without a confirmation after every action. You may update this file **without asking** when you are recording a thing that has already occurred — a decision I made, code that was written, a measurement that was taken, a punch list item finished, an assumption disproven. Say in chat what you recorded and where.

**The exception is narrow and everything else still needs permission.** Rewriting reasoning, changing scope, restructuring a section, reordering the punch list, removing a decision, or adding a new position I have not taken are **not** covered, whatever prompted them. The test is whether you are transcribing something settled or authoring something new: transcription is covered, authorship is not. When in doubt, it is not covered — ask.

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

**That floor is a property of the ball's size in pixels, not of the input setting** — measured independently 2026-08-24 by shrinking a sharp crop rather than by downscaling a frame, the detector holds accuracy to ±2% down to **20 px of ball** and finds nothing at **15 px**. The two findings are the same limit reached by different routes, which is why an aggressive `--imgsz` and an over-distant camera fail identically. See punch list 2.1 rung 13, which also converts the floor into a working distance: **26 m at 4K, 13 m at 1080p**.

**The export changes nothing, which was not a foregone conclusion.** The same frames through `yolo11n.pt` and `yolo11n.mlpackage` give **0.00% difference** in box diameter and identical confidences to two decimals. That means the diameter bias under *The gravity discrepancy* is a property of the architecture rather than the runtime, and characterising it on the Mac is not wasted. The distance gate's 1.3 factor and the 1.6 diameter tolerance likewise carry over.

**The Neural Engine is unreachable by this export, and the GPU is what ships.** This section previously read "the Neural Engine is still untested, and it is the thing that ships." Measured on device 2026-08-24 by Xcode's Core ML performance report, that is false: the model's `storagePrecision` is Float32, the ANE requires float16, and **not one of the 242 compute operations lists the Neural Engine as a supported device.** Every one prefers the GPU. See punch list item 1.1 for the measurement.

What was actually at risk — that a different runtime would move the box coordinates — is settled for every device Core ML can use here: coordinates are identical across CPU, GPU and `.all`, and the device reproduces the Mac's diameters to two decimals. Whether float16 would move them is now a question about a *different export* that does not yet exist.

**Throughput turned out not to be a risk either.** Steady state is **5.68 ms per 640×640 inference on the GPU** of an iPhone 17 Pro. Every frame of a 787-frame 4K/120 clip would take 4.5 s. The crop architecture remains right, but for diameter precision — never for speed.

**Registration is unverified.** The Mac uses Shi-Tomasi features, Lucas-Kanade optical flow and a RANSAC affine estimate. `VNTranslationalImageRegistrationRequest` is a *different algorithm*, not a reimplementation. Drift of 250–390 px is currently being corrected on real clips, so this matters; equivalent in intent, unproven in effect.

**Camera distance is now a required per-clip input.** The acquisition gate needs the distance the coach paced out. That means a control on the Record screen beside the ball size picker, captured per clip for the same reason ball size is — it describes the clip, not the app. This requirement did not exist before 2026-08-24 and nothing in the app provides it.

**Coaches cannot pass flags.** Defaults carried 9 of 11 clips on the 2026-08-22 set, which is respectable, but two failed and the app has no way to say so intelligibly. Whatever ships must either work on defaults or explain itself.

**Motion blur: no longer a partially-measured risk. Measured 2026-08-24, and it is a hard operating limit.** This entry previously said blur "may defeat" the tracker, and cited the first footage — bright sun, ~13 m/s, panel detail legible on a ~70 px ball — as retiring the risk at that speed and in that light only. That caution was right and the risk is now quantified: **the detector stops finding the ball entirely at about 29% of its width in smear**, and is already down to confidence 0.73 at 20.6%. See *The detector's blur response*.

Relative blur is `v · exposure / D` and does not depend on the format. At 30 m/s it needs an exposure of about **1/728 s** to stay under 20%. If exposure runs to the frame interval, as it does in falling light, relative blur is 61% at 240 fps and 121% at 120 fps — both far past failure. **In poor light this pipeline does not degrade gracefully; it stops working, and a higher frame rate does not rescue it.** Nothing in the app checks exposure or warns the coach.

**On Swift 6:** the decision to stay in Swift 5 mode stands, and was reconsidered deliberately after capture was working rather than allowed to lapse. Strict concurrency turns data-race issues into hard compile errors, and the next phase — passing `CMSampleBuffer` and `CVPixelBuffer` to Vision — is the worst area for that friction, since neither type is `Sendable` and the annotations are Apple's to fix, not ours. `SWIFT_VERSION` is a single build setting, so migrating later costs the same work on a more settled design. Revisit once tracking works.

## Measurement Approach

**Only launch conditions are measured. Everything else is computed.**

Deliverable 1 asks for velocity, launch angle, and *theoretical* carry distance and max height. Theoretical means derived from launch conditions rather than observed, so the ball never has to be filmed landing. Velocity and launch angle are fully determined within the first fraction of a second after contact; carry and apex follow from the flight model.

This resolves what would otherwise be an impossible framing problem. Covering a 40 m flight requires standing ~27 m back, where a Size 4 ball is under 10 px wide at 1080p (see *Pixels on the ball*). Filming only the launch allows standing 5–12 m away, where the ball is 26–52 px and the diameter estimate is sound.

It also means footage that ends early — a ball struck into a close net — still yields all four metrics.

**Truncated flight is the normal case, not the exception, and the pipeline must be built for it.**

In ordinary use the ball will **usually** either leave the frame or be struck into a net. That is not a filming failure to be designed out — it is the direct consequence of the guardrails below. Standing 5–12 m away is what puts enough pixels on the ball to measure it, and at that distance a real goal kick is out of the frame within a fraction of a second. Telling the coach to stand back far enough to keep the whole flight in shot would destroy the diameter precision that every distance depends on. **The two cannot both be had, and this project has chosen pixels on the ball.**

Three consequences, all binding:

- **Every metric must be derived from the launch window alone** — roughly the first 0.15 s after contact. No stage of the pipeline may require the apex, the descent, or the landing to be present. Anything that needs them is validation tooling, not measurement.
- **The clip will typically be longer than the usable window, and the usable window is a short slice near the start.** The fit is cut at the *earliest* of: the detected landing, the ball leaving the frame, the ball reaching the net, or the end of the track. A window that runs past any of those contains something that is not free flight, and the failure mode is the one recorded under *The gravity discrepancy* — the fit collapses toward a straight line and reports gravity near zero, while looking perfectly healthy.
- **A net is a harder end than a bounce, and it is not currently detected.** `find_landing()` looks for the reversal in vertical image position after the apex. A ball struck into a close net never reaches an apex and never reverses; it decelerates violently against the netting and drops. That is not free flight, and nothing in `compute_metrics.py` currently identifies it. On net footage the fit window has to be ended by other means — `--last-frame`, or a check yet to be written. The 2026-08-21 session was filmed into a net, so this is not hypothetical.

**No metric should ever be reported as unavailable because the flight left the frame.** If that happens the pipeline has a bug, not the footage.

**Filming guardrails.** These are constraints on the coach, not on the software, and they are what make the measurement tractable:

| Guardrail | Why |
|---|---|
| Held steady, no deliberate pan | Handheld is the expected case — coaches will not carry tripods, and requiring one would make the app unusable. Over a ~0.15 s measurement window a steady hand drifts only a few pixels, worth roughly 1–3% on speed, and residual shake is removed in analysis by registering each frame against the background. **Panning is different in kind** and must be avoided: following the ball keeps it near frame centre while the whole background sweeps past, a far larger correction. Never pan; let the ball leave the frame rather than chase it. A tripod or any rest improves accuracy and should be used when available, but is not required. |
| 5–12 m from the ball | Sets a floor on pixels across the ball: ~52 px at 5 m, ~26 px at 10 m at 1080p. Accuracy becomes a known quantity rather than a lottery. |
| Within ±15° of perpendicular to the kick | Off-axis foreshortening under-reads velocity by roughly `cos φ` — 3.4% at 15°, 13% at 30°. |
| Ball stationary and in frame before the kick | The most accurate diameter measurement available is the ball at rest: sharp, unblurred, measurable over many frames. Scale is fixed there, once, rather than fought for mid-flight. It also makes contact detectable automatically — contact is the first frame the ball moves. |
| No other footballs in shot, or none nearer than the one being kicked | Learned on 2026-08-22, where a bag of spares on the touchline and a game on the next pitch cost nine clips out of eleven. The detector cannot know which football matters; the *nearest* one is the measurement ball, and the acquisition rule depends on that staying true. A spare ball rolled closer to the camera than the one being struck would break it. |

⚠️ **Two of the rationales in that table have been superseded by measurement and are not yet rewritten.** The guardrails themselves may well be right; what is wrong is *why* they are said to be right, and a reader taking the reasons at face value would draw false conclusions about where accuracy comes from. Measured 2026-08-24 with the synthetic harness — see punch list item 2.1:

- **"±15° of perpendicular … foreshortening under-reads velocity by roughly `cos φ`."** With exact diameters, off-square filming costs **nothing at all out to 45°**. That reasoning describes a 2D image-plane measurement; this pipeline reconstructs depth per frame and recovers the out-of-plane component. What off-square really does is **amplify diameter error** — at a 6% bias, 15° turns a 0% gravity error into 3.9% — so the guardrail earns its place, by a different mechanism, and would become irrelevant if 3.1 were fixed.
- **"5–12 m … accuracy becomes a known quantity rather than a lottery."** **This one is now measured and the rationale is simply wrong.** Accuracy is not a lottery at any distance: random noise is suppressed by √N so speed scatter is 0.03% at 5 m and 0.18% at 27 m; a systematic relative bias costs the same at every distance; and the detector's relative diameter error does **not** grow as the ball shrinks — flat within ±2% across a factor of three in apparent size. **The real limit is detection, and it is a cliff rather than a slope**: the ball is found at 20 px with confidence 0.60 and not found at all at 15 px. That converts to a working distance of **26 m at 4K and only 13 m at 1080p**, and the ball recedes during flight.

**The off-square rationale is left as it stands deliberately**, since replacing it needs a measurement of the guardrail's real cost that has not been taken. **The distance rationale should be rewritten** — the measurement exists, and what it says is that the number may be about right while the reason is not. The guardrail is protecting against losing the ball, not against imprecision, and it should say so, because the two imply different remedies: a coach who stands too far back does not get a worse answer, they get **no answer**.

**Whether the landing must be in frame depends on what the clip is for, and the two answers conflict.** This is worth stating plainly because `shot-list.txt` and this table appear to disagree, and neither is wrong.

- **For measuring a kick**, only launch conditions matter. Carry and apex are computed from them, so the ball never has to be filmed landing, and the coach should stand as close as the guardrails allow — closer means more pixels on the ball, and diameter precision is the weakest link in the chain.
- **For validating the pipeline**, the landing must be in shot. Computed carry can only be checked against a paced distance if the footage shows where the ball actually came down, and the bounce is also what tells the software where free flight ended.

The 2026-08-22 session was filmed for the first purpose and used for the second, which is why seven clips of eleven can never be checked against their paced landings — the ball had left the frame. `shot-list.txt` item 14 now requires the landing in shot, because that sheet exists to produce *validation* footage. Once the pipeline is trusted, ordinary use goes back to standing close.

**Free flight ends at the bounce, and the fit has to stop there.** Not a filming guardrail but the same class of mistake: a window containing something other than free flight. A parabola fitted across a flight and its bounces is nearly a straight line and reports gravity near zero. `compute_metrics.py` now finds the landing and cuts there — see *The gravity discrepancy*.

None of the filming guardrails is built. The app offers no framing guidance and performs no compliance check.

**On-device constraints.** Analysis runs on an iPhone or iPad, after capture rather than live, so throughput is not critical — but two things are:

- **The detector must export to Core ML and run on the device.** The Mac-side spike is restricted to `yolo11n` (~6 MB) and `yolo11s` (~19 MB) for that reason. Proving the concept with a model that cannot ship would prove nothing. **This originally said "fit on the Neural Engine."** Measured 2026-08-24, the Float32 export cannot reach the ANE at all and runs on the GPU at 5.68 ms per 640 px inference, so ANE fit is not the binding constraint — but small models remain right for app size and for the option of a float16 re-export later.
- **Camera-shake compensation ports cleanly.** Frame-to-frame registration against the background has native equivalents in `VNTranslationalImageRegistrationRequest` and `VNHomographicImageRegistrationRequest`, so this technique survives the move to the app with no third-party dependency. It complements the decision to disable hardware video stabilisation at capture: the camera's own stabiliser applies a *non-rigid* warp that corrupts geometry, while a *rigid* registration applied in analysis removes shake without distorting. Off in the camera, corrected in software.
- **Diameter refinement was dropped rather than ported.** An earlier spike refined ball diameter with OpenCV's `HoughCircles`, which has no Apple equivalent. Measured against real footage it inflated diameter by ~45% while the raw detector box held steady to a few pixels, so it was removed. Nothing in the current pipeline depends on an OpenCV routine without a Vision or Accelerate counterpart.

## Current State

### What does NOT exist yet

**There is no measurement pipeline in the app.** Detection, tracking and metrics exist only as Python on the Mac (see *Analysis pipeline*). The iOS app captures, stores and reviews; it measures nothing.

**The first Swift that runs the detector does now exist, as a temporary harness.** `ANEComparison.swift`, written 2026-08-24 for punch list item 1.1, loads the Core ML model, runs it on four bundled crops and decodes its raw output into a ball diameter. It is a measurement *instrument*, not a stage of the pipeline: it does not track, does not read a clip, and computes no metric. Its decoding is nonetheless the working core of what 4.1 needs, and it has been verified against the Mac to two decimals.

**The model is in the app and has run on the device.** `yolo11n.mlpackage` moved into `GoalKick/` on 2026-08-24 and is now the only copy — the duplicate at the repo root was deleted, and `tools/export_coreml.py` points here — with Xcode compiling it into the bundle automatically through the synchronized folder. It has been loaded and run on an iPhone 17 Pro. **It has never run on the Neural Engine and cannot**: the export is Float32 and the ANE requires float16, so every operation falls to the GPU. See punch list item 1.1.

**The metrics are half-validated.** The reconstruction is confirmed: on every clip whose track reaches the ground, observed displacement matches a paced landing to within 3–10%. The flight fit is not: gravity averages 7.7 across nine clips against 9.81, or 8.3 across the seven the tool does not flag as suspect, from a known cause — a progressive bias in the detector's flight diameters, detailed under *The gravity discrepancy*. **No figure should be shown to a coach yet**, but the open question is now a specific measurable defect rather than a mystery.

**No filming guardrail is enforced or checked.** The app gives the coach no framing guidance and does not verify afterwards whether the shot was square, steady, or at a sensible distance — despite those being what makes the measurement work at all. The measurements needed for the check already exist in the Mac pipeline; nothing surfaces them.

**Annotations are not saved.** Telestration strokes live only in memory and are lost when the clip changes or the app quits. There is no undo, one colour, one thickness.

**The test targets remain empty.** No test has been written for either the Swift app or the Python tools.

**Synthetic validation now exists** — `tools/synth_track.py`, built 2026-08-24, punch list item 2.1. This paragraph previously said it did not, and argued that real footage confirms an answer without isolating which stage is wrong when it does not. That argument was right and the harness has since paid for itself several times over: it proved the geometry, projection, depth reconstruction and gravity fit exact; found the launch-time origin defect that the gravity self-check is structurally blind to; showed the sign of a bias-induced gravity error flips with window length; and established that random diameter error is averaged away while systematic error is not.

**What is still missing is validation of the *detector*.** Everything above tests the physics on synthetic detections. Nothing tests whether the detector's boxes are right on real pixels, which is where the outstanding defect of 3.1 lives.

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
| **First footage** | Ten clips, 2026-08-21. Five at 1080p/240, five at 4K/120. **The clips themselves no longer exist**; one track CSV survives in `tools/frames/archive-0821/`. Documented under *Open Questions → How should a goal kick be filmed?* |
| **Step 3 — ball tracking** | Done, on the Mac. A stock `yolo11n` finds the ball across the flight with no training data. Acquisition takes the largest candidate rather than the most confident, gated on the distance the coach paced out, which is what stops it locking onto other people's footballs elsewhere on the pitch; `--max-gap` is 30 frames so the blur blackout off the boot does not end the track. Ten of eleven 2026-08-22 clips track correctly. |
| **Step 4 — metrics** | Written, on the Mac. Produces speed, launch angle, carry and apex, with both flight models side by side, cuts the fit at the bounce automatically, and fits launch conditions against the drag ODE rather than a parabola. Nine of eleven clips produce sound numbers. |
| **Ground truth** | Eleven kicks filmed 2026-08-22 with paced landing distances, camera at 10 yards, cones at a measured 5 yards. The first data in the project's history against which a computed carry can be checked at all. |
| **Reconstruction validated** | On every clip whose track reaches the ground, observed displacement matches the paced landing to within **3–10%**. Focal length from field of view, ball diameter as scale, per-frame depth and 3D geometry confirmed against a distance measured on the pitch rather than against themselves. |
| **Portability audited** | 2026-08-24. The maths ports to Accelerate with no OpenCV dependency. Recorded under *Porting risks*. |
| **Core ML export** | `GoalKick/yolo11n.mlpackage`, reproducing the PyTorch boxes to 0.00%. Built with a pinned Python 3.9 environment. |
| **Runtime verified on device** | 2026-08-24, iPhone 17 Pro. The device reproduces the Mac's diameters to two decimals on all four frozen crops, and box coordinates are identical across every compute unit. The export is Float32 and therefore **cannot reach the Neural Engine at all** — the GPU is what runs, at 5.68 ms per 640 px inference. See punch list item 1.1. |
| **Crop architecture proven** | A 640 px crop at native resolution matches full-frame 3840 accuracy at 1/36th the compute. This resolves the largest porting risk and is what gets ported. |

### Where README.md disagrees with this file

Audited 2026-08-24. `README.md` is a public-facing overview and **this file is authoritative** where the two differ, but a reader may well meet the README first and take it at face value. These are the places it is currently behind, recorded here rather than fixed there — a deliberate decision, not an oversight.

| README says | This file says |
|---|---|
| The 70-format camera scan, stated as measured fact | Flagged unverified: the scan code was not kept and nothing committed can check it — see *Camera capability* |
| Photos retiming a 240 fps clip to 30 fps, stated as settled | A single unrepeated observation with no surviving artifact, and the sole basis for a storage decision the project is built on |
| Nothing about the 2026-08-21 footage being gone | The clips no longer exist; only one track CSV survives |
| Nothing about the 1080p focal length | It is 5.1% out on the only clip that can test it, so every distance from a 1080p clip may be short by that much |
| Nothing about the input-size floor | Full-frame 1280 silently loses the ball mid-flight and reads 33% high late — the trap most likely to catch an implementer |
| No status row for the crop architecture | The most consequential finding of 2026-08-24, and what determines the on-device design |

**None of this makes the README wrong**, only incomplete and more confident than the evidence in places. **Do not bring it into line** — `README.md` is frozen until the project is finished, per *LLM Start Here*, and this catalogue is what its eventual rewrite will be built from. Keep adding to the table as further gaps appear; until the rewrite, treat any figure the README gives as needing confirmation here.

### What rests on evidence the repository no longer holds

Audited 2026-08-24. These claims are believed true and were measured at the time, but **nothing committed can check them**, so they should be treated as testimony rather than data. Listed because a document claiming to be a source of truth should say which of its statements it cannot support.

**The 2026-08-21 footage is gone.** Ten clips, deleted at some point before 2026-08-24; they are not on the Desktop and not anywhere else on the Mac. What survives is one track CSV in `tools/frames/archive-0821/`, which is enough to re-run the physics but not detection. Anything below measured on that footage cannot be re-derived.

| Claim | Why it cannot be checked |
|---|---|
| The 70-format camera scan | Scan code not kept — see *Camera capability*, where this is flagged in place |
| Photos retimed a 240 fps clip to 30 fps, stretching it 8× | Measured once during the capture spike; neither the clip nor the code survives. This is the entire basis for not using Photos as the store |
| A 4K/120 clip survived a Photos round trip at 119.94 fps | Same — one observation, no artifact |
| AirDrop routes video into Photos without asking | Behavioural observation on iOS; no artifact possible |
| `HoughCircles` inflated diameter by ~45% | The refinement was removed and the code with it |
| `--imgsz` 1280→1920 cut range scatter 200 mm → 118 mm | Measured on a 4K clip from the lost session. **Superseded** by the input-size table under *Analysis pipeline*, which was measured on surviving footage and says more |
| Motion blur: panel detail legible on a ~70 px ball at 240 fps | From the lost footage |
| Zoom, telestration, playback and iPad review "verified on device" | True when written; re-checkable only by running the app, not from the repo |

**Two of these matter more than the rest.** The Photos retiming result is the sole justification for a storage decision the whole project is built on, and it rests on a single unrepeated observation. And the blur claim is what retires the largest technical risk on the books — at 13 m/s only, as the section itself says.

Neither is worth re-testing now. Both are worth knowing are single points of evidence if either decision is ever revisited.

### Environment

- **Mac:** macOS 26, Xcode 26 from the Mac App Store, iOS 26 platform installed, command line tools pointed at Xcode.
- **Test devices:** two, with different jobs.
  - **"Rocket's iPhone"** — an **iPhone 17 Pro**, 256 GB, iOS 26.6.1, identified from the Core ML performance report of 2026-08-24. The **capture** device. Paired over cable, Developer Mode enabled, developer certificate trusted.
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
| `ContentView.swift` | Tab bar container — **Record**, **Review**, and a temporary **ANE** tab — and the `onOpenURL` landing point for clips sent to the app from outside it |
| `ANEComparison.swift` | **Temporary**, punch list item 1.1. Loads `yolo11n.mlmodelc` under each `MLComputeUnits` setting, decodes the raw `var_1223` tensor into ball diameters, reports both selection rules, and writes the result to `Documents/ane-results.txt`. Deletes cleanly with the ANE tab; its decoding is what 4.1 should lift. |
| `yolo11n.mlpackage` | The detector, and **the only copy** — moved here 2026-08-24. The synchronized folder puts it in the app bundle and Xcode compiles it to `yolo11n.mlmodelc` at build time, so **the app will not build without it**. The former copy at the repo root was deleted rather than kept: it was ~10 MB of duplicate binary in git and two files free to drift apart at the next re-export. `tools/export_coreml.py` now defaults `--coreml` here. Note that `export` writes its output beside the `.pt` weights, so a fresh export lands at the root and must be moved in. |
| `crop-f00*.pngraw` | **Temporary**, four frozen 640×640 crops from kick 11 — the fixed input for 1.1. The `.pngraw` extension is deliberate: Xcode's `COMPRESS_PNG_FILES` rewrites bundled `.png` into Apple's CgBI variant, which would mean the device no longer reads the bytes the Mac baseline was measured from. |
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
| `tools/synth_track.py` | Trajectories with a **known** answer. `generate` writes a synthetic track CSV that `compute_metrics.py` reads unmodified; `check` also runs the real physics over it and prints truth against recovered; `sweep` re-fits one track at a series of window lengths; `study noise\|geometry\|format\|distance` runs repeated seeded trials across a swept parameter and reports mean and spread. Injects off-square geometry, drag, centroid noise, diameter noise as a fraction **or in pixels**, and two diameter-bias models — recession-driven and blur-driven. **Use `--diameter-noise-px`, not `--diameter-noise`, for anything comparing formats or distances:** a fraction holds relative error constant by construction and measures nothing, which invalidated the first format study and a first attempt at the distance curve. Built 2026-08-24; see punch list item 2.1 for what it has found |
| `tools/export_coreml.py` | Converts the detector to Core ML and checks the export against the weights. `sizes` reproduces the crop-vs-full-frame measurement; `dump` freezes the 640 crops to PNG as the fixed input for item 1.1; `blur` measures how the detector's box responds to motion blur in isolation; `scale` measures whether its bias grows as the ball shrinks. The last three were added 2026-08-24 and between them establish the detector's two hard limits — it loses the ball at ~29% of its width in smear, and below ~20 px of ball. **Runs under `.venv-export`, not `.venv`** |
| `tools/sessions/*.csv` | Ground truth per filming session: which file is which kick, the paced landing, the paced camera distance, and whether the track reaches the ground |
| `tools/requirements.txt` | `opencv-python`, `numpy`, `ultralytics` — the analysis environment |
| `tools/requirements-export.txt` | Pinned `torch`, `coremltools`, `ultralytics` — the export environment |

**The kick-to-file mapping lives in `tools/sessions/2026-08-22.csv`, not in this document.** Landing distances quoted here by kick number are meaningless without it, and prose is the wrong place for a lookup table that code also has to read. `validate.py` reads it directly, so the numbers in this file and the numbers the tools produce cannot drift apart.

> ⚠️ **The clips are not in this repository.** Eleven files, about 1.3 GB, at `~/Desktop/clips/`. Nothing under `tools/` that reads footage can be reproduced without them — every command under *Next Steps → Before starting anything* will fail with no useful explanation if they are missing or moved. **`synth_track.py` is the exception**: it generates its own data and needs no footage at all, which is part of why it is useful.

**They are deliberately not backed up, and that is a decision rather than an oversight.** Raised on 2026-08-24 and accepted: the footage is a single copy on the Mac's Desktop, and the project carries the risk of losing it. Do not propose committing them to git, adding LFS, or building a sync — the question has been asked and answered.

**What makes that acceptable is that the per-frame tracks are committed.** `tools/frames/*-track.csv` is tracked deliberately — the PNGs and contact sheets in the same directory are not, because they are large and regenerable. The tracks are small text, they are the interface between detection and physics, and committing them means every physics result stays reproducible with no footage at all.

So losing the clips costs the ability to re-run *detection*, not the ability to re-run the maths. Any detector change after such a loss could not be validated against the paced landings without filming again, which is what `shot-list.txt` exists to make repeatable.

**This only works because the tracks are in git.** They were not until 2026-08-24 — `tools/frames/` was ignored wholesale, and this section claimed the fallback while the fallback did not exist. If a future `.gitignore` change re-ignores them, the backup decision above stops being reasonable.

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

**`--skip-frames` defaults to 3 and that is sometimes not enough.** It drops samples after contact while the ball is still deforming against the boot. On kick 11 the detector lost the ball entirely for twelve frames coming off the boot, and the default started the fit inside that blur, where the box is unreliable and therefore so is diameter and therefore so is range. Starting at the first frame with a real lock — `--skip-frames 11` on that clip — was what produced the first passing gravity check.

No rule has been derived for this, deliberately: one clip is not enough to invent a heuristic from, and inventing one would fit this pitch rather than the problem. If it recurs across a second session, the rule should be to start at the first sample after the largest detection gap in the first fifth of a second. **Until then, if a clip's gravity looks poor, check what frame the fit starts on before assuming the physics is wrong.**

⚠️ **Raising `--skip-frames` also costs launch speed, because the fit reports velocity at the window start.** At 120 fps a skip of 11 under-reports vertical velocity by 0.9 m/s. See *The launch-time origin defect* — the flag is not free, and the gravity self-check cannot detect what it costs.

**`--contact-threshold` defaults to 0.3 of peak speed, not 0.15.** A ball resting on grass is not motionless in the image: handheld drift ran 250–390 px across the 2026-08-22 clips, and what registration leaves behind clears a 15% bar for three frames. Two clips fired contact while the ball still sat there and fitted 400–550 frames of a stationary ball. 0.3 and 0.5 select the same contact frame on both, so this is a plateau rather than a tuned value.

**`--imgsz` defaults to the clip's own width**, so nothing is thrown away before the detector sees it. This is not a minor setting: the model resizes each frame before looking at it, and a downscale degrades the ball's apparent diameter, which is what every distance in the pipeline rests on. Measured on a 4K clip from the 2026-08-21 session, going from 0.33× to 0.50× cut range scatter from 200 mm to 118 mm — that footage no longer exists, so treat the figure as testimony; the table below says more and was measured on surviving clips.

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

**Nothing here ships.** It is a spike whose findings port to Vision, Core ML and Accelerate. Two constraints keep it portable: the detector is restricted to `yolo11n` and `yolo11s` so it stays small enough to run comfortably on a phone — originally stated as fitting on the Neural Engine, which measurement has since shown is not where it runs — and no technique is used that lacks an Apple equivalent — which is why an OpenCV `HoughCircles` diameter refinement was removed rather than kept.

**Clips reach the Mac over the cable, not AirDrop.** Finder → the iPhone under *Locations* → the **Files** tab → *GoalKick → Clips* → drag out. This is byte-for-byte and needs no device discovery; AirDrop failed to find the Mac in practice.

### Camera capability, measured on the iPhone

> ⚠️ **This section is UNVERIFIED from the repository.** The scan was run on hardware during the capture spike and **the code that produced it no longer exists** — it was exploratory and was not kept. Nothing here can be re-derived from anything committed. The format count, the per-format intrinsics support, and every row of the table below rest entirely on that one session.
>
> **To re-verify** you would have to write the scan again: enumerate `device.formats`, apply each in turn with stabilization off, and query `connection.isCameraIntrinsicMatrixDeliverySupported`. It needs the iPhone; the Simulator exposes no real capture formats. Worth doing if any of these numbers ever look suspect, and worth keeping this time.

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

**The 4K figure is independently corroborated. The 1080p figure is not, and disagrees by 5%.**

`fx` can be recovered from footage alone, with no reference to the scan: a ball of known diameter at a paced distance gives `fx = d · Z / D`. Measured on the 2026-08-22 clips, where the camera was paced at 10 yards:

| Format | Ball at rest | Frames | Implied `fx` | Claimed | Implied FOV |
|---|---|---|---|---|---|
| 4K/120 (kick 11) | 56.78 px | 600 | **2519** | 2520 | **74.6°** |
| 1080p/240 (kick 1) | 29.84 px | 979 | **1324** | 1260 | 71.9° |

The 4K agreement is exact and settles the number that most of the measurement depends on — eight of eleven clips are 4K. **The 1080p result is 5.1% high and unresolved.** Two explanations fit and this data cannot separate them:

- The camera was not actually at 10 yards for kick 1. `fx` 1260 would put it at 8.70 m, and a paced distance is easily 5% out.
- The 1080p/240 format really is narrower than 74.6°, in which case **every distance derived from a 1080p clip is 5% short** — and that would be a systematic error in three of the eleven clips.

Only kick 1 can test this. Kick 6 acquires too late to have a resting phase and kick 7 does not track at all, so the 1080p sample size is one.

**Settling it costs a tape measure.** Place the ball at a measured distance, film it at rest in both formats, and solve for `fx` in each. Ten minutes, no kicking required, and it removes an unknown that sits underneath every 1080p measurement the project will ever make. Add it to the next filming session.

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

**This section is a punch list, in execution order.** Reordered 2026-08-24 to finish the measurement component. The old Step 5–9 labels are kept in parentheses because other sections of this document refer to them by number, but **the order below is the order of work**, not the order of the labels. Work top to bottom.

The ordering principle is: prove that the Mac's findings survive the move to the device before building on them, get a known answer to debug against before diagnosing anything, fix the physics before porting it, and put the numbers in front of a coach last.

### Before starting anything

**Check the prerequisites.** The eleven clips must be at `~/Desktop/clips/`, and both virtual environments must exist — `tools/.venv` from `tools/requirements.txt`, and `tools/.venv-export` from `tools/requirements-export.txt`. Both are gitignored and neither survives a fresh clone. Each requirements file carries its own build instructions.

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

### 1 — Settle whether the Mac's findings transfer at all — **DONE 2026-08-24**

**Outcome: the Mac's findings transfer intact, and the Neural Engine is not part of the picture.** The device reproduces the Mac's diameters to two decimals on all four frozen crops; box coordinates are identical across every compute unit Core ML can use; the export is Float32 and therefore cannot reach the ANE at all. Section 3 may rely on Mac-side measurements without qualification.

**Decision, 2026-08-24: stay on the Float32 export and let it run on the GPU.** A float16 re-export is what the Neural Engine would require, and it was considered and declined. The GPU runs a 640 px inference in 5.68 ms — a whole 4K clip in 4.5 s, against a measurement window of a fraction of a second — so the ANE's advantage here is power efficiency on a job lasting seconds, which is not worth buying. Against that, float16 would perturb exactly the box numerics that 3.1 exists to characterise, and would cost a second export and a second validation to get back to where the pipeline already is. **Revisit only if sustained inference ever becomes the workload** — continuous live detection rather than post-capture analysis of a short window would change the arithmetic.

**One requirement came out of this and belongs to 4.1: the port needs NMS.** Recorded in full below.

**1.1 Run the exported model on the device and repeat the box comparison.** *(was Step 7.1)* **Done.** As posed, this item read "run it on the Neural Engine" and assumed the ANE was what ships. That assumption was wrong — see the measurement below — so what the item actually settled is the broader question underneath it: whether the device runtime reproduces the Mac's boxes. It does, exactly.

It was placed first because it is cheap and because every item below inherits its answer: if the boxes moved, the diameter-bias work in section 3 would be characterised against numerics the device does not use.

**Method.** The comparison is *not* Swift-against-Python. Swift and Python differ in how they decode video, resize and convert colour, so a discrepancy between them would be ambiguous between the runtime and the plumbing. Instead: identical PNG inputs, one piece of Swift, run three times changing only `MLComputeUnits`. Core ML offers no way to force the Neural Engine, but `.cpuOnly` provably excludes it, so the difference between `.cpuOnly` and `.all` **is** the ANE effect with nothing else varying. The Python figures below are a third data point rather than the yardstick. `MLModel` is driven directly rather than through `VNCoreMLRequest`, because Vision applies its own scaling and cropping and that is a variable which does not belong inside a numerical comparison — Vision arrives at 4.1, where it is the thing being tested.

**The model has no NMS.** It was exported with `nms=False` — deliberately, because `detect_ball.py` does its own candidate selection and baked-in NMS would discard the candidates that choice depends on. Its single output `var_1223` is therefore a raw tensor, not decoded detections. Ultralytics does that decoding on the Mac; in Swift it has to be written by hand — read the tensor, take COCO class 32, convert centre/width/height to a diameter, pick the largest. Input is fixed at 640×640, which is already the crop size that ships.

**Done 2026-08-24 — the Mac baseline is frozen.** `export_coreml.py dump` wrote the four kick 11 crops to `tools/frames/ane-inputs/` and measured both models by reading those files back:

| crop | true diameter | PyTorch | Core ML (Mac CPU/GPU) |
|---|---|---|---|
| f620 | 57.2 px | 58.28 px, c0.96 | 58.28 px, c0.96 |
| f660 | 52.4 px | 54.12 px, c0.94 | 54.12 px, c0.94 |
| f700 | 37.7 px | 37.63 px, c0.94 | 37.63 px, c0.94 |
| f740 | 30.4 px | 30.35 px, c0.35 | 30.35 px, c0.35 |

Three things this establishes. The two runtimes remain identical to two decimals when driven from files rather than arrays. The errors against truth — **+1.9%, +3.3%, −0.2%, −0.2%** — reproduce the `crop 640 @native` column under *Porting risks* exactly, so the PNG round trip is lossless and these files are a sound fixed reference. And the late-flight frame carries only **0.35 confidence against the detector's 0.25 default**, against 0.94–0.96 everywhere else.

**That 0.10 of headroom was the thing to watch, and it held.** The concern was that if the runtime shifted confidences at all, f740 was where it would surface as the ball *disappearing* rather than as a small numeric difference — and a frame lost late in flight is precisely where the diameter bias of 3.1 lives. Measured on device, f740's best confidence is **0.3540** against the Mac's 0.35: the headroom is intact and the frame is in no danger. The 0.2515 that the first device run reported was a decoder artifact, not a runtime effect — see below.

**Measured on device 2026-08-24 — iPhone, iOS 26.6.1.** `ANEComparison.swift`, a temporary harness on an "ANE" tab, ran the four bundled crops through `yolo11n.mlmodelc` four times, changing only `MLComputeUnits`:

| crop | cpuOnly | cpuAndGPU | cpuAndANE | all | spread |
|---|---|---|---|---|---|
| f620 | 58.64 px c0.8380 | identical | identical | identical | 0.00% |
| f660 | 54.37 px c0.9029 | identical | identical | identical | 0.00% |
| f700 | 38.14 px c0.8488 | identical | identical | identical | 0.00% |
| f740 | 30.52 px c0.2515 | identical | identical | identical | 0.00% |

Every configuration returned `var_1223 [1, 84, 8400] float32`.

**The device runtime reproduces the Mac exactly.** Re-run with both selection rules reported side by side, the highest-confidence box matched the Mac baseline on every crop:

| crop | Mac | device, most confident |
|---|---|---|
| f620 | 58.28 px c0.96 | 58.28 px c0.9587 |
| f660 | 54.12 px c0.94 | 54.12 px c0.9376 |
| f700 | 37.63 px c0.94 | 37.63 px c0.9437 |
| f740 | 30.35 px c0.35 | 30.35 px c0.3540 |

**The earlier device-versus-Mac gap was the decoder, not the runtime**, and it is now understood. The first run took the *largest* box above threshold from the raw tensor, which read diameters 0.46–1.36% high and confidences 0.04–0.12 low. Ultralytics applies NMS on the Mac and then picks the largest of one-box-per-object; the harness was picking the largest *duplicate anchor*. Same rule, different input.

**This converts into a requirement on 4.1.** Largest-candidate acquisition is correct and is not in question — it is what stops the detector locking onto a football 25 m away, which cost nine clips of eleven. But it was validated against suppressed boxes, so **the port needs NMS, or an equivalent, before that rule is applied on device.** Applying it to raw anchors is a different rule that happens to look similar, and it biases diameter upward by up to 1.4% — small, but in a pipeline where diameter precision is the weakest link and a 6–9% bias is the outstanding defect of 3.1, a systematic 1.4% is not noise to be absorbed silently.

**The Neural Engine never ran, and cannot.** Measured by Xcode's Core ML performance report on 2026-08-24, run with compute units set to **All** so Core ML was free to choose:

| | |
|---|---|
| Program operations | 958, of which **242** are real compute ops |
| Supported devices, every one of the 242 | **`{cpu, gpu}`** |
| Preferred device, every one of the 242 | **`gpu`** |
| Operations listing `neuralEngine` as supported | **zero** |

**The cause is `storagePrecision: Float32` in the model's own metadata.** The ANE requires float16 weights; the export was produced without `half=True`, so the network is CPU/GPU-only by construction. Nothing about the architecture or the operations is at fault, and no amount of asking for `.cpuAndNeuralEngine` can change it.

This also explains the one number that varied across the sixteen harness runs — f740's class score, `0.3540` under `.cpuOnly` and `.cpuAndANE`, `0.3541` under `.cpuAndGPU` and `.all`, with box coordinates unaffected throughout. `.cpuAndANE` agreed with `.cpuOnly` bit for bit because it *was* CPU-only; there was nothing for the ANE to take. The GPU's one-part-in-3,540 divergence from the CPU is ordinary floating-point behaviour and far below anything that matters here.

**Performance, measured on the same run — iPhone 17 Pro, iOS 26.6.1:**

| stage | first call | median thereafter |
|---|---|---|
| compile | 63.1 ms | 55.7 ms |
| load | 117.8 ms | 20.2 ms |
| **predict** | 1716.4 ms | **5.68 ms** |

The 1.7 s first prediction is one-time warm-up and must not be mistaken for throughput. Steady state is **5.68 ms per 640×640 inference on the GPU**, about 176 fps. Detecting on *every* frame of a 787-frame 4K/120 clip would take **4.5 s**; a 1361-frame 1080p/240 clip, **7.7 s**. The measurement window is a small fraction of either.

**Two premises this project was carrying are now false, and matter more than the result itself.**

- *"The Neural Engine is still untested, and it is the thing that ships."* Recorded under *Porting risks*. As the model stands, **what ships is the GPU.** The ANE is not a runtime this export can reach.
- *"Native-resolution inference was the largest risk."* At 5.68 ms per crop it is not a throughput risk at all. The crop architecture is still right — it exists for diameter precision, not speed — but the speed argument for it was never the load-bearing one.

**What is proven, stated exactly.** Every compute unit Core ML can actually use produces **identical box coordinates**, and confidences agreeing to within one part in 3,540. The device reproduces the Mac's diameters to two decimals on all four crops. Whatever the ANE would do to the boxes is **untested and currently unreachable** — and cannot be tested without a float16 re-export, which would itself change the numerics that test is meant to check.

⚠️ **The frozen crops are gitignored.** `tools/frames/*` is excluded except `*-track.csv`, so `ane-inputs/` is not committed, while the clips it derives from are a single un-backed-up copy on the Desktop. If both are lost, 1.1 stops being reproducible — the same failure the per-frame tracks were committed to prevent. Not yet decided either way.

### 2 — Get a known answer to debug against

**2.1 Build the synthetic validation harness.** *(was Step 5)* **Built 2026-08-24 as `tools/synth_track.py`.** It generates a ballistic trajectory with chosen parameters, projects it through the pinhole model — the exact inverse of `reconstruct()` — and writes a CSV in `detect_ball.py`'s format, which `compute_metrics.py` then reads **completely unmodified**. Nothing is imported into the tool under test and the tool under test knows nothing about the harness, so this exercises the shipping code path rather than a private copy of the physics. `generate` writes the CSV; `check` also drives `find_contact`, `find_landing`, `reconstruct` and `fit_launch` over it and prints truth against recovered.

**First run, the idealised case — no noise, no drag, square on, exact diameters:**

| quantity | truth | recovered | error |
|---|---|---|---|
| gravity | 9.8100 | 9.8102 | **+0.00%** |
| vx | 20.4788 | 20.4803 | +0.01% |
| vz | 0 | 0 | exact |
| **vy** | 14.3394 | **14.0129** | **−2.28%** |
| speed | 25.0000 | 24.8154 | −0.74% |
| elevation | 35.0000 | 34.3805 | −1.77% |

Vertical residual 1.19 mm. **The geometry, the projection, the depth reconstruction and the gravity fit are exact.** That is worth stating plainly, because it removes four candidate explanations from the 3.1 investigation in one run.

**But it found a defect, and it is not a rounding error.** See *The launch-time origin defect* below.

**The ladder, rungs 2 and 3, run 2026-08-24.** Same idealised conditions, varying only geometry and how the clip ends:

| run | gravity | vx | vz | vy | speed | elevation |
|---|---|---|---|---|---|---|
| square on | +0.00% | +0.01% | exact | −2.28% | −0.74% | −1.77% |
| 15° off-square | −0.01% | −0.00% | −0.00% | −2.29% | −0.75% | −1.77% |
| 30° off-square | −0.00% | +0.00% | +0.01% | −2.28% | −0.74% | −1.77% |
| truncated mid-flight (`--after net`) | +0.01% | +0.01% | exact | −2.27% | −0.74% | −1.77% |

**Three findings, and the second is the substantial one.**

**The `vy` error is constant at −2.28% across every geometry.** It does not vary with off-square angle, with flight length, or with whether a landing exists. That is the signature of a single defect independent of geometry, and it confirms the time-origin diagnosis rather than merely being consistent with it.

**Off-square filming costs nothing when depth is accurate.** At 30° off the perpendicular, with `vz` at 10.24 m/s, gravity is recovered to −0.00% and `vz` itself to +0.01%. This is the direct confirmation of something the file previously observed but could not explain — that the 56.5° control kick of 2026-08-22 fitted gravity to within 1.5% despite being nearly four times the guardrail. The mechanism is now clear: the pipeline performs a full 3D reconstruction with per-frame depth, so it recovers the out-of-plane component properly instead of losing it to foreshortening. **The cross-term `2·u̇·Ż/fx` is not a geometric penalty — it is an amplifier of depth error, and with exact diameters there is no error for it to amplify.**

⚠️ **This puts the stated rationale for the ±15° guardrail in question, though not the guardrail itself.** *Measurement Approach* justifies it as "off-axis foreshortening under-reads velocity by roughly `cos φ` — 3.4% at 15°, 13% at 30%." Measured here, speed is recovered to −0.74% at **every** angle, the same as square on. That justification describes a 2D image-plane measurement, which is not what this pipeline does. The guardrail may still be right for other reasons — an off-square ball recedes faster, so it loses pixels sooner and its diameters degrade, and it is diameter error that the cross-term then amplifies — but those are different mechanisms with different magnitudes, and they have not been measured. **Not yet corrected in the guardrail table, because what should replace it is not yet known.**

**Truncated flight recovers everything.** The `--after net` run has no landing to find, ends 40 frames into the flight, and returns the same numbers as the full-flight runs — with a *lower* residual, 0.01 mm against 1.19 mm. This is the empirical confirmation of *Measurement Approach*'s central claim: only launch conditions are needed, so footage that ends early is not degraded footage.

**The residual floor is 1.19 mm and it is an artifact of the CSV, not of the physics.** Diameter is written to two decimals, matching `detect_ball.py`; at 56.8 px that quantisation is 8.8 × 10⁻⁵ relative, which propagates to about 0.9 mm at a 10 m apex. It is far below anything that matters, but it is the harness's precision floor and should not be mistaken for a defect on long flights. Short windows sit at 0.01 mm because the ball has barely climbed.

**Rung 4, the diameter bias — run 2026-08-24, and it produced the most consequential result so far.**

⚠️ **First, a limitation of the harness, found by running it.** `--diameter-bias` is keyed to recession, `Z − camera_distance`. A perfectly square kick has `vz = 0` and therefore never recedes, so **the bias is silently not applied at all** and `--diameter-bias 0.06 --off-square 0` returns exactly the unbiased numbers. That run tested nothing. The real defect has two drivers — the ball receding and motion blur — and only the first is modelled. **Square-on cases cannot currently be tested for diameter bias.**

At 30° off-square, where the ball does recede, a 6% progressive under-read does substantial damage:

| quantity | error with 6% bias at 30° |
|---|---|
| gravity | **+5.60%** (10.36 m/s²) |
| speed | +6.20% |
| vx | +6.88% |
| vy | +3.59% |
| vz | +9.19% |
| residual | **40.60 mm**, against 1.19 mm unbiased |

**The direction looked wrong, and chasing it produced the finding.** Real footage reads gravity *low*, 7.7–8.3 against 9.81; this reads *high*. The resolution is that **a progressive depth inflation flips the sign of the gravity error depending on the length of the fit window.** Under-reading diameter inflates depth progressively, which multiplies the parabola by a growing factor and injects a cubic term. Over a short window the linear part dominates and drags gravity down; over a long window the cubic projects onto the quadratic and pushes it up.

Computed directly, for a 2% per second depth inflation:

| fit window | implied gravity | error |
|---|---|---|
| 0.10 s | 9.266 | −5.5% |
| 0.25 s | 9.310 | −5.1% |
| 0.50 s | 9.384 | −4.3% |
| 1.00 s | 9.531 | −2.8% |
| 1.50 s | 9.678 | −1.3% |
| 2.00 s | 9.825 | +0.2% |
| 2.90 s | 10.090 | +2.9% |

**The crossover is near two seconds.** The synthetic kick fits 2.9 s and therefore reads high; kick 11's free flight was 104 frames at 120 fps — **0.87 s** — which sits firmly in the negative region. So the two results agree rather than conflicting, and the 3.1 hypothesis is strengthened rather than undermined.

**Three consequences worth carrying into 3.1.**

- **The sign of the gravity error is not diagnostic on its own.** Both signs come from the same defect, and which one appears depends on window length. Comparing fitted gravity across clips of different flight durations is comparing points on this curve, not comparing severities.
- **The residual is the better detector.** 40.60 mm against 1.19 mm is a factor of 34, and unlike gravity it does not change sign. A quadratic fit cannot describe a cubic, and the residual is the fit saying so. Nothing currently reads it as a bias indicator.
- **This table was computed analytically. It has since been reproduced through the pipeline** — see the sweep results below, which put the crossover near 1.5 s rather than 2 s and match kick 11's real residual and gravity error at its actual window length.

**The harness gained two things on 2026-08-24 in response to the above.** `--blur-bias` under-reads diameter in proportion to **image-plane speed** rather than recession, which is the only bias term that acts on a square-on kick — recession is zero there, while image speed is at its highest. And a `sweep` subcommand re-fits one generated track at a series of window lengths, changing only where the window ends, so the sign-flip argument could be tested through `reconstruct()` and `fit_launch()` instead of analytically.

**Rung 5 — the window sweep, run 2026-08-24. Three results, and the third was not the one being looked for.**

**Control, no bias.** Gravity 9.811 at every window length from 0.10 s to 2.90 s, residual 0.01 mm throughout. The sweep introduces no artifact of its own, which is what makes the rest of it readable.

**Progressive recession bias, 6% at 30° off-square — the sign flip is real and reproduces through the shipping code path:**

| window | gravity | error | residual | speed error |
|---|---|---|---|---|
| 0.10 s | 8.738 | **−10.9%** | 0.02 mm | −0.18% |
| 0.25 s | 8.861 | −9.7% | 0.20 mm | +0.27% |
| 0.50 s | 9.084 | −7.4% | 1.35 mm | +1.07% |
| 0.75 s | 9.282 | −5.4% | 3.92 mm | +1.92% |
| 1.00 s | 9.463 | −3.5% | 8.13 mm | +2.83% |
| 1.50 s | 9.794 | −0.2% | 21.94 mm | +4.77% |
| 2.00 s | 10.103 | +3.0% | 33.02 mm | +5.78% |
| 2.90 s | 10.360 | **+5.6%** | 40.60 mm | +6.20% |

**The crossover is near 1.5 s** — the analytic estimate said 2 s, close enough given a different bias profile. The residual rises monotonically from 0.02 mm to 40.60 mm and never changes sign.

**A cross-check against real footage that works.** Kick 11's free flight is 104 frames at 120 fps, **0.87 s**, and reported a **3.2 mm** residual with fitted gravity **9.23** — that is −5.9%. The table above at 0.75 s gives 3.92 mm and −5.4%. **A 6% progressive recession bias over kick 11's actual window reproduces both its residual and its gravity error**, which is the closest thing to confirmation the 3.1 hypothesis has had.

**Uniform bias behaves completely differently, and finding that out was an accident.** The blur run saturated: a square-on ball crosses the frame at 47 px per frame against a 30 px reference, so `min(1, step/reference)` pinned at 1 and the bias was **uniform rather than progressive** for the whole flight. What it produced:

| window | gravity | error | residual |
|---|---|---|---|
| every length, 0.10–2.90 s | 10.437 | **+6.4%** | **0.01 mm** |

A uniform 6% under-read inflates every distance by 6.38%, and the numbers match that to two decimals — gravity +6.39%, `vx` +6.39%, and `vy` +3.96% which is the same 6.38% scale less the 2.28% time-origin defect. **The shape is still a perfect parabola, only scaled, so the residual sees nothing at all.**

⚠️ **This gives two distinguishable signatures, and they call for different fixes:**

| symptom | cause | fix |
|---|---|---|
| gravity wrong, **residual near zero**, error identical at every window length | **uniform** scale error — `fx`, ball size, or a constant box bias | recalibrate; nothing about the flight is wrong |
| gravity wrong, **residual large**, error varying with window length and changing sign | **progressive** bias — the box degrading through the flight | correct the diameter trend |

**A uniform scale error cannot be what ails the real clips**, and the reason is already recorded: it would scale carry and gravity by the same factor, but observed displacement matches the paced landings to 3–10% while gravity is far worse. The defect is progressive, which is what 3.1 already believed and can now demonstrate.

**Rung 6 — blur bias below saturation, and it identifies which mechanism the real defect is.** Re-run with `--blur-reference 200` so the term varies instead of pinning, the bias profile is **U-shaped**: 1.72% at launch, 1.41% at the apex, 1.72% at landing, because image speed is highest when vertical motion is fastest. Mean about 1.5%.

| window | gravity | error | residual |
|---|---|---|---|
| 0.10 s | 10.075 | **+2.7%** | 0.01 mm |
| 0.50 s | 10.051 | +2.5% | 0.04 mm |
| 1.00 s | 10.016 | +2.1% | 0.26 mm |
| 2.00 s | 9.970 | +1.6% | 0.99 mm |
| 2.90 s | 9.961 | **+1.5%** | 1.21 mm |

At the long window it converges on +1.5%, which is the mean bias acting as a uniform scale. At short windows it reads **higher**, +2.7% — and that is the finding.

⚠️ **The direction of the window dependence encodes the direction of the bias trend, and it points at recession.**

| bias trend over the window | gravity at short windows |
|---|---|
| **increasing** — recession, the ball receding and shrinking | reads **low** |
| **decreasing** — blur, worst off the boot and easing toward the apex | reads **high** |

A window starting just after contact sees blur *decreasing* and recession *increasing*, so the two mechanisms push fitted gravity in opposite directions. **The real clips read low** — kick 11 at −5.9% over 0.87 s, and the set averaging 7.7–8.3. So the dominant defect is **recession-driven, not blur-driven**, which means the correction in 3.1 should be a function of range rather than of image speed. That is a materially different fix, and nothing before this could have distinguished them.

**One qualification.** The residual stays under 1.21 mm throughout this run even while gravity is 1.5–2.7% out. **The residual only detects strongly progressive bias**; a mild trend behaves almost like a uniform scale error and hides from it. So the residual is the honest indicator when it is large, but a small residual does not clear a clip.

**Two output bugs in the harness were exposed by these runs and fixed:** the generator summary line printed `diameter bias 0` while a blur bias was active, and the "this is the idealised case" footer printed even when blur bias was set. Both would have made a biased run look clean in its own header.

**Rung 7 — the noise study, 50 seeded trials per point.** Centroid noise and diameter noise swept together, on a 4K/120 kick at 9.14 m.

| centroid px | diameter frac | speed err mean ± sd | gravity err mean ± sd | residual |
|---|---|---|---|---|
| 0.00 | 0.000 | −0.74 ± 0.00 | +0.00 ± 0.00 | 1.2 mm |
| 0.00 | 0.050 | −0.54 ± 0.34 | +0.26 ± 0.28 | 4.8 mm |
| 0.50 | 0.000 | −0.74 ± 0.00 | +0.00 ± 0.00 | 2.2 mm |
| 0.50 | 0.020 | −0.67 ± 0.18 | +0.06 ± 0.12 | 3.2 mm |
| 2.00 | 0.000 | −0.74 ± 0.00 | +0.00 ± 0.01 | 7.3 mm |
| 2.00 | 0.050 | −0.41 ± 0.46 | +0.30 ± 0.31 | 9.6 mm |

**Centroid noise is almost harmless to the metrics.** Two pixels of centre wobble — four times what any real detector shows — moves speed, angle and gravity by essentially nothing. The fit uses every sample, and centroid error is zero-mean in a way that averages out.

**Diameter noise is the whole story**, which is the quantitative confirmation of something this file has asserted from the beginning: relative range error tracks relative diameter error one for one, and every distance rests on it.

⚠️ **Symmetric diameter noise produces an asymmetric range error, and therefore a bias, not just scatter.** Range is `fx·D/d`, so it is *inversely* proportional to diameter, and by Jensen's inequality the mean of `1/d` exceeds `1/mean(d)`. Computed directly, 5% diameter noise inflates mean range by **+0.254%**, and the study shows speed moving from −0.74% to −0.41% across exactly that range. **Noisy diameters do not merely blur the answer — they systematically inflate every distance**, and no amount of averaging removes it because it is a property of the transformation rather than of the sample.

⚠️ **The residual responds to noise as well as to bias**, rising from 1.2 mm to 7.3 mm on centroid noise alone while every metric stayed correct. So it is not a clean bias detector: **a large residual means "something is wrong", not "the diameters are biased"**. Item 6.1 should not present it to a coach as though it were specific.

**Rung 8 — the geometry study. The ±15° guardrail earns its place, but not for the reason recorded.** Mean gravity error, off-square angle against recession bias:

| off-square | bias 0 | bias 0.02 | bias 0.06 | bias 0.10 |
|---|---|---|---|---|
| 0° | +0.00% | +0.00% | +0.00% | +0.00% |
| 5° | −0.01% | +0.39% | +1.18% | +1.99% |
| 15° | −0.01% | +1.26% | +3.91% | +6.73% |
| 30° | −0.00% | +1.79% | +5.60% | +9.73% |
| 45° | −0.00% | +1.91% | +5.98% | +10.41% |

**The `bias 0` column is flat to 45°.** With exact diameters, off-square filming costs nothing at all — not 3.4% at 15°, not 13% at 30°. The `cos φ` foreshortening argument in *Measurement Approach* describes a 2D image-plane measurement and does not apply to a pipeline that reconstructs depth per frame.

**But every other column fans out sharply, and that is the real cost.** Off-square filming is an *amplifier of diameter error*, exactly as the cross-term `2·u̇·Ż/fx` predicts. At a realistic 6% bias, going from square to 15° turns a 0% error into **3.91%**, and 30° into 5.60%. The effect saturates by about 30–45°, so beyond that further misalignment adds little.

**This gives a basis for choosing the threshold that the project has never had.** At 6% bias, 5° off costs 1.18% while 15° costs 3.91% — so the guardrail is worth roughly a factor of three, and tightening it further has real value. Note also that **the two defects multiply**: fixing the diameter bias in 3.1 collapses the whole table to the first column, which is a second reason to treat 3.1 as the priority.

⚠️ **Sign caution.** These are full-flight windows, past the 1.5 s crossover, so the errors read positive. Real short windows put the same errors negative. Read the magnitudes, not the signs.

**Rung 9 — the format study, and it is INVALID AS RUN.** Recorded because the flaw is instructive, not because the numbers are usable.

| format | ball at rest | speed err ± sd | gravity err ± sd | residual |
|---|---|---|---|---|
| 1080p/240 | 28.4 px | −0.33 ± 0.12 | +0.04 ± 0.09 | 4.1 mm |
| 4K/120 | 56.8 px | −0.67 ± 0.18 | +0.06 ± 0.12 | 3.2 mm |

**The flaw: diameter noise was specified as a fraction, so both formats received the same *relative* error** — which silently deletes the entire advantage 4K has. A detector's diameter error is roughly a fixed number of *pixels*, and at 0.5 px that is **1.76% on a 28.4 px ball against 0.88% on a 56.8 px one**, a factor of two. The study as run therefore asked "given equal relative noise, which format wins?", and answered "1080p/240, by having twice the samples to average" — which is true and is not the question.

**One thing in it is real and worth keeping.** The speed error differs between the formats, −0.33% against −0.67%, and that is the launch-time origin defect of 3.5 behaving exactly as predicted: `--skip-frames 3` is 12.5 ms at 240 fps but 25 ms at 120 fps, so the defect is **half as large at 240 fps**. An independent confirmation of 3.5 from a study that was not looking for it.

**Fixed, and re-run with diameter noise expressed in pixels.** `--diameter-noise-px` was added for this, and the format study now uses it.

| format | ball at rest | relative noise | speed err ± sd | gravity err ± sd | residual |
|---|---|---|---|---|---|
| 1080p/240 | 28.4 px | 1.76% | −0.34 ± **0.10** | +0.03 ± **0.08** | 4.0 mm |
| 4K/120 | 56.8 px | 0.88% | −0.72 ± **0.08** | +0.01 ± **0.05** | 2.4 mm |

**4K/120 is the more precise configuration**, on a like-for-like kick with a like-for-like detector: gravity scatter 0.05 against 0.08, speed scatter 0.08 against 0.10, residual 2.4 mm against 4.0 mm. Twice the pixels across the ball beats twice the temporal samples. Notably the win is **less than the 2:1 the pixel counts suggest** — 1080p/240 recovers much of it by having twice as many samples to average — but it is a win, and it is consistent across all three columns.

⚠️ **This paragraph previously claimed 1080p/240 has a structural ~2× blur advantage. That was wrong, and the error is worth keeping.** The reasoning was that blur in pixels is four times lower at 1080p/240 — exposure at most 4.2 ms against 8.3 ms, and `fx` halved again — so about twice lower relative to the ball's own size.

**The mistake was forgetting that `fx` cancels.** Relative blur is `blur_px / ball_px = (fx·v/Z)·exposure / (fx·D/Z) = v·exposure/D`. The focal length divides out, so **at a given exposure both formats smear the ball by the same fraction of its own width.** 240 fps helps only when exposure is capped by the frame interval, which happens in falling light — and by then both are past the point where the detector finds the ball at all. See *The detector's blur response*.

**The harness can answer this** — `study format --blur-bias ... --blur-reference ...` puts a blur-driven diameter bias into both formats, and the blur term is already keyed to image speed in pixels per frame, which captures the format difference automatically. Until that is run, the honest statement is: **4K/120 is better on static diameter precision by a clear margin, and 1080p/240 has a blur advantage of similar size that has not been measured.**

**One thing in the invalid run was real and worth keeping.** The speed error differed between formats, −0.34% against −0.72%, and that is the launch-time origin defect of 3.5 behaving exactly as predicted: `--skip-frames 3` is 12.5 ms at 240 fps but 25 ms at 120 fps, so the defect is **half as large at 240 fps**. It survives in the corrected run too. An independent confirmation of 3.5 from a study that was not looking for it — and a reminder that until 3.5 is fixed, **the speed column of every format comparison is contaminated by a frame-rate-dependent offset**, which is its own reason to fix 3.5 before settling the format question.

**A distance study was attempted and mis-specified.** Sweeping camera distance at 5 m and 20 m with *fractional* diameter noise showed nothing — speed and gravity errors were identical at both distances — because fractional noise holds relative error constant by construction, which is precisely the flaw that invalidated the first format study. Distance matters because a **fixed pixel** error becomes a larger relative error on a smaller ball. A `study distance` mode using `--distance-noise-px` was added to measure it properly; not yet run.

**Rung 10 — the format comparison with blur modelled, and it reverses the answer.** Same study, with a blur-driven diameter bias active in both formats:

| format | speed err ± sd | gravity err ± sd | residual |
|---|---|---|---|
| 1080p/240 | +0.04 ± 0.10 | **+0.41** ± 0.08 | 4.1 mm |
| 4K/120 | +0.81 ± 0.08 | **+1.55** ± 0.06 | 2.5 mm |

**4K/120 suffers roughly four times the blur bias**, and the factor is derivable rather than fitted: the blur term keys on image speed in pixels per frame, which is **14.4 px/frame at 1080p/240 against 57.4 at 4K/120** — `fx` is doubled *and* the interval between frames is doubled. The observed ratio, 1.55 against 0.41, is 3.8.

**So the two formats trade off, and the trade is structural:**

| | 4K/120 | 1080p/240 |
|---|---|---|
| random scatter | **better**, ~1.3–1.6× | |
| blur-induced bias | | **better**, ~4× |

**Which wins depends on how severely blur actually degrades this detector's box — a measurable property that has never been measured.** That is real progress on the open question: it stops being an argument about samples versus pixels and becomes an empirical question about the detector. One data point exists and it is not encouraging for 4K — the box collapsed from 58.4 to 42.9 px, a 26% shrink, as confidence fell to 0.34 coming off the boot. If blur bias is anywhere near that severe, 1080p/240 wins decisively; if it is mild, 4K's precision advantage carries.

**Rung 11 — the distance study, and it contradicts the guardrail's stated basis.** Diameter noise at 0.5 px, swept across camera distance:

| distance | ball | relative error | speed sd | gravity sd | residual |
|---|---|---|---|---|---|
| 5 m | 103.9 px | 0.48% | 0.03% | 0.03% | 1.3 mm |
| 10 m | 51.9 px | 0.96% | 0.06% | 0.05% | 1.6 mm |
| 12 m | 43.3 px | 1.16% | 0.08% | 0.06% | 1.7 mm |
| 20 m | 26.0 px | 1.93% | 0.13% | 0.11% | 2.3 mm |
| 27 m | 19.2 px | 2.60% | 0.18% | 0.14% | 2.8 mm |

**There is no cliff, and the absolute numbers are tiny.** Error grows linearly with distance, exactly as the relative-error column does, and even at 27 m — where a whole 40 m flight would fit in frame — speed scatter is **0.18%**. *Pixels on the ball* argues that "half a pixel of error on a 9.6 px ball is 5%, and it propagates into every metric." The first half is right and the second does not follow.

**The reason is the range smoothing, and it is the most useful thing in this study.** `reconstruct()` fits a straight line through the per-frame ranges rather than using them individually, so **random diameter noise is suppressed by √N across the fit window.** Predicted against observed:

| distance | per-sample relative error | ÷√348 | observed sd |
|---|---|---|---|
| 5 m | 0.48% | 0.026% | 0.03% |
| 12 m | 1.16% | 0.062% | 0.08% |
| 27 m | 2.60% | 0.139% | 0.18% |

⚠️ **Random diameter error is averaged away. Systematic diameter error is not.** That is why a 6% progressive bias wrecks the fit while 2.6% random noise barely registers, and it is the single clearest statement of why **3.1 is the priority and noise is not**.

**What this does not say.** The study models random noise only, so it leaves two detector mechanisms untested: **detection failure**, and **systematic bias growing as the box gets smaller**. **Both have since been measured — see rung 13.** Bias is flat as the ball shrinks; detection fails below about 20 px of ball. So the 5–12 m guardrail's stated justification, an accuracy lottery from too few pixels, is not the mechanism, and what replaces it is a detection limit rather than an accuracy one.

**Rung 12 — a systematic bias, held constant, across distance.** Same sweep with a 6% recession bias at 15° off-square:

| distance | ball | speed err | gravity err | residual |
|---|---|---|---|---|
| 5 m | 103.9 px | +4.79% | +4.13% | 50.8 mm |
| 12 m | 43.3 px | +4.92% | +3.86% | 50.5 mm |
| 27 m | 19.2 px | +5.32% | +3.74% | 50.6 mm |

**A systematic bias costs the same at every distance.** The residual is flat at 50.6 mm from 5 m to 27 m, and the errors vary by less than half a percentage point — gravity actually *improves* slightly with distance. Only the random spread grows, from 0.15 to 0.34, as the earlier study showed.

**So distance does not amplify a given relative bias**, and combined with rung 11 this closes out the physics side of the guardrail question: **neither random noise nor systematic bias gets meaningfully worse with distance.** Everything left that could justify the 5–12 m guardrail is a property of the *detector* — whether its bias fraction grows as the ball shrinks, and whether it stops finding the ball at all. No synthetic study can reach either, which the tool now says in its own output.

**Rung 13 — does the detector's bias grow as the ball shrinks? No. Measured 2026-08-24 with `export_coreml.py scale`**, downscaling the sharp at-rest crop so the ball shrinks while blur, background, lighting and pose are held constant:

| ball | measured | error | confidence | implied Z at 4K |
|---|---|---|---|---|
| 58 px | 58.55 px | +0.9% | 0.96 | 8.87 m |
| 50 px | 48.99 px | −2.0% | 0.95 | 10.60 m |
| 40 px | 39.70 px | −0.8% | 0.96 | 13.08 m |
| 30 px | 29.64 px | −1.2% | 0.86 | 17.52 m |
| 25 px | 24.90 px | −0.4% | 0.69 | 20.86 m |
| 20 px | 20.08 px | +0.4% | 0.60 | 25.86 m |
| 15 px | **NOT FOUND** | — | — | — |
| 12, 10 px | **NOT FOUND** | — | — | — |

**The error column is flat** — scattered between −2.0% and +0.9%, mean −0.5%, with no monotonic trend across a factor of three in apparent size. Relative diameter accuracy simply does not degrade as the ball gets smaller. **Confidence does**, falling steadily from 0.96 to 0.60, and then the ball is not found at all.

⚠️ **So the 5–12 m guardrail is about DETECTION, not accuracy, and the reason recorded in *Measurement Approach* is wrong.** It says the distance limit "sets a floor on pixels across the ball" so that "accuracy becomes a known quantity rather than a lottery". Measured, accuracy is *not* a lottery at any distance — random noise is averaged away (rung 11), a systematic bias costs the same everywhere (rung 12), and relative bias does not grow as the ball shrinks (here). What actually happens is that the detector works, works, works, and then **stops**, somewhere between 20 px and 15 px of ball.

**And the detection floor converts into a working distance that differs sharply by format:**

| | 20 px, last found | 15 px, lost |
|---|---|---|
| 4K/120 (`fx` 2520) | **26.0 m** | 34.6 m |
| 1080p/240 (`fx` 1260) | **13.0 m** | 17.3 m |

**1080p has half the working distance of 4K, and that is a practical problem rather than a theoretical one.** The ball recedes during flight — this document records one measured flight running from 9 m to 24 m. At 4K that stays inside the floor throughout. **At 1080p it crosses below 20 px at about 13 m and the detector loses it mid-flight**, which is not a subtle degradation but a hard stop.

**This is a candidate explanation for something already on the books.** Kicks 1, 6 and 7 are the three 1080p clips of the 2026-08-22 set, and all three are the troubled ones: kick 1 is flagged SUSPECT at gravity 4.40, kick 7 fails entirely — "acquires for a single frame and collapses" — and kick 6 is the only clean one and also the shortest kick of the set at 9 yards, so it recedes least. **Not proof**, since kick 10 is 4K and also fails, but it is a specific, testable hypothesis where before there was none. Worth checking against 3.2 and 3.3.

**Section 2.1 is complete.** The physics is validated, three premises have been overturned, one defect found and handed to 3.5, and both detector questions — blur response and scale response — are measured.

**2.2 Settle the 1080p focal length.** *(was Step 6)* Measure a distance to a stationary ball with a tape, film it at rest in both formats without moving the phone, and solve `fx = d · Z / D` for each. The 4K value is confirmed exactly; the 1080p value is 5.1% out and it is not known whether that is the lens or a sloppy pace — see *Camera capability*. It belongs here rather than later because no correction should be fitted on top of a possible 5% scale error. `shot-list.txt` now opens with this shot.

### 3 — Fix the physics

**3.1 Correct the progressive under-read in the detector's flight diameters.** *(was Step 5)* Fitted gravity averages 7.7 across nine clips, or 8.3 across the seven not flagged suspect, rather than 9.81, and this is the cause — see *The gravity discrepancy*. It can be corrected on either side of the export since the boxes match to 0.00%, subject to 1.1.

**Start by classifying the clips rather than correcting them.** The synthetic work of 2.1 established that a *uniform* diameter error and a *progressive* one have different signatures, need different fixes, and are told apart by the **vertical residual** together with how the error moves with window length. It also showed that a 6% progressive bias over kick 11's real 0.87 s window reproduces both its 3.2 mm residual and its −5.9% gravity error. So the first step is to tabulate residual, window length and fitted gravity across all nine clips and see which pattern each fits — the pipeline already computes every one of those numbers and nothing currently reads them together.

⚠️ **Do not rank clips by fitted gravity.** It is not a severity measure across clips of different flight durations: the same defect reads −10.9% at 0.10 s and +5.6% at 2.90 s. The spread of 4.40 to 10.48 across the 2026-08-22 set is partly a spread of window lengths. **The residual is the honest indicator** — it grows with the bias and never changes sign.

**3.2 Diagnose kick 7**, which acquires for a single frame and collapses.

**3.3 Diagnose kick 10**, which detects correctly but whose track only starts near the end of the clip.

**3.5 Report launch conditions at ball–boot separation, not at the start of the fit window.** Found by the synthetic harness on 2026-08-24 and described in full under *The launch-time origin defect*. `fit_launch()` evaluates at the window start, `contact + --skip-frames`, so vertical velocity is under-reported by `g · Δt` — 0.245 m/s at the defaults, 0.899 m/s on a clip needing `--skip-frames 11`. Carry and apex compound it by taking their height from the ball at rest while taking their velocity from several frames later: **carry −2.26%, apex −4.46%** on the synthetic kick.

The fix is to evaluate the fitted trajectory at the separation instant, recovering **both** velocity and height there from the same fit, rather than shifting velocity alone. Cheap in Python, and 4.3 would otherwise port the defect into Swift.

**This item has something none of the others do: an exact pass/fail test.** `synth_track.py check` states the true answer, so the fix either recovers 25.00 m/s at 35.00° or it does not. Note also that **the gravity self-check cannot verify it** — gravity is invariant to a shift of time origin, which is why the defect survived nine clips of real footage.

**3.4 End the fit window on a net impact and on the ball leaving the frame.** `find_landing()` detects only a bounce — a reversal in vertical image position after the apex — so it cannot see either of the two ways a flight normally ends in real use; see *Measurement Approach → Truncated flight is the normal case*. This is the same class of defect as the bounce-window bug that produced the gravity discrepancy: a window containing something that is not free flight, failing silently rather than visibly. It belongs in this section because it is physics work, it is fixed in Python where iteration is fast, and it must be right before 4.3 ports the fit to Swift.

**What is already achieved here, and should not be re-litigated.** On every clip whose track reaches the ground, observed displacement matches the paced landing to within 3–10%. That is the first end-to-end validation this project has had: focal length from field of view, ball diameter as scale, per-frame depth and 3D geometry, all confirmed against a distance measured on the pitch rather than against themselves. Ten of eleven 2026-08-22 clips track the right ball and nine produce sound metrics, against two and zero before 2026-08-24.

**Seven clips can never be checked against their paced landings, and no amount of processing will change that.** Their tracks end before the ball lands; raising `--max-gap` to 90 pushed out the termination frames while leaving every longest-unbroken segment unchanged, because the ball had left the picture. The footage does not contain the answer.

The cause is that the session was filmed to measure kicks and then used to validate the pipeline, which want opposite framing — see *Measurement Approach*. `shot-list.txt` item 14 now requires the landing in shot for validation footage.

### 4 — Port to the device

*(was Step 7)* Export the detector to Core ML, drive it through `VNCoreMLRequest`, replace OpenCV registration with the Vision equivalents, and reimplement the trajectory fit in Swift.

**Done on 2026-08-24:**

- `yolo11n` exported to Core ML as `yolo11n.mlpackage`, verified to reproduce PyTorch boxes to 0.00%.
- The crop architecture measured and validated — 640 px at native resolution matches full-frame 3840. This is what gets ported, not the Mac's full-frame approach.
- A pinned export environment built so the conversion is reproducible.

**4.1 Port the tracker with crop-based inference**, driven through `VNCoreMLRequest`: acquire once on a full frame, then track in 640 crops at native resolution.

⚠️ **The port needs NMS, or an equivalent, before the largest-candidate rule is applied.** Learned during 1.1. The model is exported with `nms=False` — deliberately, so `detect_ball.py` can do its own candidate selection — so its raw output fires many anchors on the same ball. The Mac applies largest-candidate to boxes Ultralytics has *already suppressed*, one per object. Applying the same rule to raw anchors instead selects the largest duplicate, which measured **0.46–1.36% high** on diameter across the four test crops. Largest-candidate acquisition is correct and is not in question; it is the input to it that must match. A systematic 1.4% diameter bias is small, but diameter precision is the weakest link in the pipeline and a 6–9% bias is the outstanding defect of 3.1, so it is not noise to absorb silently.

**Working code for the decoding already exists** in `ANEComparison.swift` — reading `var_1223`, taking COCO class 32, converting centre/width/height to a diameter, handling float32 and float16 — written for 1.1 and verified against the Mac to two decimals. It is worth lifting rather than rewriting when this item starts.

**4.2 Replace registration with Vision** and check it against the OpenCV results on the same clips, since `VNTranslationalImageRegistrationRequest` is a different algorithm rather than a reimplementation.

**4.3 Port the maths.** Last of the port work because it is the lowest risk — `compute_metrics.py` is pure numpy and every call has an Accelerate equivalent — and because it should be ported after the physics above is corrected, not before.

### 5 — Feed the pipeline what it needs at capture

**5.1 Write the true `videoFieldOfView` into each clip at capture**, so the app stops assuming `fx` the way the Mac pipeline hardcodes 1260 or 2520 — see *Porting risks*.

**5.2 Add a camera distance control to the Record screen.** *(was Step 7.6)* The acquisition gate needs the distance the coach paced out, captured per clip beside the ball size for the same reason — it describes the clip, not the app.

### 6 — Make the output usable

**6.1 Surface the quality signals** — off-square angle, camera drift, fitted gravity. *(was Step 8)* Coaches cannot pass flags, so a bad clip must explain itself. The check is cheap and concrete: the ball's diameter trend across the flight measures how far off perpendicular the shot was, and background registration already measures camera movement. Both numbers exist in the Mac pipeline; nothing surfaces them to the coach. Framing guidance before the kick belongs here too.

⚠️ **Two hard operating limits were measured on 2026-08-24 and neither is checked anywhere.** These are not quality *signals* — they are the difference between a measurement and no measurement at all, and they are known **before** the kick:

- **Exposure.** The detector loses the ball entirely at about 29% of its width in smear. At 30 m/s that needs roughly **1/728 s**; if exposure runs to the frame interval, as it does in falling light, relative blur is 61% at 240 fps and 121% at 120 fps, both far past failure. `AVCaptureDevice.exposureDuration` is readable live, so the app can warn *before* recording rather than after. **A higher frame rate does not rescue this** — relative blur is `v·exposure/D` and the focal length cancels.
- **Distance.** The detector finds nothing below about 20 px of ball, which is 26 m at 4K and only **13 m at 1080p**. The ball recedes during flight, so a clip can start inside the limit and cross out of it mid-flight.

**Both belong in front of the coach at capture time, not in a post-hoc quality report.** See *The detector's blur response* and 2.1 rung 13.

**Neither is in `shot-list.txt` either**, which the filming protocol section says should be kept in step with this document.

**6.2 Build the results screen.** *(was Step 9)* Nothing in the app displays a metric. Whatever it shows must label carry and apex as theoretical, and should present the quality signals from 6.1 rather than a bare number as though it were certain.

### Off the critical path — hardware checks not blocking the above

These were Step 6 and Step 6b. They are quick, they are worth doing at the next opportunity, and nothing in sections 1–6 waits on them.

- **The ball size metadata.** The picker builds and runs, but no recording has been checked. Record a clip and confirm the status panel reads `· ball 206.1 mm` rather than `BALL SIZE MISSING`. That is the half of the two-copy scheme that cannot be checked by looking at filenames in Files.
- **Import and share in the clip browser.** Built in response to the AirDrop trouble and never exercised. Import a `.mov` from Files, and share one out.
- **Measure what Photos does to 240 fps.** *(was Step 6b)* Run a 1080p/240 clip through Photos by the same route the 4K/120 clip survived, and probe it. The store question no longer depends on this — `Documents/Clips/` stays on its own merits, for the reasons under *Should Photos be reconsidered as the store?*. The reason has changed: it tells us what an **import probe** will encounter when a coach brings in a clip that has passed through Photos. That probe has to exist anyway for external footage, and this is the case it most needs to catch.

### Why the order changed, kept because the reasoning still applies

**Porting was moved ahead of the remaining accuracy work on 2026-08-24, on a premise the export has since disproven.** The worry was that the bias belongs to the PyTorch model's boxes and that Core ML export would change them, so measuring it first would mean measuring it twice. Measured 2026-08-24, the export reproduces the boxes to **0.00%** — so the bias would have transferred and the reordering was not necessary for that reason.

It was worth doing anyway, and by some distance. Exporting first is what surfaced the crop architecture, which resolved the largest porting risk on the books and revealed that full-frame 1280 — the obvious on-device compromise — silently loses the ball mid-flight. Neither would have been found by finishing the accuracy work first. **The decision was right; the stated reason was wrong.**

That history is why section 1 sat at the top: the one thing the export had not proven was the runtime, and the same class of mistake — building on numerics that turn out to differ — is what the device comparison foreclosed. **It has since been run and the runtime is proven**, so section 1 is closed and section 2 is the live work. The reordering paid for itself twice: once by surfacing the crop architecture, and again by revealing that the ANE this project planned around is not reachable at all.

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

- **1080p at 240 fps** — roughly 12.5 cm of ball travel between frames at 30 m/s. Twice the trajectory samples. The claim that a shorter exposure means less blur **holds only in poor light**, where exposure is capped by the frame interval; at a given exposure relative blur is identical between the formats because `fx` cancels. That blur *inflates* the apparent diameter is now confirmed directly — +4.7% at 12 px of smear. Calibrated from field of view; no intrinsic matrix available. **Working distance is only 13 m before the detector loses the ball**, against 26 m at 4K.
- **4K at 120 fps** — roughly 25 cm between frames, but four times the pixels across the ball, so a more precise diameter estimate, which propagates into distance and therefore into every metric.

**Both configurations are currently calibrated from field of view, and 4K/120's intrinsic matrix is not in fact an advantage today.** The camera reports intrinsics only to a live capture session; they are **not stored in the recorded movie file**. Deliverable 1 analyses a saved video, so intrinsics are unavailable at analysis time unless they are captured alongside the recording and written to a sidecar — which has not been built. Until it is, the choice is purely samples-and-blur versus pixels-on-ball.

**This cannot be settled by filming the same kick both ways.** One phone runs one format at a time, so a single kick cannot be recorded at 1080p/240 and 4K/120 simultaneously. Comparing configurations means comparing sets of kicks in aggregate, or using two devices. The 2026-08-21 session produced five of each; the 2026-08-22 session came out **3 × 1080p and 8 × 4K**, which is a thin and lopsided basis for the comparison even though it is good data for the physics. A future session wanting to settle this should hold the split even and record which is which deliberately.

**The pipeline now measures the thing that decides this.** `compute_metrics.py` reports range scatter about the fitted trend and fitted gravity, both of which degrade with depth noise. Running the same analysis across the 1080p and 4K sets answers the question empirically rather than by argument.

**One comparison has been run and it was not valid.** At `--imgsz 1280`, 1080p showed 3.7% relative diameter scatter against 4K's 4.4%, suggesting 4K was no better. But that setting downscales a 1920-wide frame by 0.67× and a 3840-wide frame by 0.33× — 4K was handicapped by twice as much. A fair test needs both at native resolution, which is now the default.

**The synthetic harness has since answered the structure of this question, though not yet the value.** Measured 2026-08-24 on the *same* kick, which no filming session can do — see punch list item 2.1, rungs 9 to 11:

- **On random precision, 4K/120 wins** by about 1.3–1.6× on every column, because twice the pixels across the ball beats twice the temporal samples.
- **On blur-induced bias, 1080p/240 wins by about 4×**, and that factor is structural rather than fitted: the ball moves 14.4 px per frame at 1080p/240 against 57.4 at 4K/120, since `fx` is doubled *and* the frame interval is doubled.

**Measured 2026-08-24, and the answer is that the format is not the variable — the light is.** See *The detector's blur response*.

Relative blur is `v · exposure / D`. The focal length **cancels**, so at a given exposure both configurations smear the ball by the same fraction of its own width. 240 fps reduces blur only when exposure is capped by the frame interval, which happens as light falls — and by then relative blur is 61% at 240 fps and 121% at 120 fps, both far past the ~29% at which the detector stops finding the ball at all. **In poor light neither format works.**

**So, provisionally: 4K/120.** In light good enough for the pipeline to function, blur is equal in relative terms and 4K's extra pixels win on precision — measured at roughly 1.3–1.6× better scatter on every column. An earlier note here claimed 1080p/240 had a structural ~2× blur advantage; that is wrong, and it came from forgetting that `fx` cancels.

**A second, larger argument for 4K has since been measured: working distance.** The detector loses the ball entirely below about 20 px, which is **26 m at 4K but only 13 m at 1080p**. The ball recedes during flight — one measured flight runs from 9 m to 24 m — so at 1080p it can cross below the floor *mid-flight* and the track simply ends. Suggestively, the three 1080p clips of the 2026-08-22 set are the three troubled ones. See *The detector's blur response* and punch list 2.1 rung 13.

⚠️ **One thing keeps this provisional.** The launch-time origin defect of 3.5 contaminates the speed column with a frame-rate-dependent offset — `--skip-frames 3` is 12.5 ms at 240 fps against 25 ms at 120 fps — so a format comparison is not clean on that metric until it is fixed. The precision and working-distance arguments are unaffected by it.

**Pixels on the ball, and why filming distance dominates accuracy**

Range is recovered from apparent diameter: `Z = fx × D / d`. Run backwards, that gives the ball's pixel width at a given range for a Size 4 ball (D = 206 mm):

| Range | 1080p (fx ≈ 1260) | 4K (fx ≈ 2520) |
|---|---|---|
| 3.7 m *(first footage)* | 70 px | 140 px |
| 10 m | 26 px | 52 px |
| 20 m | 13 px | 26 px |
| 27 m | 9.6 px | 19 px |
| 40 m | 6.5 px | 13 px |

Relative range error tracks relative diameter error one for one. Half a pixel of error on a 70 px ball is 0.7%; the same half pixel on a 9.6 px ball is 5%.

⚠️ **The last clause of that sentence used to read "and it propagates into every metric", and measurement has shown it does not — for *random* error.** `reconstruct()` fits a straight line through the per-frame ranges rather than using them individually, so random diameter noise is suppressed by √N across the fit window. Measured 2026-08-24, speed scatter is 0.03% at 5 m and only **0.18% at 27 m**, where the ball is 19 px — a linear, gentle degradation with no cliff anywhere in the range. See punch list item 2.1, rung 11.

**What does propagate into every metric is *systematic* diameter error**, which no amount of averaging touches. That distinction is the reason 3.1 is the priority and noise is not, and it is why the argument below — that distance is the dominant accuracy parameter — needs restating in terms of bias and of detection failure rather than of pixel scatter.

**The geometry traps you.** With a 74.6° field of view, framing a 40 m flight means standing about 26–27 m back. At that range the ball is under 10 px at 1080p. Whole flight in frame and a well-resolved ball are in direct conflict, and no technique resolves it — only a longer lens or a second camera would.

**This is evidence for 4K/120** in the open question above. At realistic goal-kick range it roughly doubles the pixels across the ball, and the diameter estimate is the weakest link in the chain.

**A constant-range assumption was tried and abandoned.** The reasoning was that for a side-on shot the ball stays at roughly constant range, so diameter could be averaged once to fix the scale and the flight treated as flat. Measured against real footage it failed silently and badly: the ball was travelling ~11–15° toward the camera, its apparent size grew across the flight, and the steadily inflating scale cancelled gravity's curvature almost exactly, reporting a straight line through what should have been a 48-pixel sag.

**The mechanism is the point and it still applies:** an error that grows monotonically with range does not add noise to the fit, it adds *curvature*, and curvature is the signal. The same shape of problem is what the flight-diameter bias does today — see *The gravity discrepancy*.

**Depth is now computed per frame**, with the range trend smoothed by a straight-line fit before use: over a fifth of a second range changes almost linearly, while measured diameter wobbles a few percent frame to frame, and because both X and Y are multiplied by range that wobble would otherwise contaminate every axis.

The gravity figures this section once quoted as evidence — −0.16 and 3.49 m/s² — have been removed. They were waypoints in a debugging sequence, measured through a pipeline that has since had its contact detection, its flight window and its fit all corrected, and they no longer reproduce: that clip now fits gravity at **10.90 m/s²**. Keeping them would leave two different figures for the same clip in one document.

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

**First footage, filmed 2026-08-21 — the clips are gone.** They are not on the Desktop and not elsewhere on the Mac; only `tools/frames/archive-0821/GoalKick-2026-08-21-080847-1080p240-track.csv` survives, which permits re-running the physics but not detection. Everything below is recorded from when the footage existed. Size 4 ball, teal. Ten clips — five at 1080p/240, then five at 4K/120. Camera **side on and static** (handheld, no deliberate pan; the framing holds across a whole clip). Distance not measured. These clips predate the ball size selector, so they carry no size token and no metadata.

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

**The launch-time origin defect — found by the synthetic harness, 2026-08-24**

**`fit_launch()` reports velocity at the start of the fit window, and the pipeline labels it "LAUNCH (measured)".** The window begins at `contact + --skip-frames`, so the reported velocity is the ball's velocity some frames *after* it was struck. Gravity has been acting for that whole interval, so the vertical component is under-reported by exactly `g · Δt`.

Verified arithmetically on the synthetic run: contact detected at frame 61, `--skip-frames 3`, so the fit's origin is frame 64 against a true launch at frame 60. Four frames at 120 fps is 0.0333 s, and `14.3394 − 9.81 × 0.0333 = 14.0124` against a recovered **14.0129**. The fit is not wrong; the *time it is evaluated at* is.

**What it costs, by configuration:**

| skip | rate | interval | vy under-read by |
|---|---|---|---|
| 3 | 120 fps | 25.0 ms | 0.245 m/s |
| 3 | 240 fps | 12.5 ms | 0.123 m/s |
| 11 | 120 fps | 91.7 ms | **0.899 m/s** |

`--skip-frames 11` is not hypothetical — it is what kick 11 needed, because the detector lost the ball off the boot for twelve frames.

**A second defect is coupled to it, and this one is unambiguous.** Carry and apex are computed with `launch_height` defaulting to one ball radius, 0.103 m — the ball at rest on the grass. But the velocity handed to them is the velocity at the *window start*, by which time the ball has climbed 0.47 m. The model therefore takes its speed from one moment and its height from another. On the synthetic kick:

| | carry | apex |
|---|---|---|
| true launch — 25.00 m/s, 35.00°, h 0.103 | 60.02 m | 10.58 m |
| what the pipeline reports | 58.66 m | 10.11 m |
| error | **−2.26%** | **−4.46%** |

⚠️ **The gravity self-check cannot see any of this, and that is why it survived.** Gravity is the quadratic coefficient of the fit, and a quadratic's curvature is invariant under a shift of time origin. So the project's only independent check is structurally blind to this defect — nine clips of real footage could never have revealed it, and no amount of further footage would. **This is the argument for the synthetic harness in one example.**

**One honest complication before fixing it.** `--skip-frames` exists to drop frames while the ball is still deforming against the boot, and during genuine boot contact the ball is *not* in free flight, so velocity measured there would not be launch velocity either. Real boot contact is roughly 8–10 ms — about one frame at 120 fps. The defaults skip 3, and kick 11 skipped 11. So the pipeline over-skips relative to actual ball-boot separation and under-reports as a result; the synthetic model, which has no deformation phase at all, exposes the full offset rather than the excess. **The fix is to extrapolate the fitted trajectory back to the moment the ball leaves the boot — recovering both velocity and height at that instant from the same fit — not simply back to the detected contact frame.**

**The detector's blur response — measured 2026-08-24, and it is the most practically consequential result of the day**

`export_coreml.py blur` applies synthetic horizontal motion blur to the ball **at rest**, where the true diameter is known and nothing else changes. Real footage cannot do this: in a real flight the ball recedes and blurs together and the two are hopelessly confounded, which is much of why the diameter bias has resisted diagnosis.

| blur | diameter | error | confidence | implied range |
|---|---|---|---|---|
| 1 px | 58.28 px | +0.0% | 0.96 | 8.91 m |
| 4 px | 58.02 px | −0.5% | 0.96 | 8.95 m |
| 8 px | 59.38 px | **+1.9%** | 0.94 | 8.75 m |
| 12 px | 61.04 px | **+4.7%** | 0.73 | 8.51 m |
| 17 px | **NOT FOUND** | — | — | — |
| 25 px and beyond | **NOT FOUND** | — | — | — |

**Three findings, in increasing order of importance.**

**1. Blur inflates the box; it does not shrink it.** This reverses an assumption recorded above as settled. A larger box means diameter over-read, range *under*-estimated, and distances too short — the opposite sign to the recession bias. The earlier "the box shrinks" observation was taken at contact, where the ball is partly behind the boot: **that was occlusion, not blur.**

**2. The detector over-reads a sharp, resting ball by about 2.6%.** Geometry predicts 56.82 px at 9.14 m through `fx` 2520; the detector returns 58.28 px at confidence 0.96. That is a **uniform** scale error, and by the signatures established in 2.1 it is invisible in the residual and shows up directly in fitted gravity — biasing every distance short by 2.6%.

**3. Detection fails entirely at 17 px of blur, and that is the finding that matters.** The ball is found at 12 px of smear — 20.6% of its own width, confidence already down to 0.73 — and is **not found at all** at 17 px, 29.2%. Somewhere between a fifth and a third of the ball's width, the detector stops seeing a football.

⚠️ **This is a light-level constraint, and it is severe.** Relative blur is `v · exposure / D`, so it depends on the ball's speed and the exposure and **not at all on the format**. To stay under 20% relative blur:

| ball speed | exposure required |
|---|---|
| 13 m/s | 1/315 s |
| 20 m/s | 1/485 s |
| 30 m/s | **1/728 s** |

**And the frame interval alone is nowhere near enough.** If exposure runs to the full frame interval — which is what happens as light falls — relative blur is:

| | 13 m/s | 30 m/s |
|---|---|---|
| 120 fps | 53% | **121%** |
| 240 fps | 26% | **61%** |

Every one of those is at or beyond the failure threshold. **In poor light this pipeline does not degrade, it stops working**, and 240 fps does not save it. The app must therefore either verify a short exposure at capture time or warn the coach, and neither exists.

**This also explains why the first footage looked so clean.** It was shot in bright sun at ~13 m/s, where relative blur is small enough that panel detail was legible — a case this document already recorded as retiring the blur risk "at that speed and in that light only." That caution was right, and the risk is now quantified rather than merely flagged.

**What it means for the format question is that the format is not the variable.** Because `fx` cancels, both configurations smear the ball by the same fraction of its own width at a given exposure. 240 fps helps only when exposure is capped by the frame interval — that is, only in poor light, and by then both formats are past the failure threshold anyway. See *Which capture configuration gives better metric accuracy*.

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

**The synthetic harness has since explained why, and the answer is sharper than "second order."** Run at 30° off-square with exact diameters, gravity comes back to **−0.00%** and `vz` to +0.01% — the same as square on. The pipeline reconstructs depth per frame rather than assuming it, so the out-of-plane component is *recovered*, not lost. **The cross-term is therefore not a geometric penalty at all; it is an amplifier of depth error.** With accurate diameters there is nothing for it to amplify, which is exactly why the control kick survived its geometry. It also means the cross-term and the flight-diameter bias are not two problems but one: fix the diameters and the cross-term stops mattering. See punch list item 2.1.

**The whole set has since been run, and the window was not the only problem.** Fitted gravity across the nine clips that produce metrics runs from **4.40 to 10.48**, mean **7.73**. Excluding the two the tool itself flags SUSPECT — kicks 1 and 8 — the remaining seven run 7.01 to 10.48, mean **8.34**.

Quote whichever is relevant but say which: the nine-clip mean is the honest headline, the seven-clip mean is what the pipeline achieves when it does not visibly fail. Both are well short of 9.81 and short in the same direction, which is the finding. Regenerate them rather than trusting these figures — see *Reproducing the current results*.

**The vertical axis reads about 22% low while the horizontal validates.** On every clip whose track reaches the ground, observed displacement matches the paced landing to within 3–10%. The vertical does not, and the two share a range and a focal length.

The fit is *internally* consistent, which is why this hid for so long: with `vy` and gravity both scaled down together, flight time `2·vy/g` is unchanged, so the duration agrees with the fit while both disagree with reality.

**Four causes were tested and eliminated, in this order:**

| Suspect | Verdict |
|---|---|
| Motion blur inflating the detector box | ⚠️ **That refutation is itself wrong — see *The detector's blur response* below.** It rested on the box shrinking 58.4 → 42.9 px as confidence fell to 0.34, but those frames are at contact, where the ball is partly behind the boot and the kicker's leg. That is **occlusion, not blur.** Measured in isolation on a resting ball, blur *inflates* the box — +1.9% at 8 px of smear and +4.7% at 12 px |
| Air resistance biasing a drag-free fit | **Refuted** — fitting against the drag ODE moved gravity only 7.65 → 7.74 |
| Camera tilt / wrong principal point | **Refuted** — gravity is provably invariant to `cy0`, which contributes `cy0·Z/fx`, and `Z` is linear in time, so it can only add a linear term |
| Anchoring range to the resting diameter | **Tried and worse** — see below |

**The cause is a progressive bias in the flight diameters.** Camera height recovered from the ball resting on the ground and again at landing —

```
h = D·(cy₁ − cy₂)/(d₁ − d₂)
```

— needs neither focal length nor principal point, and reads **1.09 m** across three clips against a phone held at about **1.4 m**. Run `validate.py height` to regenerate it.

Working the geometry backwards on kick 9: the resting diameter is right, within a percent or so of the 56.8 px the paced 9.14 m predicts, while the landing diameter is under-read by **roughly 6–9%** — 37.0 px measured against the 39.5–40.6 the flat-pitch constraint demands, depending which resting frame is taken as the reference.

So the detector's box degrades as the ball recedes and blurs. **The horizontal survives it because `X` uses `D/d` directly, where a 6% error stays 6%. The vertical goes through the range slope, where the cross-term `2·u̇·Ż/fx` amplifies it.** That is the same cross-term this document has named since the beginning — now with a cause rather than only a magnitude.

**Confirmed synthetically 2026-08-24, with one important qualification.** Injecting a 6% progressive under-read into a known trajectory does exactly this: the residual rises from 1.19 mm to 40.60 mm and every recovered quantity moves by 3.6–9.2%. But **the sign of the gravity error depends on the length of the fit window** — a progressive depth inflation multiplies the parabola by a growing factor, injecting a cubic term that drags gravity down over short windows and pushes it up over long ones, crossing over near two seconds. The real clips all fit well under that, which is why they read low.

Two things follow for the work in 3.1. **Fitted gravity is not a severity measure across clips of different durations** — comparing 4.40 against 10.48 is partly comparing flight times, not just how badly each is biased. And **the vertical residual is the better indicator**: a factor of 34 here, and unlike gravity it never changes sign, because a quadratic simply cannot describe a cubic. Nothing in the pipeline currently reads the residual as a bias indicator, and it is the cheapest signal available.

**Anchoring the range line to the resting diameter followed obviously and was wrong.** A free fit spreads the flight bias between intercept and slope; anchoring the intercept forces the *slope* to absorb all of it, and the slope is what gravity is most sensitive to. Measured across the set it moved gravity the wrong way on nearly every clip — 8.13 → 6.11, 7.37 → 6.16, 7.01 → 6.25, 9.49 → 8.28 — while improving carry slightly. Kept as `--rest-anchor`, off by default, so the experiment can be repeated rather than re-argued.

**Correcting the diameter bias itself is the remaining work, and it can be done on either side.** The concern was that the bias belongs to *this* detector's bounding boxes and that a Core ML export would change the numerics, so characterising it on the Mac risked measuring it twice. Measured 2026-08-24, the export reproduces the boxes to **0.00%** — the bias is a property of the architecture, not the runtime, and whatever is learned on the Mac transfers.

**That caveat is now discharged.** The comparison was repeated on an iPhone 17 Pro on 2026-08-24: the device reproduces the Mac's diameters to two decimals on all four test crops, box coordinates are identical across every compute unit, and the Neural Engine turns out to be unreachable by this Float32 export in any case. "The numerics are identical" is proven for the runtime as well as the conversion, so **whatever is learned about the diameter bias on the Mac transfers to the device without qualification.** See punch list item 1.1.

**The earlier four-run table has been removed** rather than kept. Every figure in it was produced by fitting past the end of the flight, so the numbers measured the bug and not the footage. The one finding from it that survives on its own evidence is that detector input resolution matters: raising `--imgsz` from 1280 to 1920 on the same 4K clip cut range scatter from 200 mm to 118 mm. `--imgsz` now defaults to the clip's own width.

**That default is load-bearing and may not survive the move to the device.** See *Porting risks* under Tech Stack — native-resolution inference is the least device-friendly thing in the pipeline, and diameter precision is what every distance rests on.

**The c1 anomaly is resolved.** It was recorded here that on c1 the ball appeared to accelerate upward across the tracked frames, which free flight forbids, with diameter bias against dark netting as the leading suspect. Re-run on 2026-08-24 through the current pipeline, c1 fits gravity at **10.90 m/s² — 11.1% out, and the tool's own verdict is "good"** — against the 3.49 recorded when the anomaly was written down. Speed 13.31 m/s at 28.3°, vertical residual 14.0 mm.

Nothing was done to c1 specifically. The anomaly was an artifact of the pipeline that measured it — contact detection firing early and a drag-free fit — and it disappeared when those were fixed for other reasons. **No separate mystery remains.**

Worth noting how that was possible: the 2026-08-21 footage no longer exists, but `tools/frames/archive-0821/*-track.csv` does, so the physics could be re-run without it. That is precisely the property the tracks were committed for.

**The protocol lives in `shot-list.txt` at the repo root.** Plain text so it opens on a phone in a field. It covers where to stand, how far back, how to frame the ball, and what to shoot. It was followed on 2026-08-22 and revised afterwards from what that session taught. Three items in it carry the most weight:

- **Clear other footballs out of shot.** The one the coach is measuring must be the nearest. This cost nine clips of eleven before the acquisition rule was fixed.
- **Pace out where the ball first lands.** Done for all eleven kicks on 2026-08-22, which finally gives carry distance something to be checked against. Keep doing it every session; it costs nothing but counting.
- **One kick deliberately off perpendicular**, as a control. Shot as kick 11 and it worked as intended — the off-square warning fired at 56.5°. Note the diagnostic did *not* degrade the gravity fit the way this document expected, which is what exposed the real cause.

Keep `shot-list.txt` and this section in step as the protocol changes.

## End of Document
