#!/usr/bin/env python3
"""Build sentence captions from authored narration and measured Whisper word bounds.

  captions.py TIMING.json WORDS.json --output captions.vtt [--json-output captions.json] [--line-chars 42]

TIMING.json is narrate_film.py's timing.json and WORDS.json its words.json. Without --json-output, captions.json lands beside TIMING.json.
A long sentence splits into parts; each part stays up until the next part starts, and the last part ends with the sentence.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


# A line or cue that ends on one of these splits a phrase.
WEAK = set("a an the to of and or but for in on at as by with from into is are was be that this its their his her which who so if than then not no every each one".split())


# A break just before one of these starts a new clause.
OPENERS = set("and but so which while because when to as or whether rather than until even".split())


def break_cost(left: str, right: str = "") -> int:
    last = left.split()[-1]
    if last[-1] in ",;.?":
        return 0
    if last.lower() in WEAK:
        return 4
    return 1 if right.split()[:1] and right.split()[0].lower() in OPENERS else 2


def groups(text: str, line_limit: int) -> list[list[str]]:
    words = text.split()

    def fits(chunk: list[str]) -> bool:
        return all(len(line) <= line_limit for line in wrap(chunk, line_limit).split("\n")) and wrap(chunk, line_limit).count("\n") < 2

    # Fewest cues first, then a cost for uneven cues and for breaks inside a phrase.
    best: dict[int, tuple] = {len(words): (0, 0, [])}
    for i in range(len(words) - 1, -1, -1):
        options = []
        for j in range(i + 1, len(words) + 1):
            chunk = words[i:j]
            if not fits(chunk):
                break
            count, cost, rest = best[j]
            size = len(" ".join(chunk))
            phrase = 0 if j == len(words) else 200 * break_cost(" ".join(chunk), words[j])
            options.append((count + 1, cost + (2 * line_limit - size) ** 2 + phrase, [chunk] + rest))
        best[i] = min(options, key=lambda o: o[:2]) if options else (1, 0, [words[i:]] + best[i + 1][2])
    return best[0][2]


def wrap(words: list[str], line_limit: int) -> str:
    text = " ".join(words)
    if len(text) <= line_limit:
        return text
    splits = [(" ".join(words[:k]), " ".join(words[k:])) for k in range(1, len(words))]
    two = [pair for pair in splits if max(map(len, pair)) <= line_limit]
    if not two:
        return "\n".join(splits[0]) + "\nX" * 2
    return "\n".join(min(two, key=lambda pair: max(map(len, pair)) + 3 * break_cost(*pair)))


def timestamp(seconds: float) -> str:
    total_ms = round(max(0.0, seconds) * 1000)
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    whole_seconds, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{millis:03d}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("timing", type=Path, help="narrate.py timing.json")
    parser.add_argument("words", type=Path, help="align.py words.json")
    parser.add_argument("--output", required=True, type=Path, help="WebVTT output path")
    parser.add_argument("--json-output", type=Path, help="structured cue output (defaults to captions.json beside timing.json)")
    parser.add_argument("--line-chars", type=int, default=42)
    args = parser.parse_args()
    timing = json.loads(args.timing.read_text())
    word_data = json.loads(args.words.read_text())
    word_rows = word_data.get("words", [])
    if not word_rows:
        raise SystemExit("words.json contains no measured word timestamps")
    cues = []
    caption_rows = []
    for sentence in timing.get("sentences", []):
        text = sentence["text"]
        chunks = groups(text, args.line_chars)
        if not chunks:
            continue
        measured = [word for word in word_rows if word["start"] < sentence["end"] + 0.05 and word["end"] > sentence["start"] - 0.05]
        if len(measured) < len(chunks):
            raise SystemExit(f"Whisper has too few word samples for caption chunks in {sentence['id']}")
        authored_count = max(1, len(text.split()))
        offset = 0
        previous_stop = 0
        for chunk_index, chunk in enumerate(chunks):
            offset += len(chunk)
            if chunk_index == len(chunks) - 1:
                stop = len(measured)
            else:
                remaining_chunks = len(chunks) - chunk_index - 1
                stop = round(offset * len(measured) / authored_count)
                stop = max(previous_stop + 1, min(stop, len(measured) - remaining_chunks))
            begin = previous_stop
            start = max(sentence["start"], measured[begin]["start"])
            end = min(sentence["end"], measured[stop - 1]["end"])
            if stop < len(measured):
                # A part holds until the sentence's next part starts, so the caption never blinks mid-sentence.
                end = max(end, min(sentence["end"], measured[stop]["start"]))
            if end <= start:
                raise SystemExit(f"Invalid measured caption interval in {sentence['id']}")
            caption_text = wrap(chunk, args.line_chars)
            cues.append((start, end, caption_text))
            caption_rows.append({
                "id": f"{sentence['id']}-C{chunk_index + 1:02d}",
                "sentence_id": sentence["id"],
                "scene_id": sentence["scene_id"],
                "start": round(start, 3),
                "end": round(end, 3),
                "text": caption_text,
            })
            previous_stop = stop
    if not cues:
        raise SystemExit("No caption cues were generated")
    output = ["WEBVTT", ""]
    for index, (start, end, text) in enumerate(cues, 1):
        output.extend((str(index), f"{timestamp(start)} --> {timestamp(end)}", text, ""))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(output))
    json_output = args.json_output or args.timing.parent / "captions.json"
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(caption_rows, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "json_output": str(json_output), "cues": len(cues), "measured_word_samples": len(word_rows)}))


if __name__ == "__main__":
    main()
