"""Recover failed pauses with invented speech and mocked synthesis."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import soundfile as sf

import narrate_film as film
from test_narrate_reuse import rows, source, tone


class UncleanTests(unittest.TestCase):
    def setUp(self):
        self.current = rows(("opening", "ending"), 3)
        self.voiced, self.cuts = [], []
        self.failures = {}
        self.stats = {}

    def tool(self, script, args, capture=False, soft_exit=None):
        if script == "voice.py":
            texts = [p for p in args if isinstance(p, Path) and p.suffix == ".txt"]
            self.voiced.append([p.stem for p in texts])
            for p in texts:
                self.assertTrue(p.read_text().endswith(" " + film.THROWAWAY))
                sf.write(p.with_suffix(".wav"), tone(-24), film.RATE)
                p.with_suffix(".json").write_text("{}")
            return ""
        self.assertEqual(script, "cut_takes.py")
        stem = args[0].stem
        members = json.loads(args[args.index("--sentences") + 1].read_text())
        self.cuts.append((stem, [r["id"] for r in members]))
        destination = args[args.index("--out") + 1]
        destination.mkdir(exist_ok=True)
        for row in members:
            sf.write(destination / f"{row['id']}.wav", tone(-24), film.RATE)
        failed = self.failures.get(stem, [])
        return "\n".join(json.dumps({"take": stem, "after": r["id"],
                                     "clean": r["id"] not in failed, "gap_s": 0 if r["id"] in failed else .1})
                         for r in members)

    @contextlib.contextmanager
    def mocked(self):
        with patch.object(film.sys, "platform", "linux"), \
                patch.object(film, "estimate_seconds", side_effect=lambda texts, language: [1.] * len(texts)), \
                patch.object(film, "plan_runs", return_value=[["S01", "S02"]]), \
                patch.object(film, "run_tool", side_effect=self.tool), patch.object(film, "log"):
            yield

    def generate(self, root, **kwargs):
        return film.voice_takes("selected", {"engine": "run-voice"}, self.current, root, stats=self.stats, **kwargs)

    def test_unclean_run_splits_at_boundary_and_only_clean_children_are_recorded(self):
        self.failures = {"S01-S02": ["opening-02"]}
        with tempfile.TemporaryDirectory() as directory, self.mocked():
            root = Path(directory)
            audio, origins, flags, manifests = self.generate(root)
            self.assertEqual(set(audio), {r["id"] for r in self.current})
            self.assertEqual(flags, [])
            self.assertEqual(self.voiced, [["S01-S02"], ["R0001", "R0002"]])
            self.assertEqual(self.cuts[1:], [("R0001", ["opening-01", "opening-02"]),
                                            ("R0002", ["opening-03", "ending-01", "ending-02", "ending-03"])])
            self.assertEqual(len(set(origins.values())), 2)
            self.assertEqual(set(manifests), set(origins.values()))
            self.assertEqual(len({m["split_from"] for m in manifests.values()}), 1)
            for manifest in manifests.values():
                self.assertEqual(manifest["sha256"], film.sha256(Path(manifest["wav"]).read_bytes()))
                self.assertEqual(manifest["split_depth"], 1)
            self.assertEqual(self.stats, {"unclean_split_runs": 1, "unclean_revoiced_takes": 2})
            old = source(self.current, str(root))
            old.takes, old.manifests = origins, manifests
            reused = film.decide_reuse(self.current, "run-voice", [old])
            self.assertEqual(reused.takes, origins)
            self.assertEqual(reused.manifests, manifests)
            changed = [dict(r) for r in self.current]
            changed[-1]["key"] = "changed"
            self.assertEqual(film.decide_reuse(changed, "run-voice", [old]).audio, {})
            for changed in (self.current[1:], [self.current[1], self.current[0], *self.current[2:]],
                            [r for r in self.current if r["scene_id"] == "opening"]):
                self.assertEqual(film.decide_reuse(changed, "run-voice", [old]).audio, {})
            old.audio.pop("opening-01")
            self.assertEqual(film.decide_reuse(self.current, "run-voice", [old]).audio, {})

    def test_incomplete_split_group_cannot_reuse_even_a_whole_remaining_scene(self):
        self.failures = {"S01-S02": ["opening-03"]}
        with tempfile.TemporaryDirectory() as directory, self.mocked():
            root = Path(directory)
            _, origins, _, manifests = self.generate(root)
            old = source(self.current, str(root))
            old.takes = {sid: take for sid, take in origins.items() if sid.startswith("opening-")}
            old.manifests = manifests
            self.assertEqual(film.decide_reuse(self.current, "run-voice", [old]).audio, {})

    def test_second_round_uses_single_sentences_and_keeps_clean_sibling(self):
        self.failures = {"S01-S02": ["opening-02"], "R0002": ["ending-02"]}
        with tempfile.TemporaryDirectory() as directory, self.mocked():
            _, origins, flags, manifests = self.generate(Path(directory))
        self.assertEqual(flags, [])
        self.assertEqual(self.voiced, [["S01-S02"], ["R0001", "R0002"], ["R0003", "R0004", "R0005", "R0006"]])
        self.assertEqual([len(ids) for _, ids in self.cuts], [6, 2, 4, 1, 1, 1, 1])
        self.assertEqual(len(manifests), 5)
        self.assertEqual(len(set(origins.values())), 5)
        self.assertEqual({m["split_depth"] for m in manifests.values()}, {1, 2})
        self.assertEqual(self.stats, {"unclean_split_runs": 2, "unclean_revoiced_takes": 6})

    def test_unclean_singleton_stops_without_accepting_or_repeating_it(self):
        self.failures = {"S01-S02": ["opening-01"], "R0001": ["opening-01"]}
        with tempfile.TemporaryDirectory() as directory, self.mocked(), \
                self.assertRaisesRegex(SystemExit, "still has unclean cuts"):
            self.generate(Path(directory))
        self.assertEqual(self.voiced, [["S01-S02"], ["R0001", "R0002"]])

    def test_no_third_split_round_is_allowed(self):
        self.failures = {"S01-S02": ["opening-02"], "R0002": ["ending-02"], "R0003": ["opening-03"]}
        with tempfile.TemporaryDirectory() as directory, self.mocked(), \
                self.assertRaisesRegex(SystemExit, "after 2 split retries"):
            self.generate(Path(directory))
        self.assertEqual(len(self.voiced), 3)

    def test_clean_run_is_never_split(self):
        with tempfile.TemporaryDirectory() as directory, self.mocked():
            _, origins, flags, manifests = self.generate(Path(directory))
        self.assertEqual(self.voiced, [["S01-S02"]])
        self.assertEqual(flags, [])
        self.assertEqual(len(set(origins.values())), 1)
        self.assertTrue(all("split_from" not in m for m in manifests.values()))
        self.assertEqual(self.stats, {})

    def test_short_replacement_duration_budget_includes_its_throwaway(self):
        self.failures = {"S01-S02": ["opening-02"]}

        def tool(script, args, **kwargs):
            result = self.tool(script, args, **kwargs)
            if script == "voice.py":
                for p in args:
                    if isinstance(p, Path) and p.stem == "R0001":
                        # Two script seconds plus the throwaway can legitimately exceed four seconds.
                        sf.write(p.with_suffix(".wav"), tone(-24, frames=450), film.RATE)
            return result

        with tempfile.TemporaryDirectory() as directory, self.mocked(), \
                patch.object(film, "run_tool", side_effect=tool):
            _, _, flags, _ = self.generate(Path(directory))
        self.assertEqual(flags, [])
        self.assertEqual(self.voiced, [["S01-S02"], ["R0001", "R0002"]])
        self.assertNotIn("runaway_revoiced_takes", self.stats)

    def test_cached_failure_is_split_before_first_synthesis(self):
        with tempfile.TemporaryDirectory() as directory, self.mocked():
            self.generate(Path(directory), unclean_after={"opening-02"})
        self.assertEqual(self.voiced, [["R0001", "R0002"]])
        self.assertNotIn("S01-S02", [stem for stem, _ in self.cuts])

    def test_throwaway_failure_falls_back_to_single_sentences(self):
        self.failures = {"S01-S02": ["ending-03"]}
        with tempfile.TemporaryDirectory() as directory, self.mocked():
            _, _, flags, _ = self.generate(Path(directory))
        self.assertEqual(flags, [])
        self.assertEqual([len(ids) for _, ids in self.cuts], [6, 1, 1, 1, 1, 1, 1])

    def test_other_platform_retains_unclean_flags(self):
        self.failures = {"S01-S02": ["opening-02"]}
        with tempfile.TemporaryDirectory() as directory, self.mocked(), patch.object(film.sys, "platform", "other"):
            _, origins, flags, _ = self.generate(Path(directory))
        self.assertEqual(self.voiced, [["S01-S02"]])
        self.assertEqual(flags, [{"check": "unclean_cut", "take": origins["opening-02"], "after": "opening-02", "gap_s": 0}])

    def test_rerun_repairs_only_cached_bad_take_then_reuses_split_takes(self):
        self.current = rows(("opening", "ending"), 2)
        with tempfile.TemporaryDirectory() as directory, self.mocked():
            root = Path(directory)
            out, scene_file = root / "audio", root / "scenes.json"
            (out / "sentences").mkdir(parents=True)
            scene_file.write_text(json.dumps([{"id": scene, "title": "Scene", "visual": "Visual", "claim_ids": [],
                                              "narration": [r["text"] for r in self.current if r["scene_id"] == scene]}
                                             for scene in ("opening", "ending")]))
            old_origins = {r["id"]: r["scene_id"] for r in self.current}
            (out / "takes.json").write_text(json.dumps(old_origins))
            (out / "sentence-hashes.json").write_text(json.dumps({r["id"]: r["key"] for r in self.current}))
            (out / "timing.json").write_text(json.dumps({"sentences": self.current}))
            (out / "audio-checks.json").write_text(json.dumps({"flags": [
                {"check": "unclean_cut", "take": "opening", "after": "opening-01", "gap_s": 0}]}))
            for row in self.current:
                sf.write(out / "sentences" / f"{row['id']}.wav", tone(-24), film.RATE)
            cached = {r["id"]: (out / "sentences" / f"{r['id']}.wav").read_bytes()
                      for r in self.current if r["scene_id"] == "ending"}
            args = argparse.Namespace(scenes=scene_file, out=out, reuse=None, spoken=None, voice="selected", language="en", strict=False)

            def normalized(raw, final, **kwargs):
                final.write_bytes(raw.read_bytes())
                return 0.

            def aligned(wav, sents, asr, language, stats):
                return [], [[{"text": s["text"], "start": s["start"], "end": s["end"]}] for s in sents], [], 0

            with patch.object(film, "plan_runs", return_value=[["S01"]]), \
                    patch.object(film, "voice_identity", return_value=({"engine": "run-voice"}, "voice-identity")), \
                    patch.object(film, "normalize", side_effect=normalized), \
                    patch("linux_levels.correct_file", return_value={"plan": []}), \
                    patch.object(film, "transcribe", return_value=([], "local-model")), \
                    patch.object(film, "align_with_repairs", side_effect=aligned), \
                    patch.object(film, "audio_checks", side_effect=lambda timing, wav, asr, unclean, language: (unclean, {})), \
                    contextlib.redirect_stdout(io.StringIO()):
                film.narrate(args)
                first = json.loads((out / "audio-checks.json").read_text())
                origins = json.loads((out / "takes.json").read_text())
                self.assertEqual(first["flags"], [])
                self.assertEqual(first["stats"]["reused"], 2)
                self.assertEqual(first["stats"]["voiced"], 2)
                self.assertEqual(first["stats"]["unclean_revoiced_takes"], 2)
                self.assertEqual(self.voiced, [["R0001", "R0002"]])
                film.narrate(args)
                second = json.loads((out / "audio-checks.json").read_text())
                self.assertEqual(second["stats"]["reused"], 4)
                self.assertEqual(second["stats"]["voiced"], 0)
                self.assertEqual(json.loads((out / "takes.json").read_text()), origins)
                self.assertEqual(len(self.voiced), 1)
                for sid, data in cached.items():
                    self.assertEqual((out / "sentences" / f"{sid}.wav").read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
