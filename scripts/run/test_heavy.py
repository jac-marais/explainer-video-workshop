"""Verify serialization, priority and crash release with short local commands."""
import os
from pathlib import Path
import signal
import runpy
from unittest.mock import Mock, patch
import subprocess
import sys
import tempfile
import time
import unittest

HEAVY = Path(__file__).with_name("heavy")
BOOT = "from pathlib import Path; from unittest.mock import patch; import runpy,sys; root=sys.argv.pop(1); tool=sys.argv.pop(1); patch('pathlib.Path.home',return_value=Path(root)).start(); runpy.run_path(tool,run_name='__main__')"


class HeavyTests(unittest.TestCase):
    def test_nested_command_reuses_lock_and_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            nested = [sys.executable, "-c", BOOT, directory, str(HEAVY), sys.executable, "-c",
                      "import os; print(os.getpriority(os.PRIO_PROCESS, 0))"]
            code = f"import subprocess; subprocess.run({nested!r}, check=True)"
            process = subprocess.Popen([sys.executable, "-c", BOOT, directory, str(HEAVY), sys.executable, "-c", code],
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                       start_new_session=True)
            try:
                out, err = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 0, err)
                ceiling = 19 if sys.platform == "linux" else 20
                self.assertEqual(int(out.strip()), min(ceiling, os.getpriority(os.PRIO_PROCESS, 0) + 10))
                self.assertNotIn("waiting for", err)
            finally:
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGKILL)
                process.communicate()

    def test_inherited_lock_does_not_adjust_priority_again(self):
        main = runpy.run_path(str(HEAVY))["main"]
        execute = Mock(return_value=0)
        with patch.dict(os.environ, {"EXPLAINER_VIDEO_HEAVY_LOCK": str(Path.home() / ".cache/explainer-video-heavy.lock")}), \
                patch.object(sys, "argv", ["heavy", "example"]), patch.object(os, "nice") as nice, \
                patch.dict(main.__globals__, {"execute": execute}):
            self.assertEqual(main(), 0)
        nice.assert_not_called()
        execute.assert_called_once_with(["example"])

    def test_concurrent_commands_and_crash_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            processes = []
            def start(code):
                process = subprocess.Popen([sys.executable, "-c", BOOT, str(root), str(HEAVY), sys.executable, "-c", code],
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                processes.append(process)
                return process
            try:
                events = root / "events"
                def command(name):
                    return f"import os,time; f=open({str(events)!r},'a'); f.write('{name} start '+str(os.getpriority(os.PRIO_PROCESS,0))+'\\n'); f.flush(); time.sleep(0.3); f.write('{name} end\\n'); f.close()"
                first = start(command("first"))
                deadline = time.monotonic() + 5
                while not events.exists() and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertTrue(events.exists())
                second = start(command("second"))
                _, err1 = first.communicate(timeout=10)
                _, err2 = second.communicate(timeout=10)
                self.assertEqual(first.returncode, 0, err1)
                self.assertEqual(second.returncode, 0, err2)
                self.assertIn("waiting for", err2)
                lines = events.read_text().splitlines()
                self.assertEqual([line.split()[:2] for line in lines], [["first", "start"], ["first", "end"], ["second", "start"], ["second", "end"]])
                self.assertGreaterEqual(int(lines[0].split()[2]), 10)
                crashed = start("import os,signal; os.kill(os.getpid(),signal.SIGKILL)")
                crashed.communicate(timeout=5)
                self.assertEqual(crashed.returncode, -signal.SIGKILL)
                after = start("print('released')")
                out, err = after.communicate(timeout=5)
                self.assertEqual(after.returncode, 0, err)
                self.assertEqual(out.strip(), "released")
            finally:
                for process in processes:
                    if process.poll() is None:
                        process.kill()
                    process.communicate()


if __name__ == "__main__":
    unittest.main()
