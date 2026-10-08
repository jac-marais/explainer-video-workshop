# /// script
# requires-python = "==3.12.*"
# dependencies = []
# ///
"""Group consecutive scenes into TTS runs of MIN to MAX seconds, as evenly as possible, and print the best groupings.

SRC is a directory of per-scene voice.py receipts (S01.json, S02.json, ...). Each file's stem is the scene id and its duration_s is the scene's length."""
import argparse, json, statistics
from pathlib import Path

MIN_S = 60
MAX_S = 120
TARGET_S = 60
SHOW = 5

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("src", type=Path, help="directory of per-scene receipts (*.json)")
parser.add_argument("--seconds", nargs="*", default=[], metavar="ID=S", help="override scene lengths, e.g. S01=22.7 S02=37.7")
parser.add_argument("--speed", type=float, default=1.0, help="multiplies every scene length (a long run reads faster than separate takes)")
parser.add_argument("--min", type=float, default=MIN_S, dest="lo")
parser.add_argument("--max", type=float, default=MAX_S, dest="hi")
parser.add_argument("--target", type=float, default=TARGET_S, help="breaks ties between equally even groupings")
args = parser.parse_args()

scenes = {p.stem: json.loads(p.read_text())["duration_s"] for p in sorted(args.src.glob("*.json"))}
scenes.update({k: float(v) for k, v in (item.split("=") for item in args.seconds)})
scenes = dict(sorted(scenes.items()))
ids = list(scenes)
secs = [scenes[i] * args.speed for i in ids]
print(f"speed {args.speed} | min {args.lo} max {args.hi} target {args.target}")
print("scenes: " + " ".join(f"{i}={scenes[i]:g}" for i in ids) + f" (total {sum(secs):.1f} s at this speed)")
for i, s in zip(ids, secs):
    if s > args.hi:
        print(f"WARNING {i} is {s:.1f} s, over MAX: it needs splitting inside the scene")

def groupings():
    for mask in range(2 ** (len(ids) - 1)):
        runs, start = [], 0
        for k in range(1, len(ids) + 1):
            if k == len(ids) or mask >> (k - 1) & 1:
                runs.append((start, k))
                start = k
        yield runs

def score(runs):
    lens = [sum(secs[a:b]) for a, b in runs]
    violation = sum(max(0, args.lo - n) + max(0, n - args.hi) for n in lens)
    return violation, statistics.pstdev(lens), sum(abs(n - args.target) for n in lens), lens

def show(runs, violation, spread, distance, lens):
    name = lambda a, b: ids[a] if b - a == 1 else f"{ids[a]}-{ids[b - 1]}"
    print(" | ".join(f"{name(a, b)} {n:.1f}" for (a, b), n in zip(runs, lens)) + f"  || violation {violation:.1f} s, spread {spread:.1f} s, distance {distance:.1f} s")

ranked = sorted(((r, *score(r)) for r in groupings()), key=lambda t: (round(t[1], 6), t[2], t[3]))
valid = [t for t in ranked if t[1] < 1e-6]
if valid:
    print(f"{len(valid)} grouping(s) obey both rules; best {min(SHOW, len(valid))}:")
else:
    print(f"NO GROUPING FITS {args.lo:g}-{args.hi:g} s. Least-violating {SHOW}:")
for t in (valid or ranked)[:SHOW]:
    show(*t)
