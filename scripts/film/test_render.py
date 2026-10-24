"""The render guard uses a stand-in HyperFrames CLI, so no browser or film is involved."""
from pathlib import Path
import shutil, subprocess, sys, tempfile, unittest
from unittest.mock import patch

RENDER = Path(__file__).resolve().parent / "render.py"
sys.path.insert(0, str(RENDER.parent))
import render  # noqa: E402


def run(cli_body, env_extra=None, input=None):
    with tempfile.TemporaryDirectory() as d:
        cli = Path(d) / "hf.sh"
        cli.write_text(cli_body)
        env = {"PATH": "/usr/bin:/bin", **(env_extra or {})}
        return subprocess.run([sys.executable, RENDER, "--hf", cli, "--project", d, ".", "-o", Path(d) / "out.mp4"],
                              capture_output=True, text=True, env=env, input=input)


class RenderGuardTests(unittest.TestCase):
    def test_renderer_does_not_read_the_callers_pipe(self):
        r = run('read answer || true; echo "stdin=$answer"; exit 3\n', input="q\n")
        self.assertIn("stdin=\n", r.stdout)


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

    def test_an_explicit_browser_wins(self):
        r = run('echo "browser=$HYPERFRAMES_BROWSER_PATH"; exit 3\n', {"HYPERFRAMES_BROWSER_PATH": "/opt/example/browser"})
        self.assertIn("browser=/opt/example/browser\n", r.stdout)


class HostBrowserTests(unittest.TestCase):
    def test_linux_order_is_chrome_then_chromium(self):
        for available, expected in (({"google-chrome": "/a/google-chrome", "chromium": "/a/chromium"}, "/a/google-chrome"),
                                    ({"chromium": "/a/chromium", "chromium-browser": "/a/chromium-browser"}, "/a/chromium"),
                                    ({"chromium-browser": "/a/chromium-browser"}, "/a/chromium-browser"),
                                    ({}, None)):
            with self.subTest(available=available), patch.object(render.sys, "platform", "linux"), \
                    patch.object(render.shutil, "which", side_effect=available.get):
                self.assertEqual(render.host_browser(), expected)

    def test_macos_uses_the_app_only_when_installed(self):
        with patch.object(render.sys, "platform", "darwin"), patch.object(render.Path, "exists", return_value=False):
            self.assertIsNone(render.host_browser())
        with patch.object(render.sys, "platform", "darwin"), patch.object(render.Path, "exists", return_value=True):
            self.assertEqual(render.host_browser(), render.CHROME)


@unittest.skipUnless(shutil.which("ffmpeg"), "ffmpeg required")
class EncodedTruePeakTests(unittest.TestCase):
    def test_measures_the_encoded_master(self):
        with tempfile.TemporaryDirectory() as d:
            wav = Path(d) / "tone.wav"
            subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
                            "-af", "volume=-6dB", "-ar", "48000", "-ac", "1", "-c:a", "pcm_s24le", wav], check=True)
            peak = render.encoded_true_peak(wav)
            self.assertAlmostEqual(peak, render.loudness(wav)[1], delta=1.0)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["tone.wav"])

    def test_narration_filter_pads_whole_aac_frames(self):
        self.assertEqual(render.narration_filter(), "aresample=48000,pan=stereo|c0=c0|c1=c0")
        self.assertTrue(render.narration_filter(1.0).endswith(",apad=whole_len=47104"))


if __name__ == "__main__":
    unittest.main()
