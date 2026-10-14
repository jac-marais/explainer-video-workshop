"""Invented captions break only between Stanza's tokens, keep numbers whole, keep spaced punctuation with its word and avoid breaks that bind words."""
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
        cases = [("zh", "花园有二百三十八朵花，旁边还有六十七朵花。", ["二百三十八", "六十七"]),
                 ("zh", "盒内有一千2百３十四颗种子。", ["一千2百３十四"]),
                 ("ko", "상자에는 씨앗이 1２34개 들어 있고 화분은 56개 있어요.", ["1２34", "56"]),
                 ("en", "The garden has one hundred and thirty-eight roses and sixty-seven tulips.",
                  ["one hundred and thirty-eight", "sixty-seven"])]
        for language, text, numbers in cases:
            inside = {c for token in parse(text, language).tokens for c in range(token.start_char + 1, token.end_char)}
            for width in range(2, 31):
                with self.subTest(language=language, width=width):
                    result = lines(text, language, width)
                    starts, offset = [], 0
                    for line in result:
                        offset = text.index(line, offset)
                        starts.append(offset)
                        offset += len(line)
                    self.assertEqual(" ".join(result).replace(" ", ""), text.replace(" ", ""))
                    self.assertFalse(inside & set(starts), result)
                    for number in numbers:
                        self.assertTrue(any(number in line for line in result), result)

    def test_oversized_numeral_stays_whole(self):
        self.assertEqual(lines("壹仟贰佰叁拾肆", "zh", 2), ["壹仟贰佰叁拾肆"])

    def test_bound_words_are_costly_but_clause_punctuation_wins(self):
        text = "看看花园中的花朵颜色。"
        for width in range(4, 10):
            self.assertFalse(any(line.startswith(("中", "的")) for line in lines(text, "zh", width)[1:]), width)
        self.assertEqual(lines("小鸟飞过高高的山顶，然后落在河边。", "zh", 10), ["小鸟飞过高高的山顶，", "然后落在河边。"])
        text = "The small flowers grow near the old garden wall."
        groups, costs = units(text, parse(text, "en"))
        after = {join_tokens(group): cost for group, cost in zip(groups, costs)}
        self.assertGreater(after["the"], after["grow"])
        self.assertEqual(lines("The baker packs her small blue bag before the long trip.", "en", 34),
                         ["The baker packs her small blue bag", "before the long trip."])

    def test_spaced_words_decimals_and_punctuation_are_preserved(self):
        for language, text in (("en", "The jar holds 123.45 grams of seeds."), ("fr", "Le pot contient 123,45 grammes de graines.")):
            with self.subTest(language=language):
                groups, costs = units(text, parse(text, language))
                self.assertEqual([str(token) for group in groups for token in group], list(tokenize(text)))
                result = lines(text, language, 15)
                self.assertEqual(" ".join(result), text)
                self.assertTrue(all(len(line) <= 15 for line in result), result)
        text = "Le jardinier demande « pourquoi ? » puis il sourit."
        groups, _ = units(text, parse(text, "fr"))
        self.assertIn("« pourquoi ? »", [join_tokens(group) for group in groups])


if __name__ == "__main__":
    unittest.main()
