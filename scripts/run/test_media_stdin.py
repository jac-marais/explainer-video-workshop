"""Media subprocesses must leave the caller's command input alone."""
from contextlib import redirect_stdout
import ast
import io
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]


def load(name):
    path = SCRIPTS / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MediaStdinTests(unittest.TestCase):
    def test_media_helpers_close_stdin(self):
        for name, function in (("film/check_film.py", "run"), ("run/receipts.py", "run"), ("film/render.py", "sh")):
            module = load(name)
            with self.subTest(name=name), patch.object(module.subprocess, "run", return_value=SimpleNamespace(
                    returncode=0, stdout="", stderr="")) as run:
                getattr(module, function)(["ffprobe", "-version"])
                self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        module = load("film/render.py")
        with patch.object(module.subprocess, "run", return_value=SimpleNamespace(stdout="aac")) as run:
            module.aac_args()
            self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_direct_media_calls_close_stdin(self):
        # Also cover helpers outside scripts/, without loading their voice engines.
        root = SCRIPTS.parent
        for folder in (root / "scripts", root / "templates/voice"):
            for path in folder.rglob("*.py"):
                if path.name.startswith("test_"):
                    continue
                for node in ast.walk(ast.parse(path.read_text())):
                    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                        continue
                    if node.func.attr not in ("run", "Popen", "check_output", "check_call") or not node.args:
                        continue
                    command = node.args[0]
                    if not isinstance(command, (ast.List, ast.Tuple)) or not command.elts:
                        continue
                    first = command.elts[0]
                    if not isinstance(first, ast.Constant) or first.value not in ("ffmpeg", "ffprobe"):
                        continue
                    with self.subTest(path=str(path.relative_to(root)), line=node.lineno):
                        stdin = next((kw.value for kw in node.keywords if kw.arg == "stdin"), None)
                        self.assertIsNotNone(stdin)
                        self.assertEqual(ast.unparse(stdin), "subprocess.DEVNULL")

    def test_motion_probe_and_decoder_close_stdin(self):
        module = load("film/measure_motion.py")
        with patch.object(sys, "argv", ["measure_motion.py", "example.mp4"]), patch.object(
                module.subprocess, "run", side_effect=[SimpleNamespace(stdout=b"4"),
                SimpleNamespace(stdout=bytes(module.PIXELS * 20))]) as run:
            with redirect_stdout(io.StringIO()):
                module.main()
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            self.assertEqual(call.kwargs["stdin"], subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main()
