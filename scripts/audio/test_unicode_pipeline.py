"""Invented examples in several scripts exercise tokens, word alignment, sentence rules and measured cue times."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import narrate_film
from text_tokens import norm, normalized_tokens, tokenize, join_tokens

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / "film"))
sys.path.insert(0, str(SCRIPTS / "storyboard"))
from storyboard import words_of, find


class UnicodePipelineTests(unittest.TestCase):
    def exercise(self, language, text, pieces, quote, cue_start, cue_end, expected):
        self.assertEqual(normalized_tokens(text), expected)
        self.assertEqual(join_tokens(tokenize(text)), text)
        asr = [{"word": word, "start": start, "end": end} for word, start, end in pieces]
        sentence = {"id": "s01-01", "scene_id": "s01", "text": text, "spoken_text": text,
                    "start": 0, "end": pieces[-1][2]}
        aligned, fallbacks = narrate_film.align_words([sentence], asr)
        self.assertEqual(fallbacks, [])
        self.assertEqual([norm(w["text"]) for w in aligned[0]], expected)
        self.assertEqual(narrate_film.asr_differences([sentence], asr), [])
        words = words_of(text)
        hit = find(words, quote, 0)
        self.assertIsNotNone(hit)
        self.assertEqual(norm(text[words[hit][1]:words[hit + len(normalized_tokens(quote)) - 1][2]]), norm(quote))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "script.md"
            script.write_text(f'## Scene 1: Test\n\n**Narration**\n\n{text}\n\n**Visual**\n\nOn "{quote}", a shape appears.\n')
            timing = {"sentences": [sentence], "scenes": [{"id": "s01", "start": 0, "end": sentence["end"]}]}
            (root / "timing.json").write_text(json.dumps(timing))
            # Both aligned script tokens and Whisper's multi-character pieces must resolve.
            for measured in (aligned[0], [{"text": w["word"], "start": w["start"], "end": w["end"]} for w in asr]):
                (root / "words.json").write_text(json.dumps({"language": language, "words": measured}))
                result = subprocess.run([sys.executable, SCRIPTS / "audio/cues.py", script, root / "words.json",
                                         root / "timing.json", "--out", root / "cues.json", "--strict"], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                cue = json.loads((root / "cues.json").read_text())[0]
                self.assertAlmostEqual(cue["start"], cue_start, places=3)
                self.assertAlmostEqual(cue["end"], cue_end, places=3)

    def test_hindi(self):
        self.exercise("hi", "छोटा फूल धीरे खिलता है।", [("छोटा", 0, 1), ("फूल", 1, 2), ("धीरे", 2, 3), ("खिलता", 3, 4), ("है।", 4, 5)],
                      "फूल धीरे", 1, 3, ["छोटा", "फूल", "धीरे", "खिलता", "है"])

    def test_korean(self):
        self.exercise("ko", "작은 꽃이 천천히 피어 납니다.", [("작은", 0, 1), ("꽃이", 1, 2), ("천천히", 2, 3), ("피어", 3, 4), ("납니다.", 4, 5)],
                      "꽃이 천천히", 1, 3, ["작은", "꽃이", "천천히", "피어", "납니다"])

    def test_chinese(self):
        self.exercise("zh", "小花慢慢开放，garden里有123.45朵花。", [("小花慢慢", 0, 4), ("开放，", 4, 6), ("garden", 6, 7),
                      ("里有", 7, 9), ("123.45", 9, 10), ("朵花。", 10, 12)], "花慢慢开", 1, 5,
                      ["小", "花", "慢", "慢", "开", "放", "garden", "里", "有", "12345", "朵", "花"])
        self.assertEqual(normalized_tokens("カ\u3099ラスと花"), ["ガ", "ラ", "ス", "と", "花"])
        self.assertEqual(normalized_tokens("ｶﾞラス"), ["ガ", "ラ", "ス"])
        sentence = {"id": "s01-01", "text": "小花开放", "spoken_text": "小花开放"}
        self.assertTrue(narrate_film.asr_differences([sentence], [{"word": "石头滚动"}]))

    def test_a_boundary_before_a_closing_quote_moves_after_it(self):
        import text_tokens
        from types import SimpleNamespace
        from unittest.mock import patch
        text = "The seed sleeps. “Will it grow?” Rain falls."
        cuts = [text.index("“"), text.index("”"), text.index("Rain")]
        doc = SimpleNamespace(sentences=[SimpleNamespace(tokens=[SimpleNamespace(start_char=c)]) for c in [0] + cuts])
        with patch.object(text_tokens, "stanza_pipeline", return_value=lambda clean: doc):
            split = text_tokens.sentences(text, "en")
        self.assertEqual([s["text"] for s in split], ["The seed sleeps.", "“Will it grow?”", "Rain falls."])

    def test_quoted_sentences_split_when_stanza_merges_them(self):
        import text_tokens
        from types import SimpleNamespace
        from unittest.mock import patch
        text = '"I see people." "I see laptops." "They are best friends." That answer lists objects.'
        doc = SimpleNamespace(sentences=[SimpleNamespace(tokens=[SimpleNamespace(start_char=0)])])
        with patch.object(text_tokens, "stanza_pipeline", return_value=lambda clean: doc):
            split = text_tokens.sentences(text, "en")
        self.assertEqual([s["text"] for s in split], ['"I see people."', '"I see laptops."', '"They are best friends."',
                                                      "That answer lists objects."])
        # A quote that ends inside a sentence, before a lowercase word, does not split it.
        text = 'She said "Stop!" and walked home. Then it rained.'
        doc = SimpleNamespace(sentences=[SimpleNamespace(tokens=[SimpleNamespace(start_char=c)]) for c in (0, text.index("Then"))])
        with patch.object(text_tokens, "stanza_pipeline", return_value=lambda clean: doc):
            split = text_tokens.sentences(text, "en")
        self.assertEqual([s["text"] for s in split], ['She said "Stop!" and walked home.', "Then it rained."])

    def test_sentences_under_the_word_floor(self):
        from text_tokens import short_sentences
        texts = ["Ready?", "Too slow?", "The kettle boils, so she pours the tea.", "Then she waits a minute.", "“Look up.”",
                 '"Wait," she says.', "小花在阳光下开了。", "小花开了。"]
        self.assertEqual(short_sentences({"s02": texts}), [
            "s02-01: 1 word, under the 5-word floor: Ready?",
            "s02-02: 2 words, under the 5-word floor: Too slow?",
            's02-06: 3 words, under the 5-word floor: "Wait," she says.',
            "s02-08: 4 words, under the 5-word floor: 小花开了。"])
        self.assertEqual(short_sentences({"s01": ["I'm D-E-T ready now."]}), ["s01-01: 4 words, under the 5-word floor: I'm D-E-T ready now."])

    def test_numbers_inside_heard_words(self):
        for language, text, pieces in [
                ("ko", "엘리베이터가 십이 층에 서요.", [("엘리베이터가", 0, 1), ("12층에", 1, 2), ("서요.", 2, 3)]),
                ("fr", "Le niveau B deux arrive.", [("Le", 0, 1), ("niveau", 1, 2), ("b2", 2, 3), ("arrive.", 3, 4)])]:
            asr = [{"word": word, "start": start, "end": end} for word, start, end in pieces]
            sentence = {"id": "s01-01", "text": text, "spoken_text": text, "start": 0, "end": pieces[-1][2]}
            aligned, fallbacks = narrate_film.align_words([sentence], asr, language)
            self.assertEqual(fallbacks, [], language)
            self.assertEqual(narrate_film.asr_differences([sentence], asr, language), [], language)
        self.assertEqual(narrate_film.spoken_word("12층에", "en", "십이층에"), "12층에")


if __name__ == "__main__":
    unittest.main()
