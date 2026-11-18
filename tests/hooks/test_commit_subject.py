"""The 50-character commit subject check, in the Claude hook and git's.

    python3 -I -m unittest discover -s tests/hooks -t tests/hooks
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
HOOKS = os.path.join(ROOT, "hooks")
HELPER = os.path.join(HOOKS, "lib", "commit_subject.py")

SHORT = "Add CSV export for orders"
EXACT = "Refuse a quantity below one with a clear message xx"[:50]
LONG = "Refuse an order quantity below one with a clear error message"
GIT = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def long_subjects(command: str, directory: str = "/") -> list[str]:
    result = subprocess.run(["python3", "-I", "-S", HELPER, "--command",
                             directory], input=command, text=True,
                            capture_output=True, check=True)
    return [line.split("\t", 1)[1] for line in result.stdout.splitlines()]


def heredoc(message: str) -> str:
    return ('git commit -m "$(cat <<\'EOF\'\n' + message
            + "\nEOF\n)\"")


class HelperTest(unittest.TestCase):
    def test_reads_the_first_message(self) -> None:
        self.assertEqual(long_subjects(f'git commit -m "{SHORT}"'), [])
        self.assertEqual(long_subjects(f"git commit -m '{EXACT}'"), [])
        self.assertEqual(len(EXACT), 50)
        self.assertEqual(long_subjects(f'git commit -m "{LONG}"'), [LONG])
        self.assertEqual(
            long_subjects(f'git commit -m "{SHORT}" -m "{LONG} body"'), [])

    def test_reads_joined_and_long_options(self) -> None:
        for command in (f'git commit -m"{LONG}"',
                        f'git commit --message "{LONG}"',
                        f'git commit --message="{LONG}"',
                        f'git commit -qm "{LONG}"',
                        f'git -C repo commit -m "{LONG}"',
                        f'cd repo && git add a.py && git commit -m "{LONG}"'):
            with self.subTest(command=command):
                self.assertEqual(long_subjects(command), [LONG])

    def test_reads_a_heredoc(self) -> None:
        self.assertEqual(long_subjects(heredoc(f"{LONG}\n\nWhy.")), [LONG])
        self.assertEqual(long_subjects(heredoc(f"{SHORT}\n\n{LONG}")), [])
        self.assertEqual(long_subjects(
            f"git commit -F - <<'EOF'\n{LONG}\n\nWhy.\nEOF\n"), [LONG])

    def test_reads_a_message_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with open(os.path.join(directory, "msg"), "w",
                      encoding="utf-8") as handle:
                handle.write(f"{LONG}\n\nWhy.\n")
            self.assertEqual(
                long_subjects("git commit -F msg", directory), [LONG])
            self.assertEqual(
                long_subjects("git commit --file=missing", directory), [])

    def test_counts_characters_not_bytes(self) -> None:
        subject = "Ré" * 25
        self.assertEqual(long_subjects(f'git commit -m "{subject}"'), [])

    def test_passes_what_it_cannot_read_for_certain(self) -> None:
        for command in ('git commit -m "$MESSAGE"',
                        'git commit -m "$(git log -1 --format=%s)"',
                        "git commit --amend --no-edit",
                        "git commit -C HEAD",
                        "git commit",
                        'git commit -m "unterminated',
                        f'echo "git commit -m {LONG}"'):
            with self.subTest(command=command):
                self.assertEqual(long_subjects(command), [])


def run(args: list[str], cwd: str, **kwargs: object) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True,
                          env={**os.environ, **GIT}, check=False, **kwargs)


class HookTest(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.repo = os.path.realpath(temporary.name)
        run(["git", "init", "-q"], self.repo)
        os.mkdir(os.path.join(self.repo, "scripts"))
        check = os.path.join(self.repo, "scripts", "check")
        with open(check, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\n# Guides: languages/BASH\nexit 0\n")
        os.chmod(check, 0o755)
        run(["git", "add", "-A"], self.repo)
        run(["git", "commit", "-q", "--no-verify", "-m", "Base"], self.repo)

    def claude(self, command: str, cwd: str | None = None) -> int:
        event = {"tool_name": "Bash", "cwd": cwd or self.repo,
                 "tool_input": {"command": command}}
        return run([os.path.join(HOOKS, "claude_commit_gate")], self.repo,
                   input=json.dumps(event)).returncode

    def test_claude_hook_blocks_a_long_subject(self) -> None:
        self.assertEqual(self.claude(f'git commit -m "{LONG}"'), 2)
        self.assertEqual(self.claude(heredoc(f"{LONG}\n\nWhy.")), 2)

    def test_claude_hook_lets_a_short_subject_through(self) -> None:
        self.assertEqual(self.claude(f'git commit -m "{SHORT}"'), 0)
        self.assertEqual(self.claude(f'git commit -m "{EXACT}"'), 0)

    def test_claude_hook_leaves_ungated_repositories_alone(self) -> None:
        os.remove(os.path.join(self.repo, "scripts", "check"))
        run(["git", "rm", "-q", "--cached", "scripts/check"], self.repo)
        run(["git", "commit", "-q", "-m", "Ungate"], self.repo)
        self.assertEqual(self.claude(f'git commit -m "{LONG}"'), 0)

    def test_git_hook_checks_the_message_file(self) -> None:
        hook = os.path.join(HOOKS, "git_commit_msg")
        message = os.path.join(self.repo, ".git", "COMMIT_EDITMSG")
        for text, code in ((f"{LONG}\n", 1), (f"# comment\n{SHORT}\n", 0)):
            with self.subTest(text=text):
                with open(message, "w", encoding="utf-8") as handle:
                    handle.write(text)
                self.assertEqual(run([hook, message], self.repo).returncode,
                                 code)


if __name__ == "__main__":
    unittest.main()
