"""Synthetic level-correction tests; real ffmpeg probes are explicit opt-in."""
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import Mock, patch

import numpy as np

import narrate_film as film  # Measurement functions only; no speech/Stanza model loading.
import linux_levels as helper

RATE = 48000


def fixture(amplitudes, scenes=None):
    n, gap = 24000, 2400
    pieces, rows, cursor = [], [], 0
    for index, amplitude in enumerate(amplitudes):
        pieces.append(np.zeros(gap, dtype=np.int32)); cursor += gap
        samples = np.where(np.arange(n) % 48 < 24, amplitude, -amplitude)
        pcm = np.rint(samples * 2 ** 23).astype(np.int32) << 8
        pieces.append(pcm)
        rows.append({'id': f's{index}', 'scene_id': (scenes or ['same'] * len(amplitudes))[index],
                     'start': cursor / RATE, 'end': (cursor + n) / RATE})
        cursor += n
    pieces.append(np.zeros(gap, dtype=np.int32))
    return np.concatenate(pieces), rows


def run(pcm, rows, process):
    return helper.correct_levels(pcm, RATE, rows, frame_power=film.frame_power,
                                 sentence_level_db=film.sentence_level_db, frame_s=film.FRAME_S,
                                 level_dev_db=film.LEVEL_DEV_DB, scene_jump_db=film.SCENE_JUMP_DB,
                                 filter_context=process)


def gain_only(samples, rate, gain):
    return samples * 10 ** (gain / 20)


class CorrectionTests(unittest.TestCase):
    def test_good_audio_never_calls_processor_and_is_byte_identical(self):
        pcm, rows = fixture([.1, .1, .1])
        def forbidden(*args):
            self.fail('Already-good audio must not invoke a filter')
        output, result = run(pcm, rows, forbidden)
        self.assertEqual(result['plan'], [])
        self.assertEqual(output.tobytes(), pcm.tobytes())

    def test_one_quiet_sentence_lifts_and_preserves_all_other_pcm_and_source(self):
        pcm, rows = fixture([.1, .1, .06, .1, .1])
        original = pcm.copy(); calls = []
        def process(samples, rate, gain):
            calls.append(gain)
            return gain_only(samples, rate, gain)
        output, result = run(pcm, rows, process)
        self.assertGreaterEqual(len(calls), 1)
        self.assertEqual([p['id'] for p in result['plan']], ['s2'])
        start, end = round(rows[2]['start'] * RATE), round(rows[2]['end'] * RATE)
        self.assertTrue(np.array_equal(output[:start], pcm[:start]))
        self.assertTrue(np.array_equal(output[end:], pcm[end:]))
        self.assertTrue(np.array_equal(pcm, original))
        self.assertEqual(len(output), len(pcm))
        self.assertTrue(np.all((output & 255) == 0))
        self.assertLess(abs(result['after_db']['s2'] - result['median_after_db']), film.LEVEL_DEV_DB)
        self.assertTrue(result['plan'][0]['target_reached'])

    def test_peaky_sentence_single_pass_at_gate_retries_until_margin_is_measured(self):
        pcm, rows = fixture([.12, .12, .06, .12, .12])
        start, end = round(rows[2]['start'] * RATE), round(rows[2]['end'] * RATE)
        pcm[start + 480:end:960] = int(round(.9 * 2 ** 23)) << 8
        contexts = []
        def limited(samples, rate, gain):
            contexts.append(samples.copy())
            return np.clip(gain_only(samples, rate, gain), -.8, .8)
        output, result = run(pcm, rows, limited)
        plan = result['plan'][0]
        first = plan['attempts'][0]
        first_deviation = first['after_db'] - result['median_before_db']
        self.assertLess(first['gain_db'], helper.GAIN_CAP_DB)
        self.assertLess(first_deviation, -film.LEVEL_DEV_DB)
        self.assertEqual(round(first_deviation, 1), -film.LEVEL_DEV_DB)
        self.assertGreater(len(plan['attempts']), 1)
        self.assertTrue(plan['target_reached'])
        self.assertFalse(plan['gain_cap_reached'])
        self.assertGreaterEqual(result['after_db']['s2'], plan['target_db'])
        self.assertLessEqual(result['median_after_db'] - result['after_db']['s2'],
                             film.LEVEL_DEV_DB - helper.MARGIN_DB)
        gains = [a['gain_db'] for a in plan['attempts']]
        self.assertTrue(all(a < b <= helper.GAIN_CAP_DB for a, b in zip(gains, gains[1:])))
        for context in contexts[1:]:
            np.testing.assert_array_equal(context, contexts[0])
        self.assertEqual(plan['gain_db'], gains[-1])
        self.assertLess(np.max(np.abs(output.astype(np.float64) / 2 ** 31)), .81)
        np.testing.assert_array_equal(output[:start], pcm[:start])
        np.testing.assert_array_equal(output[end:], pcm[end:])
        flags, _ = film.level_flags(rows, [s['scene_id'] for s in rows],
                                    output.astype(np.float32) / np.float32(2 ** 31), RATE)
        self.assertFalse(any(f['check'] == 'loudness_outlier' for f in flags))

    def test_unresponsive_limiter_stops_at_total_cap_and_reports_unmet_target(self):
        pcm, rows = fixture([.1, .1, .06, .1, .1])
        calls = []
        def unresponsive(samples, rate, gain):
            calls.append(gain)
            return samples.copy()
        output, result = run(pcm, rows, unresponsive)
        plan = result['plan'][0]
        self.assertEqual(calls[-1], helper.GAIN_CAP_DB)
        self.assertTrue(all(g <= helper.GAIN_CAP_DB for g in calls))
        self.assertLessEqual(len(calls), 1 + int(np.ceil(helper.GAIN_CAP_DB / helper.MIN_GAIN_STEP_DB)))
        self.assertTrue(plan['gain_cap_reached'])
        self.assertFalse(plan['target_reached'])
        np.testing.assert_array_equal(output, pcm)

    def test_revisits_target_when_another_scene_lift_moves_the_median(self):
        pcm, rows = fixture([.075, .12, .10, .16], ['a', 'a', 'b', 'c'])
        output, result = run(pcm, rows, gain_only)
        self.assertGreater(result['median_after_db'], result['median_before_db'])
        first = result['plan'][0]
        self.assertGreater(first['target_db'], first['attempts'][0]['target_db'])
        for entry in result['plan']:
            self.assertTrue(entry['target_reached'])
            self.assertGreaterEqual(result['after_db'][entry['id']], entry['target_db'])

    def test_high_crest_quiet_span_uses_peak_control_instead_of_unsafe_gain(self):
        pcm, rows = fixture([.1, .1, .06, .1, .1])
        peak = round((rows[2]['start'] + .25) * RATE)
        pcm[peak] = int(round(.9 * 2 ** 23)) << 8
        seen = []
        def limited(samples, rate, gain):
            raised = gain_only(samples, rate, gain)
            seen.append(float(np.max(np.abs(raised))))
            # Bounded deterministic processor double, not an audio-quality model.
            return np.clip(raised, -.8, .8)
        output, result = run(pcm, rows, limited)
        self.assertGreater(seen[0], 1)
        self.assertLess(np.max(np.abs(output.astype(np.float64) / 2 ** 31)), .81)
        self.assertLess(abs(result['after_db']['s2'] - result['median_after_db']), film.LEVEL_DEV_DB)

    def test_pt_like_scene_endpoint_uses_scene_constraint_not_only_quiet_target(self):
        pcm, rows = fixture([.1, .1, .06, .1, .1], ['a', 'a', 'b', 'b', 'b'])
        output, result = run(pcm, rows, gain_only)
        plan = result['plan'][0]
        self.assertIn('quiet_scene_boundary_endpoint', plan['reason'])
        self.assertAlmostEqual(plan['target_db'], result['before_db']['s1'] - film.SCENE_JUMP_DB + helper.MARGIN_DB)
        self.assertLess(abs(result['after_db']['s2'] - result['after_db']['s1']), film.SCENE_JUMP_DB)

    def test_scene_jump_can_select_below_median_endpoint_without_outlier(self):
        pcm, rows = fixture([.1, .11, .075, .1, .1], ['a', 'a', 'b', 'b', 'b'])
        output, result = run(pcm, rows, gain_only)
        self.assertEqual(result['plan'][0]['reason'], ['quiet_scene_boundary_endpoint'])
        self.assertLess(abs(result['after_db']['s2'] - result['after_db']['s1']), film.SCENE_JUMP_DB)

    def test_gain_cap_is_reported_and_unresolved_quietness_remains_visible(self):
        pcm, rows = fixture([.1, .1, .015, .1, .1])
        output, result = run(pcm, rows, gain_only)
        self.assertEqual(result['plan'][0]['gain_db'], 4)
        self.assertTrue(result['plan'][0]['gain_cap_reached'])
        self.assertGreater(result['median_after_db'] - result['after_db']['s2'], film.LEVEL_DEV_DB)

    def test_changed_length_is_rejected_without_hidden_padding(self):
        pcm, rows = fixture([.1, .1, .06, .1, .1])
        with self.assertRaisesRegex(ValueError, 'frame count'):
            run(pcm, rows, lambda samples, rate, gain: samples[:-1])

    def test_clipping_and_nonfinite_processor_results_are_rejected(self):
        pcm, rows = fixture([.1, .1, .06, .1, .1])
        for value, message in [(2., 'clip'), (float('nan'), 'nonfinite')]:
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, message):
                run(pcm, rows, lambda samples, rate, gain: np.full_like(samples, value))

    def test_file_wrapper_preserves_good_file_bytes(self):
        import soundfile as sf
        pcm, rows = fixture([.1, .1, .1])
        with tempfile.TemporaryDirectory() as folder:
            wav = Path(folder) / 'narration.wav'
            sf.write(wav, pcm, RATE, subtype='PCM_24')
            before = wav.read_bytes()
            result = helper.correct_file(
                wav, rows, frame_power=film.frame_power, sentence_level_db=film.sentence_level_db,
                frame_s=film.FRAME_S, level_dev_db=film.LEVEL_DEV_DB, scene_jump_db=film.SCENE_JUMP_DB,
                filter_context=gain_only)
            self.assertEqual(result['plan'], [])
            self.assertEqual(wav.read_bytes(), before)

    def test_file_wrapper_verifies_encoded_outside_pcm_and_rate(self):
        import soundfile as sf
        pcm, rows = fixture([.1, .1, .06, .1, .1])
        with tempfile.TemporaryDirectory() as folder:
            wav = Path(folder) / 'narration.wav'
            sf.write(wav, pcm, RATE, subtype='PCM_24')
            helper.correct_file(
                wav, rows, frame_power=film.frame_power, sentence_level_db=film.sentence_level_db,
                frame_s=film.FRAME_S, level_dev_db=film.LEVEL_DEV_DB, scene_jump_db=film.SCENE_JUMP_DB,
                filter_context=gain_only)
            output, rate = sf.read(wav, dtype='int32')
            self.assertEqual(rate, RATE)
            self.assertEqual(len(output), len(pcm))
            a, b = round(rows[2]['start'] * RATE), round(rows[2]['end'] * RATE)
            self.assertTrue(np.array_equal(output[:a], pcm[:a]))
            self.assertTrue(np.array_equal(output[b:], pcm[b:]))

    def test_overlapping_sentences_rejected(self):
        pcm, rows = fixture([.1, .1, .06])
        rows[1]['start'] = rows[0]['end'] - .01
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            run(pcm, rows, gain_only)

    def test_media_child_has_closed_stdin_bounded_wait_and_cleanup(self):
        samples = np.zeros(4800)
        process = Mock()
        process.wait.return_value = 0
        with tempfile.TemporaryDirectory() as scratch, \
                patch.object(helper.subprocess, 'Popen', return_value=process) as start, \
                patch.object(helper, '_stop_owned') as stop, \
                patch('soundfile.read', return_value=(samples.copy(), RATE)):
            output = helper._filter_context(samples, RATE, 2, scratch, 'ffmpeg')
        self.assertEqual(start.call_args.kwargs['stdin'], helper.subprocess.DEVNULL)
        self.assertTrue(start.call_args.kwargs['start_new_session'])
        process.wait.assert_called_once_with(timeout=helper.FILTER_TIMEOUT_S)
        stop.assert_called_once_with(process)
        np.testing.assert_array_equal(output, samples)



@unittest.skipUnless(os.environ.get('RUN_FFMPEG_LEVEL_TESTS') == '1' and shutil.which('ffmpeg'),
                     'Run media probes explicitly through the heavy wrapper')
class RealFilterTests(unittest.TestCase):
    def test_exact_profile_has_zero_impulse_lag_and_equal_frames_at_two_lengths(self):
        for n in (24000, 38641):
            samples = np.zeros(n)
            marks = [32, n // 2, n - 33]
            samples[marks] = [.01, -.015, .012]
            with tempfile.TemporaryDirectory() as scratch:
                output = helper._filter_context(samples, RATE, 2, scratch, 'ffmpeg')
            self.assertEqual(len(output), n)
            for mark in marks:
                a, b = mark - 24, mark + 25
                self.assertEqual(a + np.argmax(np.abs(output[a:b])), mark)

    def test_low_level_tone_receives_requested_gain_without_auto_makeup(self):
        samples = .01 * np.sin(2 * np.pi * 400 * np.arange(RATE) / RATE)
        with tempfile.TemporaryDirectory() as scratch:
            output = helper._filter_context(samples, RATE, 2, scratch, 'ffmpeg')
        middle = slice(RATE // 10, 9 * RATE // 10)
        ratio = np.linalg.norm(output[middle]) / np.linalg.norm(samples[middle])
        self.assertAlmostEqual(ratio, 10 ** (2 / 20), delta=.002)

    def test_real_high_crest_correction_keeps_unselected_pcm_and_scene_gate(self):
        pcm, rows = fixture([.1, .1, .06, .1, .1], ['a', 'a', 'b', 'b', 'b'])
        peak = round((rows[2]['start'] + .25) * RATE)
        pcm[peak] = int(round(.9 * 2 ** 23)) << 8
        with tempfile.TemporaryDirectory() as scratch:
            output, result = helper.correct_levels(
                pcm, RATE, rows, frame_power=film.frame_power, sentence_level_db=film.sentence_level_db,
                frame_s=film.FRAME_S, level_dev_db=film.LEVEL_DEV_DB, scene_jump_db=film.SCENE_JUMP_DB,
                scratch_dir=scratch)
        start, end = round(rows[2]['start'] * RATE), round(rows[2]['end'] * RATE)
        self.assertTrue(np.array_equal(output[:start], pcm[:start]))
        self.assertTrue(np.array_equal(output[end:], pcm[end:]))
        self.assertEqual(len(output), len(pcm))
        self.assertLess(abs(result['after_db']['s2'] - result['after_db']['s1']), film.SCENE_JUMP_DB)


if __name__ == '__main__':
    unittest.main()
