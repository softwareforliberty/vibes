"""The wizard library in skills/wizard/templates/wizard.sh, driven through
standard input, under macOS's Bash 3.2 and the Bash on the PATH.

    python3 -I -m unittest discover -s tests/wizard -t tests/wizard
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TEMPLATE = os.path.join(ROOT, "skills", "wizard", "templates", "wizard.sh")
MARKER = "# ── STAGES"

with open(TEMPLATE, encoding="utf-8") as _stream:
    LIBRARY = _stream.read().split(MARKER)[0]

BASHES = []
for _bash in ("/bin/bash", shutil.which("bash")):
    if _bash and os.path.exists(_bash) and \
            os.path.realpath(_bash) not in map(os.path.realpath, BASHES):
        BASHES.append(_bash)

# A gh that logs what it's asked, and what it was given on standard input.
FAKE_GH = """#!/bin/sh
[ "$1" = auth ] && exit 0
printf '%s|' "$@" >> "$GH_LOG"
printf ' stdin=' >> "$GH_LOG"
cat >> "$GH_LOG"
printf '\\n' >> "$GH_LOG"
"""


class WizardLibraryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        self.env_file = os.path.join(self.dir, ".env")
        self.bin = os.path.join(self.dir, "bin")
        os.mkdir(self.bin)

    def run_wizard(self, body: str, stdin: str = "", bash: str = "",
                   gh: bool = False) -> subprocess.CompletedProcess:
        script = os.path.join(self.dir, "w.sh")
        with open(script, "w", encoding="utf-8") as stream:
            stream.write(LIBRARY + "\nWIZARD_TITLE=Test\nWIZARD_STAGES=1\n"
                         + body + "\n")
        path = os.environ.get("PATH", "")
        if gh:
            fake = os.path.join(self.bin, "gh")
            with open(fake, "w", encoding="utf-8") as stream:
                stream.write(FAKE_GH)
            os.chmod(fake, 0o755)
            path = f"{self.bin}:{path}"
        else:
            path = ":".join(p for p in path.split(":")
                            if not os.path.exists(os.path.join(p, "gh")))
        env = {"PATH": path, "HOME": self.dir, "WIZARD_NO_BROWSER": "1",
               "WIZARD_ENV_FILE": self.env_file,
               "GH_LOG": os.path.join(self.dir, "gh.log")}
        return subprocess.run([bash or BASHES[0], script], input=stdin,
                              text=True, capture_output=True, cwd=self.dir,
                              env=env, check=False)

    def each_bash(self):
        for bash in BASHES:
            with self.subTest(bash=bash):
                if os.path.exists(self.env_file):
                    os.remove(self.env_file)
                yield bash

    def env(self) -> str:
        with open(self.env_file, encoding="utf-8") as stream:
            return stream.read()

    def test_saves_a_value_and_reads_it_back(self) -> None:
        for bash in self.each_bash():
            result = self.run_wizard(
                'wizard::ask NAME "Name:"; wizard::write_env NAME "$NAME";'
                ' wizard::saved NAME', "Corner Books\n", bash)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.env(), "NAME='Corner Books'\n")
            self.assertTrue(result.stdout.endswith("Corner Books"))

    def test_quotes_survive_a_round_trip(self) -> None:
        for bash in self.each_bash():
            for value in ("it's", "a\"b", "$HOME `x` \\n", "a=b c"):
                with self.subTest(value=value):
                    result = self.run_wizard(
                        'wizard::write_env V "$1"; printf "%s" "$(wizard::saved V)"'
                        .replace('"$1"', "'" + value.replace("'", "'\\''")
                                 + "'"), bash=bash)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertTrue(result.stdout.endswith(value),
                                    result.stdout)

    def test_replaces_rather_than_repeats_a_key(self) -> None:
        for bash in self.each_bash():
            with open(self.env_file, "w", encoding="utf-8") as stream:
                stream.write("OTHER=1\nKEY='old'\n")
            result = self.run_wizard('wizard::write_env KEY new; '
                                     'wizard::write_env KEY newer', bash=bash)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.env(), "OTHER=1\nKEY='newer'\n")

    def test_a_new_env_file_is_yours_alone(self) -> None:
        for bash in self.each_bash():
            self.run_wizard("wizard::write_env KEY v", bash=bash)
            mode = stat.S_IMODE(os.stat(self.env_file).st_mode)
            self.assertEqual(mode, 0o600)

    def test_keeps_an_existing_files_permissions(self) -> None:
        for bash in self.each_bash():
            with open(self.env_file, "w", encoding="utf-8") as stream:
                stream.write("A=1\n")
            os.chmod(self.env_file, 0o640)
            self.run_wizard("wizard::write_env KEY v", bash=bash)
            self.assertEqual(stat.S_IMODE(os.stat(self.env_file).st_mode),
                             0o640)

    def test_enter_keeps_the_saved_value(self) -> None:
        for bash in self.each_bash():
            with open(self.env_file, "w", encoding="utf-8") as stream:
                stream.write("TOKEN='s3cret'\nNAME=shop\n")
            result = self.run_wizard(
                'wizard::ask_secret TOKEN "Token:"; wizard::ask NAME "Name:";'
                ' printf "<%s|%s>" "$TOKEN" "$NAME"', "\n\n", bash)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(result.stdout.endswith("<s3cret|shop>"))
            self.assertIn("[Enter keeps the saved one]", result.stdout)
            self.assertNotIn("s3cret", result.stdout.replace("<s3cret|", ""))
            self.assertIn("[shop]", result.stdout)

    def test_asks_again_while_empty_and_fails_at_the_end(self) -> None:
        for bash in self.each_bash():
            result = self.run_wizard('wizard::ask NAME "Name:"; echo "<$NAME>"',
                                     "\n\nfinally\n", bash)
            self.assertTrue(result.stdout.endswith("<finally>\n"))
            self.assertEqual(result.stdout.count("can't be empty"), 2)
            result = self.run_wizard('wizard::ask NAME "Name:"', "", bash)
            self.assertNotEqual(result.returncode, 0)

    def test_refuses_a_bad_name_or_a_line_break(self) -> None:
        for bash in self.each_bash():
            result = self.run_wizard("wizard::write_env 'A B' v", bash=bash)
            self.assertEqual(result.returncode, 2)
            result = self.run_wizard(
                "wizard::write_env A $'one\\ntwo' || echo refused", bash=bash)
            self.assertIn("refused", result.stdout)
            self.assertFalse(os.path.exists(self.env_file)
                             and "A=" in self.env())

    def test_confirm_is_no_unless_yes(self) -> None:
        for bash in self.each_bash():
            for answer, expected in (("y\n", "yes"), ("Yes\n", "yes"),
                                     ("\n", "no"), ("n\n", "no"), ("", "no")):
                with self.subTest(answer=answer):
                    result = self.run_wizard(
                        'if wizard::confirm "Delete it?"; then echo yes; '
                        'else echo no; fi', answer, bash)
                    self.assertTrue(result.stdout.endswith(expected + "\n"))

    def test_sets_a_secret_through_standard_input(self) -> None:
        for bash in self.each_bash():
            result = self.run_wizard(
                "wizard::set_secret API_KEY 'sk_test_1'; "
                "wizard::set_var REGION eu; wizard::finish", bash=bash, gh=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            with open(os.path.join(self.dir, "gh.log"), encoding="utf-8") as s:
                log = s.read()
            os.remove(os.path.join(self.dir, "gh.log"))
            self.assertIn("secret|set|API_KEY| stdin=sk_test_1", log)
            self.assertNotIn("sk_test_1|", log)
            self.assertIn("variable|set|REGION|--body|eu|", log)
            self.assertIn("✓ Done", result.stdout)

    def test_without_gh_it_says_what_is_left(self) -> None:
        for bash in self.each_bash():
            result = self.run_wizard(
                "wizard::set_secret API_KEY x; wizard::finish", bash=bash)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Done, with steps left", result.stdout)
            self.assertIn("gh secret set API_KEY", result.stdout)

    def test_finish_with_nothing_done(self) -> None:
        for bash in self.each_bash():
            result = self.run_wizard("wizard::finish", bash=bash)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("✓ Done", result.stdout)

    def test_stages_count_up(self) -> None:
        for bash in self.each_bash():
            result = self.run_wizard(
                'WIZARD_STAGES=2; wizard::stage One; wizard::stage Two',
                bash=bash)
            self.assertIn("Stage 1 of 2: One", result.stdout)
            self.assertIn("Stage 2 of 2: Two", result.stdout)

    def test_the_template_runs_from_start_to_end(self) -> None:
        for bash in self.each_bash():
            with open(TEMPLATE, encoding="utf-8") as stream:
                script = stream.read()
            path = os.path.join(self.dir, "full.sh")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write(script)
            result = subprocess.run(
                [bash, path], input="\nsk_live_x\n", text=True,
                capture_output=True, cwd=self.dir, check=False,
                env={"PATH": os.environ["PATH"], "WIZARD_NO_BROWSER": "1",
                     "WIZARD_ENV_FILE": self.env_file, "HOME": self.dir})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(self.env(), "EXAMPLE_KEY='sk_live_x'\n")
            self.assertNotIn("sk_live_x", result.stdout)


if __name__ == "__main__":
    unittest.main()
