"""lib/eval-path/git, the wrapper evals put first on PATH.

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
WRAPPER_DIR = os.path.join(ROOT, "lib", "eval-path")
SYSTEM_PATH = "/usr/bin:/bin"
FAKE_GIT = ('#!/bin/sh\necho "fake git from $(dirname -- "$0")"\n'
            'for arg in "$@"; do echo "arg <$arg>"; done\n')


class EvalPathGitTest(unittest.TestCase):
    def setUp(self) -> None:
        # Without the wrapper, PATH would find each test's fake git anyway.
        self.assertTrue(os.access(os.path.join(WRAPPER_DIR, "git"), os.X_OK))
        self.tmp = os.path.realpath(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def fake_git(self, name: str) -> str:
        """Makes a directory holding a git that echoes its arguments."""
        directory = os.path.join(self.tmp, name)
        os.makedirs(directory)
        path = os.path.join(directory, "git")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(FAKE_GIT)
        os.chmod(path, 0o755)
        return directory

    def git(self, path: str, *args: str,
            **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", *args], text=True, capture_output=True,
                              check=False, env={"PATH": path, **env})

    def test_runs_the_next_git_on_path_with_its_arguments(self) -> None:
        other = self.fake_git("other")
        found = self.git(f"{WRAPPER_DIR}:{other}:{SYSTEM_PATH}",
                         "commit", "-m", "two words")
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(found.stdout.splitlines(), [
            f"fake git from {other}", "arg <commit>", "arg <-m>",
            "arg <two words>"])

    def test_skips_itself_however_its_directory_is_spelled(self) -> None:
        other = self.fake_git("other")
        link = os.path.join(self.tmp, "link")
        os.symlink(WRAPPER_DIR, link)
        found = self.git(
            f"{WRAPPER_DIR}:{link}:{WRAPPER_DIR}/:{other}:{SYSTEM_PATH}")
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(found.stdout.splitlines(),
                         [f"fake git from {other}"])

    def test_skips_a_directory_named_git(self) -> None:
        holder = os.path.join(self.tmp, "holder")
        os.makedirs(os.path.join(holder, "git"))
        other = self.fake_git("other")
        found = self.git(f"{WRAPPER_DIR}:{holder}:{other}:{SYSTEM_PATH}")
        self.assertEqual(found.stdout.splitlines(),
                         [f"fake git from {other}"])

    def test_fails_when_no_other_git_is_on_path(self) -> None:
        found = self.git(f"{WRAPPER_DIR}:{self.tmp}:/bin")
        self.assertEqual(found.returncode, 127)
        self.assertEqual(found.stderr, "git: no other git on PATH\n")

    def test_show_prints_the_git_it_would_run_and_runs_nothing(self) -> None:
        other = self.fake_git("other")
        found = self.git(f"{WRAPPER_DIR}:{other}:{SYSTEM_PATH}", "commit",
                         VIBES_EVAL_GIT_SHOW="1")
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(found.stdout, f"{other}/git\n")

    @unittest.skipUnless(sys.platform == "darwin", "Apple's stand-in")
    def test_runs_the_developer_tools_git_for_apples_stand_in(self) -> None:
        tools = self.fake_git("developer/usr/bin")
        found = self.git(f"{WRAPPER_DIR}:{SYSTEM_PATH}", "status",
                         DEVELOPER_DIR=os.path.join(self.tmp, "developer"))
        self.assertEqual(found.returncode, 0, found.stderr)
        self.assertEqual(found.stdout.splitlines(),
                         [f"fake git from {tools}", "arg <status>"])

    @unittest.skipUnless(sys.platform == "darwin", "Apple's stand-in")
    def test_keeps_apples_stand_in_without_developer_tools(self) -> None:
        found = self.git(f"{WRAPPER_DIR}:{SYSTEM_PATH}",
                         DEVELOPER_DIR=os.path.join(self.tmp, "none"),
                         VIBES_EVAL_GIT_SHOW="1")
        self.assertEqual(found.stdout, "/usr/bin/git\n")


if __name__ == "__main__":
    unittest.main()
