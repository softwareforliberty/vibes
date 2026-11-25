"""evals/run, which runs the evals with lib/eval-path first on PATH.

    python3 -I -m unittest discover -s tests/eval_path -t tests/eval_path
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
RUN = os.path.join(ROOT, "evals", "run")
WRAPPER_DIR = os.path.join(ROOT, "lib", "eval-path")
SYSTEM_PATH = "/usr/bin:/bin"
FAKE_CLAUDE = ('#!/bin/sh\necho "claude $*"\n'
               'echo "first on PATH ${PATH%%:*}"\n')


class EvalsRunTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.bin = self.executable("bin", "claude", FAKE_CLAUDE)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def executable(self, directory: str, name: str, text: str) -> str:
        """Makes a script in a directory under the test's own, and returns
        the directory."""
        full = os.path.join(self.tmp, directory)
        os.makedirs(full, exist_ok=True)
        path = os.path.join(full, name)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.chmod(path, 0o755)
        return full

    def run_evals(self, path: str, *args: str,
                  **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([RUN, *args], text=True, capture_output=True,
                              check=False, env={"PATH": path, **env})

    def test_runs_the_plugins_evals_with_the_wrapper_first(self) -> None:
        tools = self.executable("tools", "git", "#!/bin/sh\n")
        found = self.run_evals(f"{self.bin}:{tools}:{SYSTEM_PATH}",
                               "--tag", "tdd", "--runs", "1")
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(found.stdout.splitlines(), [
            f"claude plugin eval {ROOT} --tag tdd --runs 1",
            f"first on PATH {WRAPPER_DIR}"])

    @unittest.skipUnless(sys.platform == "darwin", "Apple's stand-in")
    def test_stops_on_a_mac_with_only_apples_stand_in(self) -> None:
        found = self.run_evals(f"{self.bin}:{SYSTEM_PATH}", "--tag", "tdd",
                               DEVELOPER_DIR=os.path.join(self.tmp, "none"))
        self.assertEqual(found.returncode, 2)
        self.assertEqual(found.stdout, "")
        self.assertIn("xcode-select --install", found.stderr)
        self.assertIn("brew install git", found.stderr)


if __name__ == "__main__":
    unittest.main()
