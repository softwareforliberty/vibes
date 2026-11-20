"""bin/install-git-hooks: stubs that run the newest installed vibes, and
refuse the commit when there's none.

    python3 -I -m unittest discover -s tests/hooks -t tests/hooks
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
GIT = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}


class InstallTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = os.path.realpath(tempfile.mkdtemp())
        self.log = os.path.join(self.tmp, "ran.log")
        self.versions = os.path.join(self.tmp, "plugins", "cache", "vibes",
                                     "vibes")
        for version in ("0.5.1", "0.10.0", "0.6.0"):
            self.plugin(os.path.join(self.versions, version), version)
        self.repo = os.path.join(self.tmp, "repo")
        os.mkdir(self.repo)
        self.run_in(["git", "init", "-q"])
        self.hooks = os.path.join(self.repo, ".git", "hooks")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp)

    def plugin(self, root: str, name: str) -> None:
        """A copy of the installer and stub, with hooks that record which
        copy ran them."""
        os.makedirs(os.path.join(root, "bin"))
        os.makedirs(os.path.join(root, "hooks"))
        shutil.copy(os.path.join(ROOT, "bin", "install-git-hooks"),
                    os.path.join(root, "bin"))
        shutil.copy(os.path.join(ROOT, "hooks", "git_hook_stub"),
                    os.path.join(root, "hooks"))
        for hook in ("git_pre_commit", "git_commit_msg"):
            path = os.path.join(root, "hooks", hook)
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(f"#!/bin/sh\necho '{name} {hook}' >> "
                             f"'{self.log}'\n")
            os.chmod(path, 0o755)

    def run_in(self, command: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(command, cwd=self.repo, capture_output=True,
                              text=True, env={**os.environ, **GIT},
                              check=False)

    def install(self, root: str, *args: str) -> subprocess.CompletedProcess:
        return self.run_in([os.path.join(root, "bin", "install-git-hooks"),
                            *args])

    def commit(self) -> subprocess.CompletedProcess:
        return self.run_in(["git", "commit", "-q", "--allow-empty", "-m",
                            "Change"])

    def ran(self) -> list[str]:
        if not os.path.exists(self.log):
            return []
        with open(self.log, encoding="utf-8") as stream:
            return stream.read().splitlines()

    def test_runs_the_newest_version(self) -> None:
        result = self.install(os.path.join(self.versions, "0.5.1"))
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("pre-commit", "commit-msg"):
            path = os.path.join(self.hooks, name)
            self.assertFalse(os.path.islink(path))
            self.assertTrue(os.access(path, os.X_OK))
        self.assertEqual(self.commit().returncode, 0)
        self.assertEqual(self.ran(), ["0.10.0 git_pre_commit",
                                      "0.10.0 git_commit_msg"])

    def test_survives_removing_the_installing_version(self) -> None:
        self.install(os.path.join(self.versions, "0.5.1"))
        for version in ("0.5.1", "0.10.0"):
            shutil.rmtree(os.path.join(self.versions, version))
        self.assertEqual(self.commit().returncode, 0)
        self.assertEqual(self.ran()[0], "0.6.0 git_pre_commit")

    def test_refuses_the_commit_without_vibes(self) -> None:
        self.install(os.path.join(self.versions, "0.5.1"))
        shutil.rmtree(self.versions)
        result = self.commit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no longer installed", result.stderr)

    def test_a_plugin_outside_the_cache_is_used_where_it_is(self) -> None:
        checkout = os.path.join(self.tmp, "vibes")
        self.plugin(checkout, "checkout")
        self.install(checkout)
        self.assertEqual(self.commit().returncode, 0)
        self.assertEqual(self.ran()[0], "checkout git_pre_commit")

    def test_replaces_a_broken_vibes_link(self) -> None:
        old = os.path.join(self.hooks, "pre-commit")
        os.symlink("/gone/cache/vibes/vibes/0.3.0/hooks/git_pre_commit", old)
        result = self.install(os.path.join(self.versions, "0.6.0"))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(os.path.islink(old))

    def test_leaves_another_hook_alone_unless_asked(self) -> None:
        theirs = os.path.join(self.hooks, "pre-commit")
        with open(theirs, "w", encoding="utf-8") as stream:
            stream.write("#!/bin/sh\nexit 0\n")
        root = os.path.join(self.versions, "0.6.0")
        result = self.install(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("aren't vibes'", result.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.hooks,
                                                     "commit-msg")))
        self.assertEqual(self.install(root, "--replace").returncode, 0)
        with open(theirs, encoding="utf-8") as stream:
            self.assertIn("vibes-commit-gate", stream.read())

    def test_refuses_a_hooks_path(self) -> None:
        self.run_in(["git", "config", "core.hooksPath", ".husky"])
        result = self.install(os.path.join(self.versions, "0.6.0"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("core.hooksPath", result.stderr)


if __name__ == "__main__":
    unittest.main()
