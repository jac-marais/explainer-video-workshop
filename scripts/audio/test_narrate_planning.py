"""Offline take-planning tests with invented multilingual narration."""
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import narrate_film as film


TEXTS = {"en": "A small flower opens in the garden.", "es": "Una flor pequeña se abre en el jardín.",
         "pt": "Uma flor pequena se abre no jardim.", "fr": "Une petite fleur s’ouvre dans le jardin.",
         "hi": "बगीचे में एक छोटा फूल खिलता है।", "zh": "花园里一朵小花慢慢开放。", "ko": "정원에서 작은 꽃이 피어나요."}


class PlanningTests(unittest.TestCase):
    def test_estimates_follow_phonemes_in_every_language(self):
        for language, text in TEXTS.items():
            with self.subTest(language=language):
                one, two, bare = film.estimate_seconds([text, f"{text} {text}", text.rstrip(".。।")], language)
                self.assertTrue(0.5 < one < 5, one)
                self.assertAlmostEqual(two / one, 2, delta=0.1)
                self.assertEqual(bare, one)
                self.assertIs(film.espeak(language), film.espeak(language))
        with self.assertRaisesRegex(SystemExit, "eSpeak has no voice"):
            film.estimate_seconds(["A seed."], "xx-invented")

    def test_estimated_scenes_split_into_runs_or_fail_before_voicing(self):
        for language, text in TEXTS.items():
            with self.subTest(language=language), tempfile.TemporaryDirectory() as directory:
                # A scene's estimate is the sum of its sentences', as voice_takes adds them.
                scene = sum(film.estimate_seconds([text] * math.ceil(60 / film.estimate_seconds([text], language)[0]), language))
                oversized = 2 * scene
                seconds = {"S01": scene, "S02": scene}
                with patch.object(film, "run_tool", return_value="S01-S02 120.0  || violation 0.0"), patch.object(film, "log"):
                    self.assertEqual(film.plan_runs(seconds, Path(directory)), [["S01"], ["S02"]])
                with patch.object(film, "run_tool") as run, self.assertRaisesRegex(SystemExit, "split its narration"):
                    film.plan_runs({"S01": oversized}, Path(directory))
                run.assert_not_called()

    def test_long_groups_are_split_with_headroom(self):
        seconds = {"S01": 100.0, "S02": 100.0}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(film, "run_tool", return_value="S01-S02 120.0  || violation 0.0"), patch.object(film, "log"):
            runs = film.plan_runs(seconds, Path(directory))
        self.assertEqual(runs, [["S01"], ["S02"]])
        for run in runs:
            self.assertLessEqual(sum(seconds[s] for s in run) + film.TAKE_RESERVE_SECONDS, film.MAX_TAKE_SECONDS)

    def test_oversized_scene_fails_before_any_external_tool(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(film, "run_tool") as run:
            with self.assertRaisesRegex(SystemExit, "split its narration"):
                film.plan_runs({"S01": 200.0}, Path(directory))
            run.assert_not_called()

    def test_exact_limit_is_allowed_and_rounding_cannot_exceed_it(self):
        limit = film.MAX_TAKE_SECONDS - film.TAKE_RESERVE_SECONDS
        self.assertEqual(film.bound_runs([["S01"]], {"S01": limit}), [["S01"]])
        seconds = {"S01": limit / 2, "S02": limit / 2 + 0.001}
        self.assertEqual(film.bound_runs([["S01", "S02"]], seconds), [["S01"], ["S02"]])


if __name__ == "__main__":
    unittest.main()
