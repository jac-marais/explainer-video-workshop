"""Caption diagnostics use synthetic frame bytes without decoding or rendering media."""
from pathlib import Path
import unittest
from unittest.mock import patch

from check_film import caption_checks


class CaptionCheckTests(unittest.TestCase):
    def test_onset_failure_explains_early_cut_for_two_languages(self):
        for text in ("A small flower opens.", "小花慢慢开放。"):
            with self.subTest(text=text):
                cues = [{"id": "s01-01-C01", "start": 1, "end": 2, "text": text}]
                with patch("check_film.select_frames", side_effect=lambda path, indices, *args: {n: bytes([255] * 300) for n in indices}):
                    _, failures = caption_checks(Path("unused.mp4"), cues, 30, 100, (0, 0, 30, 10))
                onset = next(message for message in failures if "onset" in message)
                self.assertIn("no change within a frame", onset)
                self.assertIn("sentence cue", onset)
                self.assertIn("FILM.caption_onsets", onset)
                self.assertIn("pause before the cue", onset)

    def test_correct_caption_edges_still_pass(self):
        def frames(path, indices, *args):
            return {n: bytes([255 if 30 <= n < 60 else 0] * 300) for n in indices}
        with patch("check_film.select_frames", side_effect=frames):
            _, failures = caption_checks(Path("unused.mp4"), [{"id": "first", "start": 1, "end": 2, "text": "A flower."}],
                                         30, 100, (0, 0, 30, 10))
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
