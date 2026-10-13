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

    def test_short_edges_return_input(self):
        samples = np.concatenate([self.silence(.1), self.tone(1), self.silence(.1)])
        self.assertIs(film.cap_edge_silence(samples), samples)

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
        for lang, text in [("en", "Hello garden."), ("pt", "Olá jardim."), ("es", "Hola jardín.")]:
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

    def test_adjacent_spans_merge_clamp_and_load_once(self):
        sents = [sentence("a", "Alpha", .05, 1), sentence("b", "Beta", 1.2, 2),
                 sentence("c", "Gamma", 3, 4), sentence("d", "Delta", 7, 8)]
        initial = ([[], [], [], []], [{"sentence": sid} for sid in ("a", "b", "d")])
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
