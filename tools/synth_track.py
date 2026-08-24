#!/usr/bin/env python3
"""Generate a track with a KNOWN answer, and check the physics against it.

    ./tools/.venv/bin/python tools/synth_track.py check
    ./tools/.venv/bin/python tools/synth_track.py generate --out /tmp/t.csv

WHY THIS EXISTS

Every debugging session in this project so far has lacked a known answer.
Real footage tells you the pipeline disagrees with a paced landing; it does
not tell you which of contact detection, the flight window, the depth
reconstruction, the geometry or the fit is responsible. Fitted gravity
averaging 7.7 against 9.81 is a symptom that four different bugs would
produce identically.

A synthetic track removes the ambiguity. The launch conditions are chosen,
not measured, so any disagreement is a defect in the code and nothing else.
The landing-window bug -- fitting through two bounces and a roll, which
reported gravity as 1.37 m/s^2 -- would have been caught here in an
afternoon instead of surviving for weeks.

HOW IT STAYS HONEST

The generator writes a CSV in detect_ball.py's exact format, and
compute_metrics.py reads it completely unmodified. Nothing here is imported
into the tool under test, and the tool under test knows nothing about this
file. The CSV is already the interface between detection and physics, so a
synthetic track is indistinguishable from a real one to everything
downstream -- which is what makes this a test of the real code path rather
than of a private copy of it.

The projection below is the exact inverse of compute_metrics.reconstruct():

    u = cx0 + fx * X / Z        (X is horizontal, right is positive)
    v = cy0 - fx * Y / Z        (Y is vertical, UP is positive)
    d = fx * D / Z              (Z is range along the optical axis)

Get any sign or convention here wrong and the test would be measuring this
file's misunderstanding rather than compute_metrics.py's behaviour, so the
three lines above are copied deliberately from the code they must invert.

WHAT THE FIRST TEST IS, AND WHY IT IS THE BORING ONE

Idealised: no noise, no drag, camera perpendicular to the kick, perfect
diameters, and a bounce so the landing cut has something to find. Run
against `compute_metrics.py --no-drag-fit`, a pure parabola in should give
a pure parabola out -- gravity 9.81, the exact launch speed and angle.

If that fails, the defect is in the geometry or the reconstruction and has
nothing to do with any footage, which is the single most valuable thing
this harness can report. Realism is added afterwards, one cause at a time,
so that when a number moves it is known what moved it.

THE LADDER, in the order it is worth climbing:

    1. idealised, drag-free, square-on          <- start here
    2. off-square, to measure the cross-term against a known truth
    3. drag in the generator, drag in the fit
    4. centroid and diameter noise, to turn the guardrails into curves
    5. a progressive diameter bias, to reproduce the 3.1 defect on demand

Flags exist for all five. Only the first is the default.
"""
import argparse
import csv
import math
import sys
from pathlib import Path

import numpy as np

# Ball diameters in mm, from the midpoint of each size's official
# circumference range. Same figures as the app's BallSize.
BALL_MM = {3: 189.4, 4: 206.1, 5: 219.6}


def focal_length(width: int, fx: float | None) -> float:
    """Match compute_metrics.py's default, so both sides agree on scale."""
    if fx is not None:
        return fx
    return 1260.0 if width <= 1920 else 2520.0


def fly(state, dt, gravity, k, substeps=8):
    """One RK4 step of ballistic flight, with optional quadratic drag.

    k = 0 gives exact drag-free motion. RK4 integrates a parabola without
    error, so the idealised case is not approximated -- it is exact to
    floating point, which matters when the whole point is a known answer.
    """
    def derivative(s):
        vx, vy, vz = s[3], s[4], s[5]
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)
        return np.array([vx, vy, vz,
                         -k * speed * vx,
                         -gravity - k * speed * vy,
                         -k * speed * vz])

    step = dt / substeps
    for _ in range(substeps):
        a = derivative(state)
        b = derivative(state + 0.5 * step * a)
        c = derivative(state + 0.5 * step * b)
        d = derivative(state + step * c)
        state = state + (step / 6.0) * (a + 2 * b + 2 * c + d)
    return state


def trajectory(args):
    """The true 3D path, in metres, with the camera at the origin.

    Camera looks along +Z. The ball starts at the paced camera distance,
    sitting on the ground, and is struck across the view.

    Ground level is -camera_height: the camera is the origin, so the pitch
    is that far below it. The ball's centre rests one radius above that.
    """
    ball_m = args.ball_mm / 1000.0
    radius = ball_m / 2.0
    ground = -args.camera_height
    dt = 1.0 / args.fps

    # Launch direction. Elevation lifts the ball; azimuth swings it out of
    # the plane perpendicular to the camera. Azimuth 0 is perfectly square,
    # which is what the filming guardrails ask for -- vz is then zero and
    # the cross-term 2*u_dot*Z_dot/fx vanishes.
    theta = math.radians(args.angle)
    phi = math.radians(args.off_square)
    speed = args.speed
    vx = speed * math.cos(theta) * math.cos(phi)
    vz = speed * math.cos(theta) * math.sin(phi)
    vy = speed * math.sin(theta)

    gravity = args.gravity
    k = 0.0
    if args.drag:
        mass = args.ball_g / 1000.0
        area = math.pi * radius * radius
        k = 0.5 * args.air_density * args.drag_coefficient * area / mass

    samples = []          # (t, X, Y, Z, airborne)

    # --- Phase 1: the ball at rest -------------------------------------
    #
    # Not decoration. find_contact() needs a stationary stretch to measure
    # peak speed against, and the resting diameter is the one trustworthy
    # scale measurement the pipeline has -- it is what --rest-anchor uses.
    # A synthetic track without it would exercise a code path the real one
    # never takes.
    x0, y0, z0 = args.offset_x, ground + radius, args.camera_distance
    for i in range(args.rest_frames):
        samples.append((i * dt, x0, y0, z0, False))

    # --- Phase 2: free flight ------------------------------------------
    state = np.array([x0, y0, z0, vx, vy, vz], dtype=float)
    frame = args.rest_frames
    landed_at = None
    while frame < args.rest_frames + args.max_flight_frames:
        t = frame * dt
        samples.append((t, state[0], state[1], state[2], True))
        previous_y = state[1]
        state = fly(state, dt, gravity, k)
        if state[1] <= ground + radius and previous_y > ground + radius:
            landed_at = frame + 1
            break
        frame += 1

    # --- Phase 3: what happens after the ball lands ---------------------
    #
    # Three endings, and which one is used matters more than it looks.
    # project_notes.md records that truncated flight is the NORMAL case:
    # in real use the ball usually leaves the frame or reaches a net, and
    # only validation footage shows the landing. So all three are here.
    if args.after == "bounce" and landed_at is not None:
        # A damped bounce, so find_landing() has a reversal to detect.
        state[1] = ground + radius
        state[4] = -state[4] * args.restitution
        state[3] *= args.rolling_friction
        state[5] *= args.rolling_friction
        for i in range(args.after_frames):
            t = (landed_at + i) * dt
            samples.append((t, state[0], state[1], state[2], True))
            state = fly(state, dt, gravity, k)
            if state[1] < ground + radius:
                state[1] = ground + radius
                state[4] = -state[4] * args.restitution
                state[3] *= args.rolling_friction
                state[5] *= args.rolling_friction
    # "truncate" ends at the landing; "net" ends early, mid-flight, and is
    # applied below by cutting the sample list.

    if args.after == "net":
        cut = args.rest_frames + args.net_frames
        samples = samples[:cut]

    return samples, dt, landed_at


def project(samples, args, rng):
    """World metres to image pixels and apparent diameter.

    The exact inverse of compute_metrics.reconstruct(). Noise is applied
    here rather than in the trajectory, because that is where it happens in
    reality -- the ball's true path is clean and the *measurement* of it is
    not.
    """
    fx = focal_length(args.width, args.fx)
    cx0, cy0 = args.width / 2.0, args.height / 2.0
    ball_m = args.ball_mm / 1000.0

    # Pass one: clean projection. Image speed is needed before the blur
    # term can be applied, and image speed is only knowable once the
    # positions exist -- so the bias cannot be folded into a single loop.
    clean = []
    for t, X, Y, Z, airborne in samples:
        clean.append((cx0 + fx * X / Z, cy0 - fx * Y / Z,
                      fx * ball_m / Z, Z, airborne, t))

    # Pass two: degrade the measurements, then write them.
    #
    # A progressive under-read of the flight diameters is the prime suspect
    # for the gravity discrepancy. project_notes.md records TWO drivers --
    # "the detector's box degrades as the ball recedes and blurs" -- and
    # they are modelled separately because they behave differently:
    #
    #   recession  grows as the ball gets further away and smaller. It is
    #              ZERO for a perfectly square kick, where range never
    #              changes. Modelling only this made --diameter-bias
    #              silently do nothing at --off-square 0, which is how this
    #              limitation was found.
    #
    #   blur       grows with image-plane speed. It is LARGEST for a square
    #              kick, where the ball crosses the frame fastest, so it
    #              covers exactly the case recession cannot reach.
    #
    # Between them every geometry is testable. Measured on the device the
    # box is known to shrink, not grow, under blur -- 58.4 to 42.9 px as
    # confidence fell to 0.34 -- so both terms reduce the diameter.
    rows = []
    for index, (u, v, d, Z, airborne, t) in enumerate(clean):

        if airborne and args.diameter_bias:
            travelled = max(0.0, Z - args.camera_distance)
            span = max(1e-9, args.bias_reference)
            d *= 1.0 - args.diameter_bias * min(1.0, travelled / span)

        if airborne and args.blur_bias:
            previous = clean[index - 1] if index > 0 else clean[index]
            following = clean[index + 1] if index + 1 < len(clean) else clean[index]
            step = math.hypot(following[0] - previous[0],
                              following[1] - previous[1]) / 2.0
            reference = max(1e-9, args.blur_reference)
            d *= 1.0 - args.blur_bias * min(1.0, step / reference)

        if args.centroid_noise:
            u += rng.normal(0.0, args.centroid_noise)
            v += rng.normal(0.0, args.centroid_noise)
        if args.diameter_noise:
            d *= 1.0 + rng.normal(0.0, args.diameter_noise)
        if args.diameter_noise_px:
            # Noise as an absolute number of pixels, which is how a
            # detector's box error actually behaves -- a box edge is found
            # to within some fraction of a pixel regardless of how big the
            # object is. Expressing it as a fraction instead makes every
            # format equally noisy in relative terms, which silently
            # deletes the advantage of having more pixels on the ball.
            # That flaw invalidated the first format study; see
            # project_notes.md item 2.1, rung 9.
            d += rng.normal(0.0, args.diameter_noise_px)

        rows.append({
            "frame": index,
            "time_s": f"{t:.6f}",
            "detected": 1,
            "confidence": "0.9000",
            "cx": f"{u:.2f}",
            "cy": f"{v:.2f}",
            "raw_cx": f"{u:.2f}",
            "raw_cy": f"{v:.2f}",
            "diameter": f"{d:.2f}",
            "drift_px": "0.00",
            "status": "ok",
            "candidates": 1,
        })
    return rows


def off_frame(rows, args) -> int:
    """How many projected samples fall outside the picture.

    Worth reporting rather than silently allowing. The maths does not care
    -- projection is projection -- but a track whose ball is 15,000 px to
    the right of a 3840 px frame is not something any detector could have
    produced, and a guardrail or noise study run on one would be measuring
    a situation that cannot occur.

    It is also the synthetic form of a real tension recorded in
    project_notes.md: framing a whole flight and resolving the ball are in
    direct conflict, so a clip that contains the landing was filmed from
    far enough back that the ball is only a few pixels across.
    """
    outside = 0
    for row in rows:
        u, v = float(row["cx"]), float(row["cy"])
        if not (0 <= u <= args.width and 0 <= v <= args.height):
            outside += 1
    return outside


def write_csv(rows, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def truth(args):
    """What the generator was told to produce, for comparison."""
    theta = math.radians(args.angle)
    phi = math.radians(args.off_square)
    return {
        "speed": args.speed,
        "elevation": args.angle,
        "off_square": abs(args.off_square),
        "gravity": args.gravity,
        "vx": args.speed * math.cos(theta) * math.cos(phi),
        "vy": args.speed * math.sin(theta),
        "vz": args.speed * math.cos(theta) * math.sin(phi),
    }


def run_generate(args) -> None:
    rng = np.random.default_rng(args.seed)
    samples, dt, landed = trajectory(args)
    rows = project(samples, args, rng)
    write_csv(rows, args.out)

    print(f"Wrote {len(rows)} frames to {args.out}")
    print(f"  {args.rest_frames} at rest, then flight at {args.fps} fps")
    if landed is not None:
        print(f"  lands at frame {landed}, ending: {args.after}")
    else:
        print(f"  does not land within {args.max_flight_frames} frames")
    print()
    print("Now run the physics against it, unmodified:")
    print(f"  ./tools/.venv/bin/python tools/compute_metrics.py {args.out} \\")
    print(f"      --width {args.width} --height {args.height} "
          f"--ball-mm {args.ball_mm}"
          + ("" if args.drag else " --no-drag-fit"))


def run_check(args) -> None:
    """Generate, run the real physics over it, and report truth vs recovered.

    compute_metrics is imported rather than reimplemented. Its contact
    detection, its landing cut, its reconstruction and its fit are all
    exercised exactly as `report()` drives them -- the numbers below come
    from the shipping code path, not from a convenient subset of it.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import compute_metrics as cm
    except ImportError as error:
        sys.exit(f"Could not import compute_metrics.py: {error}")

    rng = np.random.default_rng(args.seed)
    samples, dt, landed = trajectory(args)
    rows = project(samples, args, rng)
    write_csv(rows, args.out)

    track = cm.read_track(args.out)
    contact = cm.find_contact(track, args.contact_threshold,
                              args.contact_sustain)

    flight = track[contact + args.skip_frames:]
    landing_index = None
    if not args.keep_after_landing:
        landing_index = cm.find_landing(flight, args.landing_sustain)
        if landing_index is not None:
            flight = flight[:landing_index + 1]

    fx = focal_length(args.width, args.fx)
    principal = (args.width / 2.0, args.height / 2.0)
    t, x, y, z, raw_range, smooth_range = cm.reconstruct(
        flight, args.ball_mm / 1000.0, fx, principal)

    fit = cm.fit_launch(t, x, y, z)

    expected = truth(args)

    print()
    print("SYNTHETIC CHECK")
    print(f"  frames        {len(rows)} total, {args.rest_frames} at rest, "
          f"ending '{args.after}'")
    print(f"  generator     {'drag Cd ' + str(args.drag_coefficient) if args.drag else 'drag-free'}"
          f", off-square {args.off_square:g} deg"
          f", centroid noise {args.centroid_noise:g} px"
          f", diameter noise {args.diameter_noise:g}"
          f", recession bias {args.diameter_bias:g}"
          f", blur bias {args.blur_bias:g}")
    outside = off_frame(rows, args)
    if outside:
        print(f"  NOTE          {outside} of {len(rows)} samples fall "
              f"outside the {args.width}x{args.height} frame")
        print("                the maths is unaffected, but no detector "
              "could have produced this track")
    print(f"  contact       frame {track[contact]['frame']} "
          f"(true contact is frame {args.rest_frames})")
    if landing_index is not None:
        print(f"  landing cut   at flight sample {landing_index}"
              + (f", true landing frame {landed}" if landed else ""))
    else:
        print("  landing cut   none found"
              + (f", true landing frame {landed}" if landed else ""))
    print()
    print(f"  {'quantity':<14}{'truth':>12}{'recovered':>12}{'error':>12}")

    worst = 0.0
    for name, key, unit in [("speed", "speed", "m/s"),
                            ("elevation", "elevation", "deg"),
                            ("off-square", "off_square", "deg"),
                            ("gravity", "gravity", "m/s^2"),
                            ("vx", "vx", "m/s"),
                            ("vy", "vy", "m/s"),
                            ("vz", "vz", "m/s")]:
        want, got = expected[key], fit[key]
        if abs(want) > 1e-9:
            error = 100 * (got / want - 1)
            shown = f"{error:+10.2f}%"
            worst = max(worst, abs(error))
        else:
            shown = f"{got - want:+10.3f} "
        print(f"  {name:<14}{want:12.4f}{got:12.4f}{shown:>12}")

    print(f"  {'residual':<14}{'':>12}{fit['residual'] * 1000:9.2f} mm")
    print()
    print(f"  Worst error on a non-zero quantity: {worst:.2f}%")
    print()

    if args.after == "bounce" and not any([args.centroid_noise,
                                           args.diameter_noise,
                                           args.diameter_bias,
                                           args.blur_bias, args.drag]):
        print("  This is the idealised case: no noise, no drag, exact")
        print("  diameters. Everything above should be near zero. Anything")
        print("  that is not is a defect in the geometry, the reconstruction")
        print("  or the fit -- not in any footage. Chase it before adding")
        print("  realism, because every later number rests on it.")


def run_sweep(args) -> None:
    """Fitted gravity against the length of the fit window.

    This exists because of a result that looked like a contradiction. A
    progressive diameter under-read makes the recovered gravity read HIGH
    on a long synthetic flight, while the real 2026-08-22 clips read LOW --
    from what is believed to be the same defect.

    The resolution is that under-reading diameter inflates depth
    progressively, which multiplies the parabola by a growing factor and
    injects a CUBIC term. A quadratic fit cannot represent a cubic, and how
    it fails depends on how much of the curve it sees: over a short window
    the linear part of the inflation dominates and drags gravity down, and
    over a long one the cubic projects onto the quadratic and pushes it up.

    That was worked out analytically. This runs it through the real
    reconstruct() and fit_launch(), on identical detections, changing only
    where the window ends -- because an analytic argument about the code is
    not the same thing as the code.

    Consequence if it holds: fitted gravity is NOT a severity measure
    across clips of different flight durations. Comparing 4.40 against
    10.48 on the 2026-08-22 set is partly comparing flight times.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import compute_metrics as cm
    except ImportError as error:
        sys.exit(f"Could not import compute_metrics.py: {error}")

    rng = np.random.default_rng(args.seed)
    samples, dt, landed = trajectory(args)
    rows = project(samples, args, rng)
    write_csv(rows, args.out)

    track = cm.read_track(args.out)
    contact = cm.find_contact(track, args.contact_threshold,
                              args.contact_sustain)
    flight = track[contact + args.skip_frames:]

    fx = focal_length(args.width, args.fx)
    principal = (args.width / 2.0, args.height / 2.0)
    expected = truth(args)

    print()
    print("WINDOW-LENGTH SWEEP")
    print(f"  bias: recession {args.diameter_bias:g}, blur {args.blur_bias:g}"
          f"; off-square {args.off_square:g} deg")
    print(f"  {len(flight)} flight samples available "
          f"({len(flight) * dt:.2f} s at {args.fps:g} fps)")
    print()
    print(f"  {'window':>9}{'frames':>8}{'gravity':>10}{'error':>9}"
          f"{'residual':>11}{'speed err':>11}")

    for seconds in args.windows:
        count = int(round(seconds / dt))
        if count < 8 or count > len(flight):
            continue
        window = flight[:count]
        t, x, y, z, _, _ = cm.reconstruct(window, args.ball_mm / 1000.0,
                                          fx, principal)
        fit = cm.fit_launch(t, x, y, z)
        g_error = 100 * (fit["gravity"] / expected["gravity"] - 1)
        s_error = 100 * (fit["speed"] / expected["speed"] - 1)
        print(f"  {seconds:8.2f}s{count:8d}{fit['gravity']:10.3f}"
              f"{g_error:+8.1f}%{fit['residual'] * 1000:9.2f} mm"
              f"{s_error:+10.2f}%")

    print()
    print("  With no bias, gravity should be flat and correct at every")
    print("  window length. With bias, watch for a sign change: that is the")
    print("  cubic overtaking the linear term, and it is what makes fitted")
    print("  gravity unusable for comparing clips of different durations.")
    print()
    print("  The residual is the honest indicator either way -- it grows")
    print("  with the bias and never changes sign, because a quadratic")
    print("  simply cannot describe a cubic.")


def analyse(args, rng, overrides=None):
    """One complete trial: generate, project, and run the real physics.

    Returns the fit, or None if the pipeline could not produce one. Every
    study below is this function called repeatedly with different settings,
    so the studies cannot diverge from what `check` does.

    `overrides` temporarily replaces attributes on args. argparse namespaces
    are plain mutable objects, so this is a small, explicit way to vary one
    parameter without rebuilding the whole configuration.
    """
    import copy
    local = copy.copy(args)
    for key, value in (overrides or {}).items():
        setattr(local, key, value)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import compute_metrics as cm

    samples, dt, landed = trajectory(local)
    rows = project(samples, local, rng)

    track = [{
        "frame": r["frame"], "t": float(r["time_s"]),
        "u": float(r["cx"]), "v": float(r["cy"]),
        "diameter": float(r["diameter"]),
    } for r in rows]

    if len(track) < 8:
        return None, local

    contact = cm.find_contact(track, local.contact_threshold,
                              local.contact_sustain)
    flight = track[contact + local.skip_frames:]
    landing = cm.find_landing(flight, local.landing_sustain)
    if landing is not None:
        flight = flight[:landing + 1]
    if len(flight) < 8:
        return None, local

    fx = focal_length(local.width, local.fx)
    principal = (local.width / 2.0, local.height / 2.0)
    t, x, y, z, _, _ = cm.reconstruct(flight, local.ball_mm / 1000.0,
                                      fx, principal)
    return cm.fit_launch(t, x, y, z), local


def errors_against_truth(fit, local):
    """Percentage error on the quantities a coach would be shown."""
    want = truth(local)
    return {
        "speed": 100 * (fit["speed"] / want["speed"] - 1),
        "elevation": fit["elevation"] - want["elevation"],
        "gravity": 100 * (fit["gravity"] / want["gravity"] - 1),
        "residual_mm": fit["residual"] * 1000,
    }


def summarise(values):
    """Mean and standard deviation, as a formatted pair."""
    if not values:
        return "     --        --"
    array = np.array(values)
    return f"{array.mean():+8.2f} {array.std():7.2f}"


def run_study(args) -> None:
    """Repeated trials across a swept parameter, aggregated.

    A single noisy run is not evidence -- one draw of the random numbers
    can flatter or damn any setting. These sweep a parameter, run
    --trials seeds at each point, and report the mean error and its spread.
    The spread matters as much as the mean: a guardrail is a promise about
    the worst case, not the average one.
    """
    print()
    if args.mode == "noise":
        print("NOISE STUDY")
        print("  What measurement noise costs, and how fast it grows.")
        print("  Centroid noise is the detector's box centre wobbling;")
        print("  diameter noise is its size wobbling. Diameter is the one")
        print("  that matters -- every distance rests on it, and relative")
        print("  range error tracks relative diameter error one for one.")
        print()
        print(f"  {args.trials} trials per point, {args.width}x{args.height} "
              f"at {args.fps:g} fps, {args.camera_distance:g} m")
        print()
        print(f"  {'centroid':>9}{'diameter':>10}"
              f"{'speed err %':>19}{'angle err deg':>19}"
              f"{'gravity err %':>19}{'residual':>10}")
        print(f"  {'px':>9}{'frac':>10}{'mean    sd':>19}{'mean    sd':>19}"
              f"{'mean    sd':>19}{'mm':>10}")

        points = [(c, d) for c in args.centroid for d in args.diameter]
        for centroid, diameter in points:
            speeds, angles, gravities, residuals = [], [], [], []
            for trial in range(args.trials):
                rng = np.random.default_rng(args.seed + trial)
                fit, local = analyse(args, rng, {
                    "centroid_noise": centroid, "diameter_noise": diameter})
                if fit is None:
                    continue
                e = errors_against_truth(fit, local)
                speeds.append(e["speed"])
                angles.append(e["elevation"])
                gravities.append(e["gravity"])
                residuals.append(e["residual_mm"])
            print(f"  {centroid:9.2f}{diameter:10.3f}"
                  f"   {summarise(speeds)}   {summarise(angles)}"
                  f"   {summarise(gravities)}{np.mean(residuals) if residuals else 0:10.1f}")
        print()
        print("  Read the spread, not just the mean. A guardrail is a")
        print("  promise about the worst case. Note also that the speed")
        print("  column carries the -0.74% launch-time origin defect of")
        print("  item 3.5 as a constant offset until that is fixed.")

    elif args.mode == "geometry":
        print("GEOMETRY STUDY")
        print("  What off-square filming actually costs.")
        print()
        print("  The +-15 degree guardrail is justified in this document by")
        print("  cos(phi) foreshortening -- 3.4% at 15 degrees. That")
        print("  reasoning describes a 2D image-plane measurement, and this")
        print("  pipeline reconstructs depth per frame instead, so with")
        print("  exact diameters off-square costs nothing at all.")
        print()
        print("  The real question is whether off-square AMPLIFIES diameter")
        print("  error, which is what the cross-term 2*u_dot*Z_dot/fx would")
        print("  do. This sweeps both together to find out.")
        print()
        print(f"  {args.trials} trials per point")
        print()
        header = "".join(f"{f'bias {b:g}':>14}" for b in args.bias)
        print(f"  {'off-square':>11}{header}")
        for angle in args.angles:
            cells = []
            for bias in args.bias:
                gravities = []
                for trial in range(args.trials):
                    rng = np.random.default_rng(args.seed + trial)
                    fit, local = analyse(args, rng, {
                        "off_square": angle, "diameter_bias": bias})
                    if fit is None:
                        continue
                    gravities.append(
                        errors_against_truth(fit, local)["gravity"])
                cells.append(f"{np.mean(gravities):+13.2f}%" if gravities
                             else f"{'--':>14}")
            print(f"  {angle:10.0f}d" + "".join(cells))
        print()
        print("  Cells are mean gravity error. If a row is flat across the")
        print("  bias columns, off-square is harmless at that bias. If the")
        print("  rows fan out as bias rises, the cross-term is amplifying")
        print("  diameter error and the guardrail earns its place -- for")
        print("  that reason rather than for foreshortening.")

    elif args.mode == "distance":
        print("DISTANCE STUDY")
        print("  What standing further back actually costs.")
        print()
        print("  The 5-12 m guardrail rests on a table of pixel counts and")
        print("  the argument that relative range error tracks relative")
        print("  diameter error one for one. This measures it instead.")
        print()
        print("  Diameter noise is in PIXELS here, which is the whole")
        print("  mechanism: a box edge is found to within some fraction of")
        print("  a pixel however far away the ball is, so the same absolute")
        print("  error becomes a larger relative one as the ball shrinks.")
        print("  Sweeping distance with FRACTIONAL noise measures nothing,")
        print("  because it holds the relative error constant by")
        print("  construction -- which is exactly the mistake that made the")
        print("  first format study meaningless.")
        print()
        print(f"  {args.trials} trials per point, {args.width}x{args.height} "
              f"at {args.fps:g} fps, diameter noise "
              f"{args.distance_noise_px:g} px")
        print()
        print(f"  {'distance':>9}{'ball px':>9}{'rel err':>9}"
              f"{'speed err %':>19}{'gravity err %':>19}{'residual':>10}")

        if args.distance_bias:
            print(f"  PLUS a systematic recession bias of "
                  f"{args.distance_bias:g}, held CONSTANT across distances.")
            print()
            print("  Note carefully what this does and does not measure. It")
            print("  measures how a GIVEN bias's effect on the metrics")
            print("  varies with how far back you stand. It does NOT")
            print("  measure how the bias itself grows as the ball gets")
            print("  smaller -- that is a property of the detector, not of")
            print("  the physics, and no synthetic study can answer it.")
            print()

        fx = focal_length(args.width, args.fx)
        for distance in args.distances:
            ball_px = fx * (args.ball_mm / 1000.0) / distance
            speeds, gravities, residuals = [], [], []
            for trial in range(args.trials):
                rng = np.random.default_rng(args.seed + trial)
                fit, local = analyse(args, rng, {
                    "camera_distance": distance,
                    "diameter_noise": 0.0,
                    "diameter_noise_px": args.distance_noise_px,
                    "diameter_bias": args.distance_bias})
                if fit is None:
                    continue
                e = errors_against_truth(fit, local)
                speeds.append(e["speed"])
                gravities.append(e["gravity"])
                residuals.append(e["residual_mm"])
            relative = 100 * args.distance_noise_px / ball_px
            print(f"  {distance:8.1f}m{ball_px:9.1f}{relative:8.2f}%"
                  f"   {summarise(speeds)}   {summarise(gravities)}"
                  f"{np.mean(residuals) if residuals else 0:10.1f}")
        print()
        if args.distance_bias:
            print("  Read the MEANS here, not the spreads. A systematic bias")
            print("  moves every trial the same way, so it shows up as an")
            print("  offset rather than as scatter -- which is exactly why")
            print("  averaging cannot remove it and why it dominates.")
        else:
            print("  The spread columns are the guardrail. Where they start")
            print("  to climb steeply is where standing further back stops")
            print("  being a matter of convenience and starts costing")
            print("  accuracy. Add --distance-bias to see what a systematic")
            print("  error does instead, which is a different question.")

    elif args.mode == "format":
        print("FORMAT STUDY")
        print("  1080p/240 against 4K/120, on the SAME kick.")
        print()
        print("  This is the comparison no single-phone filming session can")
        print("  make: one device runs one format at a time, so the two")
        print("  real sessions compared different kicks in aggregate. Here")
        print("  the trajectory is identical and only the camera changes.")
        print()
        print("  1080p/240 has twice the samples and less motion blur;")
        print("  4K/120 has twice the pixels across the ball, and diameter")
        print("  precision is the weakest link in the chain.")
        print()
        print(f"  {args.trials} trials per point, centroid noise "
              f"{args.format_centroid_noise:g} px, diameter noise "
              f"{args.format_diameter_noise_px:g} PIXELS")
        print()
        print("  Diameter noise is in pixels, not as a fraction. That is the")
        print("  whole point: a box edge is found to within some fraction of")
        print("  a pixel however big the ball is, so 4K's extra pixels are a")
        print("  real advantage. Specifying a fraction instead gives both")
        print("  formats equal relative noise and hides that entirely --")
        print("  which is how the first version of this study went wrong.")
        print()
        print(f"  {'format':>12}{'fx':>7}{'samples':>9}"
              f"{'speed err %':>19}{'gravity err %':>19}{'residual':>10}")

        formats = [("1080p/240", 1920, 1080, 240.0),
                   ("4K/120", 3840, 2160, 120.0)]
        for name, width, height, fps in formats:
            speeds, gravities, residuals, counts = [], [], [], []
            for trial in range(args.trials):
                rng = np.random.default_rng(args.seed + trial)
                fit, local = analyse(args, rng, {
                    "width": width, "height": height, "fps": fps,
                    "centroid_noise": args.format_centroid_noise,
                    "diameter_noise": 0.0,
                    "diameter_noise_px": args.format_diameter_noise_px})
                if fit is None:
                    continue
                e = errors_against_truth(fit, local)
                speeds.append(e["speed"])
                gravities.append(e["gravity"])
                residuals.append(e["residual_mm"])
            fx = focal_length(width, None)
            ball_px = fx * (args.ball_mm / 1000.0) / args.camera_distance
            relative = 100 * args.format_diameter_noise_px / ball_px
            print(f"  {name:>12}{fx:7.0f}{len(speeds):9d}"
                  f"   {summarise(speeds)}   {summarise(gravities)}"
                  f"{np.mean(residuals) if residuals else 0:10.1f}")
            print(f"  {'':>12}{'':>7}{'':>9}   ball {ball_px:.1f} px at rest, "
                  f"so {args.format_diameter_noise_px:g} px is "
                  f"{relative:.2f}% relative")
        print()
        print("  The spread columns are the answer, not the means. Both")
        print("  formats see the same truth, so a systematic offset is")
        print("  shared; what differs is how much the noise moves each.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Synthetic tracks with a known answer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("WHY THIS EXISTS")[0],
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        # --- the kick ---
        p.add_argument("--speed", type=float, default=25.0,
                       help="launch speed in m/s (default 25)")
        p.add_argument("--angle", type=float, default=35.0,
                       help="launch elevation in degrees (default 35)")
        p.add_argument("--off-square", type=float, default=0.0,
                       help="degrees off perpendicular; 0 is what the "
                            "guardrails ask for (default 0)")
        p.add_argument("--gravity", type=float, default=9.81)

        # --- the camera ---
        p.add_argument("--camera-distance", type=float, default=9.14,
                       help="metres from camera to ball, 10 yards by default "
                            "to match the 2026-08-22 session")
        p.add_argument("--camera-height", type=float, default=1.4,
                       help="camera height in metres (default 1.4)")
        p.add_argument("--offset-x", type=float, default=-4.0,
                       help="ball's horizontal offset at rest, so it starts "
                            "on one side of the frame (default -4)")
        p.add_argument("--width", type=int, default=3840)
        p.add_argument("--height", type=int, default=2160)
        p.add_argument("--fps", type=float, default=120.0)
        p.add_argument("--fx", type=float, default=None,
                       help="focal length in px; defaults as compute_metrics "
                            "does, 1260 at 1080p and 2520 at 4K")

        # --- the ball ---
        p.add_argument("--ball-mm", type=float, default=BALL_MM[4])
        p.add_argument("--ball-g", type=float, default=370.0)

        # --- how the clip ends ---
        p.add_argument("--after", choices=["bounce", "truncate", "net"],
                       default="bounce",
                       help="bounce: ball lands and bounces, so the landing "
                            "cut has a reversal to find. truncate: ends at "
                            "the landing. net: ends mid-flight, which is the "
                            "normal case in real use (default bounce)")
        p.add_argument("--rest-frames", type=int, default=60)
        p.add_argument("--max-flight-frames", type=int, default=1200)
        p.add_argument("--after-frames", type=int, default=120)
        p.add_argument("--net-frames", type=int, default=40)
        p.add_argument("--restitution", type=float, default=0.5)
        p.add_argument("--rolling-friction", type=float, default=0.7)

        # --- realism, all off by default ---
        p.add_argument("--drag", action="store_true",
                       help="generate with quadratic drag as well")
        p.add_argument("--drag-coefficient", type=float, default=0.25)
        p.add_argument("--air-density", type=float, default=1.225)
        p.add_argument("--centroid-noise", type=float, default=0.0,
                       help="gaussian sigma on cx and cy, in pixels")
        p.add_argument("--diameter-noise", type=float, default=0.0,
                       help="gaussian sigma on diameter, as a fraction. "
                            "Use --diameter-noise-px instead when comparing "
                            "formats: a fraction gives every format equal "
                            "relative noise and hides the whole benefit of "
                            "more pixels on the ball")
        p.add_argument("--diameter-noise-px", type=float, default=0.0,
                       help="gaussian sigma on diameter, in PIXELS. This is "
                            "how a detector's box error really behaves, and "
                            "it is the honest basis for a format comparison")
        p.add_argument("--diameter-bias", type=float, default=0.0,
                       help="progressive under-read of flight diameters, as "
                            "a fraction at --bias-reference metres of "
                            "recession; reproduces the 3.1 defect")
        p.add_argument("--bias-reference", type=float, default=15.0,
                       help="metres of recession at which --diameter-bias "
                            "reaches full strength (default 15)")
        p.add_argument("--blur-bias", type=float, default=0.0,
                       help="under-read of diameter driven by image-plane "
                            "speed rather than by recession. This is the "
                            "only bias term that acts on a square-on kick, "
                            "where the range never changes")
        p.add_argument("--blur-reference", type=float, default=30.0,
                       help="image speed in px per frame at which "
                            "--blur-bias reaches full strength (default 30)")
        p.add_argument("--seed", type=int, default=1)

    gen = sub.add_parser("generate", help="write a synthetic track CSV")
    common(gen)
    gen.add_argument("--out", type=Path,
                     default=Path("tools/frames/synthetic-track.csv"))
    gen.set_defaults(func=run_generate)

    chk = sub.add_parser("check",
                         help="generate, run the real physics, compare")
    common(chk)
    chk.add_argument("--out", type=Path,
                     default=Path("tools/frames/synthetic-track.csv"))
    # Mirrors compute_metrics.py's own defaults, so `check` exercises the
    # tool as it is actually run rather than a tuned variant of it.
    chk.add_argument("--contact-threshold", type=float, default=0.3)
    chk.add_argument("--contact-sustain", type=int, default=3)
    chk.add_argument("--skip-frames", type=int, default=3)
    chk.add_argument("--landing-sustain", type=int, default=4)
    chk.add_argument("--keep-after-landing", action="store_true")
    chk.set_defaults(func=run_check)

    swp = sub.add_parser("sweep",
                         help="fitted gravity against fit-window length")
    common(swp)
    swp.add_argument("--out", type=Path,
                     default=Path("tools/frames/synthetic-track.csv"))
    swp.add_argument("--contact-threshold", type=float, default=0.3)
    swp.add_argument("--contact-sustain", type=int, default=3)
    swp.add_argument("--skip-frames", type=int, default=3)
    swp.add_argument("--windows", type=float, nargs="+",
                     default=[0.10, 0.25, 0.50, 0.75, 1.00, 1.50,
                              2.00, 2.50, 2.90],
                     help="window lengths in seconds")
    swp.set_defaults(func=run_sweep)

    std = sub.add_parser("study",
                         help="repeated trials across a swept parameter")
    common(std)
    std.add_argument("mode",
                     choices=["noise", "geometry", "format", "distance"])
    std.add_argument("--trials", type=int, default=50,
                     help="random seeds per point (default 50)")
    std.add_argument("--contact-threshold", type=float, default=0.3)
    std.add_argument("--contact-sustain", type=int, default=3)
    std.add_argument("--skip-frames", type=int, default=3)
    std.add_argument("--landing-sustain", type=int, default=4)
    # noise mode
    std.add_argument("--centroid", type=float, nargs="+",
                     default=[0.0, 0.25, 0.5, 1.0, 2.0],
                     help="centroid noise levels in px")
    std.add_argument("--diameter", type=float, nargs="+",
                     default=[0.0, 0.01, 0.02, 0.05],
                     help="diameter noise levels as a fraction")
    # geometry mode
    std.add_argument("--angles", type=float, nargs="+",
                     default=[0, 5, 15, 30, 45],
                     help="off-square angles in degrees")
    std.add_argument("--bias", type=float, nargs="+",
                     default=[0.0, 0.02, 0.06, 0.10],
                     help="recession diameter-bias levels")
    # format mode
    # distance mode
    std.add_argument("--distances", type=float, nargs="+",
                     default=[5, 8, 10, 12, 15, 20, 27],
                     help="camera distances in metres; the guardrail is "
                          "5-12 and 27 is where a whole 40 m flight fits")
    std.add_argument("--distance-noise-px", type=float, default=0.5,
                     help="diameter noise in PIXELS for the distance study")
    std.add_argument("--distance-bias", type=float, default=0.0,
                     help="systematic recession bias held constant across "
                          "distances, to separate what a SYSTEMATIC error "
                          "costs from what random noise costs")
    # format mode
    std.add_argument("--format-centroid-noise", type=float, default=0.5)
    std.add_argument("--format-diameter-noise-px", type=float, default=0.5,
                     help="diameter noise in PIXELS for the format study "
                          "(default 0.5). Deliberately not a fraction -- see "
                          "the note the study prints")
    std.set_defaults(func=run_study)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
