"""Synthetic final-normalization regressions; no speech models are loaded."""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np
import soundfile as sf

import linux_levels as helper
import narrate_film as film


class LoudnessCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.wav = Path(self.folder.name) / 'final.wav'
        self.samples = .1 * np.sin(2 * np.pi * 400 * np.arange(48000) / 48000)
        sf.write(self.wav, self.samples, 48000, subtype='PCM_24')
        self.before = self.wav.read_bytes()

    def correct(self, meter, process):
        return helper.correct_loudness_file(
            self.wav, measure_loudness=meter, target_lufs=-16,
            tolerance_lu=film.LUFS_TOLERANCE, peak_ceiling_dbtp=-1.5,
            filter_context=process)

    def test_iterates_total_gain_from_original_pcm_and_records_encoded_measurements(self):
        meter = Mock(side_effect=[{'input_i': '-18', 'input_tp': '-1.5'},
                                  {'input_i': '-16.6', 'input_tp': '-1.6'},
                                  {'input_i': '-16.45', 'input_tp': '-1.6'}])
        contexts, gains = [], []
        def process(samples, rate, gain):
            contexts.append(samples.copy()); gains.append(gain)
            return samples * 10 ** (gain / 20)
        result = self.correct(meter, process)
        self.assertEqual(len(result['attempts']), 2)
        self.assertAlmostEqual(gains[0], 1.5)
        self.assertAlmostEqual(gains[1], 1.6)
        np.testing.assert_array_equal(contexts[0], contexts[1])
        self.assertEqual(result['after_lufs'], -16.45)
        self.assertTrue(result['target_reached'])
        self.assertTrue(result['total_frames_identical'])
        self.assertEqual(sf.info(self.wav).frames, len(self.samples))
        self.assertEqual(result['filter'], helper.filter_graph(48000, gains[-1]))

    def test_passing_or_not_peak_bound_never_calls_filter_or_changes_file(self):
        for loudness, peak in [(-16.8, -1.5), (-17, -1.5), (-18, -6)]:
            with self.subTest(loudness=loudness, peak=peak):
                meter = Mock(return_value={'input_i': str(loudness), 'input_tp': str(peak)})
                process = Mock(side_effect=AssertionError('Unexpected filtering'))
                self.assertIsNone(self.correct(meter, process))
                process.assert_not_called()
                self.assertEqual(self.wav.read_bytes(), self.before)

    def test_unresponsive_limiter_stops_at_cap_and_leaves_failure_visible(self):
        meter = Mock(return_value={'input_i': '-18', 'input_tp': '-1.5'})
        result = self.correct(meter, lambda samples, rate, gain: samples)
        self.assertEqual(result['gain_db'], helper.GAIN_CAP_DB)
        self.assertTrue(result['gain_cap_reached'])
        self.assertFalse(result['target_reached'])
        self.assertEqual(result['after_lufs'], -18)

    def test_invalid_length_or_peak_is_rejected_without_replacing_original(self):
        meter = Mock(return_value={'input_i': '-18', 'input_tp': '-1.5'})
        with self.assertRaisesRegex(ValueError, 'frame count'):
            self.correct(meter, lambda samples, rate, gain: samples[:-1])
        self.assertEqual(self.wav.read_bytes(), self.before)
        meter = Mock(side_effect=[{'input_i': '-18', 'input_tp': '-1.5'},
                                  {'input_i': '-16.4', 'input_tp': '-1.4'}])
        with self.assertRaisesRegex(ValueError, 'true-peak ceiling'):
            self.correct(meter, lambda samples, rate, gain: samples)
        self.assertEqual(self.wav.read_bytes(), self.before)

    def test_correction_metadata_flows_into_final_check_stats(self):
        correction = {'reason': 'peak_bound_loudness', 'total_frames_identical': True}
        timing = {'sentences': [], 'duration': 1, 'loudness_correction': correction}
        with patch.object(film, 'level_flags', return_value=([], {})), \
                patch.object(film, 'asr_differences', return_value=[]), \
                patch.object(film, 'measure_loudness', return_value={'input_i': '-16.4', 'input_tp': '-1.6'}):
            flags, stats = film.audio_checks(timing, self.wav, [], [])
        self.assertEqual(flags, [])
        self.assertEqual(stats['loudness_correction'], correction)


@unittest.skipUnless(shutil.which('ffmpeg'), 'Requires the media processor')
class NormalizationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.raw, self.final = self.root / 'raw.wav', self.root / 'final.wav'
        self.samples = .22 * np.sin(2 * np.pi * 400 * np.arange(4 * film.RATE + 137) / film.RATE)
        self.samples[:2400] = 0; self.samples[-2400:] = 0

    def baseline(self):
        baseline = self.root / 'baseline.wav'
        with patch.object(helper, 'correct_loudness_file', return_value=None):
            film.normalize(self.raw, baseline, preserve_take_levels=True)
        return baseline

    def test_peak_bound_run_reaches_loudness_margin_without_changing_frames_or_cache(self):
        self.samples[[film.RATE // 2, 2 * film.RATE]] = [.95, -.95]
        sf.write(self.raw, self.samples, film.RATE, subtype='PCM_16')
        raw_bytes = self.raw.read_bytes()
        baseline = self.baseline()
        before = film.measure_loudness(baseline)
        self.assertLess(float(before['input_i']), -16 - film.LUFS_TOLERANCE)
        correction = {}
        with patch.object(film.sys, 'platform', 'linux'):
            film.normalize(self.raw, self.final, preserve_take_levels=True, correction=correction)
        after = film.measure_loudness(self.final)
        self.assertLessEqual(abs(float(after['input_i']) + 16), film.LUFS_TOLERANCE - helper.MARGIN_DB)
        self.assertLessEqual(float(after['input_tp']), -1.5)
        self.assertLessEqual(float(after['input_tp']), film.TRUE_PEAK_MAX)
        self.assertEqual(sf.info(self.final).frames, sf.info(baseline).frames)
        self.assertEqual(sf.info(self.final).frames, len(self.samples) * 2)
        self.assertEqual(sf.info(self.final).samplerate, 48000)
        self.assertEqual(sf.info(self.final).subtype, 'PCM_24')
        self.assertEqual(self.raw.read_bytes(), raw_bytes)
        self.assertTrue(correction['target_reached'])
        self.assertEqual(correction['after_lufs'], float(after['input_i']))
        self.assertEqual(correction['after_true_peak_dbtp'], float(after['input_tp']))

    def test_passing_run_keeps_exact_normalized_bytes(self):
        sf.write(self.raw, self.samples, film.RATE, subtype='PCM_16')
        baseline = self.baseline()
        correction = {}
        with patch.object(film.sys, 'platform', 'linux'), \
                patch.object(helper, '_filter_context', side_effect=AssertionError('Unexpected filtering')):
            film.normalize(self.raw, self.final, preserve_take_levels=True, correction=correction)
        self.assertEqual(self.final.read_bytes(), baseline.read_bytes())
        self.assertEqual(correction, {})

    def test_other_platform_keeps_peak_bound_constant_gain(self):
        self.samples[[film.RATE // 2, 2 * film.RATE]] = [.95, -.95]
        sf.write(self.raw, self.samples, film.RATE, subtype='PCM_16')
        baseline = self.baseline()
        with patch.object(film.sys, 'platform', 'other'), \
                patch.object(helper, 'correct_loudness_file', side_effect=AssertionError('Unexpected correction')):
            film.normalize(self.raw, self.final, preserve_take_levels=True)
        self.assertEqual(self.final.read_bytes(), baseline.read_bytes())


if __name__ == '__main__':
    unittest.main()
