#!/usr/bin/env python3
"""Check the pipeline against ground truth, rather than against itself.

    ./tools/.venv/bin/python tools/validate.py carry
    ./tools/.venv/bin/python tools/validate.py height
    ./tools/.venv/bin/python tools/validate.py tilt CSV

Reads tools/sessions/*.csv for the kick-to-file mapping and the paced
landing distances. Run detect_ball.py first so the tracks exist.

Every one of these started as a throwaway script during the 2026-08-24
debugging session, and each produced a conclusion now recorded in
project_notes.md. They live here because a conclusion whose measuring
instrument has been thrown away cannot be re-checked, extended to new
footage, or disproved -- and the central open problem is a 6% measurement
bias, so the instruments matter.

  carry   Observed track displacement against the paced landing. This is the
          validation: it separates a reconstruction error from a flight-model
          error, because the observed track does not care what the flight
          model thinks. Only meaningful on clips whose track reaches the
          ground.

  height  Camera height from the ball resting on the ground and again at
          landing. Needs neither focal length nor principal point, so it is
          an independent check on the vertical scale. Reading 1.10 m against
          a phone held at about 1.4 m is what located the diameter bias.

  tilt    Sweeps the assumed principal point and reports fitted gravity.
          Kept as a NEGATIVE result: gravity is invariant to it, necessarily,
          because a cy0 error contributes cy0*Z/fx and Z is linear in time,
          so it can only add a linear term. Repeat this before anyone
          proposes camera tilt as an explanation again.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

BALL_M = 0.2061
YARD_M = 0.9144
TRACKS = Path("tools/frames")
SESSIONS = Path("tools/sessions")


def load_session(name: str) -> list[dict]:
    path = SESSIONS / f"{name}.csv"
    if not path.exists():
        sys.exit(f"{path} not found. Sessions: "
                 + ", ".join(p.stem for p in SESSIONS.glob("*.csv")))
    with open(path) as handle:
        rows = [r for r in csv.DictReader(
            line for line in handle if not line.startswith("#"))]
    for row in rows:
        row["kick"] = int(row["kick"])
        row["paced_m"] = float(row["paced_yards"]) * YARD_M
        row["camera_m"] = float(row["camera_m"])
        row["landing"] = row["landing"].strip().lower() == "yes"
        row["wide"] = "1080p240" not in row["file"]
        row["fx"] = 2520.0 if row["wide"] else 1260.0
        row["width"] = 3840 if row["wide"] else 1920
        row["track"] = TRACKS / (Path(row["file"]).stem + "-track.csv")
    return rows


def read_track(path: Path) -> dict[int, dict]:
    """Detected frames only, keyed by frame number."""
    found = {}
    if not path.exists():
        return found
    with open(path) as handle:
        for row in csv.DictReader(handle):
            if row["detected"] != "1":
                continue
            found[int(row["frame"])] = {
                "cx": float(row["cx"]), "cy": float(row["cy"]),
                "diameter": float(row["diameter"]),
            }
    return found


def flight_window(row: dict) -> tuple[int, int] | None:
    """Ask compute_metrics.py which frames it fitted, so we agree with it."""
    import re
    import subprocess

    result = subprocess.run(
        [sys.executable, "tools/compute_metrics.py", str(row["track"]),
         "--width", str(row["width"]),
         "--height", str(2160 if row["wide"] else 1080),
         "--ball-size", "4"],
        capture_output=True, text=True)
    found = re.search(r"frames, f(\d+) to f(\d+)", result.stdout)
    return (int(found.group(1)), int(found.group(2))) if found else None


def run_carry(args) -> None:
    """Observed displacement against the paced landing."""
    rows = load_session(args.session)
    print("Observed track displacement against the paced landing.")
    print("Only clips whose track reaches the ground can be checked; on the")
    print("rest the ball leaves frame mid-flight and the observed figure is")
    print("part of a trajectory, not all of it.")
    print()
    print(f"{'kick':>4} {'window':>14} {'observed':>10} {'paced':>8} {'error':>8}")

    errors = []
    for row in rows:
        if not row["landing"]:
            continue
        samples = read_track(row["track"])
        if not samples:
            print(f"{row['kick']:4d}   no track -- run detect_ball.py first")
            continue
        window = flight_window(row)
        if window is None:
            print(f"{row['kick']:4d}   compute_metrics found no flight")
            continue

        first, last = window
        if first not in samples or last not in samples:
            print(f"{row['kick']:4d}   window frames missing from the track")
            continue

        fx, half = row["fx"], row["width"] / 2
        ends = []
        for frame in (first, last):
            sample = samples[frame]
            z = fx * BALL_M / sample["diameter"]
            ends.append(((sample["cx"] - half) * z / fx, z))
        (xa, za), (xb, zb) = ends
        observed = math.hypot(xb - xa, zb - za)
        error = 100 * (observed / row["paced_m"] - 1)
        errors.append(error)
        print(f"{row['kick']:4d} {f'f{first}-f{last}':>14} {observed:9.2f}m "
              f"{row['paced_m']:7.2f}m {error:+7.1f}%")

    if errors:
        print()
        print(f"{len(errors)} clips, mean error {np.mean(errors):+.1f}%, "
              f"worst {max(errors, key=abs):+.1f}%")
        print()
        print("Measured 2026-08-24 this was -3% to -10%, which validates the")
        print("reconstruction: focal length, ball diameter as scale, per-frame")
        print("depth and 3D geometry, all against a distance measured on the")
        print("pitch. Computed carry from the flight model runs further short,")
        print("and that gap is a model problem, not a measurement one.")


def run_height(args) -> None:
    """Camera height, independent of focal length and principal point.

    A ball resting on the ground at range Z appears at cy = cy0 + h*fx/Z.
    Take it at rest and again at landing and both fx and cy0 cancel:

        h = D * (cy_rest - cy_land) / (d_rest - d_land)
    """
    rows = load_session(args.session)
    print("Camera height from two frames with the ball on the ground.")
    print("Independent of focal length and principal point, so it is a")
    print("check on the vertical scale that shares nothing with the fit.")
    print()
    print(f"{'kick':>4} {'rest':>22} {'landing':>22} {'height':>8}")

    heights = []
    for row in rows:
        if not row["landing"]:
            continue
        samples = read_track(row["track"])
        window = flight_window(row) if samples else None
        if not samples or window is None:
            print(f"{row['kick']:4d}   no usable track")
            continue

        first, last = window
        # A rest frame safely before contact, and the landing frame itself.
        rest_frames = [f for f in samples if f < first - args.rest_margin]
        if not rest_frames or last not in samples:
            print(f"{row['kick']:4d}   no frames before contact")
            continue
        rest = samples[max(rest_frames)]
        land = samples[last]

        spread = rest["diameter"] - land["diameter"]
        if spread <= 0:
            print(f"{row['kick']:4d}   ball did not recede; cannot solve")
            continue
        height = BALL_M * (rest["cy"] - land["cy"]) / spread
        heights.append(height)
        print(f"{row['kick']:4d} "
              f"cy={rest['cy']:7.0f} d={rest['diameter']:5.1f} "
              f"cy={land['cy']:7.0f} d={land['diameter']:5.1f} "
              f"{height:7.2f}m")

    if heights:
        print()
        print(f"mean {np.mean(heights):.2f} m across {len(heights)} clips")
        print()
        print("The phone was held at roughly 1.4 m. Measured 2026-08-24 this")
        print("read 1.10 m -- about 21% low, matching the gravity shortfall,")
        print("which is what located the bias in the flight diameters.")


def run_tilt(args) -> None:
    """Sweep the assumed principal point. Gravity should not move."""
    samples = read_track(args.track)
    if not samples:
        sys.exit(f"No detections in {args.track}")

    frames = sorted(f for f in samples if args.first <= f <= args.last)
    if len(frames) < 8:
        sys.exit(f"Only {len(frames)} frames in f{args.first}-f{args.last}")

    fx = args.fx
    t = np.array([(f - frames[0]) / args.fps for f in frames])
    cy = np.array([samples[f]["cy"] for f in frames])
    diameter = np.array([samples[f]["diameter"] for f in frames])

    raw_range = fx * BALL_M / diameter
    slope, intercept = np.polyfit(t, raw_range, 1)
    z = slope * t + intercept

    print(f"Sweeping the assumed principal point over f{frames[0]}-f{frames[-1]}.")
    print()
    print(f"{'cy0 (px)':>9} {'tilt':>8} {'gravity':>9} {'vy':>7} {'rise':>7}")
    for cy0 in range(args.centre, args.centre + 960, 60):
        y = -(cy - cy0) * z / fx
        quadratic, vy, _ = np.polyfit(t, y, 2)
        tilt = math.degrees(math.atan((cy0 - args.centre) / fx))
        print(f"{cy0:9d} {tilt:7.1f}d {-2 * quadratic:9.2f} {vy:7.2f} "
              f"{y.max() - y[0]:6.2f}m")

    print()
    print("Gravity does not move, and cannot. Y = -(cy - cy0)*Z/fx, so a cy0")
    print("error contributes cy0*Z/fx, and Z is linear in time -- it can only")
    print("add a linear term, never touch the quadratic. Camera tilt is not")
    print("an explanation for the gravity shortfall. It does shift vy and the")
    print("apparent rise, so it still matters for launch angle.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check the pipeline against ground truth.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    carry = sub.add_parser("carry", help="observed displacement vs paced")
    carry.add_argument("--session", default="2026-08-22")
    carry.set_defaults(func=run_carry)

    height = sub.add_parser("height", help="camera height, fx-independent")
    height.add_argument("--session", default="2026-08-22")
    height.add_argument("--rest-margin", type=int, default=40,
                        help="frames before contact to stay clear of "
                             "(default 40)")
    height.set_defaults(func=run_height)

    tilt = sub.add_parser("tilt", help="principal point sweep (negative result)")
    tilt.add_argument("track", type=Path)
    tilt.add_argument("--first", type=int, required=True)
    tilt.add_argument("--last", type=int, required=True)
    tilt.add_argument("--fx", type=float, default=2520.0)
    tilt.add_argument("--centre", type=int, default=1080,
                      help="image centre row (default 1080, for 4K)")
    tilt.add_argument("--fps", type=float, default=119.95)
    tilt.set_defaults(func=run_tilt)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
