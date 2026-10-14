"""Offline take-planning tests."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import narrate_film as film


class PlanningTests(unittest.TestCase):
    def test_long_groups_are_split_with_headroom(self):
        seconds = {"S01": 100.0, "S02": 100.0}
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(film, "run_uv", return_value="S01-S02 120.0  || violation 0.0"), patch.object(film, "log"):
            runs = film.plan_runs(seconds, Path(directory))
        self.assertEqual(runs, [["S01"], ["S02"]])
        for run in runs:
            self.assertLessEqual(sum(seconds[s] for s in run) + film.TAKE_RESERVE_SECONDS, film.MAX_TAKE_SECONDS)

    def test_oversized_scene_fails_before_any_external_tool(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(film, "run_uv") as run:
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
