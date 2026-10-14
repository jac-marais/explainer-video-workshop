"""Verify pipeline order, restart boundaries and failure handling without synthesis or rendering."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import make_film as film


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = self.root / "script.md"
        self.script.write_text('## Scene 1: Garden\n**Narration**\nA seed rests.\n**Visual**\n- On s01-01, show a seed.\n')
        self.scenes = self.root / "scenes.json"
        self.scenes.write_text(json.dumps([{"id": "s01", "narration": "A seed rests.", "title": "Garden", "visual": "A seed", "claim_ids": []}]))
        (self.root / "index.html").write_text('<div data-duration="1"></div>')
        self.audio = self.root / "audio"
        self.audio.mkdir()
        (self.audio / "timing.json").write_text('{"duration": 2}')
        (self.audio / "audio-checks.json").write_text('{"ok": true, "flags": [], "fallback_words": []}')
        self.argv = ["make_film.py", "--script", str(self.script), "--scenes", str(self.scenes), "--project", str(self.root),
                     "--hf", "/tmp/invented-hf", "--out", str(self.root / "film.mp4"), "--voice", "test-voice", "--language", "de"]

    def invoke(self, extra=(), effect=None):
        with patch.object(sys, "argv", self.argv + list(extra)), patch.object(film, "execute", side_effect=effect) as execute:
            film.main()
        return execute.call_args_list

    def test_full_order_and_heavy_steps(self):
        calls = self.invoke()
        names = [next(Path(str(item)).name for item in call.args[0] if str(item).endswith('.py')) for call in calls]
        self.assertEqual(names, ["narrate_film.py", "captions.py", "cues.py", "build_data.py", "render.py", "check_film.py"])
        self.assertEqual([call.kwargs.get("heavy", False) for call in calls], [True, False, False, False, True, True])
        command = calls[0].args[0]
        self.assertEqual(command[0], film.SCRIPTS / "run/py")
        self.assertEqual(command[command.index("--language") + 1], "de")
        self.assertEqual(calls[-1].args[0][2], self.root / "film.mp4")

    def test_every_restart_runs_only_suffix(self):
        for index, step in enumerate(film.STEPS):
            self.assertEqual(len(self.invoke(["--from", step])), len(film.STEPS) - index)

    def test_failure_stops_pipeline(self):
        with patch.object(sys, "argv", self.argv), patch.object(film, "execute", side_effect=subprocess.CalledProcessError(1, "fixture")) as execute:
            with self.assertRaises(subprocess.CalledProcessError):
                film.main()
            self.assertEqual(execute.call_count, 1)

    def test_flags_stop_before_captions(self):
        (self.audio / "audio-checks.json").write_text('{"ok": false, "flags": [{"check":"gap"}]}')
        with self.assertRaisesRegex(ValueError, "resolve audio flags"):
            self.invoke()

    def test_invalid_inputs_stop_before_work(self):
        self.scenes.write_text('[{"id":"s01", "narration":"A leaf grows."}]')
        with patch.object(sys, "argv", self.argv), patch.object(film, "execute") as execute:
            with self.assertRaisesRegex(ValueError, "must match"):
                film.main()
            execute.assert_not_called()

    def test_render_never_reuses_an_existing_output(self):
        (self.root / "film.mp4").write_bytes(b"invented")
        with self.assertRaisesRegex(ValueError, "choose a new --out"):
            self.invoke(["--from", "render"])
        self.assertEqual(len(self.invoke(["--from", "check"])), 1)

    def test_execute_wraps_command_without_a_shell(self):
        with patch.object(film.subprocess, "run") as run:
            film.execute(["python3", "file with spaces.py"], heavy=True)
        self.assertEqual(run.call_args.args[0], [str(film.SCRIPTS / "run/heavy"), "python3", "file with spaces.py"])
        self.assertEqual(run.call_args.kwargs, {"check": True})


if __name__ == "__main__":
    unittest.main()
