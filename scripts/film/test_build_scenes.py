"""Check fragment assembly and separate outputs without a renderer."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).with_name("build_scenes.py")
TEMPLATE = '<style>/*{{CSS}}*/</style>\n<div data-duration="{{DURATION}}">{{SCENES}}</div>\n<script>//{{JS}}</script>\n'


class BuildScenesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "composition"
        self.fragments = self.project / "scenes"
        self.fragments.mkdir(parents=True)
        self.template = self.root / "page.tpl.html"
        self.template.write_text(TEMPLATE)
        (self.project / "data.js").write_text('window.FILM = {"source": "measured", "duration": 9.25, "extra": {"duration": 100}};\n')
        (self.fragments / "s02.js").write_text('mount(SC, "second");')
        (self.fragments / "s01.js").write_text('mount(SC, "first");\n')
        (self.fragments / "s01.css").write_text('#s01 { color: blue; }\n')
        (self.fragments / "s01.html").write_text('<span>First</span>\n')
        (self.fragments / "s02.html").write_text('<span>Second</span>')

    def invoke(self, *scene_ids):
        return subprocess.run([sys.executable, TOOL, "--project", self.project,
                               "--template", self.template, *scene_ids], cwd=self.root,
                              capture_output=True, text=True)

    def test_full_build_preserves_fragment_bytes_closures_and_data_duration(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "index.html: 2 scene fragments, 9.25 s\n")
        output = (self.project / "index.html").read_text()
        self.assertIn('<style>/* s01 */\n#s01 { color: blue; }\n</style>', output)
        self.assertIn('data-duration="9.25"', output)
        self.assertIn('<svg class="plate" viewBox="0 0 1920 1080" width="1920" height="1080"></svg><span>First</span>\n</section>', output)
        self.assertIn('// ===== s01 =====\n(() => {\nconst SC = "s01";\nmount(SC, "first");\n\n})();', output)
        self.assertIn('// ===== s02 =====\n(() => {\nconst SC = "s02";\nmount(SC, "second");\n})();', output)
        self.assertLess(output.index('id="s01"'), output.index('id="s02"'))
        self.assertNotIn("{{", output)

    def test_selected_build_keeps_empty_sections_and_other_outputs(self):
        (self.project / "index.html").write_text("Keep the full film.")
        first = self.invoke("s01")
        first_output = (self.project / "index-s01.html").read_bytes()
        second = self.invoke("s02")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        output = (self.project / "index-s02.html").read_text()
        self.assertIn('<section id="s01" class="scene"><svg class="plate" viewBox="0 0 1920 1080" width="1920" height="1080"></svg></section>', output)
        self.assertIn('<span>Second</span>', output)
        self.assertIn('const SC = "s02";', output)
        self.assertNotIn('const SC = "s01";', output)
        self.assertNotIn("color: blue", output)
        self.assertEqual((self.project / "index.html").read_text(), "Keep the full film.")
        self.assertEqual((self.project / "index-s01.html").read_bytes(), first_output)

    def test_selected_filename_uses_argument_order_and_fragments_use_scene_order(self):
        result = self.invoke("s02", "s01")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = (self.project / "index-s02-s01.html").read_text()
        self.assertLess(output.index('const SC = "s01";'), output.index('const SC = "s02";'))

    def test_unknown_scene_fails_without_overwriting(self):
        for selected in (("s99",), ("s01", "s99")):
            with self.subTest(selected=selected):
                result = self.invoke(*selected)
                self.assertEqual(result.returncode, 1)
                self.assertIn("unknown scene ids ['s99']", result.stderr)
                self.assertEqual(list(self.project.glob("index*.html")), [])

    def test_each_missing_placeholder_fails_in_both_modes_without_overwriting(self):
        for name in ("CSS", "JS", "SCENES", "DURATION"):
            for selected in ((), ("s01",)):
                with self.subTest(name=name, selected=selected):
                    self.template.write_text(TEMPLATE.replace("{{" + name + "}}", ""))
                    result = self.invoke(*selected)
                    self.assertEqual(result.returncode, 1)
                    self.assertIn(f"template missing placeholders: {name}", result.stderr)
                    self.assertEqual(list(self.project.glob("index*.html")), [])

    def test_unwrapped_placeholders_produce_the_same_output(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = (self.project / "index.html").read_bytes()
        self.template.write_text(TEMPLATE.replace("/*{{CSS}}*/", "{{CSS}}").replace("//{{JS}}", "{{JS}}"))
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.project / "index.html").read_bytes(), expected)

    def test_empty_composition_fails_clearly(self):
        empty = self.root / "empty"
        empty.mkdir()
        result = subprocess.run([sys.executable, TOOL, "--project", empty, "--template", self.template, "s01"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("has no sNN.js scene fragments", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
