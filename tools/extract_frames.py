#!/usr/bin/env python3
"""Look at GoalKick footage before writing any tracking code.

This is deliberately not a tracker. Its job is to answer the questions that
decide how tracking should work, none of which can be answered by guessing:

  * Did the clip's frame timing survive the trip off the phone?
  * Where in the clip is the kick?
  * How big is the ball in pixels, and how badly is it smeared by motion blur?
  * What does the ball look like against that particular grass and sky?

Three modes:

  probe    Report what the file contains, and check the real frame timing
           against the nominal rate.
  sheet    Write one contact sheet of evenly spaced frames, to find the kick.
  extract  Write individual frames as PNGs over a chosen range.

Nothing here writes to the video. Every mode is read-only.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from pathlib import Path

try:
    import cv2
except ImportError:
    sys.exit(
        "OpenCV is not installed.\n"
        "  python3 -m venv tools/.venv\n"
        "  source tools/.venv/bin/activate\n"
        "  pip install -r tools/requirements.txt\n"
        "\n"
        "If pip cannot find an opencv-python wheel for your Python version,\n"
        "the usual cause is that Python is newer than the available wheels.\n"
        "Build the venv against an older interpreter (3.12 or 3.13) instead."
    )

import numpy as np


# --- Opening the clip ------------------------------------------------------

def open_clip(path: Path, auto_rotate: bool):
    """Open a clip, optionally defeating OpenCV's automatic rotation.

    Clips recorded by GoalKick carry a preferredTransform describing how the
    phone was held. OpenCV honours it by default and hands back upright
    frames. That is usually what you want to look at, but it means the pixel
    coordinates you see are not the ones stored in the file -- and the app's
    own analysis will have to make the same choice consciously. Getting this
    wrong swaps the trajectory's axes and turns launch angle into its
    complement, so the mode in force is always printed.
    """
    if not path.exists():
        sys.exit(f"No such file: {path}")

    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        sys.exit(
            f"Could not open {path}.\n"
            "OpenCV may lack the codec for this file. Check it plays in "
            "QuickTime first; if it does, the clip is fine and the decoder "
            "is the problem."
        )

    if not auto_rotate:
        capture.set(cv2.CAP_PROP_ORIENTATION_AUTO, 0)

    return capture


def describe(capture, path: Path, auto_rotate: bool) -> dict:
    """What the file claims about itself. Claims, not measurements."""
    info = {
        "path": path,
        "width": int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "nominal_fps": capture.get(cv2.CAP_PROP_FPS),
        "frame_count": int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
        "rotation": capture.get(cv2.CAP_PROP_ORIENTATION_META),
        "auto_rotate": auto_rotate,
    }
    fps = info["nominal_fps"]
    info["duration"] = info["frame_count"] / fps if fps else 0.0
    return info


def print_description(info: dict) -> None:
    print(f"File          {info['path'].name}")
    print(f"Frame size    {info['width']} x {info['height']}")
    print(f"Nominal rate  {info['nominal_fps']:.3f} fps")
    print(f"Frame count   {info['frame_count']}")
    print(f"Duration      {info['duration']:.3f} s")
    print(f"Rotation      {info['rotation']:.0f} degrees in metadata")
    print(
        "Auto-rotate   "
        + ("on -- frames shown upright" if info["auto_rotate"]
           else "OFF -- frames shown as stored")
    )
    print()


# --- Frame walking ---------------------------------------------------------

def frames(capture, start: int = 0, end: int | None = None):
    """Yield (index, timestamp_seconds, image), decoding sequentially.

    Sequential decode rather than seeking. Seeking by frame number in a long
    GOP is approximate, and an approximate frame index is worse than useless
    when the whole point is per-frame measurement.

    The timestamp is read before the frame it belongs to, because after a
    read() the position has already advanced to the next frame.
    """
    index = 0
    while True:
        if end is not None and index > end:
            return

        milliseconds = capture.get(cv2.CAP_PROP_POS_MSEC)
        ok, image = capture.read()
        if not ok:
            return

        if index >= start:
            yield index, milliseconds / 1000.0, image
        index += 1


# --- probe -----------------------------------------------------------------

def run_probe(args) -> None:
    """Check that real frame timing survived the trip off the phone.

    project_notes.md is emphatic that nominalFrameRate is a label rather than
    a measurement, and that dt must come from presentation timestamps. This
    is where that gets verified: if these clips had gone through Photos, the
    gaps would read 1/30 s instead of 1/240 s and every velocity computed
    later would be eight times too slow with no visible symptom.
    """
    capture = open_clip(args.video, args.auto_rotate)
    info = describe(capture, args.video, args.auto_rotate)
    print_description(info)

    print(f"Reading timestamps from the first {args.sample} frames...")
    timestamps = [t for _, t, _ in frames(capture, end=args.sample - 1)]
    capture.release()

    if len(timestamps) < 2:
        sys.exit("Too few frames decoded to measure timing.")

    gaps = np.diff(timestamps)
    gaps = gaps[gaps > 0]  # a repeated timestamp means the container, not the camera
    if len(gaps) == 0:
        sys.exit(
            "Every timestamp was identical. This decoder is not reporting "
            "per-frame timing, so timing must come from ffprobe instead."
        )

    mean_gap = float(np.mean(gaps))
    print()
    print(f"Frames measured   {len(timestamps)}")
    print(f"Mean gap          {mean_gap * 1000:.4f} ms")
    print(f"Median gap        {statistics.median(gaps) * 1000:.4f} ms")
    print(f"Min / max gap     {gaps.min() * 1000:.4f} / {gaps.max() * 1000:.4f} ms")
    print(f"Implied rate      {1 / mean_gap:.2f} fps")
    print()

    implied = 1 / mean_gap
    for expected, label in ((240.0, "1080p/240"), (120.0, "4K/120")):
        ntsc = expected / 1.001
        if abs(implied - ntsc) < expected * 0.02:
            print(
                f"MATCHES {label}: {implied:.2f} fps against an expected "
                f"{ntsc:.2f} ({expected:.0f} / 1.001). Timing is intact."
            )
            break
    else:
        print(
            f"WARNING: {implied:.2f} fps matches neither 240 nor 120 "
            "(NTSC-derived 239.76 / 119.88)."
        )
        if 25 < implied < 35:
            print(
                "  Roughly 30 fps means this clip has been retimed -- the "
                "signature of a trip through Photos. Every velocity derived "
                "from it would be eight times too slow. Re-copy the original "
                "from the phone via Finder, not via Photos."
            )


# --- sheet -----------------------------------------------------------------

def run_sheet(args) -> None:
    """One image of evenly spaced frames, to find the kick in a long clip.

    A 5.7 second clip at 240 fps is about 1,361 frames, and the part that
    matters is perhaps 60 of them. Scrubbing PNGs one by one to find contact
    is slow; one sheet answers it at a glance.
    """
    capture = open_clip(args.video, args.auto_rotate)
    info = describe(capture, args.video, args.auto_rotate)
    print_description(info)

    total = info["frame_count"]
    if total <= 0:
        sys.exit("The file reports no frames.")

    wanted = sorted(set(
        int(round(i * (total - 1) / (args.count - 1)))
        for i in range(args.count)
    )) if args.count > 1 else [0]

    columns = args.columns
    rows = (len(wanted) + columns - 1) // columns
    cell_width = args.cell
    cell_height = int(cell_width * info["height"] / info["width"])

    sheet = np.zeros((rows * cell_height, columns * cell_width, 3), dtype=np.uint8)
    collected = 0

    for index, timestamp, image in frames(capture):
        if index not in wanted:
            continue

        thumb = cv2.resize(image, (cell_width, cell_height),
                           interpolation=cv2.INTER_AREA)
        # The frame number is the point of the sheet -- it is what you pass
        # to extract once you have found the kick.
        cv2.putText(thumb, f"{index}  {timestamp:.3f}s", (6, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(thumb, f"{index}  {timestamp:.3f}s", (6, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)

        slot = wanted.index(index)
        row, column = divmod(slot, columns)
        sheet[row * cell_height:(row + 1) * cell_height,
              column * cell_width:(column + 1) * cell_width] = thumb

        collected += 1
        if collected == len(wanted):
            break

    capture.release()

    args.out.mkdir(parents=True, exist_ok=True)
    destination = args.out / f"{args.video.stem}-sheet.png"
    cv2.imwrite(str(destination), sheet)
    print(f"Wrote {destination}  ({collected} frames, {columns} x {rows})")
    print()
    print("Find the kick, note the frame number, then extract around it:")
    print(f"  python3 tools/extract_frames.py extract {args.video} "
          "--start FRAME --end FRAME")


# --- extract ---------------------------------------------------------------

def run_extract(args) -> None:
    """Write individual frames as PNGs.

    PNG rather than JPEG on purpose: JPEG compression artefacts around a
    small, blurred, fast-moving ball are exactly the detail being judged.
    """
    capture = open_clip(args.video, args.auto_rotate)
    info = describe(capture, args.video, args.auto_rotate)
    print_description(info)

    args.out.mkdir(parents=True, exist_ok=True)
    written = 0

    for index, timestamp, image in frames(capture, args.start, args.end):
        if (index - args.start) % args.step:
            continue

        destination = args.out / f"{args.video.stem}-f{index:05d}.png"
        cv2.imwrite(str(destination), image)
        written += 1

        if args.limit and written >= args.limit:
            print(f"Stopped at the {args.limit}-frame limit.")
            break

    capture.release()
    print(f"Wrote {written} frames to {args.out}/")
    if written:
        print()
        print("Open a few and look for: how many pixels across the ball is, "
              "whether it is a disc or a streak, and whether it stands out "
              "from the background by brightness or by colour.")


# --- Command line ----------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect GoalKick footage before writing tracking code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Typical first session:\n"
            "  python3 tools/extract_frames.py probe  clip.mov\n"
            "  python3 tools/extract_frames.py sheet  clip.mov\n"
            "  python3 tools/extract_frames.py extract clip.mov "
            "--start 400 --end 460\n"
        ),
    )
    parser.add_argument(
        "--raw-orientation", dest="auto_rotate", action="store_false",
        help="show frames as stored, ignoring the clip's rotation metadata",
    )
    parser.set_defaults(auto_rotate=True)

    subparsers = parser.add_subparsers(dest="mode", required=True)

    probe = subparsers.add_parser("probe", help="report contents and real frame timing")
    probe.add_argument("video", type=Path)
    probe.add_argument("--sample", type=int, default=300,
                       help="frames to measure timing over (default 300)")
    probe.set_defaults(func=run_probe)

    sheet = subparsers.add_parser("sheet", help="contact sheet, to find the kick")
    sheet.add_argument("video", type=Path)
    sheet.add_argument("--out", type=Path, default=Path("tools/frames"))
    sheet.add_argument("--count", type=int, default=48,
                       help="frames on the sheet (default 48)")
    sheet.add_argument("--columns", type=int, default=8)
    sheet.add_argument("--cell", type=int, default=320,
                       help="thumbnail width in pixels (default 320)")
    sheet.set_defaults(func=run_sheet)

    extract = subparsers.add_parser("extract", help="write frames as PNGs")
    extract.add_argument("video", type=Path)
    extract.add_argument("--out", type=Path, default=Path("tools/frames"))
    extract.add_argument("--start", type=int, default=0)
    extract.add_argument("--end", type=int, default=None)
    extract.add_argument("--step", type=int, default=1,
                         help="keep every Nth frame (default 1, every frame)")
    extract.add_argument("--limit", type=int, default=200,
                         help="stop after this many frames (default 200); 0 for no limit")
    extract.set_defaults(func=run_extract)

    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
