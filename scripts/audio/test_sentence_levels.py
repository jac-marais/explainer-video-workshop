"""Synthetic samples exercise sentence matching without synthesis or media tools."""
import unittest

import numpy as np

import narrate_film as film


def tone(db, frames=20):
    wave = np.sin(2 * np.pi * 400 * np.arange(frames * 240) / film.RATE)
    return (wave * 10 ** (db / 20) * np.sqrt(2)).astype("float32")


class SentenceLevelTests(unittest.TestCase):
    def test_short_quiet_sentences_match_and_scene_flags_clear(self):
        audio = {str(i): np.concatenate([np.zeros(240), tone(db, frames), np.zeros(240)])
                 for i, (db, frames) in enumerate([(-25, 8), (-18, 60), (-24, 10), (-18, 80), (-18, 50)])}
        original = {sid: samples.copy() for sid, samples in audio.items()}
        matched, target, gains = film.match_sentence_levels(audio)
        self.assertAlmostEqual(target, -18, places=5)
        self.assertAlmostEqual(gains["0"], 7, places=5)
        self.assertAlmostEqual(gains["2"], 6, places=5)
        cursor, sentences, parts = 0, [], []
        for sid, samples in matched.items():
            self.assertEqual(len(samples), len(audio[sid]))
            np.testing.assert_array_equal(audio[sid], original[sid])
            np.testing.assert_array_equal(samples[audio[sid] == 0], audio[sid][audio[sid] == 0])
            sentences.append({"id": sid, "start": cursor / film.RATE, "end": (cursor + len(samples)) / film.RATE})
            cursor += len(samples)
            parts.append(samples)
        flags, _ = film.level_flags(sentences, list(matched), np.concatenate(parts), film.RATE)
        self.assertFalse([flag for flag in flags if flag["check"] in ("loudness_outlier", "scene_jump")])

    def test_deadband_and_symmetric_gain_cap(self):
        audio = {str(i): tone(db) for i, db in enumerate([-40, -21.1, -20, -18.9, -7])}
        _, target, gains = film.match_sentence_levels(audio)
        self.assertAlmostEqual(target, -20, places=5)
        self.assertEqual(gains, {"0": 8, "1": 0, "2": 0, "3": 0, "4": -8})

    def test_boost_stops_at_the_peak_ceiling_without_clipping(self):
        quiet = tone(-24)
        quiet[100], quiet[200] = 0.5, -0.5
        audio = {"quiet": quiet, "normal": tone(-18), "other": tone(-18)}
        matched, _, gains = film.match_sentence_levels(audio)
        ceiling = 10 ** (film.SENTENCE_PEAK_DBFS / 20)
        self.assertAlmostEqual(gains["quiet"], film.SENTENCE_PEAK_DBFS - 20 * np.log10(0.5), places=4)
        self.assertAlmostEqual(float(np.max(np.abs(matched["quiet"]))), ceiling, places=6)
        np.testing.assert_allclose(matched["quiet"], quiet * 10 ** (gains["quiet"] / 20), rtol=1e-6)

    def test_unboosted_sentence_keeps_a_peak_above_the_ceiling(self):
        hot = tone(-18)
        hot[100], hot[200] = 0.95, -0.95
        audio = {"hot": hot, "normal": tone(-18), "quiet": tone(-26)}
        matched, _, gains = film.match_sentence_levels(audio)
        self.assertEqual(gains["hot"], 0)
        np.testing.assert_array_equal(matched["hot"], hot)
        self.assertGreater(gains["quiet"], 0)

    def test_silence_and_partial_frames_remain_finite(self):
        audio = {"silent": np.zeros(480), "short": np.zeros(20), "tone": tone(-18)}
        matched, _, gains = film.match_sentence_levels(audio)
        for sid, samples in matched.items():
            self.assertTrue(np.isfinite(samples).all())
            self.assertLessEqual(abs(gains[sid]), 8)
            self.assertEqual(samples.shape, audio[sid].shape)


if __name__ == "__main__":
    unittest.main()
