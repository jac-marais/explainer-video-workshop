"""Invented multilingual examples exercise the shared narration-to-caption path."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import narrate_film
from captions import Measure
from text_tokens import norm, normalized_tokens, tokenize, join_tokens

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / "film"))
sys.path.insert(0, str(SCRIPTS / "storyboard"))
from build_data import estimate
from storyboard import words_of, find


class UnicodePipelineTests(unittest.TestCase):
    def exercise(self, language, text, pieces, quote, cue_start, cue_end, width, expected):
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
            estimated, captions, _ = estimate(script, 150, None, language)
            self.assertEqual(len(estimated), 1)
            self.assertGreater(estimated[0]["end"], estimated[0]["start"])
            self.assertEqual("".join(normalized_tokens(" ".join(c["text"] for c in captions))), "".join(expected))
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
                result = subprocess.run([sys.executable, SCRIPTS / "audio/captions.py", root / "timing.json",
                                         root / "words.json", "--output", root / "captions.vtt", "--line-width", str(width)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                rows = json.loads((root / "captions.json").read_text())
                self.assertTrue(all(r["start"] < r["end"] for r in rows))
                lines = [line for r in rows for line in r["text"].splitlines()]
                self.assertGreater(len(lines), 1)
                self.assertTrue(all(Measure()(line) <= width for line in lines), lines)
                self.assertEqual("".join(norm(line) for line in lines), "".join(expected))
                if "garden" in text:
                    self.assertTrue(any("garden" in line for line in lines))
                    self.assertTrue(any("123.45" in line for line in lines))
                else:
                    self.assertEqual([norm(word) for line in lines for word in line.split()], expected)

    def test_hindi(self):
        self.exercise("hi", "छोटा फूल धीरे खिलता है।", [("छोटा", 0, 1), ("फूल", 1, 2), ("धीरे", 2, 3), ("खिलता", 3, 4), ("है।", 4, 5)],
                      "फूल धीरे", 1, 3, 576, ["छोटा", "फूल", "धीरे", "खिलता", "है"])
        self.assertEqual(norm("क़"), "क़")

    def test_korean(self):
        self.exercise("ko", "작은 꽃이 천천히 피어 납니다.", [("작은", 0, 1), ("꽃이", 1, 2), ("천천히", 2, 3), ("피어", 3, 4), ("납니다.", 4, 5)],
                      "꽃이 천천히", 1, 3, 384, ["작은", "꽃이", "천천히", "피어", "납니다"])
        self.assertEqual(norm("가"), norm("가"))

    def test_chinese(self):
        self.exercise("zh", "小花慢慢开放，garden里有123.45朵花。", [("小花慢慢", 0, 4), ("开放，", 4, 6), ("garden", 6, 7),
                      ("里有", 7, 9), ("123.45", 9, 10), ("朵花。", 10, 12)], "花慢慢开", 1, 5, 384,
                      ["小", "花", "慢", "慢", "开", "放", "garden", "里", "有", "12345", "朵", "花"])
        self.assertEqual(normalized_tokens("カ\u3099ラスと花"), ["ガ", "ラ", "ス", "と", "花"])
        self.assertEqual(normalized_tokens("ｶﾞラス"), ["ガ", "ラ", "ス"])
        self.assertEqual(norm("ＡＢＣ É e\u0301 ß!"), "abcééss")
        sentence = {"id": "s01-01", "text": "小花开放", "spoken_text": "小花开放"}
        self.assertTrue(narrate_film.asr_differences([sentence], [{"word": "石头滚动"}]))

    def test_sentence_ends(self):
        split = narrate_film.sentences("小花在阳光下慢慢地开了。妈妈笑着说：“真好看！”然后走进了屋里。[pause]明天它还会继续开吗？", "zh")
        self.assertEqual([s["text"] for s in split], ["小花在阳光下慢慢地开了。", "妈妈笑着说：“真好看！”然后走进了屋里。", "明天它还会继续开吗？"])
        self.assertEqual([s["pause_before"] for s in split], [False, False, True])
        split = narrate_film.sentences("छोटा फूल खिला। क्या कल भी खिलेगा?", "hi")
        self.assertEqual([s["text"] for s in split], ["छोटा फूल खिला।", "क्या कल भी खिलेगा?"])
        # Stanza splits both texts; only the boundary after a sentence terminal and its closing quote counts.
        split = narrate_film.sentences("Une graine repose dans la terre ; deux feuilles poussent vers le soleil.", "fr")
        self.assertEqual(len(split), 1)
        split = narrate_film.sentences('The gardener smiles and says, "It grows." Then she waters the soil.', "en")
        self.assertEqual([s["text"] for s in split], ['The gardener smiles and says, "It grows."', "Then she waters the soil."])

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
