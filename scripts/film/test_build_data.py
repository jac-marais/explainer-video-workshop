#!/usr/bin/env python3
"""Check that build_data.py times cues in both modes, keys a translated script's cues, and updates the composition."""
import json, subprocess, sys, tempfile, unittest
from pathlib import Path

TOOL = Path(__file__).with_name("build_data.py")

SCRIPT = """# A test film

## Scene 1: Water

**Narration**

Rain falls on the hills, and it runs downhill into the river.

**Visual**

- On "Rain falls", clouds gather.
- On "runs downhill", a stream forms.

## Scene 2: Sun

**Narration**

The sun warms the sea.

**Visual**

- On "warms the sea", vapour rises.
"""

# The same beats in another language, in the same order.
TRANSLATED = """# Ein Testfilm

## Scene 1: Wasser

**Narration**

Regen fällt auf die Hügel, und er fließt bergab in den Fluss.

**Visual**

- On "Regen fällt", clouds gather.
- On "fließt bergab", a stream forms.

## Scene 2: Sonne

**Narration**

Die Sonne wärmt das Meer.

**Visual**

- On "wärmt das Meer", vapour rises.
"""


def run(tmp, *args):
    return subprocess.run([sys.executable, TOOL, *args], capture_output=True, text=True, cwd=tmp)


def film(project):
    text = (project / "data.js").read_text()
    return json.loads(text[len("window.FILM="):].rstrip().rstrip(";"))


class BuildDataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "script.md").write_text(SCRIPT)
        (self.tmp / "translated.md").write_text(TRANSLATED)
        self.project = self.tmp / "project"
        self.project.mkdir()
        (self.project / "index.html").write_text('<div id="film" data-duration="1"></div>')

    def test_estimate_times_every_cue_and_sets_duration(self):
        r = run(self.tmp, "--script", "script.md", "--project", "project", "--estimate", "--tail", "1")
        self.assertEqual(r.returncode, 0, r.stderr)
        f = film(self.project)
        self.assertEqual(set(f["cues"]), {"s01|Rain falls", "s01|runs downhill", "s02|warms the sea"})
        self.assertLess(f["cues"]["s01|Rain falls"], f["cues"]["s01|runs downhill"])
        self.assertIn(f'data-duration="{f["duration"]}"', (self.project / "index.html").read_text())

    def test_audio_mode_reads_measured_files_and_embeds(self):
        audio = self.tmp / "audio"
        audio.mkdir()
        (audio / "cues.json").write_text(json.dumps([{"scene": "s01", "cue": "Rain falls", "start": 0.5, "end": 1.0}]))
        (audio / "captions.json").write_text(json.dumps([{"start": 0.5, "end": 2.0, "text": "Rain falls."}]))
        (audio / "timing.json").write_text(json.dumps({"duration": 9.25}))
        (self.tmp / "extra.json").write_text('{"k": 1}')
        r = run(self.tmp, "--script", "script.md", "--project", "project", "--audio", "audio", "--tail", "1.5",
                "--embed", "extra=extra.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        f = film(self.project)
        self.assertEqual(f["duration"], 10.75)
        self.assertEqual(f["cues"], {"s01|Rain falls": 0.5})
        self.assertEqual(f["extra"], {"k": 1})

    def test_translated_cues_take_the_key_scripts_names(self):
        r = run(self.tmp, "--script", "translated.md", "--project", "project", "--estimate", "--key-script", "script.md")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(set(film(self.project)["cues"]), {"s01|Rain falls", "s01|runs downhill", "s02|warms the sea"})

    def test_estimate_skips_words_that_normalize_to_nothing(self):
        (self.tmp / "accent.md").write_text(SCRIPT.replace("Rain falls on the hills", "Rain é falls on the hills").replace('On "Rain falls"', 'On "Rain é falls"'))
        r = run(self.tmp, "--script", "accent.md", "--project", "project", "--estimate")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("s01|Rain é falls", film(self.project)["cues"])

    def test_unequal_cue_counts_fail(self):
        (self.tmp / "short.md").write_text(TRANSLATED.replace('- On "fließt bergab", a stream forms.\n', ""))
        r = run(self.tmp, "--script", "short.md", "--project", "project", "--estimate", "--key-script", "script.md")
        self.assertEqual(r.returncode, 1)
        self.assertIn("scene 1: 1 cues, but the key script has 2", r.stderr)


if __name__ == "__main__":
    unittest.main()
