# /// script
# requires-python = "==3.12.*"
# dependencies = ["numpy==2.5.3", "soundfile==0.14.0", "mlx-whisper==0.4.3"]
# ///
"""Cut each take into its sentences, in the pause between Whisper's sentence-end and sentence-start words, and write <out>/<id>.wav.

Each sentence runs from cut to cut, so the pauses the voice spoke stay whole. Only the take's own start and end are trimmed, keeping MARGIN seconds before its first speech and after its last.

SENTENCES is an ordered JSON list of the film's sentences, each with at least "id", "scene" and "text".
A take is named for the scene it covers (S01.wav) or its first and last scene (S01-S06.wav).
With --throwaway, each take ends with that extra sentence, which is cut off and not written.
It logs one JSON line per cut and one per take with the seconds trimmed from each end. smooth_db is the smoothed level at the chosen low point, because a single frame can read quiet right next to a word onset."""
import argparse, difflib, json, re
from pathlib import Path

import mlx_whisper
import numpy as np
import soundfile as sf

WHISPER = "mlx-community/whisper-large-v3-turbo"
WINDOW = 0.01
SMOOTH = 8
BEFORE = 0.1
AFTER = 0.4
REFINE = 4
FLOOR_DB = -50
MARGIN = 0.2

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
    w = int(rate * WINDOW)
    rms = np.sqrt(np.mean(y[: len(y) // w * w].reshape(-1, w) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-9)
    # A real pause outlasts the silent closure inside a final consonant, so the smoothed minimum finds the pause.
    smooth = np.convolve(rms, np.ones(SMOOTH) / SMOOTH, mode="same")
    loud = np.where(20 * np.log10(smooth + 1e-9) > FLOOR_DB)[0]
    head = max(0, int((loud[0] * WINDOW - MARGIN) * rate))
    tail = min(len(y), int(((loud[-1] + 1) * WINDOW + MARGIN) * rate))
    print(json.dumps({"take": path.stem, "trim_head_s": round(head / rate, 3), "trim_tail_s": round((len(y) - tail) / rate, 3)}), flush=True)
    edges = [head]
    for k in range(len(sents) - 1):
        last = max(i for i in match if ref_sent[i] == k)
        first = min(i for i in match if ref_sent[i] == k + 1)
        end, start = words[match[last]]["end"], words[match[first]]["start"]
        # Whisper's word times often run early, and the pause can sit up to half a second after them.
        lo = max(0, int((min(end, start) - BEFORE) / WINDOW))
        hi = min(len(db), int((max(end, start) + AFTER) / WINDOW) + 1)
        mid = lo + int(np.argmin(smooth[lo:hi]))
        a = max(0, mid - REFINE)
        cut = a + int(np.argmin(db[a:mid + REFINE + 1]))
        edges.append(cut * w + w // 2)
        print(json.dumps({"take": path.stem, "after": sents[k]["id"], "word_end": round(end, 2), "next_start": round(start, 2),
                          "cut_s": round(edges[-1] / rate, 3), "floor_db": round(float(db[cut]), 1),
                          "smooth_db": round(float(20 * np.log10(smooth[mid] + 1e-9)), 1)}), flush=True)
    edges.append(tail)
    for k, s in enumerate(sents):
        if s["id"]:
            sf.write(args.out / f"{s['id']}.wav", y[edges[k]:edges[k + 1]], rate, subtype="PCM_16")
