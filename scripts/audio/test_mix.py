#!/usr/bin/env python3
"""Check synthesized stems, event handling and narration guards with generated audio."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf
import mix

TOOL = Path(__file__).with_name("mix.py")
EVENT_NAMES = {"key", "thump", "thud", "slam", "pop", "whoosh", "swish", "ding", "click", "tick", "spring", "note", "riser"}


class MixerTests(unittest.TestCase):
    def test_all_event_names_render_deterministically(self):
        self.assertEqual(set(mix.EFFECT_TRIM_DB), EVENT_NAMES)
        effects = mix.Effects(24000)
        for name in sorted(EVENT_NAMES):
            for pitch in (0, 7):
                with self.subTest(name=name, pitch=pitch):
                    sound = effects.render(name, np.random.default_rng(1), pitch)
                    repeated = effects.render(name, np.random.default_rng(1), pitch)
                    self.assertTrue(np.isfinite(sound).all())
                    self.assertGreater(len(sound), 0)
                    self.assertAlmostEqual(np.abs(sound).max(), 1.0)
                    np.testing.assert_array_equal(sound, repeated)

    def test_programs_cycle_by_order_for_arbitrary_ids(self):
        for count in (1, len(mix.SCENE_PROGRAMS) + 3):
            with self.subTest(count=count):
                scenes = [{"id": f"part-{index}", "start": index * 40.0} for index in range(count)]
                total = count * 40.0
                sections = mix.chord_timeline(scenes, total)
                self.assertEqual(sections[0][0], 0)
                self.assertEqual(sections[-1][1], total)
                self.assertTrue(all(first[1] == second[0] for first, second in zip(sections, sections[1:])))
                for index, scene in enumerate(scenes):
                    self.assertIs(mix.section_at(sections, scene["start"] + 0.1)[3], mix.SCENE_PROGRAMS[index % len(mix.SCENE_PROGRAMS)])
                renamed = [dict(scene, id="s01") for scene in scenes]
                self.assertEqual(sections, mix.chord_timeline(renamed, total))

    def test_short_music_has_no_negative_sections_and_exact_length(self):
        for seconds in (0.03, 2.0):
            with self.subTest(seconds=seconds):
                length = int(seconds * 24000)
                music, sections = mix.synthesize_music([{"start": 0}], 24000, length)
                self.assertEqual(len(music), length)
                self.assertTrue(np.isfinite(music).all())
                self.assertTrue(all(0 <= section[0] < section[1] <= seconds for section in sections))
                self.assertGreater(np.abs(music).max(), 0)

    def test_thinning_sorts_caps_and_softens_repeats(self):
        events = [{"name": "key", "t": time, "gain": 1} for time in (0.15, 0.06, 0.02, 0)]
        events += [{"name": name, "t": 0.07, "gain": 1} for name in ("tick", "click", "pop")]
        kept = mix.thin_events(events)
        self.assertEqual([event["t"] for event in kept], [0, 0.06, 0.07, 0.15])
        np.testing.assert_allclose([event["gain"] for event in kept if event["name"] == "key"], [1, 0.8, 0.64])

    def test_validation_rejects_invalid_scenes_and_events(self):
        timing = {"scenes": [{"start": 0}, {"start": 0.5}]}
        self.assertEqual(mix.validate_inputs(timing, [], 1)[1], [])
        self.assertEqual(mix.validate_inputs(timing, [{"name": "note", "t": 0}], 1)[1][0]["gain"], 1)
        for scenes in ([], [{"start": -0.1}], [{"start": float("nan")}], [{"start": 0.5}, {"start": 0.4}], [{"start": 1}]):
            with self.subTest(scenes=scenes), self.assertRaises(ValueError):
                mix.validate_inputs({"scenes": scenes}, [], 1)
        for event in ({"name": "unknown", "t": 0}, {"name": "key", "t": float("inf")},
                      {"name": "key", "t": -1}, {"name": "key", "t": 1},
                      {"name": "key", "t": 0, "gain": -1}, {"name": "key", "t": 0, "pitch": float("nan")}):
            with self.subTest(event=event), self.assertRaises(ValueError):
                mix.validate_inputs(timing, [event], 1)

    def test_effects_clipping_and_empty_events(self):
        np.testing.assert_array_equal(mix.synthesize_effects([], 24000, 100), np.zeros(100))
        buffer = np.zeros(4)
        mix.add_at(buffer, -2, np.arange(5), 1)
        np.testing.assert_array_equal(buffer, [2, 3, 4, 0])
        mix.add_at(buffer, 10, np.ones(3), 1)
        np.testing.assert_array_equal(buffer, [2, 3, 4, 0])

    def test_limiter_and_ducking(self):
        sample_rate = 24000
        audio = 0.95 * np.sin(2 * np.pi * 440 * np.arange(sample_rate) / sample_rate)
        limited, reduction = mix.true_peak_limit(audio, -1.7, sample_rate)
        self.assertGreater(reduction, 0)
        self.assertLessEqual(mix.true_peak_dbtp(limited), -1.5)
        audio[sample_rate // 3:2 * sample_rate // 3] = 0
        speech = mix.SpeechAnalysis(audio, sample_rate)
        gain = speech.ducking_gain(audio, 9, len(audio))
        self.assertTrue(np.isfinite(gain).all())
        self.assertGreater(gain[sample_rate // 2], gain[sample_rate // 4])

    def run_mixer(self, directory, narration, events):
        project = directory / "project-'#"
        audio = project / "audio"
        audio.mkdir(parents=True, exist_ok=True)
        sf.write(audio / "narration.wav", narration, 24000, subtype="FLOAT")
        (audio / "timing.json").write_text(json.dumps({"scenes": [{"id": "part", "start": 0}]}))
        event_file = directory / "sfx.json"
        event_file.write_text(json.dumps(events))
        output = directory / "mix.wav"
        stems = directory / "stems"
        result = subprocess.run([sys.executable, TOOL, "--project", project, "--events", event_file,
                                 "--out", output, "--stems", stems], capture_output=True, text=True)
        return result, output, stems

    def test_cli_writes_master_and_stems_with_and_without_events(self):
        sample_rate = 24000
        time = np.arange(sample_rate * 2) / sample_rate
        narration = 0.12 * np.sin(2 * np.pi * 220 * time)
        narration[int(0.7 * sample_rate):sample_rate] = 0
        for events in ([], [{"name": "key", "t": 0.5, "gain": 0.1, "pitch": 0}]):
            with self.subTest(events=events), tempfile.TemporaryDirectory() as temporary:
                result, output, stems = self.run_mixer(Path(temporary), narration, events)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                master, written_rate = sf.read(output)
                self.assertEqual(written_rate, sample_rate)
                self.assertEqual(len(master), len(narration))
                self.assertTrue(np.isfinite(master).all())
                self.assertEqual(sf.info(output).subtype, "PCM_24")
                self.assertLessEqual(mix.true_peak_dbtp(master), -1.5)
                self.assertLessEqual(abs(mix.integrated_loudness_lufs(master, sample_rate) - mix.integrated_loudness_lufs(narration, sample_rate)), 1)
                music, _ = sf.read(stems / "music.wav")
                effects, _ = sf.read(stems / "effects.wav")
                self.assertEqual(len(music), len(narration))
                self.assertEqual(len(effects), len(narration))
                np.testing.assert_allclose(master, narration + music + effects, atol=5e-7)
                self.assertEqual(np.max(np.abs(effects)) == 0, not events)

    def test_cli_fails_clearly_on_bad_narration(self):
        fixtures = [(np.zeros(0), "empty"), (np.zeros(24000), "silent"),
                    (np.ones((24000, 2)) * 0.1, "mono"), (np.ones(10) * 0.1, "20 ms"),
                    (np.full(24000, float("nan")), "finite")]
        for narration, message in fixtures:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temporary:
                result, output, _ = self.run_mixer(Path(temporary), narration, [])
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
