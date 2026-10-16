"""Caption and silence-edge diagnostics use synthetic frames and edge times without decoding or rendering media."""
from pathlib import Path
import unittest
from unittest.mock import patch

from check_film import caption_checks, silence_edges


class CaptionCheckTests(unittest.TestCase):
    def test_a_caption_that_never_appears_fails_its_onset(self):
        cues = [{"id": "s01-01-C01", "start": 1, "end": 2, "text": "A small flower opens."}]
        with patch("check_film.select_frames", side_effect=lambda path, indices, *args: {n: bytes([255] * 300) for n in indices}):
            _, failures = caption_checks(Path("unused.mp4"), cues, 30, 100, (0, 0, 30, 10))
        self.assertTrue(any("onset" in message for message in failures), failures)

    def test_correct_caption_edges_still_pass(self):
        def frames(path, indices, *args):
            return {n: bytes([255 if 30 <= n < 60 else 0] * 300) for n in indices}
        with patch("check_film.select_frames", side_effect=frames):
            _, failures = caption_checks(Path("unused.mp4"), [{"id": "first", "start": 1, "end": 2, "text": "A flower."}],
                                         30, 100, (0, 0, 30, 10))
        self.assertEqual(failures, [])


class SilenceEdgeTests(unittest.TestCase):
    MASTER = [2.0, 2.4, 6.1, 6.5, 9.0, 9.3]

    def test_one_edge_at_the_noise_floor_passes(self):
        for fps in (25, 30):
            with self.subTest(fps=fps):
                film = [2.0, 2.34, 6.1, 6.5, 9.0, 9.3]
                report, failure = silence_edges(self.MASTER, film, 10, fps)
                self.assertIsNone(failure)
                self.assertEqual(report["unmatched"], 1)

    def test_shifted_audio_fails(self):
        for fps, shift in ((25, 0.05), (30, 0.05), (30, 0.12)):
            with self.subTest(fps=fps, shift=shift):
                report, failure = silence_edges(self.MASTER, [m + shift for m in self.MASTER], 10, fps)
                self.assertEqual(report["unmatched"], 6)
                self.assertIn("more than 1 frame", failure)


if __name__ == "__main__":
    unittest.main()
