"""Check script conversion and both production consumers without voicing."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import make_film

TOOL = Path(__file__).with_name("scenes_json.py")
SCRIPT = """# A garden film

## Scene 1: Graine

This scene starts a fresh voice take.

**Narration.** A small seed rests in the soil.
A green leaf grows toward the sun.

**Visual.** On s01-01, show a seed.
On s01-02, show a green leaf.

## Scene 2: Rain

**Narration.** Soft rain falls across the garden.

**Visual.** On s02-01, show some rain.
"""


class ScenesJsonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.script = self.root / "authored.md"
        self.script.write_text(SCRIPT)
        self.output = self.root / "narration-scenes.json"

    def invoke(self):
        return subprocess.run([sys.executable, TOOL, "--script", self.script, "--out", self.output],
                              cwd=self.root, capture_output=True, text=True)

    def test_inline_period_headings_preserve_fields_and_fresh_take_mark(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "2 scenes\n")
        rows = json.loads(self.output.read_text())
        self.assertEqual(rows[0], {"id": "s01", "title": "Graine", "visual": "On s01-01, show a seed.\nOn s01-02, show a green leaf.",
                                   "claim_ids": [], "narration": "A small seed rests in the soil.\nA green leaf grows toward the sun.",
                                   "starts_fresh_take": True})
        self.assertEqual(set(rows[1]), {"id", "title", "visual", "claim_ids", "narration"})
        self.assertEqual(self.output.read_text(), json.dumps(rows, indent=1, ensure_ascii=False) + "\n")

    def test_multiline_headings_without_periods_produce_the_same_json(self):
        self.assertEqual(self.invoke().returncode, 0)
        expected = self.output.read_bytes()
        self.script.write_text(SCRIPT.replace("**Narration.** ", "**Narration**\n\n").replace("**Visual.** ", "**Visual**\n\n"))
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.output.read_bytes(), expected)

    def test_fresh_take_phrase_in_narration_or_visual_is_only_text(self):
        for heading in ("**Narration.**", "**Visual.**"):
            with self.subTest(heading=heading):
                self.script.write_text(SCRIPT.replace("This scene starts a fresh voice take.\n\n", "")
                                       .replace(heading, heading + " This scene starts a fresh voice take.", 1))
                result = self.invoke()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("starts_fresh_take", json.loads(self.output.read_text())[0])

    def test_output_passes_production_consumers(self):
        import narrate_film
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        split = lambda text: [{"text": line, "pause_before": False} for line in text.replace(". ", ".\n").splitlines()]
        with patch.object(narrate_film, "sentences", side_effect=lambda text, language: split(text)):
            loaded = narrate_film.load_scenes(self.output, "en")
        self.assertEqual([row["id"] for row in loaded], ["s01", "s02"])
        self.assertEqual([len(row["_sentences"]) for row in loaded], [2, 1])
        args = argparse.Namespace(script=self.script, scenes=self.output, key_script=None,
                                  language="en", key_language=None, start="narrate")
        with patch.object(make_film, "split_sentences", side_effect=lambda texts: [[part["text"] for part in split(text)] for _, text in texts]):
            make_film.validate_inputs(args)

    def test_invalid_script_does_not_overwrite_existing_output(self):
        cases = (("# Empty\n", "script has no scenes"),
                 (SCRIPT.replace("## Scene 2:", "## Scene 1:"), "duplicate scene id: s01"),
                 (SCRIPT.replace("**Visual.** On s02-01, show some rain.", ""), "needs a **Narration.** part followed by a **Visual.** part"),
                 (SCRIPT.replace("**Visual.** On s02-01, show some rain.", "**Visual.**"), "needs a non-empty visual"),
                 (SCRIPT.replace("Soft rain falls across the garden.", ""), "needs a non-empty narration"))
        for script_text, message in cases:
            with self.subTest(message=message):
                self.script.write_text(script_text)
                self.output.write_text("Keep the prior scenes.")
                result = self.invoke()
                self.assertEqual(result.returncode, 1)
                self.assertIn(message, result.stderr)
                self.assertEqual(self.output.read_text(), "Keep the prior scenes.")


if __name__ == "__main__":
    unittest.main()
