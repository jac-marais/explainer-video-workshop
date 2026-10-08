#!/usr/bin/env python3
"""Time every quoted visual cue in a script against the measured words, so a new voice re-times the film by rebuild.

  cues.py SCRIPT.md WORDS.json TIMING.json --out cues.json [--aliases ALIASES.json] [--strict]

SCRIPT.md has a `## Scene N` section per scene with a `**Visual**` part. Each quoted beat there, written `On "words"` or
`**"words"**`, must be words the narrator says. The cue is matched to those consecutive measured words inside scene
sN's window in TIMING.json (padded 0.6 s), and cues.json gets the first word's start and the last word's end, in seconds.
A cue that matches nothing gets null times, is listed on stderr, and fails the run under --strict.

Words compare after lowercasing and dropping everything but letters and digits, so `A-C-P` and `ACP` are the same word.
ALIASES.json maps such a normalized word to the words that stand for it on the other side: {"2036": ["twenty", "thirtysix"]}.
It applies to both script and Whisper, so use it for spoken forms and for words that Whisper spells differently.
"""
import argparse, json, re, sys
from pathlib import Path

PAD = 0.6  # seconds; a cue may start a little outside its scene window because Whisper times are rough


def norm(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("words", type=Path, help="words.json from narrate_film.py")
    ap.add_argument("timing", type=Path, help="timing.json from narrate_film.py")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--aliases", type=Path, help="JSON map from a normalized word to the words that stand for it")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any cue is unmatched")
    args = ap.parse_args()

    aliases = {}
    if args.aliases:
        aliases = {norm(k): [norm(p) for p in v] for k, v in json.loads(args.aliases.read_text()).items()}
    expand = lambda token: aliases.get(token, [token])
    timing = json.loads(args.timing.read_text())
    scenes = {sc["id"]: sc for sc in timing["scenes"]}
    seq = [(part, w["start"], w["end"]) for w in json.loads(args.words.read_text())["words"] for part in expand(norm(w["text"]))]

    rows = []
    text = args.script.read_text()
    for m in re.finditer(r"## Scene (\d+):.*?(?=\n## |\n---\n|\Z)", text, re.S):
        sid = f"s{int(m.group(1)):02d}"
        if sid not in scenes:
            raise SystemExit(f"{sid} is in the script but not in {args.timing}")
        lo, hi = scenes[sid]["start"] - PAD, scenes[sid]["end"] + PAD
        visual = m.group(0).split("**Visual**", 1)[-1]
        for quote in re.findall(r'(?:On (?:the )?|\*\*)"([^"]+)"', visual):
            toks = [p for t in quote.split() if norm(t) for p in expand(norm(t))]
            hit = None
            for i in range(len(seq) - len(toks) + 1):
                if lo <= seq[i][1] <= hi and all(seq[i + k][0] == toks[k] for k in range(len(toks))):
                    hit = (seq[i][1], seq[i + len(toks) - 1][2])
                    break
            rows.append({"scene": sid, "cue": quote, "start": hit and round(hit[0], 3), "end": hit and round(hit[1], 3)})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(rows, indent=1, ensure_ascii=False) + "\n")
    misses = [r for r in rows if r["start"] is None]
    for r in rows:
        print(r["scene"], r["start"], r["end"], r["cue"])
    for r in misses:
        print(f'unmatched: {r["scene"]} "{r["cue"]}"', file=sys.stderr)
    print(len(rows), "cues,", len(misses), "unmatched")
    if misses and args.strict:
        sys.exit(1)


if __name__ == "__main__":
    main()
