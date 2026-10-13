#!/usr/bin/env python3
"""Write a composition's data.js from a script's cues and captions, so the picture reads every time from the voice.

  build_data.py --script SCRIPT.md --project DIR --audio AUDIO_DIR [--tail S] [options]
  build_data.py --script SCRIPT.md --project DIR --estimate [--wpm 150] [--scenes N] [options]

  options: [--strings STRINGS.json] [--key-script KEY_SCRIPT.md] [--embed NAME=FILE.json ...]

--audio reads AUDIO_DIR/cues.json (from cues.py), captions.json (from captions.py) and timing.json (from narrate_film.py).
--estimate times whitespace words or Han/Kana characters evenly at --wpm, with short pauses after sentences and scenes, for a silent
preview before any voice exists; --scenes N stops after scene N. Both modes write the same shape to DIR/data.js:

  window.FILM = {source, duration, cues: {"sNN|quoted words": start seconds}, captions, strings, ...embeds}

and set the first data-duration attribute in DIR/index.html, because the renderer reads it before any script runs.
duration is the narration length plus --tail. --strings adds the on-screen text for one language. --key-script names
every cue by the cue at the same position in the same scene of another script, so a translated film keeps the cue
names its code uses; the run exits 1 when a scene's cue counts differ. --embed adds a JSON file under NAME.
The run exits 1 on a cue with no time.
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audio"))
from text_tokens import norm, tokenize, normalized_tokens, join_tokens  # noqa: E402
from cues import CUE, SCENE, VISUAL  # noqa: E402

NARRATION = re.compile(r"\*\*Narration\.?\*\*")
END = re.compile(r"[.?!。？！।]$")


def scenes(script):
    """Each scene's number, its narration as one line, and its cue quotes in order."""
    for m in SCENE.finditer(script.read_text()):
        narration, visual = VISUAL.split(NARRATION.split(m.group(0), 1)[1], 1)
        yield int(m.group(1)), " ".join(narration.split()), CUE.findall(visual)


def estimate(script, wpm, last_scene):
    """Even token timing (whitespace words or Han/Kana characters) with short pauses after sentences and scenes; planning only."""
    cues, captions, t, per_word = [], [], 0.4, 60 / wpm
    for num, text, quotes in scenes(script):
        if last_scene and num > last_scene:
            break
        sid, words, starts = f"s{num:02d}", tokenize(text), []
        for w in words:
            starts.append(t)
            t += per_word + (0.35 if END.search(w) else 0)
        ends = starts[1:] + [t]
        # A caption part breaks at a sentence end, at a comma once it has 5 words, or at 9 words.
        part, s0 = [], None
        for i, w in enumerate(words):
            s0 = starts[i] if s0 is None else s0
            part.append(w)
            last = i == len(words) - 1
            if last or END.search(w) or (w.endswith(",") and len(part) >= 5) or len(part) >= 9:
                end = starts[i] + per_word if last or END.search(w) else starts[i + 1]
                captions.append({"id": f"{sid}-{len(captions):03d}", "scene_id": sid, "start": round(s0, 3),
                                 "end": round(end, 3), "text": join_tokens(part)})
                part, s0 = [], None
        # Punctuation-only tokens are skipped on both sides, as in cues.py.
        kept = [(norm(w), i) for i, w in enumerate(words) if norm(w)]
        normed = [n for n, _ in kept]
        for q in quotes:
            toks = normalized_tokens(q)
            at = next((k for k in range(len(normed)) if normed[k:k + len(toks)] == toks), None)
            if not toks or at is None:
                sys.exit(f'{sid}: cue not in narration: "{q}"')
            first, last = kept[at][1], kept[at + len(toks) - 1][1]
            cues.append({"scene": sid, "cue": q, "start": round(starts[first], 3), "end": round(ends[last], 3)})
        t += 0.8
    return cues, captions, round(t + 1.5, 3)


def cue_keys(script, key_script):
    """Map each (scene, quote) of script to the quote at the same position in key_script."""
    keys = {num: quotes for num, _, quotes in scenes(key_script)}
    out = {}
    for num, _, quotes in scenes(script):
        if len(quotes) != len(keys.get(num, [])):
            sys.exit(f"scene {num}: {len(quotes)} cues, but the key script has {len(keys.get(num, []))}")
        out.update({(f"s{num:02d}", q): k for q, k in zip(quotes, keys[num])})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--project", type=Path, required=True, help="composition folder; data.js is written here")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audio", type=Path, help="folder with cues.json, captions.json and timing.json")
    mode.add_argument("--estimate", action="store_true", help="time the script evenly, before any voice exists")
    ap.add_argument("--wpm", type=float, default=150)
    ap.add_argument("--scenes", type=int, help="with --estimate, stop after scene N")
    ap.add_argument("--tail", type=float, default=0, help="seconds of picture after the narration ends")
    ap.add_argument("--strings", type=Path, help="on-screen text for this language")
    ap.add_argument("--key-script", type=Path, help="script whose cue quotes name the cues")
    ap.add_argument("--embed", action="append", default=[], metavar="NAME=FILE.json", help="add a JSON file under NAME")
    a = ap.parse_args()

    if a.estimate:
        cues, captions, duration = estimate(a.script, a.wpm, a.scenes)
        source = f"estimate at {a.wpm:g} WPM"
    else:
        cues = json.loads((a.audio / "cues.json").read_text())
        captions = json.loads((a.audio / "captions.json").read_text())
        duration = json.loads((a.audio / "timing.json").read_text())["duration"]
        source = str(a.audio)
    missing = [c["cue"] for c in cues if c.get("start") is None]
    if missing:
        sys.exit(f"cues with no time: {missing}")
    keyed = cue_keys(a.script, a.key_script) if a.key_script else {}
    data = {"source": source, "duration": round(duration + a.tail, 3),
            "cues": {f'{c["scene"]}|{keyed.get((c["scene"], c["cue"]), c["cue"])}': c["start"] for c in cues},
            "captions": captions, "strings": json.loads(a.strings.read_text()) if a.strings else {}}
    for item in a.embed:
        name, _, path = item.partition("=")
        data[name] = json.loads(Path(path).read_text())
    (a.project / "data.js").write_text("window.FILM=" + json.dumps(data, ensure_ascii=False) + ";\n")
    index = a.project / "index.html"
    if index.exists():
        index.write_text(re.sub(r'data-duration="[^"]*"', f'data-duration="{data["duration"]}"', index.read_text(), count=1))
    print(f"{a.project / 'data.js'}: {len(cues)} cues, {len(captions)} captions, {data['duration']} s ({source})")


if __name__ == "__main__":
    main()
