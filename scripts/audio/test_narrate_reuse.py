# /// script
# requires-python = "==3.12.*"
# dependencies = ["numpy==2.5.3", "soundfile==0.14.0"]
# ///
"""Exercise narration reuse and provenance without loading or running a speech model."""
import argparse
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

import narrate_film as film


def rows(scene_ids=("opening", "middle-with-hyphens", "ending"), count=2):
    return [{"id": f"{scene}-{index:02d}", "scene_id": scene, "alias": f"S{number:02d}",
             "text": f"{scene} sentence {index}.", "spoken": f"{scene} sentence {index}.",
             "key": film.cache_key("voice-identity", f"{scene} sentence {index}.")}
            for number, scene in enumerate(scene_ids, 1) for index in range(1, count + 1)]


def source(current, directory="/tmp/old", groups=None, legacy=False):
    groups = groups or {"origin:three-scenes": [row["scene_id"] for row in current]}
    takes = {row["id"]: take for row in current for take, covered in groups.items() if row["scene_id"] in covered}
    return film.ReuseSource(Path(directory), {r["id"]: r["key"] for r in current}, None if legacy else takes,
                            {r["id"]: r["scene_id"] for r in current},
                            {r["id"]: Path(directory) / "sentences" / f"{r['id']}.wav" for r in current})


def tone(level_db, frames=20):
    wave = np.sin(2 * np.pi * 400 * np.arange(frames * 240) / film.RATE)
    return (wave * 10 ** (level_db / 20) * np.sqrt(2)).astype("float32")


class TakeGainTests(unittest.TestCase):
    def fixture(self):
        current = rows(count=2)
        scenes = [{"id": r["scene_id"], "title": "Scene", "visual": "Visual", "claim_ids": [],
                   "_sentences": [{"text": x["text"], "pause_before": index == 1 and number == 1}
                                  for index, x in enumerate(current[number * 2:number * 2 + 2])]} 
                  for number, r in enumerate(current[::2])]
        audio = {r["id"]: tone(db, frames=20 + index) for index, (r, db) in enumerate(zip(current, [-32, -28, -24, -20, -16, -12]))}
        takes = {r["id"]: f"take-{index // 2}" for index, r in enumerate(current)}
        return scenes, {r["id"]: r for r in current}, audio, takes

    def test_three_takes_match_medians_without_changing_sentence_dynamics_or_timing(self):
        scenes, current, audio, takes = self.fixture()
        original = {sid: data.copy() for sid, data in audio.items()}
        target, gains = film.calculate_take_gains(audio, takes)
        self.assertAlmostEqual(target, -22, places=5)
        self.assertEqual(set(gains), set(takes.values()))
        reference = film.assemble(scenes, current, audio)
        assembled = film.assemble(scenes, current, audio, takes, gains)
        self.assertEqual(assembled[1:], reference[1:])
        self.assertEqual(len(assembled[0]), len(reference[0]))
        medians = {}
        for row in assembled[2]:
            sid = row["id"]
            start = round(row["start"] * film.RATE)
            actual = assembled[0][start:start + len(audio[sid])]
            np.testing.assert_allclose(actual, audio[sid] * 10 ** (gains[takes[sid]] / 20))
            medians.setdefault(takes[sid], []).append(film.sentence_level_db(film.frame_power(actual, film.RATE)))
            np.testing.assert_array_equal(audio[sid], original[sid])
        for values in medians.values():
            self.assertAlmostEqual(sum(values) / 2, target, places=5)
            self.assertAlmostEqual(values[1] - values[0], 4, places=5)
        mask = reference[0] == 0
        np.testing.assert_array_equal(assembled[0][mask], reference[0][mask])

    def test_single_take_gain_is_zero(self):
        _, _, audio, _ = self.fixture()
        target, gains = film.calculate_take_gains(audio, {sid: "only" for sid in audio})
        self.assertAlmostEqual(target, -22, places=5)
        self.assertEqual(gains, {"only": 0})

    def test_level_measurement_keeps_strict_active_gate_and_discards_partial_frames(self):
        frames = np.array([1.0, 0.01, 0.001, 0.0001, 0], dtype="float64")
        self.assertAlmostEqual(film.sentence_level_db(frames), 10 * np.log10(0.505))
        samples = np.concatenate([np.full(240, 0.25), np.full(240, 0.5), np.full(239, 100)])
        np.testing.assert_array_equal(film.frame_power(samples, film.RATE), [0.0625, 0.25])
        self.assertEqual(film.sentence_level_db(np.zeros(5)), -180)
        self.assertEqual(film.sentence_level_db(np.array([])), -180)

    def test_level_flags_preserve_known_active_levels_and_silent_floor(self):
        samples = np.concatenate([np.zeros(2400, dtype="float32"), tone(-30), tone(-24), tone(-18), np.zeros(2400, dtype="float32")])
        sents = [{"id": str(index), "start": 0.1 + index * 0.2, "end": 0.3 + index * 0.2} for index in range(3)]
        flags, stats = film.level_flags(sents, ["first", "first", "second"], samples, film.RATE)
        self.assertEqual(stats["median_sentence_db"], -24)
        self.assertEqual(stats["max_dev_db"], 6)
        self.assertEqual([flag for flag in flags if flag["check"] == "loudness_outlier"],
                         [{"check": "loudness_outlier", "sentence": "0", "db_from_median": -6},
                          {"check": "loudness_outlier", "sentence": "2", "db_from_median": 6}])
        self.assertEqual([flag for flag in flags if flag["check"] == "scene_jump"],
                         [{"check": "scene_jump", "between": ["1", "2"], "db": 6}])

    def test_audio_checks_copy_recorded_gain_stats_for_check_only(self):
        timing = {"sentences": [{"id": "first", "scene_id": "opening", "text": "Hello.", "start": 0.1, "end": 0.3}],
                  "duration": 0.4, "take_gain_db": {"original": 4.5}, "take_target_sentence_db": -24,
                  "normalization_gain_db": -0.65, "final_take_target_sentence_db": -24.65}
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            wav = Path(directory) / "narration.wav"
            sf.write(wav, np.concatenate([np.zeros(2400), tone(-24), np.zeros(2400)]), film.RATE)
            with patch.object(film, "measure_loudness", return_value={"input_i": -16, "input_tp": -1.5}), \
                    patch.object(film, "asr_differences", return_value=[]):
                _, stats = film.audio_checks(timing, wav, [], [])
            self.assertEqual(stats["take_gain_db"], timing["take_gain_db"])
            self.assertEqual(stats["take_target_sentence_db"], timing["take_target_sentence_db"])
            self.assertEqual(stats["normalization_gain_db"], timing["normalization_gain_db"])
            self.assertEqual(stats["final_take_target_sentence_db"], timing["final_take_target_sentence_db"])


class NormalizationTests(unittest.TestCase):
    def test_common_gain_is_loudness_limited_or_peak_limited(self):
        for measured, expected in (({"input_i": "-20", "input_tp": "-10"}, 4),
                                   ({"input_i": "-16.40", "input_tp": "-0.90"}, -0.60)):
            with self.subTest(measured=measured), patch.object(film, "measure_loudness", return_value=measured), \
                    patch.object(film, "ffmpeg") as ffmpeg, patch.object(film, "log"):
                self.assertAlmostEqual(film.normalize(Path("raw.wav"), Path("final.wav"), preserve_take_levels=True), expected)
                ffmpeg.assert_called_once_with(["-y", "-i", "raw.wav", "-af", f"volume={expected:.8f}dB:precision=double",
                                               "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", "final.wav"])

    def test_kokoro_keeps_existing_two_pass_loudnorm(self):
        measured = {"input_i": "-20", "input_tp": "-10", "input_lra": "3", "input_thresh": "-30", "target_offset": "0.1"}
        with patch.object(film, "measure_loudness", return_value=measured), patch.object(film, "ffmpeg") as ffmpeg:
            self.assertIsNone(film.normalize(Path("raw.wav"), Path("final.wav"), preserve_take_levels=False))
        ffmpeg.assert_called_once_with(["-y", "-i", "raw.wav", "-af",
                                       "loudnorm=I=-16:TP=-1.5:LRA=11:measured_I=-20:measured_TP=-10:measured_LRA=3"
                                       ":measured_thresh=-30:offset=0.1:linear=true",
                                       "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", "final.wav"])


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.rows = rows()
        self.source = source(self.rows)

    def pending_scenes(self, decision, current=None):
        return {r["scene_id"] for r in (current or self.rows) if r["id"] not in decision.audio}

    def test_changed_sentence_invalidates_three_scene_take_for_every_run_engine(self):
        for engine in ("qwen3", "qwen3-preset", "chatterbox"):
            with self.subTest(engine=engine):
                changed = [dict(r) for r in self.rows]
                changed[2]["key"] = film.cache_key("voice-identity", "New words.")
                decision = film.decide_reuse(changed, engine, [self.source])
                self.assertEqual(decision.audio, {})
                self.assertEqual(self.pending_scenes(decision, changed), {r["scene_id"] for r in changed})

    def test_unchanged_take_reuses_every_sentence_and_origin(self):
        decision = film.decide_reuse(self.rows, "qwen3", [self.source])
        self.assertEqual(decision.audio, self.source.audio)
        self.assertEqual(decision.takes, self.source.takes)
        self.assertEqual(self.pending_scenes(decision), set())

    def test_one_changed_take_leaves_other_complete_takes_reused(self):
        current = self.rows + rows(("recap",), 2)
        old = source(current, groups={"first:three-scenes": [r["scene_id"] for r in self.rows],
                                      "second:recap": ["recap"]})
        changed = [dict(r) for r in current]
        changed[2]["key"] = "changed"
        decision = film.decide_reuse(changed, "qwen3", [old])
        self.assertEqual(set(decision.audio), {r["id"] for r in current if r["scene_id"] == "recap"})
        self.assertEqual(set(decision.takes.values()), {"second:recap"})
        self.assertEqual(self.pending_scenes(decision, changed), {r["scene_id"] for r in self.rows})

    def test_deleted_source_scene_invalidates_take(self):
        current = [r for r in self.rows if r["scene_id"] != "middle-with-hyphens"]
        self.assertEqual(film.decide_reuse(current, "qwen3", [self.source]).audio, {})

    def test_added_removed_or_reordered_sentence_invalidates_take(self):
        added = self.rows + rows(("opening",), 3)[-1:]
        variants = [added, self.rows[1:], [self.rows[1], self.rows[0], *self.rows[2:]], self.rows[2:] + self.rows[:2]]
        for current in variants:
            with self.subTest(ids=[r["id"] for r in current]):
                self.assertEqual(film.decide_reuse(current, "qwen3", [self.source]).audio, {})

    def test_missing_audio_or_voice_identity_change_invalidates_take(self):
        missing = source(self.rows)
        missing.audio.pop(self.rows[0]["id"])
        changed_identity = [{**r, "key": film.cache_key("different-voice", r["spoken"])} for r in self.rows]
        self.assertEqual(film.decide_reuse(self.rows, "qwen3", [missing]).audio, {})
        self.assertEqual(film.decide_reuse(changed_identity, "qwen3", [self.source]).audio, {})

    def test_legacy_clone_source_never_reused(self):
        self.assertEqual(film.decide_reuse(self.rows, "qwen3", [source(self.rows, legacy=True)]).audio, {})

    def test_kokoro_keeps_sentence_reuse_for_new_and_legacy_sources(self):
        changed = [dict(r) for r in self.rows]
        changed[2]["key"] = "changed"
        for legacy in (False, True):
            with self.subTest(legacy=legacy):
                decision = film.decide_reuse(changed, "kokoro", [source(self.rows, legacy=legacy)])
                self.assertEqual(len(decision.audio), len(self.rows) - 1)
                self.assertNotIn(changed[2]["id"], decision.audio)

    def test_kokoro_matches_cache_key_after_sentence_id_moves(self):
        moved = [{**r, "id": f"new-{r['id']}"} for r in self.rows]
        decision = film.decide_reuse(moved, "kokoro", [self.source])
        self.assertEqual(set(decision.audio), {r["id"] for r in moved})
        self.assertEqual(set(decision.takes.values()), {"origin:three-scenes"})

    def test_overlap_discards_lower_take_whole_in_both_source_orders(self):
        middle = [r for r in self.rows if r["scene_id"] == "middle-with-hyphens"]
        higher = source(middle, "/tmp/own", {"own:middle": ["middle-with-hyphens"]})
        decision = film.decide_reuse(self.rows, "qwen3", [self.source, higher])
        self.assertEqual(set(decision.audio), {r["id"] for r in middle})
        self.assertEqual(set(decision.takes.values()), {"own:middle"})
        self.assertEqual(self.pending_scenes(decision), {"opening", "ending"})
        reverse = film.decide_reuse(self.rows, "qwen3", [higher, self.source])
        self.assertEqual(reverse.audio, self.source.audio)
        self.assertEqual(reverse.takes, self.source.takes)

    def test_invalid_higher_take_does_not_hide_valid_lower_take(self):
        higher = source(self.rows, "/tmp/own")
        higher.hashes[self.rows[0]["id"]] = "stale"
        decision = film.decide_reuse(self.rows, "qwen3", [self.source, higher])
        self.assertEqual(decision.audio, self.source.audio)

    def test_own_output_only_preserves_take_and_own_output_wins_when_complete(self):
        own = source(self.rows, "/tmp/own", {"own:all": [r["scene_id"] for r in self.rows]})
        for sources in ([own], [self.source, own]):
            with self.subTest(sources=len(sources)):
                decision = film.decide_reuse(self.rows, "qwen3", sources)
                self.assertEqual(decision.audio, own.audio)
                self.assertEqual(decision.takes, own.takes)

    def test_multiple_takes_in_one_scene_cannot_be_partially_reused(self):
        broken = source(self.rows)
        broken.takes[self.rows[0]["id"]] = "separate:partial"
        self.assertEqual(film.decide_reuse(self.rows, "qwen3", [broken]).audio, {})

    def test_reused_unclean_cut_flags_and_manifest_survive(self):
        take = "origin:three-scenes"
        flag = {"check": "unclean_cut", "take": take, "after": self.rows[0]["id"], "gap_s": 0.01}
        manifest = {"sentences": [r["id"] for r in self.rows], "scenes": list(dict.fromkeys(r["scene_id"] for r in self.rows)),
                    "sha256": "original-raw-hash", "receipt_sha256": "original-receipt-hash"}
        self.source.unclean = [flag, {**flag, "take": "unused:take"}]
        self.source.manifests = {take: manifest}
        decision = film.decide_reuse(self.rows, "qwen3", [self.source])
        self.assertEqual(decision.unclean, [flag])
        self.assertEqual(decision.manifests, {take: manifest})

    def test_original_manifest_rejects_incomplete_provenance(self):
        take = "origin:three-scenes"
        self.source.manifests[take] = {"sentences": [r["id"] for r in self.rows],
                                        "scenes": [r["scene_id"] for r in self.rows] + ["deleted"]}
        self.assertEqual(film.decide_reuse(self.rows, "qwen3", [self.source]).audio, {})


class SourceLoadingTests(unittest.TestCase):
    def test_legacy_skip_logs_once_even_when_reuse_is_own_output(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            (root / "sentence-hashes.json").write_text(json.dumps({"first-01": "hash"}))
            with patch.object(film, "log") as log:
                self.assertEqual(film.load_reuse_sources([root, root], "qwen3"), [])
            log.assert_called_once_with(f"reuse skipped: {root} has no takes.json")
            with patch.object(film, "log") as log:
                self.assertEqual(len(film.load_reuse_sources([root, root], "kokoro")), 1)
            log.assert_not_called()

    def test_reads_actual_scene_ids_and_preserves_source_order(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root = Path(directory)
            (root / "sentences").mkdir()
            current = rows(("arbitrary-scene_id", "deleted-scene"), 1)
            (root / "sentence-hashes.json").write_text(json.dumps({r["id"]: r["key"] for r in current}))
            (root / "takes.json").write_text(json.dumps({r["id"]: "unique:take" for r in current}))
            (root / "timing.json").write_text(json.dumps({"sentences": [{"id": r["id"], "scene_id": r["scene_id"]} for r in current]}))
            for row in current:
                (root / "sentences" / f"{row['id']}.wav").write_bytes(b"exists")
            loaded = film.load_reuse_sources([root], "qwen3")
            self.assertEqual(film.decide_reuse(current, "qwen3", loaded).takes, {r["id"]: "unique:take" for r in current})
            self.assertEqual(film.decide_reuse(current[:1], "qwen3", loaded).audio, {})


class GenerationTests(unittest.TestCase):
    def fake_run_uv(self, script, args, capture=False):
        if script == "voice.py":
            for item in args:
                if isinstance(item, Path) and item.suffix == ".txt":
                    sf.write(item.with_suffix(".wav"), np.full(2400, 0.01, dtype="float32"), film.RATE, subtype="PCM_16")
                    item.with_suffix(".json").write_text(json.dumps({"duration_s": 0.1, "seed": 123}))
            return ""
        if script == "cut_takes.py":
            destination = args[args.index("--out") + 1]
            destination.mkdir()
            sentence_file = args[args.index("--sentences") + 1]
            for row in json.loads(sentence_file.read_text()):
                sf.write(destination / f"{row['id']}.wav", np.full(2400, 0.01, dtype="float32"), film.RATE, subtype="PCM_16")
            return json.dumps({"take": "S01-S03", "after": "opening-01", "clean": False, "gap_s": 0.02}) + "\n"
        self.fail(f"unexpected voice tool {script}")

    def test_whole_pending_scenes_are_grouped_and_provenance_matches_raw_hashes(self):
        current = rows(count=1)
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, patch.object(film, "run_uv", side_effect=self.fake_run_uv), \
                patch.object(film, "plan_runs", return_value=[["S01", "S02", "S03"]]) as planner:
            audio, takes, flags, manifests = film.voice_takes("clone", {"engine": "qwen3"}, current, Path(directory))
            self.assertEqual(set(audio), {r["id"] for r in current})
            self.assertEqual(set(planner.call_args.args[0]), {"S01", "S02", "S03"})
            self.assertEqual(len(set(takes.values())), 1)
            take = next(iter(takes.values()))
            self.assertEqual(flags[0]["take"], take)
            manifest = manifests[take]
            self.assertEqual(manifest["sentences"], [r["id"] for r in current])
            self.assertEqual(manifest["scenes"], [r["scene_id"] for r in current])
            self.assertEqual(manifest["sha256"], film.sha256(Path(manifest["wav"]).read_bytes()))
            self.assertEqual(manifest["receipt_sha256"], film.sha256(Path(manifest["receipt"]).read_bytes()))

    def test_kokoro_generations_get_unique_ids_per_sentence_and_rerun(self):
        current = rows(("opening",), 2)
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, patch.object(film, "run_uv", side_effect=self.fake_run_uv):
            first = film.voice_takes("kokoro", {"engine": "kokoro"}, current, Path(directory) / "first")
            second = film.voice_takes("kokoro", {"engine": "kokoro"}, current, Path(directory) / "second")
            self.assertEqual(len(set(first[1].values())), len(current))
            self.assertTrue(set(first[1].values()).isdisjoint(second[1].values()))
            self.assertEqual(first[2], [])

    def test_disk_gain_preserves_raw_sentence_bytes_across_external_reuse_and_reruns(self):
        for engine in ("qwen3", "chatterbox", "kokoro"):
            for reuse_mode in ("own", "external"):
                with self.subTest(engine=engine, reuse_mode=reuse_mode), tempfile.TemporaryDirectory(dir="/tmp") as directory:
                    root, current = Path(directory), rows(count=1)
                    scene_file, output = root / "scenes.json", root / "first"
                    scene_file.write_text(json.dumps([{"id": r["scene_id"], "title": "Scene", "visual": "Visual", "claim_ids": [],
                                                      "narration": r["text"]} for r in current]))
                    args = argparse.Namespace(scenes=scene_file, out=output, spoken=None, voice="selected", reuse=None, strict=False)
                    expected_cache = {}

                    def fake_audio_tools(script, argv, capture=False):
                        if script == "voice.py":
                            for item in argv:
                                if isinstance(item, Path) and item.suffix == ".txt":
                                    index = next(i for i, row in enumerate(current) if item.stem in (row["id"], row["alias"]))
                                    sf.write(item.with_suffix(".wav"), tone(-30 + index * 8), film.RATE, subtype="PCM_16")
                                    item.with_suffix(".json").write_text(json.dumps({"duration_s": 0.2, "seed": 123}))
                                    if engine == "kokoro":
                                        expected_cache[item.stem] = item.with_suffix(".wav").read_bytes()
                            return ""
                        if script == "cut_takes.py":
                            destination = argv[argv.index("--out") + 1]
                            destination.mkdir()
                            for index, row in enumerate(current):
                                path = destination / f"{row['id']}.wav"
                                sf.write(path, tone(-30 + index * 8), film.RATE, subtype="PCM_16")
                                expected_cache[row["id"]] = path.read_bytes()
                            return json.dumps({"take": "S01", "after": "opening-01", "clean": False, "gap_s": 0.02}) + "\n"
                        self.fail(f"unexpected voice tool {script}")

                    def aligned(sentences, asr):
                        return [[{"text": s["text"], "start": s["start"], "end": s["end"]}] for s in sentences], []

                    def normalized(raw, final, **kwargs):
                        final.write_bytes(raw.read_bytes())
                        return -0.65 if kwargs["preserve_take_levels"] else None

                    with patch.object(film, "voice_identity", return_value=({"engine": engine}, "voice-identity")), \
                            patch.object(film, "run_uv", side_effect=fake_audio_tools) as voice_tools, \
                            patch.object(film, "plan_runs", return_value=[["S01"], ["S02"], ["S03"]]), \
                            patch.object(film, "normalize", side_effect=normalized) as normalizer, \
                            patch.object(film, "transcribe", return_value=([], "local-model")), \
                            patch.object(film, "align_words", side_effect=aligned), \
                            patch.object(film, "audio_checks", side_effect=lambda timing, wav, asr, unclean: (unclean, {})), \
                            patch.object(film, "log") as logged, patch("sys.stdout", new=io.StringIO()):
                        film.narrate(args)
                        self.assertEqual(normalizer.call_args.kwargs, {"preserve_take_levels": engine != "kokoro"})
                        first_timing = json.loads((output / "timing.json").read_text())
                        first_checks = json.loads((output / "audio-checks.json").read_text())
                        origins = json.loads((output / "takes.json").read_text())
                        assembled_bytes = (output / "narration-raw.wav").read_bytes()
                        tool_count = voice_tools.call_count
                        self.assertEqual(first_timing["take_gain_db"], first_checks["stats"]["take_gain_db"])
                        self.assertEqual(first_timing["normalization_gain_db"], first_checks["stats"]["normalization_gain_db"])
                        if engine == "kokoro":
                            self.assertEqual(first_timing["take_gain_db"], {})
                            self.assertIsNone(first_timing["take_target_sentence_db"])
                            self.assertIsNone(first_timing["normalization_gain_db"])
                            self.assertIsNone(first_timing["final_take_target_sentence_db"])
                        else:
                            self.assertEqual(set(first_timing["take_gain_db"]), set(origins.values()))
                            self.assertGreater(max(abs(g) for g in first_timing["take_gain_db"].values()), 3)
                            self.assertAlmostEqual(first_timing["final_take_target_sentence_db"], first_timing["take_target_sentence_db"] - 0.65)
                            self.assertTrue(any("take gain exceeds 3 dB" in call.args[0] for call in logged.call_args_list))
                        raw_audio = {sid: film.read_audio(output / "sentences" / f"{sid}.wav") for sid in origins}
                        raw_reference = film.assemble(film.load_scenes(scene_file), {r["id"]: r for r in current}, raw_audio)
                        actual_audio = film.read_audio(output / "narration-raw.wav")
                        self.assertEqual(len(actual_audio), len(raw_reference[0]))
                        self.assertEqual(first_timing["sentences"], raw_reference[2])
                        self.assertEqual(first_timing["scenes"], raw_reference[1])
                        self.assertEqual(first_timing["duration"], round(raw_reference[3], 3))
                        if engine == "kokoro":
                            np.testing.assert_array_equal(actual_audio, raw_reference[0])
                        else:
                            self.assertFalse(np.array_equal(actual_audio, raw_reference[0]))
                        if reuse_mode == "external":
                            args.reuse, args.out = output, root / "second"
                        for _ in range(2):
                            film.narrate(args)
                            timing = json.loads((args.out / "timing.json").read_text())
                            checks = json.loads((args.out / "audio-checks.json").read_text())
                            self.assertEqual(timing, first_timing)
                            self.assertEqual(checks["flags"], first_checks["flags"])
                            self.assertEqual(checks["stats"]["take_gain_db"], first_timing["take_gain_db"])
                            self.assertEqual(checks["stats"]["reused"], len(current))
                            self.assertEqual(json.loads((args.out / "takes.json").read_text()), origins)
                            self.assertEqual((args.out / "narration-raw.wav").read_bytes(), assembled_bytes)
                            for sid, expected in expected_cache.items():
                                self.assertEqual((args.out / "sentences" / f"{sid}.wav").read_bytes(), expected)
                                self.assertEqual((output / "sentences" / f"{sid}.wav").read_bytes(), expected)
                        self.assertEqual(voice_tools.call_count, tool_count)

    def test_narrate_writes_complete_take_and_same_output_reuses_origin_and_cut_flag(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            root, current = Path(directory), rows(count=1)
            scene_file, output = root / "scenes.json", root / "audio"
            scene_file.write_text(json.dumps([{"id": r["scene_id"], "title": "Scene", "visual": "Visual", "claim_ids": [],
                                              "narration": r["text"]} for r in current]))
            (output / "sentences").mkdir(parents=True)
            stale = output / "sentences" / "stale.wav"
            stale.write_bytes(b"left by an older script")
            args = argparse.Namespace(scenes=scene_file, out=output, spoken=None, voice="clone", reuse=None, strict=False)

            def aligned(sentences, asr):
                return [[{"text": s["text"], "start": s["start"], "end": s["end"]}] for s in sentences], []

            with patch.object(film, "voice_identity", return_value=({"engine": "qwen3"}, "voice-identity")), \
                    patch.object(film, "run_uv", side_effect=self.fake_run_uv) as voice_tools, \
                    patch.object(film, "plan_runs", return_value=[["S01", "S02", "S03"]]) as planner, \
                    patch.object(film, "normalize", side_effect=lambda raw, final, **kwargs: final.write_bytes(raw.read_bytes())), \
                    patch.object(film, "transcribe", return_value=([{"word": "words", "start": 0, "end": 1}], "local-model")), \
                    patch.object(film, "align_words", side_effect=aligned), \
                    patch.object(film, "audio_checks", side_effect=lambda timing, wav, asr, unclean: (unclean, {})), \
                    patch.object(film, "log"), patch("sys.stdout", new=io.StringIO()):
                film.narrate(args)
                origins = json.loads((output / "takes.json").read_text())
                self.assertEqual(set(origins), {r["id"] for r in current})
                self.assertEqual(len(set(origins.values())), 1)
                first_checks = json.loads((output / "audio-checks.json").read_text())
                self.assertEqual(first_checks["stats"]["voiced"], len(current))
                self.assertEqual(first_checks["stats"]["voiced_takes"], 1)
                self.assertEqual(first_checks["stats"]["reused_takes"], 0)
                film.narrate(args)
                second_checks = json.loads((output / "audio-checks.json").read_text())
                self.assertEqual(json.loads((output / "takes.json").read_text()), origins)
                self.assertEqual(second_checks["flags"], first_checks["flags"])
                self.assertEqual(second_checks["stats"]["reused"], len(current))
                self.assertEqual(second_checks["stats"]["reused_takes"], 1)
                self.assertEqual(second_checks["stats"]["voiced"], 0)
                self.assertEqual(second_checks["stats"]["voiced_takes"], 0)
                planner.assert_called_once()
                self.assertEqual(voice_tools.call_count, 2)
            self.assertFalse(stale.exists())
            self.assertNotIn("stale", json.loads((output / "sentence-hashes.json").read_text()))


if __name__ == "__main__":
    unittest.main()
