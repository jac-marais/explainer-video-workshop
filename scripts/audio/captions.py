#!/usr/bin/env python3
"""Build sentence captions from authored narration and measured Whisper word bounds.

  captions.py TIMING.json WORDS.json --output captions.vtt [--json-output captions.json]
              [--font FILE[#INDEX] ...] [--font-size PX] [--font-weight N] [--line-width PX]

A cue holds at most two lines, each at most --line-width pixels wide in the caption font, and spans its words' measured
times until the sentence's next cue. Lines break between Stanza's tokens, never inside a number, at the break that
cuts the fewest and loosest links of Stanza's dependency parse, as subtitle guidelines ask. Run it with scripts/run/py.
"""
from __future__ import annotations

import argparse
import bisect
import functools
import itertools
import json
import unicodedata
from pathlib import Path
from text_tokens import norm, tokenize, join_tokens, timed_tokens, stanza_pipeline

# Universal Dependencies relations that tie a function word or a fixed expression to its head.
BOUND = {"aux", "cop", "mark", "det", "clf", "case", "cc", "fixed", "flat", "compound"}
BOUND_COST, DANGLING_COST = 4, 2
# One cost unit weighs as much as this fraction of a line's width.
LINE_WEIGHT, CUE_WEIGHT = 0.1, 0.15
MISSING = "\U0010fffd"  # A private-use character that no font draws, so it shows each font's missing glyph.
SCALE = 64  # Pillow rounds each advance to a whole pixel, so it measures large and scales down.


class Measure:
    """Width in pixels of a text in the caption fonts."""

    def __init__(self, fonts: list[str] = (), size: float = 48, weight: float = 400):
        from PIL import ImageFont
        self.size = size
        self.fonts = []
        for spec in fonts or [None]:
            path, _, index = (spec or "").partition("#")
            pair = [ImageFont.truetype(path, s, index=int(index or 0)) if path else ImageFont.load_default(s)
                    for s in (size * SCALE, 32)]
            for font in pair:
                try:
                    axes = font.get_variation_axes()
                except OSError:
                    break
                font.set_variation_by_axes([min(max(weight, axis["minimum"]), axis["maximum"]) if axis["name"] == b"Weight"
                                            else axis["default"] for axis in axes])
            self.fonts.append((pair[0], pair[1], self.glyph(pair[1], MISSING)))

    @staticmethod
    def glyph(font, char: str):
        return font.getlength(char), font.getbbox(char), bytes(font.getmask(char))

    @functools.cache
    def font(self, char: str) -> int | None:
        if char.isspace():
            return 0
        return next((i for i, (_, small, missing) in enumerate(self.fonts) if self.glyph(small, char) != missing), None)

    @functools.cache
    def __call__(self, text: str) -> float:
        width = 0.0
        for index, run in itertools.groupby(text, self.font):
            run = "".join(run)
            width += self.size * len(run) if index is None else self.fonts[index][0].getlength(run) / SCALE
        return width


def inside_number(tags: list[str], i: int) -> bool:
    """Whether a break after word i of a sentence with these UPOS tags falls inside number words, such as one hundred and five."""
    left, right = tags[i], tags[i + 1]
    return (left == right == "NUM" or left == "NUM" and right == "CCONJ" and tags[i + 2:i + 3] == ["NUM"]
            or left == "CCONJ" and right == "NUM" and i > 0 and tags[i - 1] == "NUM")


def units(text: str, sentence) -> tuple[list[list], list[float]]:
    """The sentence's display tokens grouped where a line may break, and the parse cost of each break."""
    tokens = tokenize(text)
    stanza_tokens = sentence.tokens
    ends = [token.end_char for token in stanza_tokens]
    inside = {c for token in stanza_tokens for c in range(token.start_char + 1, token.end_char)}
    place = {word.id: i for i, token in enumerate(stanza_tokens) for word in token.words}
    tags = [word.upos for word in sentence.words]
    groups, costs = [[tokens[0]]], []
    for left, right in zip(tokens, tokens[1:]):
        k = bisect.bisect_right(ends, right.start)
        cut = [word for word in sentence.words if word.head and (place[word.id] < k) != (place[word.head] < k)]
        numerals = left.end == right.start and all(unicodedata.numeric(c, None) is not None for c in text[left.end - 1:right.start + 1])
        last, first = stanza_tokens[k - 1].words[-1], stanza_tokens[k].words[0]
        # Spaced punctuation, such as a French guillemet, stays with the word it belongs to.
        punctuation = (last.upos == "PUNCT" and not norm(left) and last.head and place[last.head] >= k
                       or first.upos == "PUNCT" and not norm(right) and first.head and place[first.head] < k)
        # A number reads as one value, whether in numerals or in number words.
        if right.start in inside or numerals or inside_number(tags, last.id - 1) or punctuation:
            groups[-1].append(right)
            continue
        cost = sum(BOUND_COST if word.deprel.split(":")[0] in BOUND else 1 for word in cut if word.deprel != "punct")
        if last.upos != "PUNCT" and last.head and place[last.head] >= k:
            cost += DANGLING_COST
        groups.append([right])
        costs.append(cost)
    return groups, costs


def layout(groups: list[list], costs: list[float], measure, line_width: float) -> list[list[list]]:
    """Cues of lines of display tokens: the fewest cues, then even cues and lines with cheap breaks."""
    space = measure(" ")
    widths = [measure(join_tokens(group)) for group in groups]

    def width(i: int, j: int) -> float:
        return sum(widths[i:j]) + space * sum(groups[k][0].spaced for k in range(i + 1, j))

    @functools.cache
    def lines(i: int, j: int) -> tuple[float, list[int]] | None:
        """The cheapest split of groups i to j into one or two lines, or None when they need more."""
        if width(i, j) <= line_width or j == i + 1:
            return 0.0, [i, j]
        splits = [(max(width(i, k), width(k, j)) / line_width + LINE_WEIGHT * costs[k - 1], k)
                  for k in range(i + 1, j) if max(width(i, k), width(k, j)) <= line_width]
        if not splits:
            return None
        k = min(splits)[1]
        return costs[k - 1], [i, k, j]

    best = {len(groups): (0, 0.0, [])}
    for i in range(len(groups) - 1, -1, -1):
        options = []
        for j in range(i + 1, len(groups) + 1):
            split = lines(i, j)
            if split is None:
                break
            count, cost, rest = best[j]
            slack = 2 - width(i, j) / line_width
            options.append((count + 1, cost + slack ** 2 + CUE_WEIGHT * (split[0] + (costs[j - 1] if j < len(groups) else 0)),
                            [split[1]] + rest))
        best[i] = min(options, key=lambda option: option[:2])
    return [[[token for group in groups[a:b] for token in group] for a, b in zip(bounds, bounds[1:])] for bounds in best[0][2]]


def timestamp(seconds: float) -> str:
    total_ms = round(max(0.0, seconds) * 1000)
    hours, rest = divmod(total_ms, 3_600_000)
    minutes, rest = divmod(rest, 60_000)
    whole_seconds, millis = divmod(rest, 1000)
    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d}.{millis:03d}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("timing", type=Path, help="narrate_film.py timing.json")
    parser.add_argument("words", type=Path, help="narrate_film.py words.json")
    parser.add_argument("--output", required=True, type=Path, help="WebVTT output path")
    parser.add_argument("--json-output", type=Path, help="structured cue output (defaults to captions.json beside timing.json)")
    parser.add_argument("--font", action="append", default=[], metavar="FILE[#INDEX]",
                        help="caption font; repeat in CSS fallback order, #INDEX picks a face in a collection (default: Pillow's own)")
    parser.add_argument("--font-size", type=float, default=48, help="pixels (default 48)")
    parser.add_argument("--font-weight", type=float, default=400, help="sets a variable font's Weight axis (default 400)")
    parser.add_argument("--line-width", type=float, default=1100, help="pixels (default 1100)")
    args = parser.parse_args()
    timing = json.loads(args.timing.read_text())
    word_data = json.loads(args.words.read_text())
    word_rows = timed_tokens(word_data.get("words", []))
    if not word_rows:
        raise SystemExit("words.json contains no measured word timestamps")
    if not word_data.get("language"):
        raise SystemExit("words.json names no language; rerun narrate_film.py")
    measure = Measure(args.font, args.font_size, args.font_weight)
    sentences = timing.get("sentences", [])
    parses = stanza_pipeline(word_data["language"], parse=True).process_many([s["text"] for s in sentences])
    cues = []
    caption_rows = []
    for sentence, parse in zip(sentences, parses):
        text = sentence["text"]
        if len(parse.sentences) != 1:
            raise SystemExit(f"Stanza did not read {sentence['id']} as one sentence")
        chunks = layout(*units(text, parse.sentences[0]), measure, args.line_width)
        measured = [word for word in word_rows if word["start"] < sentence["end"] + 0.05 and word["end"] > sentence["start"] - 0.05]
        if len(measured) < len(chunks):
            raise SystemExit(f"Whisper has too few word samples for caption chunks in {sentence['id']}")
        authored_count = max(1, len(tokenize(text)))
        offset = 0
        previous_stop = 0
        for chunk_index, chunk in enumerate(chunks):
            offset += sum(map(len, chunk))
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
            caption_text = "\n".join(join_tokens(line) for line in chunk)
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
