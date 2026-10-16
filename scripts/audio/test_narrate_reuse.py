"""Exercise narration reuse and provenance without loading or running a speech model."""
import argparse
import contextlib
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
        reference = film.assemble(scenes, current, audio, takes)
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

    def test_run_on_sentences_are_not_flagged_as_cut_short(self):
        sentences = [{"id": "first", "scene_id": "opening", "text": "Hello.", "start": 0.1, "end": 0.3},
                     {"id": "second", "scene_id": "opening", "text": "Again.", "start": 0.3, "end": 0.5}]
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            wav = Path(directory) / "narration.wav"
            sf.write(wav, np.concatenate([tone(-70, 10), tone(-24), tone(-24), tone(-70, 10)]), film.RATE)
            for none_after, cut in [([], ["first", "second"]), (["first"], ["second"])]:
                with self.subTest(none_after=none_after), \
                        patch.object(film, "measure_loudness", return_value={"input_i": -16, "input_tp": -1.5}), \
                        patch.object(film, "asr_differences", return_value=[]):
                    timing = {"sentences": sentences, "duration": 0.6, "pauses": {"none_after": none_after}}
                    flags, stats = film.audio_checks(timing, wav, [], [])
                    self.assertEqual([flag["sentence"] for flag in flags if flag["check"] == "word_cut_short"], cut)
                    self.assertGreater(stats["max_tail_above_floor_db"], film.TAIL_ABOVE_FLOOR_DB)



class RunOnTests(unittest.TestCase):
    def assembled_starts(self, run_on=None, pause_third=False, takes=None, scene_ids=("only",), count=3):
        current = rows(scene_ids=scene_ids, count=count)
        scenes = [{"id": scene, "title": "Scene", "visual": "Visual", "claim_ids": [],
                   "_sentences": [{"text": r["text"], "pause_before": pause_third and r["id"].endswith("-03")}
                                  for r in current if r["scene_id"] == scene]} for scene in scene_ids]
        audio = {r["id"]: tone(-20) for r in current}
        _, _, sentences, _ = film.assemble(scenes, {r["id"]: r for r in current}, audio, takes=takes, run_on=run_on)
        return [(row["start"], row["end"]) for row in sentences]

    def test_separate_generations_get_the_sentence_gap(self):
        (_, end1), (start2, end2), (start3, _) = self.assembled_starts(takes={"only-01": "a", "only-02": "b", "only-03": "c"})
        self.assertAlmostEqual(start2 - end1, film.SENTENCE_PAUSE, places=3)
        self.assertAlmostEqual(start3 - end2, film.SENTENCE_PAUSE, places=3)

    def test_sentences_of_one_take_join_as_spoken(self):
        (_, end1), (start2, end2), (start3, _) = self.assembled_starts(takes={"only-01": "a", "only-02": "a", "only-03": "b"})
        self.assertAlmostEqual(start2, end1, places=3)
        self.assertAlmostEqual(start3 - end2, film.SENTENCE_PAUSE, places=3)

    def test_a_scene_join_and_a_pause_inside_one_take_keep_their_gaps(self):
        same = {f"{scene}-{i:02d}": "a" for scene in ("one", "two") for i in range(1, 4)}
        starts = self.assembled_starts(takes=same, scene_ids=("one", "two"), pause_third=True)
        gaps = [round(start - end, 3) for (_, end), (start, _) in zip(starts, starts[1:])]
        self.assertEqual(gaps, [0, film.EXPLICIT_PAUSE, film.SCENE_PAUSE, 0, film.EXPLICIT_PAUSE])

    def test_unclean_cut_joins_without_a_gap(self):
        (_, end1), (start2, end2), (start3, _) = self.assembled_starts(run_on={"only-01"})
        self.assertAlmostEqual(start2, end1, places=3)
        self.assertAlmostEqual(start3 - end2, film.SENTENCE_PAUSE, places=3)

    def test_explicit_pause_survives_an_unclean_cut(self):
        _, (_, end2), (start3, _) = self.assembled_starts(run_on={"only-02"}, pause_third=True)
        self.assertAlmostEqual(start3 - end2, film.EXPLICIT_PAUSE, places=3)


class SentenceSplitTests(unittest.TestCase):
    def test_a_sentence_ending_inside_a_quotation_splits_after_the_closing_mark(self):
        split = film.sentences('The cup fills. "It spills," she says, "every time." The table is wet. [pause] Then “it dries.” Done.', "en")
        self.assertEqual([s["text"] for s in split], ["The cup fills.", '"It spills," she says, "every time."',
                                                      "The table is wet.", "Then “it dries.”", "Done."])
        self.assertEqual([s["pause_before"] for s in split], [False, False, False, True, False])



class NormalizationTests(unittest.TestCase):
    def test_common_gain_is_loudness_limited_or_peak_limited(self):
        for measured, expected in (({"input_i": "-20", "input_tp": "-10"}, 4),
                                   ({"input_i": "-16.40", "input_tp": "-0.90"}, -0.60)):
            with self.subTest(measured=measured), patch.object(film, "measure_loudness", return_value=measured), \
                    patch.object(film, "ffmpeg") as ffmpeg, patch.object(film, "log"):
                self.assertAlmostEqual(film.normalize(Path("raw.wav"), Path("final.wav"), preserve_take_levels=True), expected)
                self.assertTrue(ffmpeg.call_args.args[0][ffmpeg.call_args.args[0].index("-af") + 1].startswith("volume="))



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

    def test_missing_audio_invalidates_take(self):
        missing = source(self.rows)
        missing.audio.pop(self.rows[0]["id"])
        self.assertEqual(film.decide_reuse(self.rows, "qwen3", [missing]).audio, {})

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
            log.assert_called_once()
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
    def fake_run_tool(self, script, args, capture=False, soft_exit=None):
        if script == "voice.py":
            for item in args:
                if isinstance(item, Path) and item.suffix == ".txt":
                    sf.write(item.with_suffix(".wav"), np.full(2400, 0.01, dtype="float32"), film.RATE, subtype="PCM_16")
                    item.with_suffix(".json").write_text(json.dumps({"duration_s": 0.1, "seed": 123}))
            return ""
        if script == "cut_takes.py":
            destination = args[args.index("--out") + 1]
            destination.mkdir(exist_ok=True)
            sentence_file = args[args.index("--sentences") + 1]
            for row in json.loads(sentence_file.read_text()):
                sf.write(destination / f"{row['id']}.wav", np.full(2400, 0.01, dtype="float32"), film.RATE, subtype="PCM_16")
            return json.dumps({"take": "S01-S03", "after": "opening-01", "clean": False, "gap_s": 0.02}) + "\n"
        self.fail(f"unexpected voice tool {script}")

    def test_whole_pending_scenes_are_grouped_and_provenance_matches_raw_hashes(self):
        current = rows(count=1)
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, patch.object(film, "run_tool", side_effect=self.fake_run_tool), \
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

    def voice_with_lengths(self, lengths, calls):
        """A clone voice whose takes last the next of lengths seconds, and a cutter that finds clean cuts."""
        def tool(script, args, capture=False, soft_exit=None):
            texts = [a for a in args if isinstance(a, Path) and a.suffix == ".txt"]
            if script == "voice.py":
                calls.append([t.stem for t in texts])
                for item in texts:
                    sf.write(item.with_suffix(".wav"), np.full(round(lengths.pop(0) * film.RATE), 0.01, dtype="float32"),
                             film.RATE, subtype="PCM_16")
                    item.with_suffix(".json").write_text(json.dumps({"duration_s": 0, "seed": 1}))
                return ""
            destination = args[args.index("--out") + 1]
            destination.mkdir(exist_ok=True)
            for row in json.loads(args[args.index("--sentences") + 1].read_text()):
                sf.write(destination / f"{row['id']}.wav", np.full(2400, 0.01, dtype="float32"), film.RATE, subtype="PCM_16")
            return ""
        return tool

    def test_only_a_runaway_take_is_voiced_again(self):
        calls = []
        # Each sentence is estimated at 1 s, so S01 plans 2 s and S02-S03 plans 4 s.
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, \
                patch.object(film, "run_tool", side_effect=self.voice_with_lengths([9, 4, 2], calls)), \
                patch.object(film, "estimate_seconds", side_effect=lambda texts, language: [1.0] * len(texts)), \
                patch.object(film, "plan_runs", return_value=[["S01"], ["S02", "S03"]]), patch.object(film, "log"):
            audio, takes, _, manifests = film.voice_takes("clone", {"engine": "qwen3"}, rows(), Path(directory))
            self.assertEqual(calls, [["S01", "S02-S03"], ["S01"]])
            self.assertEqual(len(audio), 6)
            for manifest in manifests.values():
                self.assertEqual(manifest["sha256"], film.sha256(Path(manifest["wav"]).read_bytes()))

    def test_a_take_the_cutter_cannot_cut_is_voiced_again(self):
        calls, cuts = [], []
        voice = self.voice_with_lengths([2, 4, 2], calls)

        def tool(script, args, capture=False, soft_exit=None):
            if script == "cut_takes.py":
                self.assertEqual(soft_exit, film.UNCUTTABLE_EXIT)
                cuts.append(args[0].stem)
                if cuts == ["S01"]:
                    return None
            return voice(script, args, capture)
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, patch.object(film, "run_tool", side_effect=tool), \
                patch.object(film, "estimate_seconds", side_effect=lambda texts, language: [1.0] * len(texts)), \
                patch.object(film, "plan_runs", return_value=[["S01"], ["S02", "S03"]]), patch.object(film, "log"):
            audio, _, _, manifests = film.voice_takes("clone", {"engine": "qwen3"}, rows(), Path(directory))
            self.assertEqual(calls, [["S01", "S02-S03"], ["S01"]])
            self.assertEqual(cuts, ["S01", "S02-S03", "S01"])
            self.assertEqual(len(audio), 6)
            for manifest in manifests.values():
                self.assertEqual(manifest["sha256"], film.sha256(Path(manifest["wav"]).read_bytes()))

    def test_only_the_cutters_uncuttable_exit_is_soft(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, patch.object(film, "VOICE_DIR", Path(directory)):
            (Path(directory) / "tool.py").write_text("import sys\nprint('done')\nsys.exit(int(sys.argv[1]))\n")
            self.assertEqual(film.run_tool("tool.py", [0], capture=True, soft_exit=3), "done\n")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertIsNone(film.run_tool("tool.py", [3], capture=True, soft_exit=3))
            with self.assertRaisesRegex(SystemExit, "exit 1"):
                film.run_tool("tool.py", [1], capture=True, soft_exit=3)

    def test_a_take_that_keeps_running_away_stops_the_build(self):
        calls = []
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, \
                patch.object(film, "run_tool", side_effect=self.voice_with_lengths([13] * 3, calls)), \
                patch.object(film, "estimate_seconds", side_effect=lambda texts, language: [1.0] * len(texts)), \
                patch.object(film, "plan_runs", return_value=[["S01", "S02", "S03"]]), patch.object(film, "log"), \
                self.assertRaisesRegex(SystemExit, "S01-S03 13 s for 6 s planned"):
            film.voice_takes("clone", {"engine": "qwen3"}, rows(), Path(directory))
        self.assertEqual(calls, [["S01-S03"]] * 3)

    def test_kokoro_generations_get_unique_ids_per_sentence_and_rerun(self):
        current = rows(("opening",), 2)
        with tempfile.TemporaryDirectory(dir="/tmp") as directory, patch.object(film, "run_tool", side_effect=self.fake_run_tool):
            first = film.voice_takes("kokoro", {"engine": "kokoro"}, current, Path(directory) / "first")
            second = film.voice_takes("kokoro", {"engine": "kokoro"}, current, Path(directory) / "second")
            self.assertEqual(len(set(first[1].values())), len(current))
            self.assertTrue(set(first[1].values()).isdisjoint(second[1].values()))
            self.assertEqual(first[2], [])

    def test_disk_gain_preserves_raw_sentence_bytes_across_external_reuse_and_reruns(self):
        for engine in ("qwen3", "kokoro"):
            for reuse_mode in ("own", "external"):
                with self.subTest(engine=engine, reuse_mode=reuse_mode), tempfile.TemporaryDirectory(dir="/tmp") as directory:
                    root, current = Path(directory), rows(count=1)
                    scene_file, output = root / "scenes.json", root / "first"
                    scene_file.write_text(json.dumps([{"id": r["scene_id"], "title": "Scene", "visual": "Visual", "claim_ids": [],
                                                      "narration": r["text"]} for r in current]))
                    args = argparse.Namespace(scenes=scene_file, out=output, spoken=None, voice="selected", reuse=None, strict=False, language="en")
                    expected_cache = {}

                    def fake_audio_tools(script, argv, capture=False, soft_exit=None):
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
                            destination.mkdir(exist_ok=True)
                            for index, row in enumerate(current):
                                path = destination / f"{row['id']}.wav"
                                sf.write(path, tone(-30 + index * 8), film.RATE, subtype="PCM_16")
                                expected_cache[row["id"]] = path.read_bytes()
                            return json.dumps({"take": "S01", "after": "opening-01", "clean": False, "gap_s": 0.02}) + "\n"
                        self.fail(f"unexpected voice tool {script}")

                    def aligned(sentences, asr, language="en"):
                        return [[{"text": s["text"], "start": s["start"], "end": s["end"]}] for s in sentences], []

                    def normalized(raw, final, **kwargs):
                        final.write_bytes(raw.read_bytes())
                        return -0.65 if kwargs["preserve_take_levels"] else None

                    with patch.object(film, "voice_identity", return_value=({"engine": engine}, "voice-identity")), \
                            patch.object(film, "run_tool", side_effect=fake_audio_tools) as voice_tools, \
                            patch.object(film, "plan_runs", return_value=[["S01"], ["S02"], ["S03"]]), \
                            patch.object(film, "normalize", side_effect=normalized) as normalizer, \
                            patch.object(film, "transcribe", return_value=([], "local-model")), \
                            patch.object(film, "align_words", side_effect=aligned), \
                            patch.object(film, "audio_checks", side_effect=lambda timing, wav, asr, unclean, language="en": (unclean, {})), \
                            patch.object(film, "log"), patch("sys.stdout", new=io.StringIO()):
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
                        raw_audio = {sid: film.read_audio(output / "sentences" / f"{sid}.wav") for sid in origins}
                        run_on = {f["after"] for f in first_checks["flags"] if f.get("check") == "unclean_cut"}
                        self.assertEqual(first_timing["pauses"]["none_after"], sorted(run_on))
                        raw_reference = film.assemble(film.load_scenes(scene_file, "en"), {r["id"]: r for r in current}, raw_audio,
                                                     takes=origins, run_on=run_on)
                        actual_audio = film.read_audio(output / "narration-raw.wav")
                        self.assertEqual(len(actual_audio), len(raw_reference[0]))
                        self.assertEqual(first_timing["sentences"], raw_reference[2])
                        self.assertEqual(first_timing["scenes"], raw_reference[1])
                        self.assertEqual(first_timing["duration"], round(raw_reference[3], 3))
                        self.assertFalse(np.array_equal(actual_audio, raw_reference[0]))
                        if engine == "kokoro":
                            matched, target, gains = film.match_sentence_levels(raw_audio)
                            expected = film.assemble(film.load_scenes(scene_file, "en"), {r["id"]: r for r in current}, matched,
                                                     takes=origins, run_on=run_on)[0]
                            np.testing.assert_allclose(actual_audio, expected, atol=1 / 32768)
                            self.assertEqual(first_timing["sentence_gain_db"], gains)
                            self.assertEqual(first_timing["sentence_target_db"], target)
                            self.assertEqual(first_checks["stats"]["sentence_gain_db"], gains)
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



if __name__ == "__main__":
    unittest.main()
