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
"""
import argparse
import sys
from pathlib import Path

SPORTS_BALL = 32          # COCO class index
DEFAULT_MODEL = "yolo11n.pt"
CROP = 640


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
    print("conversion preserves the boxes exactly. Note what that does and")
    print("does not prove: ultralytics runs Core ML on the Mac's CPU or GPU,")
    print("not the Neural Engine. The ANE may use float16 and is the thing")
    print("that actually ships, so this has to be repeated on a device.")


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
    compare.add_argument("--coreml", default="yolo11n.mlpackage")
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

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
