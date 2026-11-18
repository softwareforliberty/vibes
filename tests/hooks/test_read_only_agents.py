"""The read-only agents hook, driven with the JSON Claude Code sends it.

    python3 -I -m unittest discover -s tests/hooks -t tests/hooks
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks", "claude_read_only_agents")
RUN = "/work/project/.vibes/optimise-parse/"


def hook(agent: str, tool: str, **tool_input: str) -> int:
    event = {"agent_type": agent, "tool_name": tool, "tool_input": tool_input}
    return subprocess.run([HOOK], input=json.dumps(event), text=True,
                          capture_output=True, check=False).returncode


class ProfilerTest(unittest.TestCase):
    def test_writes_in_its_run_directory(self) -> None:
        for path in ("bench/harness.py", "profile/baseline.md",
                     "profile/candidate-2/report.md"):
            with self.subTest(path=path):
                self.assertEqual(
                    hook("vibes:profiler", "Write", file_path=RUN + path), 0)

    def test_never_writes_the_code(self) -> None:
        for path in ("/work/project/src/parse.py",
                     RUN + "wt/candidate/src/parse.py",
                     "/work/project/.vibes/parse/state.md",
                     RUN + "../../src/parse.py",
                     ".vibes/optimise-parse/bench/harness.py"):
            for tool in ("Write", "Edit"):
                with self.subTest(path=path, tool=tool):
                    self.assertEqual(
                        hook("profiler", tool, file_path=path), 2)

    def test_bash_is_left_to_the_main_agent_check(self) -> None:
        self.assertEqual(hook("profiler", "Bash", command="make bench"), 0)


class ReviewerTest(unittest.TestCase):
    def test_reviewers_still_write_only_their_findings(self) -> None:
        findings = "/p/.vibes/x/review/spike-1/bug-reviewer.md"
        self.assertEqual(hook("bug-reviewer", "Write", file_path=findings), 0)
        self.assertEqual(hook("bug-reviewer", "Write", file_path="/p/a.py"), 2)

    def test_the_project_docs_reviewer_never_edits_the_docs(self) -> None:
        own = "/p/.vibes/x/review/spec-1/project-docs-reviewer.md"
        self.assertEqual(
            hook("vibes:project-docs-reviewer", "Write", file_path=own), 0)
        for path in ("/p/docs/architecture.md", "/p/docs/specs/x/spec.md"):
            with self.subTest(path=path):
                self.assertEqual(hook("vibes:project-docs-reviewer", "Edit",
                                      file_path=path), 2)

    def test_the_spec_reviewer_runs_but_never_changes_git(self) -> None:
        self.assertEqual(hook("spec-reviewer", "Bash", command="make test"), 0)
        self.assertEqual(
            hook("spec-reviewer", "Bash", command="git commit -m x"), 2)

    def test_other_agents_are_free(self) -> None:
        self.assertEqual(hook("optimiser", "Write", file_path="/p/a.py"), 0)
        self.assertEqual(hook("", "Write", file_path="/p/a.py"), 0)


class SuggesterTest(unittest.TestCase):
    AGENT = "vibes:commit-message-suggester"

    def test_reads_the_staged_change(self) -> None:
        for command in ("git diff --cached --stat", "git log -5 --format=%s",
                        "printf '%s' 'Add CSV export' | wc -m"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 0)

    def test_never_commits_or_writes(self) -> None:
        for command in ("git commit -m x", "git add a.py", "git reset",
                        "echo x > msg.txt"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 2)
        self.assertEqual(hook(self.AGENT, "Write", file_path="/p/msg"), 2)


if __name__ == "__main__":
    unittest.main()
