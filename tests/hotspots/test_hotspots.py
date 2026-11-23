"""bin/hotspots, on repositories with a made-up history.

    python3 -I -m unittest discover -s tests/hotspots -t tests/hotspots
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "hotspots")
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null",
       "GIT_CONFIG_NOSYSTEM": "1"}


class HotspotsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = tempfile.mkdtemp()
        self.git("init", "-q", "-b", "main")
        self.commits = 0

    def tearDown(self) -> None:
        shutil.rmtree(self.repo)

    def git(self, *args: str) -> None:
        subprocess.run(["git", *args], cwd=self.repo, check=True,
                       capture_output=True, env=ENV)

    def commit(self, *paths: str) -> None:
        """Changes each path in one commit."""
        self.commits += 1
        for path in paths:
            full = os.path.join(self.repo, path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "a", encoding="utf-8") as stream:
                stream.write(f"{self.commits}\n")
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "-m", f"Change {self.commits}")

    def hotspots(self, *args: str) -> list[str]:
        found = subprocess.run([SCRIPT, *args], cwd=self.repo, text=True,
                               capture_output=True, check=False, env=ENV)
        self.assertEqual(found.returncode, 0, found.stderr)
        return found.stdout.splitlines()

    def test_ranks_files_then_directories_by_changes(self) -> None:
        for _ in range(3):
            self.commit("src/orders/pricing.py")
        self.commit("src/orders/pricing.py", "src/orders/tax.py")
        self.commit("src/cli.py")
        self.assertEqual(self.hotspots(), [
            "FILES", "4  src/orders/pricing.py", "1  src/cli.py",
            "1  src/orders/tax.py", "DIRECTORIES", "6  src/",
            "5  src/orders/"])

    def test_leaves_out_what_is_not_the_projects_code(self) -> None:
        for path in ("README.md", "docs/guide.rst", "Cargo.lock",
                     "package-lock.json", "vendor/lib/a.c",
                     "node_modules/x/index.js", "dist/app.js", "notes.txt"):
            self.commit(path)
        self.commit("src/main.c")
        self.assertEqual(self.hotspots()[:3],
                         ["FILES", "1  src/main.c", "DIRECTORIES"])

    def test_leaves_out_files_that_are_gone(self) -> None:
        self.commit("src/old.py", "src/new.py")
        os.remove(os.path.join(self.repo, "src", "old.py"))
        self.git("add", "-A")
        self.git("-c", "user.name=t", "-c", "user.email=t@example.com",
                 "commit", "-q", "-m", "Remove old")
        self.assertEqual(self.hotspots()[1], "1  src/new.py")
        self.assertNotIn("src/old.py", "\n".join(self.hotspots()))

    def test_keeps_paths_with_spaces(self) -> None:
        self.commit("src/my module/a b.py")
        self.assertEqual(self.hotspots()[1], "1  src/my module/a b.py")

    def test_limits_the_lists_and_the_history(self) -> None:
        for name in "abcd":
            self.commit(f"src/{name}.py")
        self.assertEqual(self.hotspots("--top", "2"), [
            "FILES", "1  src/a.py", "1  src/b.py", "DIRECTORIES",
            "4  src/"])
        self.assertEqual(self.hotspots("--commits", "1")[1], "1  src/d.py")

    def test_refuses_bad_options_and_no_history(self) -> None:
        for args in (("--top",), ("--commits", "x"), ("--bogus",)):
            with self.subTest(args=args):
                self.assertEqual(subprocess.run(
                    [SCRIPT, *args], cwd=self.repo, capture_output=True,
                    check=False, env=ENV).returncode, 2)
        found = subprocess.run([SCRIPT], cwd=self.repo, capture_output=True,
                               text=True, check=False, env=ENV)
        self.assertEqual(found.returncode, 2)
        self.assertEqual(found.stderr, "hotspots: no commits here\n")


if __name__ == "__main__":
    unittest.main()
