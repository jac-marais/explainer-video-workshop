"""Check invented sentence cues in measured builds."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cues import cue_names, sentence_ref, sentence_time

SCRIPTS = Path(__file__).resolve().parents[1]


def script(text, visual="- On `s03-01`, show a seed.\n- On s03-02+0.4, show a leaf."):
    return f"## Scene 3: Garden\n\n**Narration**\n\n{text}\n\n**Visual**\n\n{visual}\n"


def run(tool, *args):
    return subprocess.run([sys.executable, SCRIPTS / tool, *map(str, args)], capture_output=True, text=True, timeout=120)


class SentenceCueTests(unittest.TestCase):
    def test_syntax_and_bad_fraction(self):
        self.assertEqual(cue_names('- On `s03-01`, a seed.\n- **s03-02+0.4** leaf.\n- On "the rain", water.\n- `s03-03` sky.'),
                         ["s03-01", "s03-02+0.4", "the rain", "s03-03"])
        for cue in ("s03-02+1.2", "s03-02+-0.1", "s03-02+oops"):
            with self.assertRaisesRegex(ValueError, "invalid sentence cue"):
                sentence_ref(cue)
        self.assertIsNone(sentence_ref("the rain"))
        with self.assertRaisesRegex(ValueError, "missing sentence s03-02"):
            sentence_time("s03-02", "s03", [])

    def test_measured_sentence_cues_override_a_stale_cues_file(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            source = project / "script.md"
            source.write_text(script("A small seed rests in the soil. Two green leaves grow toward the sun."))
            timing = {"duration": 8, "scenes": [{"id": "s03", "start": 1, "end": 7}], "sentences": [
                {"id": "s03-01", "scene_id": "s03", "start": 1, "end": 3},
                {"id": "s03-02", "scene_id": "s03", "start": 4, "end": 7}]}
            (project / "timing.json").write_text(json.dumps(timing))
            (project / "words.json").write_text('{"words": []}')
            (project / "captions.json").write_text('[]')
            result = run("audio/cues.py", source, project / "words.json", project / "timing.json", "--out", project / "cues.json", "--strict")
            self.assertEqual(result.returncode, 0, result.stderr)
            measured = json.loads((project / "cues.json").read_text())
            self.assertEqual([(r["start"], r["end"]) for r in measured], [(1, 3), (5.2, 7)])
            measured[1]["start"] = 99
            (project / "cues.json").write_text(json.dumps(measured))
            result = run("film/build_data.py", "--script", source, "--project", project, "--audio", project)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((project / "data.js").read_text()[12:-2])
            self.assertEqual(data["cues"], {"s03|s03-01": 1, "s03|s03-02+0.4": 5.2})

    def test_mixed_cues_keep_sentence_names_when_quoted_order_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, key = root / "script.md", root / "key.md"
            key.write_text(script("A seed rests. Two leaves grow.", '- On s03-01, seed.\n- On "Two leaves", leaves.\n- On s03-02+0.4, light.'))
            source.write_text(script("Une graine repose. Deux feuilles poussent.", '- On "Deux feuilles", leaves.\n- On s03-01, seed.\n- On s03-02+0.4, light.'))
            (root / "timing.json").write_text(json.dumps({"duration": 6, "scenes": [{"id": "s03", "start": 0, "end": 6}], "sentences": [
                {"id": "s03-01", "scene_id": "s03", "start": 0, "end": 2}, {"id": "s03-02", "scene_id": "s03", "start": 3, "end": 6}]}))
            (root / "cues.json").write_text(json.dumps([{"scene": "s03", "cue": "Deux feuilles", "start": 3, "end": 4}]))
            (root / "captions.json").write_text("[]")
            result = run("film/build_data.py", "--script", source, "--key-script", key, "--project", root, "--audio", root)
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((root / "data.js").read_text()[12:-2])
            self.assertEqual(set(data["cues"]), {"s03|s03-01", "s03|Two leaves", "s03|s03-02+0.4"})

    def test_missing_sentence_fails_in_cues_and_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "script.md"
            source.write_text(script("A seed rests."))
            (root / "words.json").write_text('{"words": []}')
            (root / "timing.json").write_text(json.dumps({"duration": 3, "scenes": [{"id": "s03", "start": 0, "end": 3}],
                "sentences": [{"id": "s03-01", "start": 0, "end": 3}]}))
            (root / "cues.json").write_text('[]')
            (root / "captions.json").write_text('[]')
            commands = [("audio/cues.py", source, root / "words.json", root / "timing.json", "--out", root / "out.json"),
                        ("film/build_data.py", "--script", source, "--project", root, "--audio", root)]
            for command in commands:
                result = run(*command)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing sentence s03-02", result.stderr)


if __name__ == "__main__":
    unittest.main()
