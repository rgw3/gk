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

  focal   Solves fx = d*Z/D from a stationary ball at a TAPE-MEASURED
          distance. Punch list item 2.2. The 4K focal length is confirmed
          exactly; the 1080p one reads 5.1% high and nobody knows whether
          that is the lens or a paced distance being 5% out. Run it on both
          calibration clips: the RATIO of the two answers is independent of
          the ball's true size and of the tape, so it settles the question
          even if neither absolute figure is perfect.
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


def run_focal(args) -> None:
    """Solve for focal length from a ball of known size at a measured range.

    PUNCH LIST ITEM 2.2. What this settles and why it matters.

    Every distance this project computes comes from fx, and fx comes from
    AVCaptureDevice.Format.videoFieldOfView -- a nominal figure, not a
    measured one. It can be recovered from footage instead, with no
    reference to what the camera claims:

        fx = d * Z / D

    for a ball of true diameter D at range Z measuring d pixels across.

    Measured on the 2026-08-22 clips, where the camera was PACED at 10
    yards, the 4K figure came back at 2519 against a claimed 2520 -- exact,
    and it settles the number most of the pipeline rests on. The 1080p
    figure came back at 1324 against a claimed 1260: 5.1% high, and
    unresolved. Two explanations fit and that data cannot separate them:

      - the camera was not actually at 10 yards for that clip. fx 1260
        would put it at 8.70 m, and a paced distance is easily 5% out.
      - the 1080p/240 format really is narrower than the 74.6 degrees it
        reports, in which case EVERY distance from a 1080p clip is 5%
        short.

    Only one clip can test it, so the sample size is one.

    WHY THE CALIBRATION SHOT SETTLES IT AND THE OLD DATA CANNOT

    The shot films one stationary ball, at a TAPE-MEASURED distance,
    without moving the phone between formats. That removes both unknowns
    at once:

      - the distance is measured rather than paced, so the first
        explanation is eliminated outright
      - the same ball at the same distance is used for both formats, so
        the RATIO of the two focal lengths is independent of both the
        ball's true diameter and the distance. Even if the ball is not
        206.1 mm and the tape is off, fx_4K / fx_1080p is still right.

    That second point is why the ball is not measured: a Size 4 ball is
    legal from 202.1 to 210.1 mm, which is +-1.9% on the absolute fx
    values, but it cancels exactly from the comparison. If the ratio is
    2.0 the two formats share a lens and the 1080p claim of 1260 is right;
    if it is nearer 1.9 the 1080p format is genuinely narrower.

    A resting ball is also the best measurement available anywhere in this
    project: sharp, unblurred, at high confidence, and averaged over
    hundreds of frames rather than estimated from a few.
    """
    track = read_track(Path(args.track))
    if not track:
        sys.exit(f"No detections in {args.track}. Run detect_ball.py first.")

    frames = sorted(track)
    if args.first is not None:
        frames = [f for f in frames if f >= args.first]
    if args.last is not None:
        frames = [f for f in frames if f <= args.last]
    if len(frames) < 10:
        sys.exit(f"Only {len(frames)} usable frames; need at least 10.")

    diameters = np.array([track[f]["diameter"] for f in frames])

    # The ball is supposed to be stationary. If it is not -- someone
    # nudged it, or the detector wandered onto something else -- the
    # spread says so, and a calibration built on that would be wrong in a
    # way nothing downstream could detect.
    spread = float(diameters.std())
    mean = float(diameters.mean())
    relative = 100 * spread / mean

    ball_m = args.ball_mm / 1000.0
    fx = mean * args.distance / ball_m
    fov = 2 * math.degrees(math.atan(args.width / (2 * fx)))

    print()
    print(f"FOCAL LENGTH from {Path(args.track).name}")
    print(f"  {len(frames)} frames, ball at a measured {args.distance:.3f} m")
    print()
    print(f"  Diameter            {mean:.2f} px  "
          f"(sd {spread:.2f}, {relative:.2f}%)")
    print(f"  Implied fx          {fx:.1f} px")
    print(f"  Implied field of view {fov:.2f} degrees")

    if args.claimed:
        error = 100 * (fx / args.claimed - 1)
        print(f"  Claimed fx          {args.claimed:.1f} px  "
              f"-- measured is {error:+.2f}% from it")

    print()
    if relative > 2.0:
        print(f"  WARNING: diameter varies by {relative:.1f}% across these")
        print("  frames. A ball at rest should be steady to a fraction of a")
        print("  percent. Something moved, or the detector is not on the")
        print("  ball. Do not calibrate from this.")
    else:
        print("  Diameter is steady, so the ball was genuinely at rest and")
        print("  this average is worth trusting.")

    print()
    print("  Run this on BOTH calibration clips, then compare. The ratio of")
    print("  the two focal lengths is independent of the ball's true size")
    print("  and of the tape measure, because the same ball sat at the same")
    print("  distance for both:")
    print()
    print("     ratio 2.00   the two formats share a lens, 1260 is right,")
    print("                  and the 5.1% seen on the 2026-08-22 clip was a")
    print("                  sloppy pace")
    print("     ratio ~1.90  the 1080p/240 format is genuinely narrower, and")
    print("                  every distance ever computed from a 1080p clip")
    print("                  is about 5% short")


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

    focal = sub.add_parser("focal",
                           help="solve fx from a ball at a measured distance")
    focal.add_argument("track", type=Path,
                       help="track CSV from a CALIBRATION clip -- a "
                            "stationary ball, not a kick")
    focal.add_argument("--distance", type=float, required=True,
                       help="TAPE-MEASURED metres from camera to ball. Not "
                            "paced; pacing is what left the question open")
    focal.add_argument("--ball-mm", type=float, default=BALL_M * 1000,
                       help="ball diameter in mm (default 206.1, a Size 4). "
                            "Affects the absolute fx but cancels from the "
                            "ratio between the two formats")
    focal.add_argument("--width", type=int, default=3840,
                       help="frame width, used only to report field of view")
    focal.add_argument("--claimed", type=float, default=None,
                       help="the fx the camera implies, for comparison: "
                            "2520 at 4K, 1260 at 1080p")
    focal.add_argument("--first", type=int, default=None,
                       help="ignore frames before this")
    focal.add_argument("--last", type=int, default=None,
                       help="ignore frames after this")
    focal.set_defaults(func=run_focal)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
