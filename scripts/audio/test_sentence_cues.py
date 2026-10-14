"""Check invented sentence cues across measured and estimated language builds."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from cues import cue_names, sentence_ref, sentence_time

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / "storyboard"))
from storyboard import build


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

    def test_two_languages_build_same_names_in_both_modes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            keys = []
            for lang, text in (("en", "A seed rests. Two leaves grow."), ("fr", "Une graine repose. Deux feuilles poussent.")):
                project = root / lang
                project.mkdir()
                source = project / "script.md"
                source.write_text(script(text))
                (project / "index.html").write_text('<div data-duration="1"></div>')
                result = run("film/build_data.py", "--script", source, "--project", project, "--estimate", "--language", lang)
                self.assertEqual(result.returncode, 0, result.stderr)
                estimated = json.loads((project / "data.js").read_text()[12:-2])
                keys.append(set(estimated["cues"]))
                self.assertLess(estimated["cues"]["s03|s03-01"], estimated["cues"]["s03|s03-02+0.4"])
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
                keys.append(set(data["cues"]))
                page, errors, _ = build(source, None, lang)
                self.assertEqual(errors, [])
                self.assertIn("s03-02+0.4", page)
            self.assertTrue(all(value == keys[0] for value in keys))

    def test_mixed_cues_keep_sentence_names_when_quoted_order_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, key = root / "script.md", root / "key.md"
            key.write_text(script("A seed rests. Two leaves grow.", '- On s03-01, seed.\n- On "Two leaves", leaves.\n- On s03-02+0.4, light.'))
            source.write_text(script("Une graine repose. Deux feuilles poussent.", '- On "Deux feuilles", leaves.\n- On s03-01, seed.\n- On s03-02+0.4, light.'))
            result = run("film/build_data.py", "--script", source, "--key-script", key, "--project", root, "--estimate", "--language", "fr")
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads((root / "data.js").read_text()[12:-2])
            self.assertEqual(set(data["cues"]), {"s03|s03-01", "s03|Two leaves", "s03|s03-02+0.4"})

    def test_unicode_sentence_boundaries_and_pause_in_storyboard(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "script.md"
            source.write_text(script('小花在阳光下慢慢地开了。妈妈笑着说：“真好看！”然后走进了屋里。[pause]明天它还会继续开吗？',
                                     '- On s03-02+0.4, leaf.\n- On s03-03, sky.'))
            page, errors, _ = build(source, None, "zh")
            self.assertEqual(errors, [])
            self.assertIn('明天它还会继续开吗？', page)
            result = run("film/build_data.py", "--script", source, "--project", directory, "--estimate", "--language", "zh")
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_sentence_fails_in_every_tool_and_translation_count_in_the_storyboard(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, key = root / "script.md", root / "key.md"
            source.write_text(script("A seed rests."))
            key.write_text(script("A seed rests. Two leaves grow."))
            (root / "words.json").write_text('{"words": []}')
            (root / "timing.json").write_text(json.dumps({"duration": 3, "scenes": [{"id": "s03", "start": 0, "end": 3}],
                "sentences": [{"id": "s03-01", "start": 0, "end": 3}]}))
            (root / "cues.json").write_text('[]')
            (root / "captions.json").write_text('[]')
            commands = [("audio/cues.py", source, root / "words.json", root / "timing.json", "--out", root / "out.json"),
                        ("storyboard/storyboard.py", source, "--language", "en", "--out", root / "board.html"),
                        ("film/build_data.py", "--script", source, "--project", root, "--estimate", "--language", "en"),
                        ("film/build_data.py", "--script", source, "--project", root, "--audio", root)]
            for command in commands:
                result = run(*command)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("missing sentence s03-02", result.stderr)
            source.write_text(script("A seed rests.", '- On s03-01, show a seed.'))
            result = run(*commands[1], "--key-script", key, "--key-language", "en")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("scene 3: 1 sentences, but the key script has 2", result.stderr)


if __name__ == "__main__":
    unittest.main()
