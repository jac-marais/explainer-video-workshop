"""Cut each take into its sentences using pauses near Whisper word times, and write <out>/<id>.wav.

Whisper only says roughly where pauses are. Quiet is judged on loudness averaged over 50 ms against the take's own
floor, so one near-silent frame cannot pass for a pause.
Matching uses shared Unicode letters, marks and numbers; --language selects Whisper (default en).
Unmatched sentences use nearest matched words on each side (or take edges), and their cuts are unclean.
Consecutive boundaries with equal bounds share one search window and take its longest distinct quiet stretches, one per
boundary in time order, each grown to its whole pause and cut at the middle. With too few stretches, the remaining cuts
bisect the widest interval left in the window, and every cut in a shared window is unclean.
A lone boundary without a quiet stretch of at least MIN_GAP cuts at the quietest averaged point and is logged as unclean.
Cuts must strictly increase, or the take stops with its sentence ids before any of its sentence WAVs are written, and
the cutter exits with UNCUTTABLE_EXIT.

Nothing is trimmed and nothing is faded: each sentence runs from cut to cut, the first from the take's start, so the
written sentences rejoin into the take exactly. Film assembly follows methods/voice-explainer-video.md, including its
edge silence exception.

SENTENCES is an ordered JSON list of the film's sentences, each with at least "id", "scene" and "text".
A take is named for the scene it covers (S01.wav) or its first and last scene (S01-S06.wav).
With --throwaway, each take ends with that extra sentence, which is cut off and not written.
It logs one JSON line per cut, one per sentence written, and one per take with its floor and unclean cuts."""
import argparse, difflib, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/audio"))
from text_tokens import norm as letters

WHISPER = "mlx-community/whisper-large-v3-turbo"
WINDOW = 0.01  # loudness frame, seconds
SMOOTH = 5  # frames in the moving average of power
FLOOR_PCT = 5  # the take's noise floor is this percentile of smoothed loudness
QUIET_DB = 12  # quiet means within this many dB of the floor
MIN_GAP = 0.06  # a stop consonant's closure lasts about this long, so shorter dips are never cut
BEFORE = 0.1
AFTER = 0.4
UNCUTTABLE_EXIT = 3  # a take whose cuts cannot strictly increase, which narrate_film.py voices again

def uncuttable(message):
    print(message, file=sys.stderr)
    raise SystemExit(UNCUTTABLE_EXIT)


def sentence_bounds(sents, words, duration):
    """Return (left end, right start, matched) for each sentence boundary.

    Missing matches use the nearest matched words on either side, or the take
    edge when that side has none. Such bounds always mark the cut unclean.
    """
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
    bounds = []
    for k in range(len(sents) - 1):
        left = [i for i in match if ref_sent[i] <= k]
        right = [i for i in match if ref_sent[i] > k]
        last, first = max(left, default=None), min(right, default=None)
        end = words[match[last]]["end"] if last is not None else 0.0
        start = words[match[first]]["start"] if first is not None else duration
        matched = (last is not None and first is not None and
                   ref_sent[last] == k and ref_sent[first] == k + 1)
        bounds.append((end, start, matched))
    return bounds


def main():
    import mlx_whisper
    import numpy as np
    import soundfile as sf

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("takes", nargs="+", type=Path)
    parser.add_argument("--sentences", required=True, type=Path, metavar="FILE.json")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--throwaway", metavar="TEXT", help="the sentence voiced after each take's last one")
    parser.add_argument("--language", default="en", help="Whisper language code (default: en)")
    args = parser.parse_args()
    segments = json.loads(args.sentences.read_text())
    order = list(dict.fromkeys(s["scene"] for s in segments))
    args.out.mkdir(parents=True, exist_ok=True)

    for path in args.takes:
        first_scene, last_scene = (path.stem.split("-") * 2)[:2]
        covered = order[order.index(first_scene):order.index(last_scene) + 1]
        sents = [s for s in segments if s["scene"] in covered] + ([{"id": None, "text": args.throwaway}] if args.throwaway else [])
        y, rate = sf.read(path, dtype="float32")
        invalid = f"{path.name}: cannot place strictly increasing cuts for sentences " + ", ".join(s["id"] or "<throwaway>" for s in sents)
        # A file path makes Whisper resample to 16 kHz, so its timestamps are in seconds of this file.
        words = [w for seg in mlx_whisper.transcribe(str(path), path_or_hf_repo=WHISPER, language=args.language, word_timestamps=True,
                                                      condition_on_previous_text=False)["segments"] for w in seg["words"]]
        bounds = sentence_bounds(sents, words, len(y) / rate)
        n = int(rate * WINDOW)
        power = np.mean(y[: len(y) // n * n].reshape(-1, n) ** 2, axis=1)
        # Average power, not dB, so one near-silent frame cannot pass for a quiet stretch.
        smooth = 10 * np.log10(np.convolve(power, np.ones(SMOOTH) / SMOOTH, mode="same") + 1e-18)
        # Some voices emit exact digital silence, which would drag the floor to -180 dB.
        floor = float(np.percentile(smooth[power > 0], FLOOR_PCT))
        quiet = smooth <= floor + QUIET_DB
        edges, log = [0], []
        k = 0
        while k < len(bounds):
            end, start, matched = bounds[k]
            stop = k + 1
            while stop < len(bounds) and bounds[stop][:2] == (end, start): stop += 1
            count = stop - k
            # Whisper's word times often run early, and the pause can sit up to half a second after them.
            lo = max(0, int((min(end, start) - BEFORE) / WINDOW))
            hi = min(len(smooth), int((max(end, start) + AFTER) / WINDOW) + 1)
            if lo >= hi:
                uncuttable(invalid)
            runs, i = [], lo
            while i < hi:
                j = i
                while j < hi and quiet[j]: j += 1
                if j - i >= MIN_GAP / WINDOW: runs.append((j - i, i))
                i = max(j, i + 1)
            cuts = {}
            for length, at in sorted(runs, reverse=True)[:count]:
                # Whisper can clip the window short of the pause, so grow the run to the whole pause before taking its middle.
                a, b = at, at + length
                while a > 0 and quiet[a - 1]: a -= 1
                while b < len(quiet) and quiet[b]: b += 1
                cut, gap = (a + b) // 2, (b - a) * WINDOW
                cuts[cut * n + n // 2] = gap
            if not runs and count == 1:
                cut = lo + int(np.argmin(smooth[lo:hi]))
                cuts[cut * n + n // 2] = 0.0
            while len(cuts) < count:
                anchors = sorted({edges[-1], *cuts, len(y)})
                a, b = max(((max(a, lo * n - 1), min(b, hi * n)) for a, b in zip(anchors, anchors[1:])),
                           key=lambda pair: pair[1] - pair[0])
                if b - a <= 1:
                    uncuttable(invalid)
                cuts[(a + b) // 2] = 0.0
            for edge, gap in sorted(cuts.items()):
                edges.append(edge)
                log.append({"take": path.stem, "after": sents[k]["id"], "word_end": round(end, 2), "next_start": round(start, 2),
                            "cut_s": round(edge / rate, 3), "gap_s": round(gap, 2), "clean": gap > 0 and matched and count == 1,
                            "smooth_db": round(float(smooth[edge // n]), 1)})
                k += 1
        edges.append(len(y))
        if any(a >= b for a, b in zip(edges, edges[1:])):
            uncuttable(invalid)
        for k, s in enumerate(sents):
            if s["id"]:
                sf.write(args.out / f"{s['id']}.wav", y[edges[k]:edges[k + 1]], rate, subtype="PCM_16")
                log.append({"take": path.stem, "id": s["id"], "seconds": round((edges[k + 1] - edges[k]) / rate, 3)})
        print(json.dumps({"take": path.stem, "floor_db": round(floor, 1), "quiet_below_db": round(floor + QUIET_DB, 1),
                          "unclean_cuts": [r["after"] for r in log if r.get("clean") is False]}), flush=True)
        for r in log: print(json.dumps(r), flush=True)


if __name__ == "__main__":
    main()
