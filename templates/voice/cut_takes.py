# /// script
# requires-python = "==3.12.*"
# dependencies = ["numpy==2.5.3", "soundfile==0.14.0", "mlx-whisper==0.4.3"]
# ///
"""Cut each take into its sentences, in the pause between Whisper's sentence-end and sentence-start words, and write <out>/<id>.wav.

Whisper only says roughly where a pause is. The cut goes in the middle of the whole quiet stretch that is longest near
those word times, judged on loudness averaged over 50 ms against the take's own floor, so one near-silent frame cannot
pass for a pause.
A cut with no quiet stretch of at least MIN_GAP falls back to the quietest averaged point and is logged as unclean.

Nothing is trimmed and nothing is faded: each sentence runs from cut to cut, the first from the take's start, so the
written sentences rejoin into the take exactly. Add a pause only at a clean cut.

SENTENCES is an ordered JSON list of the film's sentences, each with at least "id", "scene" and "text".
A take is named for the scene it covers (S01.wav) or its first and last scene (S01-S06.wav).
With --throwaway, each take ends with that extra sentence, which is cut off and not written.
It logs one JSON line per cut, one per sentence written, and one per take with its floor and unclean cuts."""
import argparse, difflib, json, re
from pathlib import Path

import mlx_whisper
import numpy as np
import soundfile as sf

WHISPER = "mlx-community/whisper-large-v3-turbo"
WINDOW = 0.01  # loudness frame, seconds
SMOOTH = 5  # frames in the moving average of power
FLOOR_PCT = 5  # the take's noise floor is this percentile of smoothed loudness
QUIET_DB = 12  # quiet means within this many dB of the floor
MIN_GAP = 0.06  # a stop consonant's closure lasts about this long, so shorter dips are never cut
BEFORE = 0.1
AFTER = 0.4

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("takes", nargs="+", type=Path)
parser.add_argument("--sentences", required=True, type=Path, metavar="FILE.json")
parser.add_argument("--out", required=True, type=Path)
parser.add_argument("--throwaway", metavar="TEXT", help="the sentence voiced after each take's last one")
args = parser.parse_args()
segments = json.loads(args.sentences.read_text())
order = list(dict.fromkeys(s["scene"] for s in segments))
args.out.mkdir(parents=True, exist_ok=True)
letters = lambda text: re.sub(r"[^a-z0-9]", "", text.lower())

for path in args.takes:
    first_scene, last_scene = (path.stem.split("-") * 2)[:2]
    covered = order[order.index(first_scene):order.index(last_scene) + 1]
    sents = [s for s in segments if s["scene"] in covered] + ([{"id": None, "text": args.throwaway}] if args.throwaway else [])
    y, rate = sf.read(path, dtype="float32")
    # A file path makes Whisper resample to 16 kHz, so its timestamps are in seconds of this file.
    words = [w for seg in mlx_whisper.transcribe(str(path), path_or_hf_repo=WHISPER, language="en", word_timestamps=True,
                                                  condition_on_previous_text=False)["segments"] for w in seg["words"]]
    ref, ref_sent = "", []
    for k, s in enumerate(sents):
        ref += letters(s["text"]); ref_sent += [k] * len(letters(s["text"]))
    hyp, hyp_word = "", []
    for i, w in enumerate(words):
        hyp += letters(w["word"]); hyp_word += [i] * len(letters(w["word"]))
    # Letter alignment survives Whisper joining "A-M-S" into "AMS"; numerals it writes as digits stay unmatched.
    match = {}
    for a, b, n in difflib.SequenceMatcher(None, ref, hyp, autojunk=False).get_matching_blocks():
        match.update({a + d: hyp_word[b + d] for d in range(n)})
    n = int(rate * WINDOW)
    power = np.mean(y[: len(y) // n * n].reshape(-1, n) ** 2, axis=1)
    # Average power, not dB, so one near-silent frame cannot pass for a quiet stretch.
    smooth = 10 * np.log10(np.convolve(power, np.ones(SMOOTH) / SMOOTH, mode="same") + 1e-18)
    # Some voices emit exact digital silence, which would drag the floor to -180 dB.
    floor = float(np.percentile(smooth[power > 0], FLOOR_PCT))
    quiet = smooth <= floor + QUIET_DB
    edges, log = [0], []
    for k in range(len(sents) - 1):
        last = max(i for i in match if ref_sent[i] == k)
        first = min(i for i in match if ref_sent[i] == k + 1)
        end, start = words[match[last]]["end"], words[match[first]]["start"]
        # Whisper's word times often run early, and the pause can sit up to half a second after them.
        lo = max(0, int((min(end, start) - BEFORE) / WINDOW))
        hi = min(len(smooth), int((max(end, start) + AFTER) / WINDOW) + 1)
        runs, i = [], lo
        while i < hi:
            j = i
            while j < hi and quiet[j]: j += 1
            if j - i >= MIN_GAP / WINDOW: runs.append((j - i, i))
            i = max(j, i + 1)
        if runs:
            length, at = max(runs)
            # Whisper can clip the window short of the pause, so grow the run to the whole pause before taking its middle.
            a, b = at, at + length
            while a > 0 and quiet[a - 1]: a -= 1
            while b < len(quiet) and quiet[b]: b += 1
            cut, gap = (a + b) // 2, (b - a) * WINDOW
        else:
            cut, gap = lo + int(np.argmin(smooth[lo:hi])), 0.0
        edges.append(cut * n + n // 2)
        log.append({"take": path.stem, "after": sents[k]["id"], "word_end": round(end, 2), "next_start": round(start, 2),
                    "cut_s": round(edges[-1] / rate, 3), "gap_s": round(gap, 2), "clean": bool(runs),
                    "smooth_db": round(float(smooth[cut]), 1)})
    edges.append(len(y))
    for k, s in enumerate(sents):
        if s["id"]:
            sf.write(args.out / f"{s['id']}.wav", y[edges[k]:edges[k + 1]], rate, subtype="PCM_16")
            log.append({"take": path.stem, "id": s["id"], "seconds": round((edges[k + 1] - edges[k]) / rate, 3)})
    print(json.dumps({"take": path.stem, "floor_db": round(floor, 1), "quiet_below_db": round(floor + QUIET_DB, 1),
                      "unclean_cuts": [r["after"] for r in log if r.get("clean") is False]}), flush=True)
    for r in log: print(json.dumps(r), flush=True)
