"""Verify pipeline order, restart boundaries and failure handling without synthesis or rendering."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import make_film as film

SPLIT = film.split_sentences


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = self.root / "script.md"
        self.script.write_text('## Scene 1: Garden\n**Narration**\nA small seed rests in the soil.\n**Visual**\n- On s01-01, show a seed.\n')
        self.scenes = self.root / "scenes.json"
        self.scenes.write_text(json.dumps([{"id": "s01", "narration": "A small seed rests in the soil.", "title": "Garden", "visual": "A seed", "claim_ids": []}]))
        (self.root / "index.html").write_text('<div data-duration="1"></div>')
        self.audio = self.root / "audio"
        self.audio.mkdir()
        (self.audio / "timing.json").write_text('{"duration": 2}')
        (self.audio / "audio-checks.json").write_text('{"ok": true, "flags": [], "fallback_words": []}')
        self.argv = ["make_film.py", "--script", str(self.script), "--scenes", str(self.scenes), "--project", str(self.root),
                     "--hf", "/tmp/invented-hf", "--out", str(self.root / "film.mp4"), "--voice", "test-voice", "--language", "fr"]
        # A stand-in splits after ". "; test_split_runs_text_tokens_once_under_heavy covers the real split.
        split = patch.object(film, "split_sentences", side_effect=lambda texts: [text.replace(". ", ".\n").splitlines() for _, text in texts])
        split.start()
        self.addCleanup(split.stop)

    def invoke(self, extra=(), effect=None):
        with patch.object(sys, "argv", self.argv + list(extra)), patch.object(film, "execute", side_effect=effect) as execute:
            film.main()
        return execute.call_args_list

    def test_full_order_and_heavy_steps(self):
        calls = self.invoke()
        names = [next(Path(str(item)).name for item in call.args[0] if str(item).endswith('.py')) for call in calls]
        self.assertEqual(names, ["narrate_film.py", "captions.py", "cues.py", "build_data.py", "render.py", "check_film.py"])
        self.assertEqual([call.kwargs.get("heavy", False) for call in calls], [True, True, False, False, True, True])
        command = calls[0].args[0]
        self.assertEqual(command[0], film.SCRIPTS / "run/py")
        self.assertEqual(command[command.index("--language") + 1], "fr")
        self.assertEqual(calls[1].args[0][0], film.SCRIPTS / "run/py")
        self.assertFalse({"--font", "--font-size", "--font-weight", "--line-width"} & set(map(str, calls[1].args[0])))
        self.assertEqual(calls[-1].args[0][2], self.root / "film.mp4")

    def test_caption_font_options_reach_captions(self):
        calls = self.invoke(["--from", "captions", "--caption-font", "a.woff2", "--caption-font", "b.ttc#2",
                             "--caption-font-size", "40", "--caption-font-weight", "600", "--caption-line-width", "900"])
        command = list(map(str, calls[0].args[0]))
        self.assertEqual(command[command.index("--json-output") + 2:],
                         ["--font", "a.woff2", "--font", "b.ttc#2", "--font-size", "40.0", "--font-weight", "600.0", "--line-width", "900.0"])

    def test_split_runs_text_tokens_once_under_heavy(self):
        texts = [["en", "A seed rests."], ["fr", "Une graine. Deux feuilles."]]
        output = json.dumps([[{"text": "A seed rests.", "pause_before": False}],
                             [{"text": "Une graine.", "pause_before": False}, {"text": "Deux feuilles.", "pause_before": False}]])
        with patch.object(film.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, output)) as run:
            self.assertEqual(SPLIT(texts), [["A seed rests."], ["Une graine.", "Deux feuilles."]])
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], [film.SCRIPTS / "run/heavy", film.SCRIPTS / "run/py", film.SCRIPTS / "audio/text_tokens.py"])
        self.assertEqual(json.loads(run.call_args.kwargs["input"]), texts)
        with patch.object(film.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, "")):
            with self.assertRaisesRegex(ValueError, "could not split"):
                SPLIT(texts)

    def test_key_script_needs_its_language_and_equal_sentence_counts(self):
        key = self.root / "key.md"
        key.write_text('## Scene 1: Garden\n**Narration**\nA small seed rests in the soil. A green leaf grows toward the sun.\n**Visual**\n- On s01-01, show a seed.\n')
        with self.assertRaises(SystemExit):
            self.invoke(["--key-script", str(key)])
        with self.assertRaisesRegex(ValueError, "scene 1: 1 sentences, but the key script has 2"):
            self.invoke(["--key-script", str(key), "--key-language", "en"])

    def test_quoted_cue_translations_may_split_differently(self):
        self.script.write_text('## Scene 1: Garden\n**Narration**\nA small seed rests in the soil.\n**Visual**\n- On "seed", show a seed.\n')
        key = self.root / "key.md"
        key.write_text('## Scene 1: Garden\n**Narration**\nA small seed rests in the soil. A green leaf grows toward the sun.\n**Visual**\n- On "seed", show a seed.\n')
        self.assertEqual(len(self.invoke(["--key-script", str(key), "--key-language", "en"])), 6)

    def test_a_sentence_under_the_word_floor_stops_before_voicing(self):
        self.script.write_text('## Scene 1: Garden\n**Narration**\nA seed rests.\n**Visual**\n- On s01-01, show a seed.\n')
        self.scenes.write_text('[{"id":"s01", "narration":"A seed rests."}]')
        with patch.object(sys, "argv", self.argv), patch.object(film, "execute") as execute:
            with self.assertRaisesRegex(ValueError, "s01-01: 3 words, under the 5-word floor: A seed rests."):
                film.main()
            execute.assert_not_called()
        # A picture-only restart keeps the words already voiced.
        self.assertEqual(len(self.invoke(["--from", "render"])), 2)

    def test_a_translation_is_held_to_its_key_scripts_floor(self):
        self.script.write_text('## Scene 1: Garden\n**Narration**\nUne graine dort.\n**Visual**\n- On s01-01, show a seed.\n')
        self.scenes.write_text('[{"id":"s01", "narration":"Une graine dort."}]')
        key = self.root / "key.md"
        key.write_text('## Scene 1: Garden\n**Narration**\nA small seed rests in the soil.\n**Visual**\n- On s01-01, show a seed.\n')
        args = ["--key-script", str(key), "--key-language", "en"]
        self.assertEqual(len(self.invoke(args)), 6)
        key.write_text('## Scene 1: Garden\n**Narration**\nA seed rests.\n**Visual**\n- On s01-01, show a seed.\n')
        with self.assertRaisesRegex(ValueError, "s01-01: 3 words, under the 5-word floor: A seed rests."):
            self.invoke(args)

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
