"""Shared Unicode matching and display tokens for narration, cues and captions.

Matching uses NFKC/casefold and keeps letters, combining marks and numbers.
Han and Kana use character tokens; other scripts use whitespace-delimited words.
Display tokens retain authored spelling, punctuation, spacing boundaries and spans.
"""
import re
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
