#!/usr/bin/env python3
"""Write a composition's data.js from a script's cues and captions, so the picture reads every time from the voice.

  build_data.py --script SCRIPT.md --project DIR --audio AUDIO_DIR [--tail S] [options]
  build_data.py --script SCRIPT.md --project DIR --estimate --language CODE [--wpm 150] [--scenes N] [options]

  options: [--strings STRINGS.json] [--key-script KEY_SCRIPT.md] [--embed NAME=FILE.json ...]

--audio reads AUDIO_DIR/cues.json (from cues.py), captions.json (from captions.py) and timing.json (from narrate_film.py).
--estimate times whitespace words or Han/Kana characters evenly at --wpm, with short pauses after sentences and scenes, for a silent
preview before any voice exists; --language names the script's language for the sentence split in text_tokens.py, and
--scenes N stops after scene N. Run --estimate with scripts/run/py, which has Stanza. Both modes write the same shape to DIR/data.js:

  window.FILM = {source, duration, cues: {"sNN|quoted words": start seconds}, caption_onsets: {"sNN|sNN-NN": start seconds}, captions, strings, ...embeds}

and set the first data-duration attribute in DIR/index.html, because the renderer reads it before any script runs.
duration is the narration length plus --tail. --strings adds the on-screen text for one language. --key-script names
every quoted cue by the quoted cue at the same position in the same scene of another script, so a translated film keeps the cue
names its code uses; the run exits 1 when a scene's quoted cue counts differ. make_film.py and storyboard.py check sentence counts.
Sentence cue names stay unchanged in both modes without --key-script; measured starts come from timing.json. --embed adds a JSON file under NAME.
caption_onsets holds the first caption start for each sentence with caption metadata; missing entries have no inferred fallback.
The run exits 1 on a cue with no time.
"""
import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "audio"))
from text_tokens import norm, tokenize, normalized_tokens, join_tokens, sentences  # noqa: E402
from cues import SCENE, VISUAL, cue_names, sentence_ref, sentence_time  # noqa: E402

NARRATION = re.compile(r"\*\*Narration\.?\*\*")


def scenes(script):
    """Each scene's number, its narration as one line, and its cue quotes in order."""
    for m in SCENE.finditer(script.read_text()):
        parts = NARRATION.split(m.group(0), 1)
        if len(parts) != 2:
            raise ValueError(f"scene {m.group(1)}: no **Narration** part")
        narration, *visual = VISUAL.split(parts[1], 1)
        yield int(m.group(1)), " ".join(narration.split()), cue_names("".join(visual))


def check_sentence_counts(counts, key_counts):
    """Fail when a translation's sentence count per scene differs from its key script's."""
    for num in sorted(counts.keys() | key_counts.keys()):
        if counts.get(num) != key_counts.get(num):
            raise ValueError(f"scene {num}: {counts.get(num, 0)} sentences, but the key script has {key_counts.get(num, 0)}")


def estimate(script, wpm, last_scene, language):
    """Even token timing (whitespace words or Han/Kana characters) with short pauses after sentences and scenes; planning only."""
    cues, captions, t, per_word = [], [], 0.4, 60 / wpm
    for num, text, quotes in scenes(script):
        if last_scene and num > last_scene:
            break
        sid, words, starts, sentence_rows, word_sentences = f"s{num:02d}", [], [], [], []
        for index, sentence in enumerate(sentences(text, language), 1):
            if sentence["pause_before"]:
                t += 3.0
            start = t
            for w in tokenize(sentence["text"]):
                words.append(w)
                starts.append(t)
                word_sentences.append(f"{sid}-{index:02d}")
                t += per_word
            sentence_rows.append({"id": f"{sid}-{index:02d}", "scene_id": sid, "start": start, "end": t})
            t += 0.35
        ends = starts[1:] + [t]
        # A caption part breaks at a sentence end, at a comma once it has 5 words, or at 9 words.
        part, s0 = [], None
        for i, w in enumerate(words):
            s0 = starts[i] if s0 is None else s0
            part.append(w)
            last = i == len(words) - 1
            sentence_end = last or word_sentences[i] != word_sentences[i + 1]
            if sentence_end or (w.endswith(",") and len(part) >= 5) or len(part) >= 9:
                end = starts[i] + per_word if sentence_end else starts[i + 1]
                captions.append({"id": f"{sid}-{len(captions):03d}", "scene_id": sid,
                                 "sentence_id": word_sentences[i], "start": round(s0, 3),
                                 "end": round(end, 3), "text": join_tokens(part)})
                part, s0 = [], None
        # Punctuation-only tokens are skipped on both sides, as in cues.py.
        kept = [(norm(w), i) for i, w in enumerate(words) if norm(w)]
        normed = [n for n, _ in kept]
        for q in quotes:
            measured = sentence_time(q, sid, sentence_rows)
            if measured is not None:
                cues.append({"scene": sid, "cue": q, "start": measured[0], "end": measured[1]})
                continue
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
    keys = {num: [q for q in quotes if sentence_ref(q) is None] for num, _, quotes in scenes(key_script)}
    out = {}
    for num, _, quotes in scenes(script):
        quotes = [q for q in quotes if sentence_ref(q) is None]
        if len(quotes) != len(keys.get(num, [])):
            sys.exit(f"scene {num}: {len(quotes)} cues, but the key script has {len(keys.get(num, []))}")
        out.update({(f"s{num:02d}", q): k for q, k in zip(quotes, keys[num])})
    return out


def caption_onsets(captions):
    """Keep the earliest caption start for every sentence with explicit metadata."""
    onsets = {}
    for caption in captions:
        if caption.get("sentence_id") and caption.get("scene_id"):
            key = f'{caption["scene_id"]}|{caption["sentence_id"]}'
            onsets[key] = min(onsets.get(key, caption["start"]), caption["start"])
    return onsets


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--script", type=Path, required=True)
    ap.add_argument("--project", type=Path, required=True, help="composition folder; data.js is written here")
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--audio", type=Path, help="folder with cues.json, captions.json and timing.json")
    mode.add_argument("--estimate", action="store_true", help="time the script evenly, before any voice exists")
    ap.add_argument("--language", help="with --estimate, the script's language code, such as pt")
    ap.add_argument("--wpm", type=float, default=150)
    ap.add_argument("--scenes", type=int, help="with --estimate, stop after scene N")
    ap.add_argument("--tail", type=float, default=0, help="seconds of picture after the narration ends")
    ap.add_argument("--strings", type=Path, help="on-screen text for this language")
    ap.add_argument("--key-script", type=Path, help="script whose cue quotes name the cues")
    ap.add_argument("--embed", action="append", default=[], metavar="NAME=FILE.json", help="add a JSON file under NAME")
    a = ap.parse_args()

    if a.estimate:
        if not a.language:
            ap.error("--estimate needs --language")
        cues, captions, duration = estimate(a.script, a.wpm, a.scenes, a.language)
        source = f"estimate at {a.wpm:g} WPM"
    else:
        cues = json.loads((a.audio / "cues.json").read_text())
        captions = json.loads((a.audio / "captions.json").read_text())
        timing = json.loads((a.audio / "timing.json").read_text())
        duration = timing["duration"]
        for num, _, names in scenes(a.script):
            for name in names:
                measured = sentence_time(name, f"s{num:02d}", timing.get("sentences", []))
                if measured is not None:
                    cues = [c for c in cues if (c["scene"], c["cue"]) != (f"s{num:02d}", name)]
                    cues.append({"scene": f"s{num:02d}", "cue": name, "start": measured[0], "end": measured[1]})
        source = str(a.audio)
    missing = [c["cue"] for c in cues if c.get("start") is None]
    if missing:
        sys.exit(f"cues with no time: {missing}")
    keyed = cue_keys(a.script, a.key_script) if a.key_script else {}
    data = {"source": source, "duration": round(duration + a.tail, 3),
            "cues": {f'{c["scene"]}|{keyed.get((c["scene"], c["cue"]), c["cue"])}': c["start"] for c in cues},
            "caption_onsets": caption_onsets(captions),
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
    try:
        main()
    except ValueError as exc:
        sys.exit(str(exc))
