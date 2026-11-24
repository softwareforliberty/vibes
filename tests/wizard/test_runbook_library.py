"""The runbook library in skills/runbook/templates/runbook.sh, driven in a
pseudo-terminal as a person would, under macOS's Bash 3.2 and the Bash on
the PATH.

    python3 -I -m unittest discover -s tests/wizard -t tests/wizard
"""

from __future__ import annotations

import os
import pty
import select
import shutil
import subprocess
import tempfile
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TEMPLATE = os.path.join(ROOT, "skills", "runbook", "templates", "runbook.sh")
WIZARD = os.path.join(ROOT, "skills", "wizard", "templates", "wizard.sh")

with open(TEMPLATE, encoding="utf-8") as _stream:
    LIBRARY = _stream.read().split("# ── STEPS")[0]

BASHES = []
for _bash in ("/bin/bash", shutil.which("bash")):
    if _bash and os.path.exists(_bash) and \
            os.path.realpath(_bash) not in map(os.path.realpath, BASHES):
        BASHES.append(_bash)

# Three steps: a check every time, a one-way change, and a step after it.
# Each records that it ran in counts/, and the last fails while fail exists.
STEPS = """
readonly RUNBOOK_TITLE="Move the database"
step_ready() {
  echo x >> counts/ready
  runbook::check "the backup exists" test -f backup
}
step_migrate() {
  echo x >> counts/migrate
  runbook::run "Migrate" touch migrated
  runbook::verify "the data moved" test -f migrated
}
step_switch() {
  echo x >> counts/switch
  runbook::verify "the switch worked" test ! -f fail
}
steps() {
  runbook::always ready "Check the backup" step_ready
  runbook::one_way migrate "Migrate the data" "the old tables are dropped" \\
    "restore from the backup" step_migrate
  runbook::do switch "Switch the app over" step_switch
}
main() {
  runbook::begin "$@"
  steps
  runbook::finish
}
main "$@"
"""


class RunbookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir)
        os.mkdir(os.path.join(self.dir, "counts"))
        self.write("backup", "")
        self.script = self.write("runbook.sh", LIBRARY + STEPS)

    def write(self, name: str, text: str) -> str:
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
        return path

    def count(self, step: str) -> int:
        path = os.path.join(self.dir, "counts", step)
        if not os.path.exists(path):
            return 0
        with open(path, encoding="utf-8") as stream:
            return len(stream.read().split())

    def log(self) -> list[list[str]]:
        path = os.path.join(self.dir, "runbook.log")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as stream:
            return [line.rstrip("\n").split("\t")[1:3] for line in stream]

    def drive(self, bash: str, answers: dict[str, str],
              *args: str) -> tuple[int, str]:
        """Runs the runbook in a pseudo-terminal, answering each prompt
        whose text it shows: Enter for a pause, the reply given for the
        rest."""
        pid, fd = pty.fork()
        if pid == 0:
            os.chdir(self.dir)
            os.environ["TERM"] = "dumb"
            os.execv(bash, [bash, self.script, *args])
        output = ""
        answered = 0
        deadline = time.time() + 30
        while time.time() < deadline:
            ready, _, _ = select.select([fd], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(fd, 4096).decode(errors="replace")
                except OSError:
                    break
                if not chunk:
                    break
                output += chunk
            pending = output[answered:]
            for prompt, reply in [("Press Enter", ""), *answers.items()]:
                if prompt in pending:
                    os.write(fd, reply.encode() + b"\n")
                    answered = output.index(prompt, answered) + len(prompt)
                    break
        _, status = os.waitpid(pid, 0)
        return os.waitstatus_to_exitcode(status), output

    def each_bash(self):
        for bash in BASHES:
            with self.subTest(bash=bash):
                self.setUp()
                yield bash

    def test_does_every_step_once_confirmed(self) -> None:
        for bash in self.each_bash():
            status, output = self.drive(bash, {"Type migrate": "migrate"})
            self.assertEqual(status, 0, output)
            self.assertEqual([self.count(s) for s in
                              ("ready", "migrate", "switch")], [1, 1, 1])
            self.assertIn(["confirmed", "migrate"], self.log())
            self.assertIn(["done", "switch"], self.log())

    def test_anything_but_the_name_stops_before_the_step(self) -> None:
        for bash in self.each_bash():
            status, output = self.drive(bash, {"Type migrate": "y"})
            self.assertEqual(status, 3, output)
            self.assertIn("nothing in it has run", output)
            self.assertEqual(self.count("migrate"), 0)
            self.assertIn(["refused", "migrate"], self.log())

    def test_a_failed_check_stops_before_any_change(self) -> None:
        for bash in self.each_bash():
            os.remove(os.path.join(self.dir, "backup"))
            status, output = self.drive(bash, {"Type migrate": "migrate"})
            self.assertEqual(status, 1, output)
            self.assertIn("Not ready: the backup exists", output)
            self.assertEqual(self.count("migrate"), 0)

    def test_resumes_without_repeating_a_finished_step(self) -> None:
        for bash in self.each_bash():
            self.write("fail", "")
            status, output = self.drive(bash, {"Type migrate": "migrate"})
            self.assertEqual(status, 1, output)
            self.assertIn("It didn't work: the switch worked", output)
            self.assertIn(["stopped", "switch"], self.log())
            os.remove(os.path.join(self.dir, "fail"))
            status, output = self.drive(bash, {"Type migrate": "migrate"})
            self.assertEqual(status, 0, output)
            self.assertNotIn("Type migrate", output)
            self.assertEqual([self.count(s) for s in
                              ("ready", "migrate", "switch")], [2, 1, 2])

    def test_a_failing_command_stops_it_with_the_recovery(self) -> None:
        for bash in self.each_bash():
            with open(self.script, encoding="utf-8") as stream:
                text = stream.read()
            self.write("runbook.sh", text.replace(
                'runbook::verify "the data moved" test -f migrated',
                "false\n  touch after-false"))
            status, output = self.drive(bash, {"Type migrate": "migrate"})
            self.assertNotEqual(status, 0, output)
            self.assertIn("To recover: restore from the backup", output)
            self.assertFalse(os.path.exists(
                os.path.join(self.dir, "after-false")))
            self.assertIn(["stopped", "migrate"], self.log())

    def test_plan_shows_the_steps_and_runs_none(self) -> None:
        for bash in self.each_bash():
            result = subprocess.run([bash, self.script, "--plan"],
                                    cwd=self.dir, text=True,
                                    capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("2. Migrate the data (one-way)", result.stdout)
            self.assertIn("To recover: restore from the backup",
                          result.stdout)
            self.assertEqual(self.count("ready"), 0)

    def test_needs_a_person_at_a_terminal(self) -> None:
        for bash in self.each_bash():
            result = subprocess.run([bash, self.script], cwd=self.dir,
                                    input="migrate\n", text=True,
                                    capture_output=True, check=False)
            self.assertEqual(result.returncode, 2)
            self.assertIn("needs a person at a terminal", result.stdout)
            self.assertEqual(self.count("ready"), 0)

    def test_a_broken_runbook_runs_nothing(self) -> None:
        for bash in self.each_bash():
            with open(self.script, encoding="utf-8") as stream:
                text = stream.read()
            self.write("runbook.sh", text.replace(
                '"restore from the backup" step_migrate', '"" step_migrate')
                .replace('runbook::do switch', 'runbook::do ready'))
            status, output = self.drive(bash, {"Type migrate": "migrate"})
            self.assertEqual(status, 2, output)
            self.assertIn("must say what it changes and how to recover",
                          output)
            self.assertIn("ready is used twice", output)
            self.assertEqual(self.count("ready"), 0)

    def test_keeps_the_wizard_library_unchanged(self) -> None:
        with open(WIZARD, encoding="utf-8") as stream:
            wizard = stream.read()
        start = "# ── The vibes wizard library"
        wizard_library = wizard[wizard.index(start):
                                wizard.index("# ── STAGES")]
        runbook_library = LIBRARY[LIBRARY.index(start):
                                  LIBRARY.index("# ── The vibes runbook")]
        self.assertEqual(runbook_library, wizard_library)


if __name__ == "__main__":
    unittest.main()
