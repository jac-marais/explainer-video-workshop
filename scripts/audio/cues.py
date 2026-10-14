#!/usr/bin/env python3
"""Time every quoted or sentence visual cue in a script against the measured words, so a new voice re-times the film by rebuild.

  cues.py SCRIPT.md WORDS.json TIMING.json --out cues.json [--aliases ALIASES.json] [--strict]

SCRIPT.md has a `## Scene N` section per scene with a `**Visual**` part. Each quoted beat there, written `On "words"` or
`**"words"**`, must be words the narrator says. The cue is matched to those consecutive measured words inside scene
sN's window in TIMING.json (padded 0.6 s), and cues.json gets the first word's start and the last word's end, in seconds.
Sentence cues such as `On s03-02` or `On s03-02+0.4` use timing.json sentence bounds directly.
The suffix is a fraction from 0 to 1; missing sentences always fail. --key-script checks sentence counts.
A quoted cue that matches nothing gets null times, is listed on stderr, and fails the run under --strict.

Tokens compare after NFKC/casefold, keeping Unicode letters, marks and numbers, so `A-C-P` and `ACP` are the same word.
ALIASES.json maps such a normalized word to the words that stand for it on the other side: {"2036": ["twenty", "thirtysix"]}.
Han/Kana split by character; other scripts split on whitespace.
It applies to both script and Whisper, so use it for spoken forms and for words that Whisper spells differently.
"""
import argparse, json, re, sys
from pathlib import Path
from text_tokens import norm, normalized_tokens, timed_tokens, sentences

PAD = 0.6  # seconds; a cue may start a little outside its scene window because Whisper times are rough
SCENE = re.compile(r"## Scene (\d+):.*?(?=\n## |\n---\n|\Z)", re.S)
SENTENCE_NAME = r"s\d{2,}-\d{2,}(?:\+[^\s`*\",:;]+)?"
CUE = re.compile(r'(?:On (?:the )?|\*\*)(?:"([^"]+)"|`?(' + SENTENCE_NAME + r'))|`(' + SENTENCE_NAME + r')`')
VISUAL = re.compile(r"\*\*Visual\.?\*\*")


def cue_text(match):
    return next(group for group in match.groups() if group is not None)


def cue_names(visual):
    return [cue_text(match) for match in CUE.finditer(visual)]


def sentence_ref(cue):
    if not re.match(r"^s\d+-\d+", cue):
        return None
    match = re.fullmatch(r"(s\d{2,}-\d{2,})(?:\+(0(?:\.\d+)?|1(?:\.0+)?))?", cue)
    if not match:
        raise ValueError(f"invalid sentence cue: {cue}; use s03-02 or s03-02+0.4 with a fraction from 0 to 1")
    return match[1], float(match[2] or 0)


def sentence_time(cue, scene, rows):
    ref = sentence_ref(cue)
    if ref is None:
        return None
    name, fraction = ref
    row = next((row for row in rows if row["id"] == name and row.get("scene_id", name.rsplit("-", 1)[0]) == scene), None)
    if row is None:
        raise ValueError(f"{scene}: missing sentence {name} for cue {cue}")
    start, end = float(row["start"]), float(row["end"])
    if not 0 <= start <= end < float("inf"):
        raise ValueError(f"{name}: invalid sentence timing")
    return round(start + fraction * (end - start), 3), round(end, 3)


def validate_translation(script, key_script):
    def counts(path):
        result = {}
        for match in SCENE.finditer(path.read_text()):
            body = re.split(r"\*\*Narration\.?\*\*", match[0], maxsplit=1)
            if len(body) != 2:
                raise ValueError(f"scene {match[1]}: no **Narration** part")
            result[int(match[1])] = len(sentences(VISUAL.split(body[1], 1)[0]))
        return result
    actual, expected = counts(script), counts(key_script)
    for num in sorted(actual.keys() | expected.keys()):
        if actual.get(num) != expected.get(num):
            raise ValueError(f"scene {num}: {actual.get(num, 0)} sentences, but the key script has {expected.get(num, 0)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", type=Path)
    ap.add_argument("words", type=Path, help="words.json from narrate_film.py")
    ap.add_argument("timing", type=Path, help="timing.json from narrate_film.py")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--aliases", type=Path, help="JSON map from a normalized word to the words that stand for it")
    ap.add_argument("--key-script", type=Path, help="validate translated sentence counts")
    ap.add_argument("--strict", action="store_true", help="exit 1 when any cue is unmatched")
    args = ap.parse_args()

    if args.key_script:
        validate_translation(args.script, args.key_script)
    aliases = {}
    if args.aliases:
        aliases = {norm(k): [t for p in v for t in normalized_tokens(p)] for k, v in json.loads(args.aliases.read_text()).items()}
    expand = lambda token: aliases.get(token, [token])
    timing = json.loads(args.timing.read_text())
    scenes = {sc["id"]: sc for sc in timing["scenes"]}
    seq = [(part, w["start"], w["end"]) for w in timed_tokens(json.loads(args.words.read_text())["words"]) for part in expand(norm(w["text"]))]

    rows = []
    text = args.script.read_text()
    for m in SCENE.finditer(text):
        sid = f"s{int(m.group(1)):02d}"
        if sid not in scenes:
            raise SystemExit(f"{sid} is in the script but not in {args.timing}")
        lo, hi = scenes[sid]["start"] - PAD, scenes[sid]["end"] + PAD
        visual = VISUAL.split(m.group(0), 1)[-1]
        for quote in cue_names(visual):
            measured = sentence_time(quote, sid, timing.get("sentences", []))
            if measured is not None:
                rows.append({"scene": sid, "cue": quote, "start": measured[0], "end": measured[1]})
                continue
            toks = [p for t in normalized_tokens(quote) for p in expand(t)]
            hit = None
            for i in range(len(seq) - len(toks) + 1 if toks else 0):
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
    try:
        main()
    except ValueError as exc:
        sys.exit(str(exc))
