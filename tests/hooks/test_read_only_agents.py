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


class RetrospectiveTest(unittest.TestCase):
    AGENT = "vibes:retrospective"
    REPORT = "/p/.vibes/retro-2026-11-23-1/retro.md"

    def test_writes_its_report(self) -> None:
        self.assertEqual(hook(self.AGENT, "Write", file_path=self.REPORT), 0)
        self.assertEqual(
            hook(self.AGENT, "Bash", command=f"cat notes > {self.REPORT}"), 0)

    def test_never_writes_anything_else(self) -> None:
        for path in ("/p/scripts/check", "/p/CLAUDE.md",
                     "/p/.vibes/retro-1/digest.md",
                     "/p/.vibes/retro-1/x/retro.md",
                     "/p/.vibes/retro-1/../../scripts/check",
                     ".vibes/retro-1/retro.md"):
            for tool in ("Write", "Edit"):
                with self.subTest(path=path, tool=tool):
                    self.assertEqual(
                        hook(self.AGENT, tool, file_path=path), 2)

    def test_reads_but_never_changes_files_or_git(self) -> None:
        for command in ("/v/bin/session-digest --show m4 /t.jsonl",
                        "git log -5 --stat", "cat scripts/check"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 0)
        for command in ("sed -i 's/ruff//' scripts/check",
                        "echo x >> CODING_STANDARDS.md", "git commit -m x",
                        "rm scripts/check-file"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 2)


class SurveyTest(unittest.TestCase):
    RUN = "/p/.vibes/survey-orders/"

    def test_the_surveyor_writes_its_survey_and_comparison(self) -> None:
        for name in ("survey.md", "comparison.md"):
            with self.subTest(name=name):
                self.assertEqual(hook("vibes:surveyor", "Write",
                                      file_path=self.RUN + name), 0)

    def test_a_designer_writes_only_its_design(self) -> None:
        self.assertEqual(hook("vibes:interface-designer", "Write",
                              file_path=self.RUN + "designs/a.md"), 0)
        for path in (self.RUN + "survey.md", self.RUN + "designs/x/a.md",
                     "/p/src/orders.py"):
            with self.subTest(path=path):
                self.assertEqual(hook("vibes:interface-designer", "Write",
                                      file_path=path), 2)

    def test_the_surveyor_never_writes_the_code_or_designs(self) -> None:
        for path in ("/p/src/orders.py", "/p/GLOSSARY.md",
                     "/p/docs/adr/0002-x.md", self.RUN + "designs/a.md",
                     self.RUN + "../../src/orders.py", self.RUN + "x.md"):
            for tool in ("Write", "Edit"):
                with self.subTest(path=path, tool=tool):
                    self.assertEqual(hook("surveyor", tool,
                                          file_path=path), 2)

    def test_the_surveyor_reads_history_but_changes_nothing(self) -> None:
        self.assertEqual(hook("surveyor", "Bash",
                              command="git log --oneline -- src/a.py"), 0)
        self.assertEqual(hook("surveyor", "Bash",
                              command=f"cat x > {self.RUN}survey.md"), 0)
        for command in ("git checkout -b x", "echo x > src/a.py",
                        "rm src/a.py"):
            with self.subTest(command=command):
                self.assertEqual(hook("surveyor", "Bash", command=command), 2)


class ResearcherTest(unittest.TestCase):
    AGENT = "vibes:researcher"

    def test_writes_its_note(self) -> None:
        for run in ("order-export", "debug-month-end", "optimise-parse"):
            with self.subTest(run=run):
                self.assertEqual(hook(self.AGENT, "Write", file_path=(
                    f"/p/.vibes/{run}/research/pagination.md")), 0)

    def test_never_writes_anything_else(self) -> None:
        for path in ("/p/docs/specs/x/spec.md", "/p/src/api.py",
                     "/p/.vibes/x/research/deep/a.md",
                     "/p/.vibes/x/y/research/a.md",
                     "/p/.vibes/x/research/../../../src/api.py",
                     "/p/.vibes/x/research/a.txt"):
            for tool in ("Write", "Edit"):
                with self.subTest(path=path, tool=tool):
                    self.assertEqual(
                        hook(self.AGENT, tool, file_path=path), 2)

    def test_reads_versions_but_changes_nothing(self) -> None:
        for command in ("pip show requests", "git log -3 -- poetry.lock",
                        "cat package-lock.json"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 0)
        for command in ("rm -rf node_modules", "git checkout v2",
                        "echo x > src/api.py"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 2)


class PrWriterTest(unittest.TestCase):
    AGENT = "vibes:pr-writer"

    def test_writes_its_body_and_sources(self) -> None:
        for name in ("pr.md", "sources.md"):
            for tool in ("Write", "Edit"):
                with self.subTest(name=name, tool=tool):
                    self.assertEqual(hook(self.AGENT, tool, file_path=(
                        f"/p/.vibes/pr-vibe-sales-csv/{name}")), 0)

    def test_never_writes_anything_else(self) -> None:
        for path in ("/p/README.md", "/p/.github/pull_request_template.md",
                     "/p/.vibes/pr-x/diff.patch",
                     "/p/.vibes/pr-x/sub/pr.md",
                     "/p/.vibes/sales-csv/pr.md",
                     "/p/.vibes/pr-x/../../README.md",
                     ".vibes/pr-x/pr.md"):
            for tool in ("Write", "Edit"):
                with self.subTest(path=path, tool=tool):
                    self.assertEqual(
                        hook(self.AGENT, tool, file_path=path), 2)


class IssueReaderTest(unittest.TestCase):
    AGENT = "vibes:issue-reader"

    def test_writes_its_brief_and_triage(self) -> None:
        for name in ("brief.md", "triage.md"):
            for tool in ("Write", "Edit"):
                with self.subTest(name=name, tool=tool):
                    self.assertEqual(hook(self.AGENT, tool, file_path=(
                        f"/p/.vibes/issues/123/{name}")), 0)

    def test_never_writes_anything_else(self) -> None:
        for path in ("/p/.github/workflows/ci.yml", "/p/scripts/check",
                     "/p/.vibes/issues/123/issue.json",
                     "/p/.vibes/issues/approved.tsv",
                     "/p/.vibes/issues/abc/brief.md",
                     "/p/.vibes/issues/123/x/brief.md",
                     "/p/.vibes/issues/123/../../../CLAUDE.md",
                     ".vibes/issues/123/brief.md"):
            for tool in ("Write", "Edit"):
                with self.subTest(path=path, tool=tool):
                    self.assertEqual(
                        hook(self.AGENT, tool, file_path=path), 2)


class WizardWriterTest(unittest.TestCase):
    AGENT = "vibes:wizard-writer"
    WIZARD = "/p/.vibes/sales-csv/wizard.sh"

    def test_writes_its_runbook(self) -> None:
        self.assertEqual(hook(self.AGENT, "Write",
                              file_path="/p/.vibes/db-move/runbook.sh"), 0)
        self.assertEqual(hook(self.AGENT, "Write",
                              file_path="/p/scripts/runbook.sh"), 2)

    def test_writes_its_wizard(self) -> None:
        self.assertEqual(hook(self.AGENT, "Write", file_path=self.WIZARD), 0)
        self.assertEqual(hook(self.AGENT, "Bash", command=(
            f"sed 's/x/y/' t > {self.WIZARD}")), 0)

    def test_never_writes_anything_else(self) -> None:
        for path in ("/p/.env", "/p/scripts/setup", "/p/.vibes/x/plan.md",
                     "/p/.vibes/x/y/wizard.sh",
                     "/p/.vibes/x/../../.env", ".vibes/x/wizard.sh"):
            with self.subTest(path=path):
                self.assertEqual(hook(self.AGENT, "Write", file_path=path), 2)

    def test_checks_but_never_runs_or_changes(self) -> None:
        for command in ("bash -n /p/.vibes/x/wizard.sh",
                        "shellcheck /p/.vibes/x/wizard.sh",
                        "grep -n secrets. .github/workflows/ci.yml"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 0)
        for command in ("echo KEY=1 >> .env", "rm .env",
                        "git commit -m x", "chmod +x scripts/setup"):
            with self.subTest(command=command):
                self.assertEqual(hook(self.AGENT, "Bash", command=command), 2)


if __name__ == "__main__":
    unittest.main()
