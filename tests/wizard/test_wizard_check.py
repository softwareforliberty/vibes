"""bin/wizard-check, on wizards that keep and break the template's
library.

    python3 -I -m unittest discover -s tests/wizard -t tests/wizard
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "wizard-check")
TEMPLATE = os.path.join(ROOT, "skills", "wizard", "templates", "wizard.sh")


class WizardCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        with open(TEMPLATE, encoding="utf-8") as stream:
            self.template = stream.read()
        # Neither ShellCheck nor Docker, so the check is skipped.
        self.env = {"PATH": "/usr/bin:/bin"}

    def check(self, text: str) -> subprocess.CompletedProcess:
        path = os.path.join(self.dir, "wizard.sh")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
        return subprocess.run([SCRIPT, path], text=True, capture_output=True,
                              check=False, env=self.env)

    def test_passes_the_template_with_its_header_filled_in(self) -> None:
        text = self.template.replace("<Title>", "Set up Acme Pay")
        result = self.check(text)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, "SYNTAX OK\nLIBRARY INTACT\n"
                                        "SHELLCHECK NOT AVAILABLE\n")

    def test_fails_a_changed_library(self) -> None:
        text = self.template.replace("umask 077", "umask 022")
        result = self.check(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("LIBRARY CHANGED", result.stdout)

    def test_fails_a_missing_library(self) -> None:
        result = self.check("#!/usr/bin/env bash\necho hi\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("LIBRARY CHANGED", result.stdout)

    def test_fails_broken_syntax(self) -> None:
        text = self.template.replace("main() {", "main() { if", 1)
        result = self.check(text)
        self.assertEqual(result.returncode, 1)
        self.assertIn("SYNTAX BROKEN", result.stdout)

    def test_runs_shellcheck_when_it_is_installed(self) -> None:
        fake = os.path.join(self.dir, "bin")
        os.mkdir(fake)
        with open(os.path.join(fake, "shellcheck"), "w",
                  encoding="utf-8") as stream:
            stream.write("#!/bin/sh\necho 'SC2086: quote this'\nexit 1\n")
        os.chmod(os.path.join(fake, "shellcheck"), 0o755)
        self.env = {"PATH": f"{fake}:/usr/bin:/bin"}
        result = self.check(self.template)
        self.assertEqual(result.returncode, 1)
        self.assertIn("SHELLCHECK PROBLEMS\nSC2086: quote this", result.stdout)

    def test_refuses_bad_arguments(self) -> None:
        for args in ([], ["/nonexistent.sh"]):
            with self.subTest(args=args):
                result = subprocess.run([SCRIPT, *args], text=True,
                                        capture_output=True, check=False)
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
