#!/usr/bin/env python3
"""Export the ball detector to Core ML, and check the export changed nothing.

Run this with tools/.venv-export, NOT tools/.venv:

    ./tools/.venv-export/bin/python tools/export_coreml.py export
    ./tools/.venv-export/bin/python tools/export_coreml.py compare CLIP

Why a second environment. coremltools converts from TorchScript and is
pinned to torch versions it has been tested against. tools/.venv runs
Python 3.14 with torch 2.13 because that is what makes detection fast on
this Mac; coremltools 9.0 has tested up to torch 2.7 and fails on 2.13 with
a cascade of frontend errors, each patch revealing the next. Patching a
model *converter* by hand is a bad trade when the whole point is measuring
bounding boxes to a few percent: it can export cleanly and compute
something subtly different.

So the two environments do different jobs and are allowed to disagree.
tools/.venv is the fast path and runs constantly. tools/.venv-export runs
once per model version, does not care about speed, and is pinned to
versions coremltools actually supports. See tools/requirements-export.txt.

Input size is the interesting parameter. Measured on a 4K clip with the
ball at a known 57.2 px:

    imgsz  640   ball not found at all
    imgsz  960   found, confidence 0.43
    imgsz 1280   found, but LOST mid-flight and 33% wrong late
    imgsz 3840   accurate to 1.6% throughout, confidence 0.82-0.94

which is why the Mac pipeline defaults to the clip's own width. On a phone
that means a 3840 px Core ML input, 36x what a YOLO export normally takes.

The way out is not a bigger model input, it is a smaller picture. Cropping
640 px around where the ball is predicted to be, at native resolution,
matches full-frame 3840 accuracy while the model sees only 640 px:

    frame          truth   full@1280      full@3840    crop640@native
    at rest       57.2px      +0.6%           -0.1%            +1.9%
    early flight  52.4px      +6.0%           +0.1%            +3.3%
    mid flight    37.7px  not found           +0.0%            -0.2%
    late flight   30.4px     +32.9%           -1.6%            -0.2%

The ball keeps every pixel it had; only the empty grass around it is
discarded. That is the architecture to port: acquire once on a full frame,
then track in crops.

Settled on device, 2026-08-24 (punch list item 1.1, project_notes.md).
An iPhone 17 Pro reproduces the diameters above to two decimals, and box
coordinates are identical across CPU, GPU and .all. Two things that were
assumed here turned out to be wrong, and both are worth knowing before
touching this file:

  - The Neural Engine is NOT what runs. This export is Float32, the ANE
    requires float16, and none of the model's 242 compute operations
    lists the ANE as supported. Every one prefers the GPU. Staying on
    Float32 is a recorded decision, not an oversight.

  - Native-resolution inference was never a throughput problem. The GPU
    runs a 640 px inference in 5.68 ms -- every frame of a 787-frame 4K
    clip in 4.5 s. The crop architecture is still right, but for diameter
    precision, which is the reason that survives.

One trap for whoever ports this. Ultralytics applies NMS before selecting
a box; the model itself is exported with nms=False, so a raw Core ML
decoder has none. Applying the pipeline's largest-candidate rule to raw
anchors picks the largest DUPLICATE and reads 0.5-1.4% high. The rule is
right; the input to it has to be suppressed boxes.
"""
import argparse
import sys
from pathlib import Path

SPORTS_BALL = 32          # COCO class index
DEFAULT_MODEL = "yolo11n.pt"
CROP = 640

# The Core ML export lives inside the app target, not at the repo root, and
# there is deliberately only one copy of it. GoalKick/ is a synchronized
# folder, so anything in it joins the app automatically and Xcode compiles
# this into yolo11n.mlmodelc at build time -- which means the app will not
# build without it. Keeping a second copy at the root would have been ~10 MB
# of duplicate binary in git and two files free to drift apart on the next
# re-export.
#
# Consequence for `export`: ultralytics writes its output next to the .pt
# weights, so a fresh export lands at the repo root and has to be moved here.
DEFAULT_COREML = "GoalKick/yolo11n.mlpackage"


def biggest_ball(model, image, imgsz):
    """Largest sports-ball box in one image, as (diameter, confidence)."""
    result = model.predict(image, imgsz=imgsz, verbose=False)[0]
    best = None
    for box in result.boxes:
        if int(box.cls.item()) != SPORTS_BALL:
            continue
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        diameter = ((x2 - x1) + (y2 - y1)) / 2
        if best is None or diameter > best[0]:
            best = (diameter, box.conf.item())
    return best


def run_export(args) -> None:
    from ultralytics import YOLO

    weights = Path(args.model)
    if not weights.exists():
        sys.exit(f"{weights} not found. Run from the repo root.")

    print(f"Exporting {weights} at {args.imgsz} px...")
    print()
    print("  NMS is left off deliberately. detect_ball.py does its own")
    print("  candidate selection -- nearest ball wins, gated on the paced")
    print("  camera distance -- and baked-in NMS would discard the very")
    print("  candidates that choice depends on.")
    print()

    model = YOLO(str(weights))
    path = model.export(format="coreml", imgsz=args.imgsz, nms=False)
    print()
    print(f"Wrote {path}")
    print()
    print("Now check the export changed nothing:")
    print(f"  ./tools/.venv-export/bin/python {sys.argv[0]} compare CLIP")


def run_compare(args) -> None:
    """Same frames through both models, so any difference is the export."""
    import cv2
    from ultralytics import YOLO

    torch_model = YOLO(args.model)
    coreml_model = YOLO(args.coreml)

    capture = cv2.VideoCapture(str(args.clip))
    if not capture.isOpened():
        sys.exit(f"Could not open {args.clip}")

    frames = [int(f) for f in args.frames.split(",")]
    print(f"Comparing {args.model} against {args.coreml} at {CROP} px, "
          f"on native-resolution crops.")
    print()
    print(f"{'frame':>7} {'pytorch':>18} {'coreml':>18} {'delta':>9}")

    worst = 0.0
    for frame_number in frames:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, image = capture.read()
        if not ok:
            print(f"{frame_number:7d}   could not read")
            continue

        # Without a track to predict from, crop the frame centre. The point
        # is comparing two models on identical pixels, not finding the ball.
        cy, cx = image.shape[0] // 2, image.shape[1] // 2
        if args.at:
            cx, cy = (int(v) for v in args.at.split(","))
        x0 = max(0, min(image.shape[1] - CROP, cx - CROP // 2))
        y0 = max(0, min(image.shape[0] - CROP, cy - CROP // 2))
        window = image[y0:y0 + CROP, x0:x0 + CROP]

        a = biggest_ball(torch_model, window, CROP)
        b = biggest_ball(coreml_model, window, CROP)

        left = f"{a[0]:7.2f}px c{a[1]:.2f}" if a else "not found"
        right = f"{b[0]:7.2f}px c{b[1]:.2f}" if b else "not found"
        if a and b:
            change = 100 * (b[0] / a[0] - 1)
            worst = max(worst, abs(change))
            delta = f"{change:+8.2f}%"
        else:
            delta = "--"
        print(f"{frame_number:7d} {left:>18} {right:>18} {delta:>9}")

    capture.release()
    print()
    print(f"Worst diameter difference: {worst:.2f}%")
    print()
    print("Measured on 2026-08-24 this was 0.00% on every frame, so the")
    print("conversion preserves the boxes exactly.")
    print()
    print("This has since been confirmed on the device as well, so the")
    print("caveat that used to sit here is discharged. An iPhone 17 Pro")
    print("reproduces these diameters to two decimals, and box coordinates")
    print("are identical across CPU, GPU and .all.")
    print()
    print("The Neural Engine turned out not to be involved: the export is")
    print("Float32, the ANE requires float16, and not one of the model's")
    print("242 compute operations lists it as a supported device. The GPU")
    print("runs it at 5.68 ms per 640 px inference. Staying on Float32 is")
    print("a recorded decision -- see project_notes.md punch list item 1.1.")


def run_sizes(args) -> None:
    """Reproduce the measurement that chose the on-device architecture.

    Full frame downscaled to various sizes, against a 640 crop at native
    resolution. Kept as code rather than only as a table in the docstring:
    the conclusion decided what gets ported, and it should be re-checkable
    on new footage and on a different model.
    """
    import cv2
    from ultralytics import YOLO

    model = YOLO(args.model)
    capture = cv2.VideoCapture(str(args.clip))
    if not capture.isOpened():
        sys.exit(f"Could not open {args.clip}")

    cases = []
    for entry in args.cases.split(";"):
        frame, cx, cy, truth = entry.split(",")
        cases.append((int(frame), int(cx), int(cy), float(truth)))

    sizes = [int(s) for s in args.sizes.split(",")]
    header = "".join(f"{f'full@{s}':>18}" for s in sizes)
    print(f"{'frame':>6} {'truth':>8}{header}{'crop640@native':>18}")

    for frame_number, cx, cy, truth in cases:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, image = capture.read()
        if not ok:
            print(f"{frame_number:6d}   could not read")
            continue

        x0 = max(0, min(image.shape[1] - CROP, cx - CROP // 2))
        y0 = max(0, min(image.shape[0] - CROP, cy - CROP // 2))
        window = image[y0:y0 + CROP, x0:x0 + CROP]

        cells = []
        for image_in, size in [(image, s) for s in sizes] + [(window, CROP)]:
            found = biggest_ball(model, image_in, size)
            if found is None:
                cells.append(f"{'not found':>18}")
            else:
                cells.append(f"{found[0]:7.2f}px {100 * (found[0] / truth - 1):+5.1f}%"
                             f" c{found[1]:.2f}")
        print(f"{frame_number:6d} {truth:7.1f}px" + "".join(cells))

    capture.release()
    print()
    print("Measured 2026-08-24 on a 4K clip: the 640 crop matched full-frame")
    print("3840 while the model saw 1/36th the pixels. Full-frame 1280 lost")
    print("the ball mid-flight and read 33% high late -- the trap a naive")
    print("port would fall into, because it presents as bad physics.")


def run_dump(args) -> None:
    """Freeze the comparison inputs to disk, and baseline them from disk.

    Item 1.1 of the punch list asks whether the Neural Engine changes the
    boxes. Answering that means running the same model on the same pixels
    on a phone, and "the same pixels" is the hard part: if the Mac decodes
    the clip with OpenCV and the phone decodes it with AVFoundation, any
    difference in the answer is ambiguous between the runtime and the
    decoder. So the crops are written once, here, and both sides read the
    same files.

    The baseline below is deliberately measured by handing the model a
    PNG *path* rather than the in-memory crop. Reading back what was
    written is what proves the file is the input, not a lossy copy of it.

    Colour order is the trap worth naming. OpenCV works in BGR and
    cv2.imwrite expects BGR, so the PNG on disk has correct colour;
    cv2.imread gives BGR back and ultralytics expects that. On the phone
    the same PNG loads as RGB and Core ML's image input wants RGB. Both
    sides are therefore correct without either converting -- but only
    because the file sits in the middle. Feeding Swift a raw BGR buffer
    would swap red and blue and quietly change every box.
    """
    import cv2
    from ultralytics import YOLO

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(args.clip))
    if not capture.isOpened():
        sys.exit(f"Could not open {args.clip}")

    cases = []
    for entry in args.cases.split(";"):
        frame, cx, cy, truth = entry.split(",")
        cases.append((int(frame), int(cx), int(cy), float(truth)))

    torch_model = YOLO(args.model)
    coreml_model = YOLO(args.coreml)

    print(f"Writing {CROP}x{CROP} native-resolution crops to {out}/")
    print()
    print(f"{'file':>28} {'truth':>9} {'pytorch':>18} {'coreml(cpu/gpu)':>18}")

    written = 0
    for frame_number, cx, cy, truth in cases:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        ok, image = capture.read()
        if not ok:
            print(f"{'f' + str(frame_number):>28}   could not read")
            continue

        x0 = max(0, min(image.shape[1] - CROP, cx - CROP // 2))
        y0 = max(0, min(image.shape[0] - CROP, cy - CROP // 2))
        window = image[y0:y0 + CROP, x0:x0 + CROP]

        name = f"crop-f{frame_number:05d}-x{x0}-y{y0}.png"
        path = out / name
        if not cv2.imwrite(str(path), window):
            sys.exit(f"Could not write {path}")
        written += 1

        # Read it back from disk. The file is the experiment's input, so
        # the baseline has to come from the file.
        a = biggest_ball(torch_model, str(path), CROP)
        b = biggest_ball(coreml_model, str(path), CROP)
        left = f"{a[0]:7.2f}px c{a[1]:.2f}" if a else "not found"
        right = f"{b[0]:7.2f}px c{b[1]:.2f}" if b else "not found"
        print(f"{name:>28} {truth:8.1f}px {left:>18} {right:>18}")

    capture.release()
    print()
    print(f"Wrote {written} crops.")
    print()
    print("The crop origin is in each filename because the diameter is the")
    print("only number being compared and it is crop-relative -- but the")
    print("centre is not, and 4.1 will need to map a crop box back to the")
    print("full frame. Recording it now costs nothing and saves guessing.")
    print()
    print("These PNGs are the frozen input for punch list item 1.1, which")
    print("is COMPLETE -- there is nothing further to run here. They are")
    print("kept because they are the fixed reference the device was")
    print("checked against, and regenerating them is how you would re-check")
    print("it after any change to the export.")
    print()
    print("What 1.1 found, on an iPhone 17 Pro: the device reproduces the")
    print("pytorch column above to two decimals, box coordinates are")
    print("identical across every compute unit, and the Neural Engine is")
    print("unreachable because this export is Float32. See project_notes.md.")
    print()
    print("One caveat if you compare a device run against this table by")
    print("hand. Ultralytics applies NMS before picking a box; a raw Core")
    print("ML decoder has none, so 'largest candidate' over raw anchors")
    print("selects the largest DUPLICATE and reads 0.5-1.4% high. Compare")
    print("against the most-confident box, or apply NMS first.")


def run_blur(args) -> None:
    """How the detector's box responds to motion blur, in isolation.

    THE QUESTION THIS SETTLES

    1080p/240 and 4K/120 trade off against each other and the trade is
    structural. Measured synthetically (project_notes.md item 2.1, rung 10):
    4K/120 wins on random precision by about 1.4x, because it puts twice as
    many pixels across the ball; 1080p/240 wins on blur-induced bias by
    about 4x, because the ball moves 14.4 px per frame there against 57.4
    at 4K/120 -- fx is doubled AND the frame interval is doubled.

    Which advantage dominates depends on ONE number nobody has measured:
    how severely blur degrades this detector's bounding box. That is what
    this measures.

    WHY SYNTHETIC BLUR ON A STILL FRAME, RATHER THAN REAL FOOTAGE

    In a real flight the ball recedes and blurs at the same time, and both
    shrink the box. The two effects are hopelessly confounded -- which is
    exactly why the diameter bias has resisted diagnosis for so long. Here
    the ball is at rest at a known 9.14 m with a known true diameter of
    58.28 px, and the ONLY thing that changes is the blur. Whatever the box
    does is the blur doing it.

    Blur is applied as a horizontal box filter, which is what a linear
    motion across the sensor during an exposure actually produces.

    WHAT MATTERS IS BLUR RELATIVE TO THE BALL, AND fx CANCELS OUT

        blur_px  = (fx * v / Z) * exposure
        ball_px  =  fx * D / Z
        ratio    =  v * exposure / D          <- no fx

    So a format's focal length does NOT affect how blurred the ball looks
    relative to its own size. Only the exposure does. At 30 m/s with a
    Size 4 ball:

        exposure           4K/120   1080p/240
        1/1000 s bright      15%        15%      <- identical
        1/500 s              29%        29%      <- identical
        frame-limited       121%        61%      <- 240 fps wins

    This corrects an earlier claim that 1080p/240 has a structural ~2x
    blur advantage. It has that advantage ONLY when exposure is capped by
    the frame interval, which means only in poor light. In bright sun both
    formats blur the ball equally in relative terms, and 4K's extra pixels
    win on precision with nothing to offset them.

    Which makes the light the deciding variable, not the format -- and it
    fits the one real observation on record: first footage in bright sun
    at ~13 m/s showed panel detail legible on a ~70 px ball, meaning the
    exposure was far shorter than the frame interval.
    """
    import cv2
    import numpy as np
    from ultralytics import YOLO

    source = Path(args.crop)
    if not source.exists():
        sys.exit(f"{source} not found. Run `dump` first.")

    image = cv2.imread(str(source))
    if image is None:
        sys.exit(f"Could not read {source}")

    model = YOLO(args.model)

    print(f"Blur response of {args.model} on {source.name}")
    print(f"True diameter {args.truth:.2f} px, from a ball at rest.")
    print()
    print("Blur is a horizontal box filter, the shape a linear motion")
    print("across the sensor during one exposure actually produces.")
    print()
    print(f"{'blur px':>9}{'diameter':>11}{'error':>10}{'confidence':>12}"
          f"{'implied range':>15}")

    ball_m = args.ball_mm / 1000.0
    lengths = [int(v) for v in args.lengths.split(",")]
    for length in lengths:
        if length <= 1:
            blurred = image
        else:
            kernel = np.zeros((length, length), dtype=np.float32)
            kernel[length // 2, :] = 1.0 / length
            blurred = cv2.filter2D(image, -1, kernel)

        found = biggest_ball(model, blurred, CROP)
        if found is None:
            print(f"{length:9d}{'NOT FOUND':>11}{'--':>10}{'--':>12}{'--':>15}")
            continue

        diameter, confidence = found
        error = 100 * (diameter / args.truth - 1)
        implied = args.fx * ball_m / diameter
        print(f"{length:9d}{diameter:10.2f}px{error:+9.1f}%{confidence:12.2f}"
              f"{implied:14.2f}m")

    print()
    print(f"For reference, the ball was actually at {args.distance:.2f} m.")
    print()
    print("HOW TO READ THIS")
    print()
    print("  A box that SHRINKS with blur under-reads diameter, which")
    print("  over-estimates range, which is the sign of the bias believed")
    print("  to drive the gravity discrepancy. A box that GROWS would mean")
    print("  the opposite and would refute it.")
    print()
    print("  Then convert to a format verdict. At 30 m/s and 9.14 m, blur")
    print("  on THIS 4K crop, where the ball is 56.8 px, is roughly:")
    print("      1/1000 s, bright sun      8 px")
    print("      1/500 s, overcast        17 px")
    print("      1/120 s, frame-limited   69 px")
    print()
    print("  Relative blur is v*exposure/D and fx cancels, so 1080p/240")
    print("  does NOT blur less in bright light -- both formats see the")
    print("  same fraction of the ball smeared. 240 fps only helps when")
    print("  exposure is capped by the frame interval, i.e. in poor light,")
    print("  where it halves the exposure and so halves the blur.")
    print()
    print("  So: if the error stays small out to ~8-17 px, blur is not a")
    print("  problem in daylight and 4K/120 wins on pixels alone. If it")
    print("  degrades sharply in that range, the format choice becomes a")
    print("  light-level decision rather than a fixed one.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the detector to Core ML and verify it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Input size is")[0],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    export = sub.add_parser("export", help="convert the weights to Core ML")
    export.add_argument("--model", default=DEFAULT_MODEL)
    export.add_argument("--imgsz", type=int, default=CROP,
                        help=f"model input size (default {CROP}, which is "
                             "the crop size the tracker should use)")
    export.set_defaults(func=run_export)

    compare = sub.add_parser("compare",
                             help="check the export against the weights")
    compare.add_argument("clip", type=Path)
    compare.add_argument("--model", default=DEFAULT_MODEL)
    compare.add_argument("--coreml", default=DEFAULT_COREML)
    compare.add_argument("--frames", default="620,660,700,740",
                         help="comma-separated frame numbers")
    compare.add_argument("--at", default=None,
                         help="cx,cy to centre the crop on; defaults to the "
                              "frame centre")
    compare.set_defaults(func=run_compare)

    sizes = sub.add_parser("sizes",
                           help="crop vs full-frame at various input sizes")
    sizes.add_argument("clip", type=Path)
    sizes.add_argument("--model", default=DEFAULT_MODEL)
    sizes.add_argument("--sizes", default="1280,3840",
                       help="full-frame input sizes to compare")
    sizes.add_argument("--cases",
                       default="620,3178,1618,57.2;660,2985,1525,52.4;"
                               "700,2271,1309,37.7;740,1855,1341,30.4",
                       help="semicolon-separated frame,cx,cy,true_diameter; "
                            "defaults are kick 11 of the 2026-08-22 session")
    sizes.set_defaults(func=run_sizes)

    dump = sub.add_parser("dump",
                          help="freeze the 640 crops to PNG for the device")
    dump.add_argument("clip", type=Path)
    dump.add_argument("--model", default=DEFAULT_MODEL)
    dump.add_argument("--coreml", default=DEFAULT_COREML)
    dump.add_argument("--out", default="tools/frames/ane-inputs",
                      help="directory to write the crops into")
    dump.add_argument("--cases",
                      default="620,3178,1618,57.2;660,2985,1525,52.4;"
                              "700,2271,1309,37.7;740,1855,1341,30.4",
                      help="semicolon-separated frame,cx,cy,true_diameter; "
                           "defaults are kick 11 of the 2026-08-22 session, "
                           "the same four frames the crop architecture was "
                           "measured on")
    dump.set_defaults(func=run_dump)

    blur = sub.add_parser("blur",
                          help="how the detector's box responds to motion blur")
    blur.add_argument("--crop",
                      default="tools/frames/ane-inputs/"
                              "crop-f00620-x2858-y1298.png",
                      help="a crop of the ball AT REST; the resting frame is "
                           "the only one whose true diameter is known")
    blur.add_argument("--model", default=DEFAULT_MODEL)
    blur.add_argument("--truth", type=float, default=58.28,
                      help="true diameter in px for that crop (default "
                           "58.28, measured 2026-08-24)")
    blur.add_argument("--lengths", default="1,4,8,12,17,25,35,50,69",
                      help="blur lengths in px, on a 56.8 px ball. The "
                           "defaults bracket real exposures at 30 m/s: 8 px "
                           "is bright sun at 1/1000 s, 17 px is overcast at "
                           "1/500 s, 69 px is frame-limited at 1/120 s")
    blur.add_argument("--ball-mm", type=float, default=206.1)
    blur.add_argument("--fx", type=float, default=2520.0)
    blur.add_argument("--distance", type=float, default=9.14)
    blur.set_defaults(func=run_blur)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
