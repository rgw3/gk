#!/usr/bin/env python3
"""Find the ball in every frame, using a pre-trained detector.

This is Step 3 from project_notes.md: produce a per-frame table of ball centre
and apparent diameter in pixels. Nothing here computes velocity or angle --
that is Step 4, and it is arithmetic once this table is trustworthy.

Why a pre-trained model rather than a colour threshold: the ball will not
always be teal. COCO, the dataset behind every off-the-shelf detector, has a
"sports ball" class, so a stock model finds footballs of any colour with no
training data and no labelling. Training a custom model on the first ten clips
would overfit to one ball at one range -- the same brittleness as a colour
threshold, wearing a different hat.

Diameter comes from the detector's bounding box. An earlier version refined it
by fitting a circle with cv2.HoughCircles; measured against real footage that
made it worse, not better -- the fit locked onto a ring larger than the ball
and inflated diameter by about 45%, while the raw box held steady to within a
few pixels. The refinement is gone. A useful side effect is that nothing here
now depends on an OpenCV routine with no Apple equivalent, so the method
ports to Vision on iOS.

The detector alone is not enough. Once the ball enters a net or leaves frame,
a stock model will happily report the next roundest object -- on the first
footage, a yellow training cone -- at a confidence high enough that no
threshold catches it. Continuity gating is what rejects that: a ball cannot
teleport, and it cannot change size abruptly.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

try:
    import cv2
except ImportError:
    sys.exit("OpenCV is missing. See tools/requirements.txt.")

# The frame walking and clip description already exist next door. Running this
# as `python3 tools/detect_ball.py` puts tools/ on the import path.
from extract_frames import describe, frames, open_clip, print_description

# COCO class 32. The stock model knows 80 classes and we want exactly one --
# without this filter it will report the kicker as a person and the parked car
# as a car.
SPORTS_BALL_CLASS = 32


def load_model(name: str, device: str | None):
    """Load a pre-trained YOLO model, fetching the weights on first run."""
    try:
        from ultralytics import YOLO
    except ImportError:
        sys.exit(
            "ultralytics is not installed.\n"
            "  pip install -r tools/requirements.txt"
        )

    if device is None:
        # Apple Silicon exposes its GPU to PyTorch as "mps". Falling back to
        # CPU works but is several times slower over a thousand frames.
        try:
            import torch
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        except Exception:
            device = "cpu"

    print(f"Loading {name} on {device}...")
    return YOLO(name), device


def detect_candidates(model, image, device: str, imgsz: int, confidence: float):
    """Every sports-ball box in one frame, best confidence first.

    All candidates are returned rather than just the best, because the most
    confident detection is not always the ball -- when the ball is half hidden
    in a net, a cone in clear view can outscore it. The gating below picks by
    plausibility, not by confidence alone.
    """
    results = model.predict(
        image,
        imgsz=imgsz,
        conf=confidence,
        classes=[SPORTS_BALL_CLASS],
        device=device,
        verbose=False,
    )

    candidates = []
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            width, height = x2 - x1, y2 - y1
            candidates.append({
                "cx": (x1 + x2) / 2,
                "cy": (y1 + y2) / 2,
                # Mean of the two sides: a sphere's box should be square, and
                # averaging halves the effect of one side being clipped.
                "diameter": (width + height) / 2,
                "confidence": float(box.conf[0]),
            })

    return sorted(candidates, key=lambda c: -c["confidence"])


class Stabiliser:
    """Cancel camera shake by registering each frame against the background.

    Coaches hold the phone; they do not carry tripods. Over a ~0.15 s
    measurement window a steady hand drifts only a few pixels, but the ball's
    whole vertical travel is only a couple of hundred, so uncorrected drift
    leaks straight into launch angle. Worse, it leaks unevenly, and the
    parabola fit downstream absorbs some of it into its quadratic term --
    which is to say, into apparent gravity.

    The method: pick trackable corners, follow them with optical flow, and
    solve for the rigid transform that best explains where they went. The
    background dominates the frame, so RANSAC treats the kicker and the ball
    as the outliers they are.

    Hardware video stabilisation is deliberately off at capture because it
    applies a non-rigid warp that corrupts geometry. This is the rigid
    equivalent, applied afterwards, which does not.

    Apple's Vision framework offers the same operation through
    VNTranslationalImageRegistrationRequest and its homographic sibling, so
    this ports to the app.
    """

    # Chosen for a static-ish outdoor scene: enough corners on fences, trees
    # and roofs to survive a moving subject in the middle of frame.
    FEATURE_PARAMS = dict(maxCorners=600, qualityLevel=0.01,
                          minDistance=12, blockSize=7)
    FLOW_PARAMS = dict(winSize=(21, 21), maxLevel=3,
                       criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
                                 30, 0.01))

    def __init__(self, enabled: bool):
        self.enabled = enabled
        self.previous_grey = None
        self.previous_points = None
        # Maps current-frame coordinates into the first frame's coordinates.
        self.to_reference = np.eye(3, dtype=np.float64)
        self.failures = 0

    def _find_features(self, grey, exclude):
        mask = np.full(grey.shape, 255, dtype=np.uint8)
        if exclude is not None:
            cx, cy, radius = exclude
            # Keep the ball itself out of the background estimate; it is the
            # one thing in frame guaranteed not to be background.
            cv2.circle(mask, (int(cx), int(cy)), int(radius * 2.5), 0, -1)
        return cv2.goodFeaturesToTrack(grey, mask=mask, **self.FEATURE_PARAMS)

    def update(self, image, exclude=None):
        """Advance to this frame. Returns the transform into reference space."""
        if not self.enabled:
            return self.to_reference

        grey = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        if self.previous_grey is None:
            self.previous_grey = grey
            self.previous_points = self._find_features(grey, exclude)
            return self.to_reference

        moved = None
        if self.previous_points is not None and len(self.previous_points) >= 12:
            moved, status, _ = cv2.calcOpticalFlowPyrLK(
                self.previous_grey, grey, self.previous_points, None,
                **self.FLOW_PARAMS)

        if moved is not None:
            kept = status.ravel() == 1
            source = self.previous_points[kept]
            destination = moved[kept]

            if len(source) >= 12:
                # Partial affine: rotation, uniform scale and translation.
                # A full affine would let shear absorb real motion, and a
                # handheld phone does not shear the world.
                matrix, _ = cv2.estimateAffinePartial2D(
                    destination, source, method=cv2.RANSAC,
                    ransacReprojThreshold=3.0)
                if matrix is not None:
                    step = np.vstack([matrix, [0, 0, 1]])
                    self.to_reference = self.to_reference @ step
                else:
                    self.failures += 1
            else:
                self.failures += 1
        else:
            self.failures += 1

        self.previous_grey = grey
        # Re-seed features every frame: cheap at this resolution, and it stops
        # the tracked set thinning out as points drift off frame.
        self.previous_points = self._find_features(grey, exclude)

        return self.to_reference

    def to_reference_point(self, x: float, y: float) -> tuple[float, float]:
        if not self.enabled:
            return x, y
        point = self.to_reference @ np.array([x, y, 1.0])
        return float(point[0]), float(point[1])

    def drift(self, width: int, height: int) -> float:
        """How far the frame centre has moved, in pixels, since the start."""
        if not self.enabled:
            return 0.0
        cx, cy = self.to_reference_point(width / 2, height / 2)
        return math.hypot(cx - width / 2, cy - height / 2)


class Track:
    """Accepts or rejects detections by whether the ball could have moved there.

    Two independent checks, because they fail on different things:

      * Distance. A ball has a finite speed, so its position between adjacent
        frames is bounded. Where a previous step exists the expected position
        is extrapolated from it, which tightens the bound considerably during
        steady flight.

      * Size. Apparent diameter changes slowly, because range changes slowly.
        A candidate a third the size of the established ball is a different
        object however plausible its position.

    The first detection is the largest candidate, not the most confident.
    The ball being measured is the one the coach stood 10 yards from, so it
    is the nearest object in shot and therefore the biggest. Everything else
    a pitch offers -- the bag of spare balls on the touchline, the next age
    group's game two pitches over -- is further away and smaller.

    This is not a tie-breaker, it is the whole acquisition rule, and it was
    learned the hard way. Taking the detector's own ranking picked a ball
    25 m away in nine clips out of eleven, because a distant ball sitting
    still is crisper than a near one and scores higher for it. Worse, the
    size gate below then locked around that wrong ball, so the real one was
    rejected as the wrong size for the rest of the clip -- a track that
    looks immaculate and measures nothing.
    """

    def __init__(self, max_jump: float, diameter_tolerance: float):
        self.max_jump = max_jump
        self.diameter_tolerance = diameter_tolerance
        self.accepted: list[dict] = []

    @property
    def median_diameter(self) -> float | None:
        if not self.accepted:
            return None
        return float(np.median([a["diameter"] for a in self.accepted]))

    def _expected_position(self, frame: int) -> tuple[float, float] | None:
        """Where the ball should be, extrapolated from the last two fixes."""
        if len(self.accepted) < 2:
            if self.accepted:
                last = self.accepted[-1]
                return last["cx"], last["cy"]
            return None

        previous, last = self.accepted[-2], self.accepted[-1]
        span = last["frame"] - previous["frame"]
        if span <= 0:
            return last["cx"], last["cy"]

        vx = (last["cx"] - previous["cx"]) / span
        vy = (last["cy"] - previous["cy"]) / span
        ahead = frame - last["frame"]
        return last["cx"] + vx * ahead, last["cy"] + vy * ahead

    def consider(self, frame: int, candidates: list[dict]):
        """Return (accepted_candidate, status) for this frame."""
        if not candidates:
            return None, "no-detection"

        if not self.accepted:
            # Largest, not first. See the class docstring -- the detector's
            # ranking is by confidence, and confidence favours the distant
            # stationary ball over the near one we actually came to measure.
            chosen = max(candidates, key=lambda c: c["diameter"])
            chosen["frame"] = frame
            self.accepted.append(chosen)
            return chosen, "ok"

        expected = self._expected_position(frame)
        gap = frame - self.accepted[-1]["frame"]
        allowed = self.max_jump * max(1, gap)
        established = self.median_diameter

        rejection = "rejected-jump"
        for candidate in candidates:
            distance = math.hypot(candidate["cx"] - expected[0],
                                  candidate["cy"] - expected[1])
            if distance > allowed:
                continue

            ratio = candidate["diameter"] / established
            if ratio > self.diameter_tolerance or ratio < 1 / self.diameter_tolerance:
                rejection = "rejected-size"
                continue

            candidate["frame"] = frame
            self.accepted.append(candidate)
            return candidate, "ok"

        return None, rejection


def run(args) -> None:
    capture = open_clip(args.video, args.auto_rotate)
    info = describe(capture, args.video, args.auto_rotate)
    print_description(info)

    if args.imgsz is None:
        # Default to the clip's own width, so nothing is thrown away before
        # the detector ever sees it. Measured on one 4K clip, dropping the
        # downscale from 0.33x to 0.50x cut range scatter from 200 mm to
        # 118 mm and moved fitted gravity from 7.49 to 8.86 m/s^2 -- the
        # physics did not change, only how much of the ball the model got to
        # look at. YOLO wants a multiple of 32.
        args.imgsz = int(round(info["width"] / 32)) * 32
        print(f"Running the detector at {args.imgsz} px, the clip's own "
              "width — no downscale.")
        if args.imgsz > 2048:
            print("This is slow at 4K. Pass --imgsz 1920 for a quicker, "
                  "slightly coarser run.")
        print()
    elif info["width"] > args.imgsz:
        # Worth stating plainly, because it is the most common reason
        # small-ball detection fails, and because it silently degrades
        # diameter -- which is what every distance in the pipeline rests on.
        scale = args.imgsz / info["width"]
        print(
            f"NOTE: frames are {info['width']} px wide and the model sees "
            f"{args.imgsz} px, so the ball is scaled to {scale:.2f}x its "
            "size in the file. This costs diameter precision and therefore "
            "range. Omit --imgsz to run at full width."
        )
        print()

    model, device = load_model(args.model, args.device)
    track = Track(args.max_jump, args.diameter_tolerance)
    stabiliser = Stabiliser(args.stabilise)
    if args.stabilise:
        print("Stabilising against the background "
              "(coaches hold the phone; this removes the shake).")

    args.out.mkdir(parents=True, exist_ok=True)
    annotated_dir = args.out / "annotated"
    if args.annotate:
        annotated_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    examined = 0
    consecutive_misses = 0
    last_known = None
    max_drift = 0.0

    print(f"Scanning frames {args.start} to "
          f"{args.end if args.end is not None else 'end'}...")

    for index, timestamp, image in frames(capture, args.start, args.end):
        examined += 1

        # Register this frame against the background before looking for the
        # ball, so that gating and the CSV both work in a coordinate system
        # that does not move with the operator's hands.
        stabiliser.update(image, exclude=last_known)
        drift = stabiliser.drift(info["width"], info["height"])
        max_drift = max(max_drift, drift)

        candidates = detect_candidates(model, image, device,
                                       args.imgsz, args.confidence)
        for candidate in candidates:
            candidate["raw_cx"], candidate["raw_cy"] = candidate["cx"], candidate["cy"]
            candidate["cx"], candidate["cy"] = stabiliser.to_reference_point(
                candidate["cx"], candidate["cy"])

        chosen, status = track.consider(index, candidates)

        if chosen:
            last_known = (chosen["raw_cx"], chosen["raw_cy"], chosen["diameter"] / 2)

        rows.append({
            "frame": index,
            "time_s": f"{timestamp:.6f}",
            "detected": 1 if chosen else 0,
            "confidence": f"{chosen['confidence']:.4f}" if chosen else "",
            "cx": f"{chosen['cx']:.2f}" if chosen else "",
            "cy": f"{chosen['cy']:.2f}" if chosen else "",
            "raw_cx": f"{chosen['raw_cx']:.2f}" if chosen else "",
            "raw_cy": f"{chosen['raw_cy']:.2f}" if chosen else "",
            "diameter": f"{chosen['diameter']:.2f}" if chosen else "",
            "drift_px": f"{drift:.2f}",
            "status": status,
            "candidates": len(candidates),
        })

        if chosen:
            consecutive_misses = 0
        else:
            consecutive_misses += 1
            # Once the ball is genuinely gone -- into a net, out of frame --
            # there is nothing to re-acquire, and continuing only risks
            # picking the track back up on some other object.
            if track.accepted and consecutive_misses >= args.max_gap:
                print(f"Track ended at frame {index}: {args.max_gap} "
                      "consecutive frames without a plausible ball.")
                break

        if args.annotate and chosen and (index - args.start) % args.annotate_every == 0:
            canvas = image.copy()
            radius = int(chosen["diameter"] / 2)
            # Drawn at raw coordinates: this is where the ball sits in this
            # image. The stabilised position belongs to the reference frame,
            # not to the pixels on screen.
            cv2.circle(canvas, (int(chosen["raw_cx"]), int(chosen["raw_cy"])),
                       radius, (0, 255, 0), 2)
            cv2.putText(canvas,
                        f"f{index} conf {chosen['confidence']:.2f} "
                        f"d {chosen['diameter']:.1f}px  drift {drift:.1f}px",
                        (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        (0, 255, 0), 2, cv2.LINE_AA)
            cv2.imwrite(str(annotated_dir / f"{args.video.stem}-f{index:05d}.png"),
                        canvas)

    capture.release()

    destination = args.out / f"{args.video.stem}-track.csv"
    with destination.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    summarise(rows, examined, destination, info, args, max_drift, stabiliser)


def summarise(rows, examined, destination, info, args,
              max_drift, stabiliser) -> None:
    hits = [r for r in rows if r["detected"] == 1]

    print()
    print(f"Wrote {destination}")
    print(f"Frames examined   {examined}")
    print(f"Ball accepted in  {len(hits)}")

    if stabiliser.enabled:
        print(f"Camera drift      {max_drift:.1f} px peak "
              f"({stabiliser.failures} frames could not be registered)")
        if hits:
            # What matters is not total drift over the clip but drift across
            # the frames actually fitted, since only that biases the answer.
            span = [float(r["drift_px"]) for r in hits]
            print(f"                  {max(span) - min(span):.1f} px across "
                  "the tracked frames -- this is the part that would have "
                  "biased the fit")

    rejected = [r for r in rows if r["status"].startswith("rejected")]
    if rejected:
        jumps = sum(1 for r in rejected if r["status"] == "rejected-jump")
        sizes = sum(1 for r in rejected if r["status"] == "rejected-size")
        print(f"Rejected          {len(rejected)}  "
              f"({jumps} implausible move, {sizes} wrong size)")

    if not hits:
        print()
        print("No detections at all. Things to try, in order:")
        print("  --imgsz 1920       stop the model shrinking the ball")
        print("  --confidence 0.10  accept weaker detections")
        print("  --model yolo11s.pt the larger of the two shippable models")
        print()
        print("If yolo11s at imgsz 1920 and confidence 0.10 still finds "
              "nothing, that is a real result: a stock COCO detector cannot "
              "do this, and the fallback is a fine-tuned model trained on "
              "corrected detections from footage where it does work.")
        return

    diameters = [float(r["diameter"]) for r in hits]
    median_diameter = float(np.median(diameters))
    print(f"Diameter          median {median_diameter:.1f} px, "
          f"range {min(diameters):.1f} to {max(diameters):.1f}, "
          f"sd {np.std(diameters):.2f}")

    # The longest unbroken run matters more than the overall count: a table
    # with holes through the middle of the flight cannot yield a trajectory,
    # even if most frames detected something.
    longest = current = 0
    first_frame = last_frame = None
    run_start = None
    for row in rows:
        if row["detected"] == 1:
            run_start = row["frame"] if current == 0 else run_start
            current += 1
            if current > longest:
                longest = current
                first_frame, last_frame = run_start, row["frame"]
        else:
            current = 0

    print(f"Longest unbroken  {longest} frames "
          f"(f{first_frame} to f{last_frame}, "
          f"{longest / info['nominal_fps']:.3f} s)")

    # A first, very rough range estimate, purely as a sanity check on scale.
    focal_length = 1260.0 if info["width"] <= 1920 else 2520.0
    ball_metres = args.ball_mm / 1000.0
    if median_diameter > 0:
        distance = focal_length * ball_metres / median_diameter
        millimetres_per_pixel = 1000 * ball_metres / median_diameter
        print(f"Implied range     ~{distance:.1f} m "
              f"(fx {focal_length:.0f}, ball {args.ball_mm:.0f} mm)")
        print(f"Scale             {millimetres_per_pixel:.3f} mm per pixel")

    print()
    print("Check the annotated frames before trusting any of this. A tidy "
          "table can come from a detector that latched onto something round "
          "that is not the ball.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Per-frame ball centre and diameter, using a pre-trained detector.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python3 tools/detect_ball.py clip.mov --start 540 --end 620 --annotate\n"
        ),
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, default=Path("tools/frames"))
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)

    # Deliberately limited to the two smallest models. The app has to run this
    # on an iPhone or iPad, so whatever is proven here must export to Core ML
    # and fit on the Neural Engine. yolo11n is ~6 MB and yolo11s ~19 MB; the
    # larger variants would prove something that cannot ship.
    parser.add_argument("--model", default="yolo11n.pt",
                        choices=["yolo11n.pt", "yolo11s.pt"],
                        help="pre-trained weights (default yolo11n.pt); "
                             "restricted to what will run on-device")
    parser.add_argument("--imgsz", type=int, default=None,
                        help="size the model resizes frames to; defaults to "
                             "the clip's own width, which is the most "
                             "accurate and the slowest")
    parser.add_argument("--confidence", type=float, default=0.25,
                        help="minimum detection confidence (default 0.25)")
    parser.add_argument("--device", default=None,
                        help="mps, cpu or cuda; autodetected when omitted")

    parser.add_argument("--max-jump", type=float, default=150.0,
                        help="furthest the ball may move from its predicted "
                             "position, in pixels per frame (default 150)")
    parser.add_argument("--diameter-tolerance", type=float, default=1.6,
                        help="largest factor by which a candidate's diameter "
                             "may differ from the established ball (default 1.6)")
    # 30 rather than 10, because the ball is genuinely unfindable for a
    # moment as it comes off the boot: blurred, half behind the kicker's
    # leg, and accelerating hardest. Measured on a real kick at 4K/120 the
    # blackout ran twelve frames, and a limit of 10 ended the track inside
    # it -- discarding the entire flight to save a tenth of a second.
    parser.add_argument("--max-gap", type=int, default=30,
                        help="stop after this many consecutive frames with no "
                             "plausible ball (default 30)")

    parser.add_argument("--no-stabilise", dest="stabilise", action="store_false",
                        help="skip background registration; use this to see "
                             "how much the camera shake was actually costing")
    parser.set_defaults(stabilise=True)

    parser.add_argument("--ball-mm", type=float, default=206.1,
                        help="ball diameter in mm (default 206.1, a Size 4)")

    parser.add_argument("--annotate", action="store_true",
                        help="write frames with the detected ball drawn on")
    parser.add_argument("--annotate-every", type=int, default=1,
                        help="annotate every Nth frame (default every one)")

    parser.add_argument("--raw-orientation", dest="auto_rotate", action="store_false",
                        help="ignore the clip's rotation metadata")
    parser.set_defaults(auto_rotate=True)

    return parser


def main() -> None:
    run(build_parser().parse_args())


if __name__ == "__main__":
    main()
