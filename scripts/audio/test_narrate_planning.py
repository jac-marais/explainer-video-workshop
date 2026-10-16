"""Offline take-planning tests with invented narration."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import narrate_film as film


class PlanningTests(unittest.TestCase):
    def test_later_respellings_leave_earlier_pins_whole(self):
        quote = (film.re.compile(r'"([^"]+)"'), r'"[\1](en-us)"')
        word = (film.re.compile(r"\bGarden\b"), "[Garden](/ɡˈɑːɹdən/)")
        text = 'Ela disse "Garden walks help." e Garden.'
        self.assertEqual(film.respell(text, [quote, word]), 'Ela disse "[Garden walks help.](en-us)" e [Garden](/ɡˈɑːɹdən/).')
        self.assertEqual(film.respell(text, [word, quote]), 'Ela disse "[Garden](/ɡˈɑːɹdən/) walks help." e [Garden](/ɡˈɑːɹdən/).')

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



if __name__ == "__main__":
    unittest.main()
