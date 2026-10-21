"""Offline span-repair tests using invented narration and mocked Whisper."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np
import narrate_film as film


def sentence(sid, text, start, end):
    return dict(id=sid, text=text, spoken_text=text, start=start, end=end)


def word(text, start, end):
    return dict(word=text, start=start, end=end)


def result(words):
    return {"segments": [{"words": words}]}


class EdgeSilenceTests(unittest.TestCase):
    def tone(self, seconds):
        t = np.arange(round(seconds * film.RATE)) / film.RATE
        return np.sin(2 * np.pi * 400 * t).astype(np.float32)

    def silence(self, seconds):
        return np.zeros(round(seconds * film.RATE), dtype=np.float32)

    def test_long_edges_are_capped(self):
        tone = self.tone(1)
        samples = np.concatenate([self.silence(1), tone, self.silence(1)])
        expected = np.concatenate([self.silence(.3), tone, self.silence(.3)])
        np.testing.assert_array_equal(film.cap_edge_silence(samples), expected)

    def test_second_pass_is_identical(self):
        samples = np.concatenate([self.silence(1), self.tone(1), self.silence(1)])
        capped = film.cap_edge_silence(samples)
        np.testing.assert_array_equal(film.cap_edge_silence(capped), capped)
        self.assertIs(film.cap_edge_silence(capped), capped)

    def test_silence_returns_input(self):
        samples = self.silence(3)
        self.assertIs(film.cap_edge_silence(samples), samples)

    def test_quiet_breath_is_kept(self):
        breath = self.tone(.1) * 10 ** (-30 / 20)
        rest = np.concatenate([breath, self.silence(.6), self.tone(1)])
        samples = np.concatenate([self.silence(1), rest, self.silence(1)])
        expected = np.concatenate([self.silence(.3), rest, self.silence(.3)])
        np.testing.assert_array_equal(film.cap_edge_silence(samples), expected)


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.samples = np.arange(16000 * 8, dtype=np.float32)
        self.whisper = Mock()
        self.loader = Mock(return_value=self.samples)
        self.modules = patch.dict(sys.modules, {
            "mlx_whisper": SimpleNamespace(transcribe=self.whisper),
            "linux_whisper": SimpleNamespace(transcribe=self.whisper, SAMPLE_RATE=16000, load_audio=self.loader),
            "mlx_whisper.audio": SimpleNamespace(SAMPLE_RATE=16000, load_audio=self.loader),
            "huggingface_hub": SimpleNamespace(snapshot_download=Mock(return_value="cached-model")),
        })
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.path = Path("narration.wav")

    def test_gap_repaired_offsets_and_midpoint_replacement(self):
        sents = [sentence("a", "Hello.", 0, 1), sentence("b", "Bright flowers bloom.", 2, 4),
                 sentence("c", "Goodbye.", 5, 6)]
        original = [word("Hello.", .1, .7), word("bloom.", 3.5, 3.9), word("Goodbye.", 5.1, 5.8)]
        replacement = [word("Bright", .2, .6), word("flowers", .7, 1.2), word("bloom.", 1.3, 1.9)]
        self.whisper.side_effect = [result(original), result(replacement)]
        asr, model = film.transcribe(self.path)
        self.assertTrue(film.align_words(sents, asr)[1])
        self.assertTrue(film.asr_differences(sents, asr))
        repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, asr)
        self.assertEqual((fallbacks, count, model), ([], 1, "cached-model"))
        self.assertEqual(film.asr_differences(sents, repaired), [])
        self.assertEqual([w["word"] for w in repaired], ["Hello.", "Bright", "flowers", "bloom.", "Goodbye."])
        self.assertEqual(repaired[0], original[0])
        self.assertEqual(repaired[-1], original[-1])
        self.assertAlmostEqual(repaired[1]["start"], 2.05)
        self.assertAlmostEqual(repaired[1]["end"], 2.45)
        self.assertEqual(rows[1][0]["start"], 2.05)
        self.loader.assert_called_once_with(str(self.path))
        np.testing.assert_array_equal(self.whisper.call_args.args[0], self.samples[29600:66400])
        self.assertEqual(self.whisper.call_count, 2)
        for call in self.whisper.call_args_list:
            self.assertEqual(call.kwargs, dict(path_or_hf_repo=film.WHISPER, language="en",
                                              word_timestamps=True, condition_on_previous_text=False))

    def test_fully_aligned_languages_have_identical_results_and_no_extra_call(self):
        for lang, text in [("en", "Hello garden."), ("pt", "Olá jardim."), ("es", "Hola jardín."),
                           ("ko", "여기 Garden으로 가요."), ("hi", "नीले फूल।")]:
            with self.subTest(language=lang):
                self.whisper.reset_mock()
                self.whisper.return_value = result([word(t, i + .1, i + .8) for i, t in enumerate(text.split())])
                sents = [sentence("a", text, 0, 3)]
                asr, _ = film.transcribe(self.path, lang)
                expected = film.align_words(sents, asr, lang)
                repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, asr, lang)
                self.assertIs(repaired, asr)
                self.assertEqual((rows, fallbacks), expected)
                self.assertEqual((fallbacks, count), ([], 0))
                self.whisper.assert_called_once()
                self.assertEqual(self.whisper.call_args.kwargs["language"], lang)
        self.loader.assert_not_called()

    def test_korean_term_is_heard_again_in_english(self):
        sents = [sentence("a", "여기 Garden으로 가요.", 2, 5)]
        original = [word("여기", 2.1, 2.6), word("가든으로", 2.7, 3.6), word("가요.", 3.8, 4.5)]
        native = [word(w["word"], w["start"] - 1.85, w["end"] - 1.85) for w in original]
        english = [word("Here", .25, .75), word("Garden", .85, 1.75), word("go.", 1.95, 2.65)]
        self.whisper.side_effect = [result(native), result(english)]
        self.assertEqual(len(film.align_words(sents, original, "ko")[1]), 1)
        stats = {}
        repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, original, "ko", stats=stats)
        self.assertEqual((fallbacks, count), ([], 1))
        self.assertEqual(stats, {"english_retranscribed_spans": 1})
        self.assertEqual([w["word"] for w in repaired], ["여기", "Garden", "가요."])
        self.assertEqual((repaired[0], repaired[-1]), (original[0], original[-1]))
        self.assertEqual(rows[0][1], dict(text="Garden으로", start=2.7, end=3.6))
        self.assertEqual([c.kwargs["language"] for c in self.whisper.call_args_list], ["ko", "en"])
        for call in self.whisper.call_args_list:
            np.testing.assert_array_equal(call.args[0], self.samples[29600:82400])
        self.loader.assert_called_once()

    def test_full_english_quote_is_heard_again_in_english(self):
        sents = [sentence("a", "꽃이 피어요.", 0, 1), sentence("b", '"Small birds sing softly."', 2, 5),
                 sentence("c", "끝이에요.", 6, 7)]
        original = [word("꽃이", .1, .4), word("피어요.", .5, .9), word("스몰", 2.1, 2.5),
                    word("버즈", 2.6, 3), word("싱", 3.1, 3.5), word("소프틀리.", 3.6, 4.5),
                    word("끝이에요.", 6.1, 6.8)]
        native = [word(w["word"], w["start"] - 1.85, w["end"] - 1.85) for w in original[2:6]]
        english = [word(t, .25 + i * .6, .75 + i * .6)
                   for i, t in enumerate(["Small", "birds", "sing", "softly."])]
        self.whisper.side_effect = [result(native), result(english)]
        self.assertEqual(len(film.align_words(sents, original, "ko")[1]), 4)
        repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, original, "ko")
        self.assertEqual((fallbacks, count), ([], 1))
        self.assertEqual(film.asr_differences(sents, repaired, "ko"), [])
        self.assertEqual(repaired[:2], original[:2])
        self.assertEqual(repaired[-1], original[-1])
        self.assertEqual([w["text"] for w in rows[1]], ['"Small', "birds", "sing", 'softly."'])
        self.assertEqual([c.kwargs["language"] for c in self.whisper.call_args_list], ["ko", "en"])

    def test_english_and_non_latin_fallbacks_do_not_rehear_in_english(self):
        for language, text, heard in [("en", "Garden", "flowers"), ("ko", "꽃이", "여기"),
                                      ("ko", "42", "여기")]:
            with self.subTest(language=language, text=text):
                self.whisper.reset_mock()
                self.whisper.return_value = result([word(heard, .2, .8)])
                sents = [sentence("a", text, 0, 1)]
                stats = {}
                original = [word(heard, .2, .8)]
                before = film.align_words(sents, original, language)
                self.assertTrue(before[1])
                repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, original,
                                                                          language, stats=stats)
                self.assertIs(repaired, original)
                self.assertEqual((rows, fallbacks), before)
                self.assertEqual(count, 1)
                self.assertEqual(stats, {})
                self.whisper.assert_called_once()
                self.assertEqual(self.whisper.call_args.kwargs["language"], language)

    def test_english_rehearing_without_improvement_is_discarded(self):
        sents = [sentence("a", "여기 Garden으로 가요.", 2, 5)]
        original = [word("여기", 2.1, 2.6), word("가든으로", 2.7, 3.6), word("가요.", 3.8, 4.5)]
        self.whisper.side_effect = [result([]), result([word("flowers", .85, 1.75)])]
        before = film.align_words(sents, original, "ko")
        repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, original, "ko")
        self.assertIs(repaired, original)
        self.assertEqual((rows, fallbacks), before)
        self.assertEqual(count, 1)
        self.assertEqual([c.kwargs["language"] for c in self.whisper.call_args_list], ["ko", "en"])

    def test_english_merge_keeps_the_native_transcript_with_fewer_fallbacks(self):
        sents = [sentence("a", "꽃이 Garden green.", 0, 2)]
        original = [word("꽃이", .1, .5), word("가든", .6, 1.1), word("그린.", 1.2, 1.8)]
        english = [word("Garden", .6, 1.1), word("green.", 1.2, 1.8)]
        native = [word("여기", .1, .5), *english]
        self.assertEqual(len(film.align_words(sents, original, "ko")[1]), 2)
        self.assertEqual(len(film.align_words(sents, native, "ko")[1]), 1)
        self.whisper.side_effect = [result(native), result(english)]
        repaired, _, fallbacks, count = film.align_with_repairs(self.path, sents, original, "ko")
        self.assertEqual((fallbacks, count), ([], 1))
        self.assertEqual(repaired, [original[0], *english])

    def test_adjacent_spans_merge_clamp_and_load_once(self):
        sents = [sentence("a", "Alpha", .05, 1), sentence("b", "Beta", 1.2, 2),
                 sentence("c", "Gamma", 3, 4), sentence("d", "Delta", 7, 8)]
        initial = ([[], [], [], []], [{"sentence": sid, "word": "花", "start": 0} for sid in ("a", "b", "d")])
        self.whisper.return_value = result([])
        with patch.object(film, "align_words", side_effect=[initial, ([], []), ([], [])]) as align:
            _, _, _, count = film.align_with_repairs(self.path, sents, [], "pt")
        self.assertEqual(count, 2)
        self.assertEqual(align.call_count, 3)
        self.loader.assert_called_once()
        np.testing.assert_array_equal(self.whisper.call_args_list[0].args[0], self.samples[:34400])
        np.testing.assert_array_equal(self.whisper.call_args_list[1].args[0], self.samples[109600:])
        self.assertTrue(all(c.kwargs["language"] == "pt" for c in self.whisper.call_args_list))

    def test_span_that_times_fewer_words_is_discarded(self):
        sents = [sentence("a", "Hello.", 0, 1), sentence("b", "Bright flowers bloom.", 2, 4)]
        original = [word("Hello.", .1, .7), word("bloom.", 3.5, 3.9)]
        self.whisper.return_value = result([word("Singing", .2, .6), word("loudly.", .7, 1.2)])
        before = film.align_words(sents, original)
        repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, original)
        self.assertIs(repaired, original)
        self.assertEqual((rows, fallbacks), before)
        self.assertEqual(count, 1)

    def test_empty_repair_is_not_retried(self):
        sents = [sentence("a", "Flowers bloom.", 1, 2)]
        self.whisper.return_value = result([])
        _, _, fallbacks, count = film.align_with_repairs(self.path, sents, [])
        self.assertTrue(fallbacks)
        self.assertEqual(count, 1)
        self.whisper.assert_called_once()

    def test_failed_merged_span_is_reheard_sentence_by_sentence(self):
        sents = [sentence("a", "नीले फूल।", .05, 1), sentence("b", "छोटे पक्षी।", 1.2, 2)]
        original = []
        self.whisper.side_effect = [result([]),
                                    result([word("नीले", .2, .4), word("फूल।", .5, .8)]),
                                    result([word("छोटे", .2, .4), word("पक्षी।", .5, .8)])]
        stats = {}
        with patch.object(sys, "platform", "linux"):
            repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, original, "hi", stats=stats)
        self.assertEqual((fallbacks, count), ([], 3))
        self.assertEqual(stats, {"sentence_retranscribed_spans": 2})
        self.assertEqual(film.asr_differences(sents, repaired, "hi"), [])
        self.assertAlmostEqual(rows[1][0]["start"], 1.25)
        self.assertEqual([c.kwargs["language"] for c in self.whisper.call_args_list], ["hi"] * 3)
        for call, (start, end) in zip(self.whisper.call_args_list, [(0, 34400), (0, 18400), (16800, 34400)]):
            np.testing.assert_array_equal(call.args[0], self.samples[start:end])
        self.loader.assert_called_once()

    def test_sentence_retry_keeps_partial_merged_improvement_and_skips_clean_sentence(self):
        sents = [sentence("a", "नीले फूल।", 0, 1), sentence("b", "छोटे पक्षी।", 1.2, 2)]
        self.whisper.side_effect = [result([word("नीले", .2, .4), word("फूल।", .5, .8)]),
                                    result([word("छोटे", .2, .4), word("पक्षी।", .5, .8)])]
        with patch.object(sys, "platform", "linux"):
            repaired, _, fallbacks, count = film.align_with_repairs(self.path, sents, [], "hi")
        self.assertEqual((fallbacks, count), ([], 2))
        self.assertEqual([w["word"] for w in repaired], ["नीले", "फूल।", "छोटे", "पक्षी।"])
        self.assertEqual(self.whisper.call_count, 2)
        np.testing.assert_array_equal(self.whisper.call_args.args[0], self.samples[16800:34400])

    def test_sentence_retries_without_strict_improvement_are_discarded(self):
        sents = [sentence("a", "नीले फूल।", 0, 1), sentence("b", "छोटे पक्षी।", 1.2, 2)]
        original = [word("नीले", .2, .4), word("छोटे", 1.3, 1.5)]
        self.whisper.side_effect = [result([]), result([word("नीले", .2, .4)]), result([])]
        expected = film.align_words(sents, original, "hi")
        with patch.object(sys, "platform", "linux"):
            repaired, rows, fallbacks, count = film.align_with_repairs(self.path, sents, original, "hi")
        self.assertIs(repaired, original)
        self.assertEqual((rows, fallbacks), expected)
        self.assertEqual(count, 3)

    def test_sentence_retries_preserve_existing_platform_and_english_paths(self):
        for platform, language, multi in [("darwin", "hi", True), ("linux", "en", True), ("linux", "hi", False)]:
            with self.subTest(platform=platform, language=language, multi=multi):
                self.whisper.reset_mock()
                self.whisper.return_value = result([])
                sents = [sentence("a", "नीले फूल।", 0, 1), sentence("b", "छोटे पक्षी।", 1.2, 2)]
                if not multi:
                    sents = sents[:1]
                with patch.object(sys, "platform", platform):
                    _, _, fallbacks, count = film.align_with_repairs(self.path, sents, [], language)
                self.assertTrue(fallbacks)
                self.assertEqual(count, 1)
                self.whisper.assert_called_once()

    def test_existing_span_repairs_finish_before_sentence_retries(self):
        sents = [sentence("a", "नीले फूल।", 0, 1), sentence("b", "छोटे पक्षी।", 1.2, 2),
                 sentence("c", "यहाँ।", 3, 4), sentence("d", "बादल।", 5, 6)]
        original = [word("यहाँ।", 3.2, 3.8)]
        self.whisper.side_effect = [result([]), result([word("बादल।", .2, .8)]),
                                    result([word("नीले", .2, .4), word("फूल।", .5, .8)]),
                                    result([word("छोटे", .2, .4), word("पक्षी।", .5, .8)])]
        with patch.object(sys, "platform", "linux"):
            _, _, fallbacks, count = film.align_with_repairs(self.path, sents, original, "hi")
        self.assertEqual((fallbacks, count), ([], 4))
        for call, (start, end) in zip(self.whisper.call_args_list,
                                      [(0, 34400), (77600, 98400), (0, 18400), (16800, 34400)]):
            np.testing.assert_array_equal(call.args[0], self.samples[start:end])

    def test_sentence_retry_padding_is_clamped_to_audio_end(self):
        sents = [sentence("a", "नीले फूल।", .05, 1), sentence("b", "छोटे पक्षी।", 7, 8)]
        self.whisper.side_effect = [result([]),
                                    result([word("नीले", .2, .4), word("फूल।", .5, .8)]),
                                    result([word("छोटे", .2, .4), word("पक्षी।", .5, .8)])]
        with patch.object(sys, "platform", "linux"):
            _, rows, fallbacks, count = film.align_with_repairs(self.path, sents, [], "hi")
        self.assertEqual((fallbacks, count), ([], 3))
        self.assertEqual(rows[1][0]["start"], 7.05)
        np.testing.assert_array_equal(self.whisper.call_args.args[0], self.samples[109600:])

    def test_sentence_retry_rehears_latin_fallbacks_in_english(self):
        sents = [sentence("a", "여기 Garden 가요.", 0, 1.5), sentence("b", "꽃이 피어요.", 2, 3)]
        original = [word("여기", .1, .3), word("가든", .4, .8), word("가요.", .9, 1.3)]
        native = original
        english = [word("Garden", .4, .8)]
        self.whisper.side_effect = [result([]), result([]), result(native), result(english),
                                    result([word("꽃이", .25, .5), word("피어요.", .6, .9)])]
        stats = {}
        with patch.object(sys, "platform", "linux"):
            repaired, _, fallbacks, count = film.align_with_repairs(self.path, sents, original, "ko", stats=stats)
        self.assertEqual((fallbacks, count), ([], 3))
        self.assertEqual(stats, {"english_retranscribed_spans": 2, "sentence_retranscribed_spans": 2})
        self.assertEqual([c.kwargs["language"] for c in self.whisper.call_args_list], ["ko", "en", "ko", "en", "ko"])
        self.assertEqual([w["word"] for w in repaired], ["여기", "Garden", "가요.", "꽃이", "피어요."])

    def test_check_only_uses_repaired_asr_and_records_count(self):
        sents = [sentence("a", "Flowers bloom.", 1, 2)]
        self.whisper.side_effect = [result([word("bloom.", 1.6, 1.9)]),
                                    result([word("Flowers", .2, .6), word("bloom.", .7, 1)])]
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            (root / "timing.json").write_text(json.dumps({"sentences": sents}))
            def checks(timing, wav, asr, unclean, language):
                return film.asr_differences(timing["sentences"], asr, language), {}
            with patch.object(film, "audio_checks", side_effect=checks), \
                    patch.object(film, "report", return_value={"ok": True}) as report, \
                    self.assertRaises(SystemExit) as stopped:
                film.check_only(root, None)
            self.assertEqual(stopped.exception.code, 0)
            self.assertEqual(report.call_args.args[:3], ([], {"retranscribed_spans": 1}, []))


if __name__ == "__main__":
    unittest.main()
