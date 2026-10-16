"""Invented English captions break only between Stanza's tokens, keep numbers whole, keep every token and avoid breaks that bind words."""
import unittest

from captions import layout, units
from text_tokens import join_tokens, stanza_pipeline, tokenize


def parse(text: str, language: str):
    sentences = stanza_pipeline(language, parse=True)(text).sentences
    assert len(sentences) == 1, text
    return sentences[0]


def lines(text: str, language: str, width: int) -> list[str]:
    """Caption lines at a width in characters, measured with len."""
    return [join_tokens(line) for cue in layout(*units(text, parse(text, language)), len, width) for line in cue]


class CaptionBreakTests(unittest.TestCase):
    def test_numbers_survive_line_and_cue_breaks(self):
        text = "The garden has one hundred and thirty-eight roses and sixty-seven tulips."
        inside = {c for token in parse(text, "en").tokens for c in range(token.start_char + 1, token.end_char)}
        for width in range(2, 31):
            with self.subTest(width=width):
                result = lines(text, "en", width)
                starts, offset = [], 0
                for line in result:
                    offset = text.index(line, offset)
                    starts.append(offset)
                    offset += len(line)
                self.assertEqual(" ".join(result).replace(" ", ""), text.replace(" ", ""))
                self.assertFalse(inside & set(starts), result)
                for number in ["one hundred and thirty-eight", "sixty-seven"]:
                    self.assertTrue(any(number in line for line in result), result)

    def test_bound_words_are_costly(self):
        text = "The small flowers grow near the old garden wall."
        groups, costs = units(text, parse(text, "en"))
        after = {join_tokens(group): cost for group, cost in zip(groups, costs)}
        self.assertGreater(after["the"], after["grow"])
        self.assertEqual(lines("The baker packs her small blue bag before the long trip.", "en", 34),
                         ["The baker packs her small blue bag", "before the long trip."])

    def test_every_token_and_decimal_is_preserved(self):
        text = "The jar holds 123.45 grams of seeds."
        groups, costs = units(text, parse(text, "en"))
        self.assertEqual([str(token) for group in groups for token in group], list(tokenize(text)))
        result = lines(text, "en", 15)
        self.assertEqual(" ".join(result), text)
        self.assertTrue(all(len(line) <= 15 for line in result), result)


if __name__ == "__main__":
    unittest.main()
