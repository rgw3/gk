#!/usr/bin/env python3
"""Turn the per-frame ball table into goalkeeper metrics.

This is Step 4 from project_notes.md. It reads the CSV written by
detect_ball.py and produces velocity, launch angle, carry distance and max
height. It never opens the video: the CSV is the interface between detection
and physics, so the arithmetic can be re-run in a second without paying for
the model again.

**The reconstruction is three-dimensional, and it has to be.** An earlier
version assumed the ball moved in a flat plane at fixed range, converting
pixels to metres through one constant scale. Measured against real footage
that failed silently and badly: the ball was travelling ~15 degrees toward
the camera, its apparent size grew 19% across the flight, and the steadily
inflating scale cancelled gravity's curvature almost exactly. The fit
reported gravity as -0.16 m/s^2 -- a straight line through what should have
been a 48-pixel sag.

The fix uses data already in the table. Apparent diameter gives range, range
plus image position gives true 3D position, and the trajectory is then fitted
in three dimensions. Gravity becomes a genuine independent check again,
because no amount of camera angle can fake it.

Two flight models are computed and shown side by side, deliberately. Carry
distance and max height are not measured -- they are derived from launch
conditions -- so the model is not a refinement of those numbers, it *is*
those numbers.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

GRAVITY = 9.80665

# Mass by ball size, from the official ranges. Only the drag model uses these;
# the drag-free parabola is mass-independent, which is part of its appeal.
BALL_MASS_GRAMS = {3: 310.0, 4: 370.0, 5: 430.0}


def read_track(path: Path) -> list[dict]:
    """Load the detector's CSV, keeping only accepted detections."""
    if not path.exists():
        sys.exit(f"No such file: {path}")

    with path.open(newline="") as handle:
        rows = [r for r in csv.DictReader(handle) if r["detected"] == "1"]

    if len(rows) < 5:
        sys.exit(f"Only {len(rows)} detections in {path}; nothing to fit.")

    return [{
        "frame": int(r["frame"]),
        "t": float(r["time_s"]),
        "u": float(r["cx"]),
        "v": float(r["cy"]),
        "diameter": float(r["diameter"]),
    } for r in rows]


def find_contact(samples: list[dict], threshold_fraction: float,
                 sustain: int) -> int:
    """Index of the first sample where the ball is properly under way.

    Before the kick the ball sits still and its speed is near zero; after it,
    speed jumps by orders of magnitude.

    Motion has to be *sustained* to count. A single frame of movement is
    usually the detector's box twitching as the boot arrives and changes what
    the ball looks like -- on the first footage that produced a 3 px blip two
    frames before the real launch, which was enough to start the fit early
    and drag the boot-contact phase into it.
    """
    speeds = []
    for previous, current in zip(samples, samples[1:]):
        dt = current["t"] - previous["t"]
        distance = math.hypot(current["u"] - previous["u"],
                              current["v"] - previous["v"])
        speeds.append(distance / dt if dt > 0 else 0.0)

    if not speeds:
        return 0

    cutoff = max(speeds) * threshold_fraction
    for index in range(len(speeds) - sustain + 1):
        if all(speeds[index + k] >= cutoff for k in range(sustain)):
            # speeds[i] describes movement between sample i and i+1.
            return index + 1

    return 0


def find_landing(samples: list[dict], sustain: int) -> int | None:
    """Index of the frame where the ball first reaches the ground, or None.

    Free flight ends at the bounce. What follows is a different problem --
    a bounce, a roll, a ball being collected -- and fitting one parabola
    across that boundary is not a small error. On the 30-degree control kick
    of 2026-08-22 the fit ran through two bounces and the roll and reported
    gravity as 1.37 m/s^2 with a 222 mm vertical residual. Cut at the bounce,
    the same detections gave 9.66 m/s^2 and 3.2 mm. Nothing else changed.

    The landing is found in image space, not from physics. Vertical image
    position falls to the apex, climbs back as the ball descends, and then
    reverses when the ball bounces. That turning point is the ground, and
    finding it this way needs no scale, no focal length and no depth -- all
    of which are noisier than the pixel row the ball sits on.

    The reversal has to be sustained, for the same reason contact does: a
    single frame of the box twitching is noise, and truncating the flight on
    noise costs more than the frames it saves.
    """
    if len(samples) < sustain + 3:
        return None

    heights = [s["v"] for s in samples]
    apex = min(range(len(heights)), key=heights.__getitem__)
    if apex >= len(heights) - 1:
        return None

    # Image y grows downward, so the largest v is the lowest point on screen.
    lowest = max(range(apex + 1, len(heights)), key=heights.__getitem__)

    after = heights[lowest + 1:lowest + 1 + sustain]
    if len(after) < sustain:
        # The ball never came back up: it left the frame still descending, or
        # the track ended at the ground. Either way there is nothing to cut,
        # and guessing would throw away real flight.
        return None

    if all(height < heights[lowest] for height in after):
        return lowest
    return None


def reconstruct(samples: list[dict], ball_metres: float, fx: float,
                principal: tuple[float, float]):
    """Recover true 3D position per frame from image position and diameter.

    Range comes from the ball's apparent size: Z = fx * D / d. Image position
    then back-projects to X and Y at that range.

    Range is smoothed with a straight-line fit before use rather than taken
    per frame. Over a tenth of a second the ball's distance from the camera
    changes almost linearly, while measured diameter wobbles by a few percent
    frame to frame -- and because X and Y are both multiplied by Z, that
    wobble would otherwise be injected into every axis. Fitting the trend
    keeps the real depth change and discards the noise.

    Y is negated so that up is positive. This assumes the camera was roughly
    level; a tilted phone rotates the reconstructed axes, which is what the
    CoreMotion attitude correction in project_notes.md is eventually for.
    """
    t = np.array([s["t"] for s in samples])
    t = t - t[0]
    u = np.array([s["u"] for s in samples])
    v = np.array([s["v"] for s in samples])
    diameter = np.array([s["diameter"] for s in samples])

    raw_range = fx * ball_metres / diameter
    slope, intercept = np.polyfit(t, raw_range, 1)
    smoothed_range = slope * t + intercept

    x = (u - principal[0]) * smoothed_range / fx
    y = -(v - principal[1]) * smoothed_range / fx
    z = smoothed_range

    return t, x, y, z, raw_range, smoothed_range


def fit_launch(t, x, y, z):
    """Fit the flight in three dimensions.

    X and Z are linear in time -- no horizontal forces worth speaking of over
    a fifth of a second -- and Y is quadratic. Fitting rather than differencing
    adjacent frames uses every sample and is far less sensitive to any one of
    them.
    """
    vx, _ = np.polyfit(t, x, 1)
    vz, _ = np.polyfit(t, z, 1)

    quadratic, vy, _ = np.polyfit(t, y, 2)
    implied_gravity = -2 * quadratic

    speed = math.sqrt(vx * vx + vy * vy + vz * vz)
    horizontal = math.hypot(vx, vz)
    elevation = math.degrees(math.atan2(vy, horizontal))
    # How far the flight ran across the camera's view rather than along it.
    # Zero is perfectly side-on, which is what the guardrails ask for.
    off_square = math.degrees(math.atan2(abs(vz), abs(vx)))

    residual = float(np.sqrt(np.mean((y - np.polyval(np.polyfit(t, y, 2), t)) ** 2)))

    return {
        "speed": speed, "elevation": elevation, "off_square": off_square,
        "vx": vx, "vy": vy, "vz": vz, "horizontal": horizontal,
        "gravity": implied_gravity, "residual": residual,
    }


def carry_drag_free(speed: float, angle_degrees: float, launch_height: float):
    """Closed-form parabola: no air, no spin, no assumptions beyond gravity."""
    angle = math.radians(angle_degrees)
    vx = speed * math.cos(angle)
    vy = speed * math.sin(angle)

    apex = launch_height + vy * vy / (2 * GRAVITY)
    discriminant = vy * vy + 2 * GRAVITY * launch_height
    flight_time = (vy + math.sqrt(discriminant)) / GRAVITY

    return vx * flight_time, apex, flight_time


def carry_with_drag(speed: float, angle_degrees: float, launch_height: float,
                    mass_grams: float, diameter_metres: float,
                    drag_coefficient: float, air_density: float):
    """Numerically integrate with quadratic air resistance.

    Drag acceleration is -(1/2) rho Cd A |v| v / m, integrated with RK4 at a
    small fixed step until the ball returns to ground level.

    Two honest limitations. The drag coefficient of a football is not
    constant -- it falls sharply through the drag crisis around 10-15 m/s and
    varies with panelling -- and this uses a single value. And spin is ignored
    entirely, so no Magnus force: a ball struck with backspin carries further
    than this predicts, sometimes considerably.
    """
    angle = math.radians(angle_degrees)
    mass = mass_grams / 1000.0
    area = math.pi * (diameter_metres / 2) ** 2
    k = 0.5 * air_density * drag_coefficient * area / mass

    def derivative(state):
        _, _, vx, vy = state
        speed_now = math.hypot(vx, vy)
        return np.array([vx, vy,
                         -k * speed_now * vx,
                         -GRAVITY - k * speed_now * vy])

    state = np.array([0.0, launch_height,
                      speed * math.cos(angle), speed * math.sin(angle)])
    step = 0.001
    apex = launch_height
    elapsed = 0.0

    while state[1] >= 0.0 and elapsed < 30.0:
        previous = state.copy()

        k1 = derivative(state)
        k2 = derivative(state + step * k1 / 2)
        k3 = derivative(state + step * k2 / 2)
        k4 = derivative(state + step * k3)
        state = state + step * (k1 + 2 * k2 + 2 * k3 + k4) / 6
        elapsed += step
        apex = max(apex, state[1])

        if state[1] < 0.0:
            # Interpolate the landing point rather than overshooting by up to
            # one step, which at 30 m/s would be 3 cm of spurious carry.
            fraction = previous[1] / (previous[1] - state[1])
            landing = previous[0] + fraction * (state[0] - previous[0])
            return landing, apex, elapsed - step * (1 - fraction)

    return state[0], apex, elapsed


def report(args) -> None:
    samples = read_track(args.track)

    contact = args.contact_index if args.contact_index is not None \
        else find_contact(samples, args.contact_threshold, args.contact_sustain)

    fx = args.fx if args.fx is not None else (1260.0 if args.width <= 1920 else 2520.0)
    principal = (args.width / 2, args.height / 2)
    ball_metres = args.ball_mm / 1000.0

    stationary = samples[:contact]
    flight = samples[contact + args.skip_frames:]
    landing = None
    if args.last_frame is not None:
        flight = [s for s in flight if s["frame"] <= args.last_frame]
    elif not args.keep_after_landing:
        landing = find_landing(flight, args.landing_sustain)
        if landing is not None:
            flight = flight[:landing + 1]

    if len(flight) < 8:
        sys.exit(
            f"Only {len(flight)} frames of flight after contact at index "
            f"{contact}. Widen the detector's range, or set --contact-index."
        )

    t, x, y, z, raw_range, smoothed = reconstruct(flight, ball_metres, fx, principal)
    fit = fit_launch(t, x, y, z)

    print("=" * 64)
    print(f"  {args.track.name}")
    print("=" * 64)
    print()
    print("TRACK")
    print(f"  Detections          {len(samples)}")
    print(f"  Contact at          frame {samples[contact]['frame']} "
          f"(index {contact})")
    print(f"  Flight fitted over  {len(flight)} frames, "
          f"f{flight[0]['frame']} to f{flight[-1]['frame']} "
          f"({t[-1]:.4f} s)")
    if landing is not None:
        print(f"  Landing detected at frame {flight[-1]['frame']} "
              f"-- samples after it are the bounce, and are excluded")
    elif args.last_frame is None and not args.keep_after_landing:
        print("  No landing found     the ball is still descending at the end "
              "of the track;")
        print("                       if it in fact lands, the fit is running "
              "past it -- check")
        print("                       the gravity self-check below before "
              "trusting anything")
    print()

    print("GEOMETRY")
    print(f"  Focal length        {fx:.0f} px")
    print(f"  Ball diameter       {args.ball_mm:.1f} mm assumed")
    if stationary:
        rest = float(np.median([s["diameter"] for s in stationary]))
        print(f"  Ball at rest        {rest:.1f} px across "
              f"({len(stationary)} frames before contact)")
    print(f"  Range at launch     {smoothed[0]:.2f} m")
    print(f"  Range at end        {smoothed[-1]:.2f} m")
    change = (smoothed[-1] - smoothed[0]) / smoothed[0] * 100
    print(f"  Range change        {change:+.1f}%  "
          f"({'toward' if change < 0 else 'away from'} the camera)")
    print(f"  Off-square angle    {fit['off_square']:.1f} degrees")
    if fit["off_square"] > args.square_warning:
        print()
        print(f"  WARNING: the guardrail asks for within "
              f"{args.square_warning:.0f} degrees of perpendicular.")
        print("  Beyond that, more of the ball's motion runs along the view")
        print("  axis, where a single camera measures it worst -- depth comes")
        print("  only from apparent size, which is the noisiest input here.")
    print()

    print("LAUNCH  (measured)")
    print(f"  Speed               {fit['speed']:.2f} m/s   "
          f"({fit['speed'] * 2.23694:.1f} mph, {fit['speed'] * 3.6:.1f} km/h)")
    print(f"  Launch angle        {fit['elevation']:.2f} degrees above horizontal")
    print(f"  Across view (vx)    {fit['vx']:+.2f} m/s")
    print(f"  Vertical   (vy)     {fit['vy']:+.2f} m/s")
    print(f"  Along view (vz)     {fit['vz']:+.2f} m/s")
    print()

    print("SELF-CHECK")
    error = abs(fit["gravity"] - GRAVITY) / GRAVITY * 100
    verdict = "good" if error < 15 else ("fair" if error < 30 else "SUSPECT")
    print(f"  Gravity from fit    {fit['gravity']:.2f} m/s^2 "
          f"({error:.1f}% from {GRAVITY:.2f}) -- {verdict}")
    print(f"  Vertical residual   {fit['residual'] * 1000:.1f} mm RMS")
    print(f"  Range scatter       {float(np.std(raw_range - smoothed)) * 1000:.0f} mm "
          "about the fitted trend")
    if error >= 15:
        print()
        print("  Nothing tells this fit that gravity is 9.81; the number is")
        print("  derived from the pixel scale, the frame timestamps and the")
        print("  reconstruction alone. A large error means one of those is")
        print("  wrong -- a mis-stated ball size, a mistracked frame, a tilted")
        print("  camera, or a flight window that includes the boot or the net.")
    print()

    launch_height = args.launch_height
    if launch_height is None:
        launch_height = args.ball_mm / 2000.0  # ball centre sits one radius up

    mass = args.ball_g if args.ball_g is not None else \
        BALL_MASS_GRAMS.get(args.ball_size, 370.0)

    free = carry_drag_free(fit["speed"], fit["elevation"], launch_height)
    drag = carry_with_drag(fit["speed"], fit["elevation"], launch_height, mass,
                           ball_metres, args.drag_coefficient, args.air_density)

    print("FLIGHT  (computed, not measured)")
    print(f"  {'':<20}{'drag-free':>14}{'with drag':>14}{'difference':>14}")
    for label, a, b, unit in (
        ("Carry distance", free[0], drag[0], "m"),
        ("Max height", free[1], drag[1], "m"),
        ("Time of flight", free[2], drag[2], "s"),
    ):
        delta = (b - a) / a * 100 if a else 0
        print(f"  {label:<20}{a:>13.2f}{unit}{b:>13.2f}{unit}{delta:>13.1f}%")
    print()
    print(f"  Drag model assumes  Cd {args.drag_coefficient}, mass {mass:.0f} g, "
          f"air {args.air_density} kg/m^3, no spin")
    print()
    print("Carry and max height are computed from launch conditions, not")
    print("observed. Present them as theoretical, never as where the ball")
    print("would land.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Velocity, launch angle, carry and apex from a track CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example:\n"
            "  python3 tools/compute_metrics.py "
            "tools/frames/GoalKick-...-track.csv\n"
        ),
    )
    parser.add_argument("track", type=Path)

    parser.add_argument("--width", type=int, default=1920,
                        help="frame width in pixels (default 1920)")
    parser.add_argument("--height", type=int, default=1080,
                        help="frame height in pixels (default 1080)")
    parser.add_argument("--fx", type=float, default=None,
                        help="focal length in pixels; defaults to 1260 for "
                             "1080p and 2520 for 4K, from field of view")

    parser.add_argument("--ball-mm", type=float, default=206.1,
                        help="ball diameter in mm (default 206.1, a Size 4)")
    parser.add_argument("--ball-size", type=int, default=4, choices=[3, 4, 5],
                        help="ball size, used only to pick a mass (default 4)")
    parser.add_argument("--ball-g", type=float, default=None,
                        help="ball mass in grams; overrides --ball-size")

    parser.add_argument("--contact-index", type=int, default=None,
                        help="override automatic contact detection")
    parser.add_argument("--contact-threshold", type=float, default=0.15,
                        help="fraction of peak speed that counts as moving "
                             "(default 0.15)")
    parser.add_argument("--contact-sustain", type=int, default=3,
                        help="frames the ball must keep moving before contact "
                             "is believed (default 3)")
    parser.add_argument("--skip-frames", type=int, default=3,
                        help="frames to drop after contact, while the ball is "
                             "still deforming against the boot (default 3)")
    parser.add_argument("--last-frame", type=int, default=None,
                        help="ignore samples after this frame, for excluding "
                             "a ball that has reached a net; overrides the "
                             "automatic landing cut")
    parser.add_argument("--landing-sustain", type=int, default=4,
                        help="frames the ball must keep rising after the "
                             "lowest point before that point is called a "
                             "landing (default 4)")
    parser.add_argument("--keep-after-landing", action="store_true",
                        help="fit the whole track, bounce and roll included; "
                             "for seeing what the landing cut is worth")

    parser.add_argument("--square-warning", type=float, default=15.0,
                        help="warn beyond this many degrees off perpendicular "
                             "(default 15)")

    parser.add_argument("--launch-height", type=float, default=None,
                        help="ball centre height at launch in metres "
                             "(default: one ball radius)")
    parser.add_argument("--drag-coefficient", type=float, default=0.25,
                        help="drag coefficient (default 0.25)")
    parser.add_argument("--air-density", type=float, default=1.225,
                        help="air density in kg/m^3 (default 1.225)")

    return parser


def main() -> None:
    report(build_parser().parse_args())


if __name__ == "__main__":
    main()
