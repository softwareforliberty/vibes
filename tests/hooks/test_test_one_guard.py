"""The test-one guard: the builder runs its tests with scripts/test-one.

    python3 -I -m unittest discover -s tests/hooks -t tests/hooks
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
HOOK = os.path.join(ROOT, "hooks", "claude_test_one_guard")


def guard(event: dict) -> subprocess.CompletedProcess:
    return subprocess.run([HOOK], input=json.dumps(event), text=True,
                          capture_output=True, check=False)


def bash(command: str, cwd: str, agent: str = "vibes:builder") -> dict:
    event = {"tool_name": "Bash", "cwd": cwd,
             "tool_input": {"command": command}}
    if agent:
        event["agent_type"] = agent
    return event


def project(test_one: bool = True) -> str:
    """A repository with scripts/check and, unless told not to, test-one."""
    root = os.path.realpath(tempfile.mkdtemp())
    subprocess.run(["git", "init", "-q", root], check=True)
    os.makedirs(os.path.join(root, "scripts"))
    names = ["check", "test-one"] if test_one else ["check"]
    for name in names:
        path = os.path.join(root, "scripts", name)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("#!/bin/sh\n")
        os.chmod(path, 0o755)
    os.makedirs(os.path.join(root, "src"))
    return root


class BuilderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = project()

    def tearDown(self) -> None:
        shutil.rmtree(self.root)

    def test_a_bare_gate_run_is_refused(self) -> None:
        for command in ("scripts/check", "./scripts/check",
                        f"{self.root}/scripts/check", "bash scripts/check",
                        "time scripts/check", "JOBS=2 scripts/check",
                        "scripts/check 2>&1 | tail -20",
                        "cd src && ../scripts/check",
                        "timeout 600 scripts/check",
                        "make build && scripts/check"):
            with self.subTest(command=command):
                result = guard(bash(command, self.root))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("scripts/test-one <test>", result.stderr)

    def test_every_name_of_the_builder_is_held(self) -> None:
        for agent in ("vibes:builder", "builder", "vibes-builder"):
            with self.subTest(agent=agent):
                result = guard(bash("scripts/check", self.root, agent))
                self.assertEqual(result.returncode, 2)

    def test_the_modes_and_the_other_scripts_stay_open(self) -> None:
        for command in ("scripts/check --all", "scripts/check --static",
                        "JOBS=2 scripts/check --all 2>&1 | tail",
                        "scripts/test-one tests/test_a.py",
                        "scripts/check-file src/a.py",
                        "scripts/check-requirements --all",
                        "git commit -m 'Add a thing'",
                        "grep -n check scripts/check",
                        "cat scripts/check", "echo 'scripts/check'"):
            with self.subTest(command=command):
                result = guard(bash(command, self.root))
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_gate_run_from_another_folder_is_held_by_its_project(
            self) -> None:
        elsewhere = tempfile.mkdtemp()
        try:
            result = guard(bash(f"cd {self.root} && scripts/check", elsewhere))
            self.assertEqual(result.returncode, 2)
        finally:
            shutil.rmtree(elsewhere)


class OthersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = project()

    def tearDown(self) -> None:
        shutil.rmtree(self.root)

    def test_the_main_agent_and_other_agents_may_run_the_gate(self) -> None:
        for agent in ("", "vibes:spiker", "vibes:diagnoser",
                      "vibes:profiler", "general-purpose"):
            with self.subTest(agent=agent):
                result = guard(bash("scripts/check", self.root, agent))
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_other_tools_are_left_alone(self) -> None:
        result = guard({"tool_name": "Write", "agent_type": "vibes:builder",
                        "tool_input": {"file_path": "scripts/check"}})
        self.assertEqual(result.returncode, 0)


class WithoutTestOneTest(unittest.TestCase):
    def test_a_project_without_test_one_lets_the_builder_run_the_gate(
            self) -> None:
        root = project(test_one=False)
        try:
            result = guard(bash("scripts/check", root))
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            shutil.rmtree(root)

    def test_a_folder_outside_any_repository_is_left_alone(self) -> None:
        folder = tempfile.mkdtemp()
        try:
            result = guard(bash("scripts/check", folder))
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            shutil.rmtree(folder)


if __name__ == "__main__":
    unittest.main()
