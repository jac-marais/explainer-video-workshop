"""The render guard uses a stand-in HyperFrames CLI, so no browser or film is involved."""
from pathlib import Path
import subprocess, sys, tempfile, unittest

RENDER = Path(__file__).resolve().parent / "render.py"


def run(cli_body, env_extra=None):
    with tempfile.TemporaryDirectory() as d:
        cli = Path(d) / "hf.sh"
        cli.write_text(cli_body)
        env = {"PATH": "/usr/bin:/bin", **(env_extra or {})}
        return subprocess.run([sys.executable, RENDER, "--hf", cli, "--project", d, ".", "-o", Path(d) / "out.mp4"],
                              capture_output=True, text=True, env=env)


class RenderGuardTests(unittest.TestCase):
    def test_screenshot_fallback_fails_even_when_the_cli_succeeds(self):
        r = run('echo "drawElement self-verification failed; re-rendering via screenshot"\n')
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("re-rendering via screenshot", r.stdout)
        self.assertIn("fell back to screenshot capture", r.stderr)
        self.assertFalse(Path(r.args[-1]).exists())

    def test_self_verify_is_off_unless_the_environment_sets_it(self):
        for env, expected in (({}, "0"), ({"HF_DE_VERIFY": "4"}, "4")):
            with self.subTest(env=env):
                r = run('echo "verify=$HF_DE_VERIFY"; exit 3\n', env)
                self.assertIn(f"verify={expected}\n", r.stdout)
                self.assertIn("failed:", r.stderr)


if __name__ == "__main__":
    unittest.main()
