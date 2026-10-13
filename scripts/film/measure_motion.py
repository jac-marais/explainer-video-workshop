#!/usr/bin/env python3
"""Measure three motion gates on an MP4; exit 0 on pass, 1 on metric failure, 2 on input failure."""
import argparse
import math
import subprocess
import sys

FPS, PIXELS = 5, 160 * 90


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("film")
    ap.add_argument("--pixel-delta", type=float, default=12, help="changed pixel: absolute grayscale delta > this (default: 12)")
    ap.add_argument("--near-still-pct", type=float, default=1, help="near-still: changed pixels < this percent (default: 1)")
    ap.add_argument("--max-still-run", type=float, default=3, help="fail consecutive near-still runs >= this many seconds (default: 3)")
    ap.add_argument("--big-pct", type=float, default=20, help="big: 2-second endpoint change >= this percent (default: 20)")
    ap.add_argument("--min-big-share", type=float, default=15, help="minimum percent of complete 2-second windows that are big (default: 15)")
    ap.add_argument("--cut-pct", type=float, default=40, help="cut/layout change: adjacent samples change >= this percent (default: 40)")
    ap.add_argument("--max-cut-gap", type=float, default=8, help="maximum seconds between cuts, including start and end (default: 8)")
    a = ap.parse_args()
    try:
        probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                "stream=duration", "-of", "default=nw=1:nk=1", a.film],
                               capture_output=True, check=True)
        duration = float(probe.stdout)
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError("invalid video stream duration")
        decoded = subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", a.film, "-map", "0:v:0", "-an",
                                  "-vf", "fps=5:start_time=0,scale=160:90,format=gray", "-fps_mode", "passthrough",
                                  "-f", "rawvideo", "-"], capture_output=True, check=True)
        raw = decoded.stdout
        frames = [raw[i:i + PIXELS] for i in range(0, len(raw), PIXELS)]
        if len(raw) % PIXELS or len(frames) < 16 or len(frames) < math.floor(duration * FPS + 1e-6):
            raise ValueError("undersized or truncated samples; need at least 15 steps and full video coverage")
    except (OSError, ValueError, subprocess.CalledProcessError) as e:
        print(f"motion input error: {e}", file=sys.stderr)
        return 2

    def changed(left, right):
        return 100 * sum(abs(p - q) > a.pixel_delta for p, q in zip(left, right)) / PIXELS

    run_steps, longest, cuts = 0, 0.0, [0.0]
    for i in range(1, len(frames)):
        pct = changed(frames[i - 1], frames[i])
        run_steps = run_steps + 1 if pct < a.near_still_pct else 0
        longest = max(longest, run_steps / FPS)
        if pct >= a.cut_pct:
            cuts.append(i / FPS)
    if run_steps:
        longest = max(longest, run_steps / FPS + max(0, duration - (len(frames) - 1) / FPS))
    cuts.append(duration)
    gap = max(right - left for left, right in zip(cuts, cuts[1:]))
    endpoints = [changed(frames[i], frames[i + 10]) for i in range(0, len(frames) - 10, 10)]
    big = sum(pct >= a.big_pct for pct in endpoints)
    share = 100 * big / len(endpoints)
    rows = [
        ("near-still run", f"{longest:.2f}s", f"< {a.max_still_run:g}s", longest < a.max_still_run),
        ("big endpoints", f"{big}/{len(endpoints)} ({share:.2f}%)", f">= {a.min_big_share:g}%", share >= a.min_big_share),
        ("cut/layout gap", f"{gap:.2f}s", f"<= {a.max_cut_gap:g}s", gap <= a.max_cut_gap + 1e-9),
    ]
    print(f"{'metric':<18} {'value':<20} {'limit':<12} result")
    for name, value, limit, passed in rows:
        print(f"{name:<18} {value:<20} {limit:<12} {'PASS' if passed else 'FAIL'}")
    return 0 if all(row[3] for row in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
