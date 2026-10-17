"""The Linux offline verdict requires render tools, without voice models or eSpeak."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

CHECK = Path(__file__).with_name('setup_check.sh')


class SetupCheckTests(unittest.TestCase):
    def test_linux_render_only_verdict_and_browser_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            binaries = root / 'bin'
            binaries.mkdir()
            models = root / 'models'
            models.mkdir()
            (models / 'resources.json').write_text('{}')
            commands = {
                'uname': 'echo Linux',
                'ffmpeg': 'echo " drawtext "',
                'ffprobe': 'exit 0',
                'uv': f'echo "{models}"',
                'node': 'echo 22',
                'chromium': 'exit 0',
            }
            for name, body in commands.items():
                path = binaries / name
                path.write_text('#!/bin/sh\n' + body + '\n')
                path.chmod(0o755)
            env = {**os.environ, 'HOME': str(root), 'PATH': str(binaries) + ':' + os.defpath}
            env.pop('HYPERFRAMES_BROWSER_PATH', None)
            def check():
                return subprocess.run(['sh', str(CHECK)], env=env, capture_output=True, text=True)
            result = check()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('Linux renders existing audio', result.stdout)
            self.assertNotIn('== voice', result.stdout)
            self.assertNotIn('== whisper', result.stdout)
            self.assertIn(str(binaries / 'chromium'), result.stdout)
            (binaries / 'chromium').unlink()
            self.assertNotEqual(check().returncode, 0)
            env['HYPERFRAMES_BROWSER_PATH'] = str(binaries / 'node')
            self.assertEqual(check().returncode, 0)
            env['HYPERFRAMES_BROWSER_PATH'] = str(root / 'missing-browser')
            self.assertNotEqual(check().returncode, 0)


if __name__ == '__main__':
    unittest.main()
