"""Shared Unicode matching, display tokens and sentences for narration, cues and captions.

Matching uses NFKC/casefold and keeps letters, combining marks and numbers.
Han and Kana use character tokens; other scripts use whitespace-delimited words.
Display tokens retain authored spelling, punctuation, spacing boundaries and spans.
Sentences and syntax come from Stanza's models for the language, loaded offline from Stanza's per-user cache.
short_sentences() counts these tokens against the narration word floor that storyboard.py and make_film.py enforce.

  text_tokens.py < [[LANGUAGE, TEXT], ...]   prints each text's sentences as JSON, for tools outside the environment
"""
import functools
import json
import re
import sys
import unicodedata


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).casefold()
    return "".join(c for c in text if unicodedata.category(c)[0] in "LMN")


def character_token(char: str) -> bool:
    name = unicodedata.name(unicodedata.normalize("NFKC", char)[0], "")
    return name.startswith(("CJK UNIFIED IDEOGRAPH", "CJK COMPATIBILITY IDEOGRAPH", "HIRAGANA", "KATAKANA")) or char in "々〆〇ー"


class Token(str):
    """A display token with its original offsets and preceding whitespace boundary."""
    def __new__(cls, text, start, end, spaced):
        obj = super().__new__(cls, text[start:end])
        obj.start, obj.end, obj.spaced = start, end, spaced
        return obj


def tokenize(text: str) -> list[Token]:
    result = []
    for match in re.finditer(r"\S+", text):
        start = match.start()
        content, previous_character = False, False
        for i in range(start, match.end()):
            char = text[i]
            # Marks stay attached to their base, including decomposed Kana.
            if (unicodedata.category(char)[0] not in "LN"
                    or all(unicodedata.category(c)[0] == "M" for c in unicodedata.normalize("NFKC", char))):
                continue
            current_character = character_token(char)
            if content and (current_character or previous_character):
                result.append(Token(text, start, i, start == match.start()))
                start = i
            content, previous_character = True, current_character
        result.append(Token(text, start, match.end(), start == match.start()))
    return result


def normalized_tokens(text: str) -> list[str]:
    return [value for token in tokenize(text) if (value := norm(token))]


MIN_WORDS = 5
OPENING_QUOTES, CLOSING_QUOTES = "\"'“‘«„「『", "\"'”’»“」』"


def short_sentences(scenes: dict[str, list[str]]) -> list[str]:
    """An error for each narration sentence under MIN_WORDS tokens, keyed by scene ID such as s03.

    A sentence wholly inside quotation marks passes, because its source fixed its words.
    """
    return [f"{sid}-{i:02d}: {count} word{'' if count == 1 else 's'}, under the {MIN_WORDS}-word floor: {text}"
            for sid, texts in scenes.items() for i, text in enumerate(texts, 1)
            if (count := len(normalized_tokens(text))) < MIN_WORDS
            and not (text.startswith(tuple(OPENING_QUOTES)) and text.endswith(tuple(CLOSING_QUOTES)))]


def join_tokens(tokens: list[str]) -> str:
    return "".join((" " if i and getattr(token, "spaced", True) else "") + token
                   for i, token in enumerate(tokens))


def timed_tokens(rows: list[dict], key: str = "text") -> list[dict]:
    """Split ASR pieces into tokens, apportioning their bounds by normalized length.

    Character times inside a multi-character ASR piece are interpolated, not
    independent measurements. Already-tokenized word bounds remain unchanged.
    """
    result = []
    for row in rows:
        tokens = tokenize(row[key])
        weights = [len(norm(token)) for token in tokens]
        total = sum(weights)
        offset = 0
        for token, weight in zip(tokens, weights):
            if not weight:
                continue
            start = row["start"] + (row["end"] - row["start"]) * offset / total
            offset += weight
            end = row["end"] if offset == total else row["start"] + (row["end"] - row["start"]) * offset / total
            result.append({**row, key: token, "start": start, "end": end})
    return result


@functools.cache
def stanza_pipeline(language: str, parse: bool = False):
    """Stanza's tokenizer for a language; with parse, also its tagger and dependency parser, one sentence per text."""
    import stanza  # Only sentence and syntax users pay for loading Stanza.
    processors = "tokenize,pos,lemma,depparse" if parse else "tokenize"
    try:
        # ERROR, because Stanza warns on every load that it added the multi-word token expander a language needs.
        return stanza.Pipeline(language, processors=processors, tokenize_no_ssplit=parse,
                               download_method=None, logging_level="ERROR")
    except FileNotFoundError as exc:
        raise SystemExit(f"Stanza has no {processors} models for {language!r}; download them as Setup in README.md says ({exc})")


def sentences(text: str, language: str) -> list[dict]:
    """Split narration into the sentences that Stanza's tokenizer for the language finds.

    A boundary counts only where the text before it ends in a Unicode Sentence_Terminal, then any closing punctuation and spaces.
    A proposed boundary moves past closing punctuation that touches the text before it, so a closing quote stays with its sentence.
    A terminal, a closing quote, then a space and anything but a lowercase letter always ends a sentence, because a tokenizer
    for one language can merge quoted sentences in another, such as English sample answers in Spanish or Hindi narration.
    A [pause] mark never splits a sentence. It sets pause_before on the sentence that holds the text after it.
    """
    import regex  # Standard-library tools import this module too, and only the environment has regex.
    pieces = [" ".join(piece.split()) for piece in re.split(r"\[pause\]", text, flags=re.IGNORECASE)]
    clean, pauses = "", set()
    for index, piece in enumerate(pieces):
        if piece:
            clean += " " if clean else ""
            if index:
                pauses.add(len(clean))
            clean += piece
    if not clean:
        raise ValueError("scene narration must not be empty")
    end = regex.compile(r"\p{Sentence_Terminal}[\p{SB=Close}\s]*\Z")
    closing = regex.compile(r"[\p{Pe}\p{Pf}]*\s*")
    quoted = regex.compile(r"\p{Sentence_Terminal}\p{SB=Close}+\s+(?=[^\s\p{Ll}])")
    proposed = (sentence.tokens[0].start_char for sentence in stanza_pipeline(language)(clean).sentences[1:])
    settled = {closing.match(clean, start).end() if not clean[start - 1].isspace() else start for start in proposed}
    settled |= {m.end() for m in quoted.finditer(clean)}
    starts = [0] + sorted(start for start in settled if start < len(clean) and end.search(clean, 0, start)) + [len(clean)]
    return [{"text": clean[a:b].strip(), "pause_before": any(a <= p < b for p in pauses)} for a, b in zip(starts, starts[1:])]


if __name__ == "__main__":
    print(json.dumps([sentences(text, language) for language, text in json.load(sys.stdin)], ensure_ascii=False))
