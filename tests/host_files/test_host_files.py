"""bin/host-files, writing Codex's agents and a Gemini CLI extension.

    python3 -I -m unittest discover -s tests/host_files -t tests/host_files
"""

from __future__ import annotations

import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
SCRIPT = os.path.join(ROOT, "bin", "host-files")
AGENTS = sorted(os.path.basename(path)[:-3]
                for path in glob.glob(os.path.join(ROOT, "agents", "*.md")))
# Gemini CLI's built-in tools, as its agents' tools lists name them.
GEMINI_TOOLS = {"read_file", "read_many_files", "list_directory",
                "grep_search", "glob", "write_file", "replace",
                "run_shell_command", "web_fetch", "google_web_search"}
# The frontmatter keys Gemini CLI accepts in an agent; it rejects others.
GEMINI_AGENT_KEYS = {"name", "description", "kind", "display_name", "tools",
                     "mcp_servers", "model", "temperature", "max_turns",
                     "timeout_mins"}


def host_files(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([SCRIPT, *args], text=True, capture_output=True,
                          check=False)


def user_only_skills() -> list[str]:
    names = []
    for path in glob.glob(os.path.join(ROOT, "skills", "*", "SKILL.md")):
        with open(path, encoding="utf-8") as stream:
            if "\ndisable-model-invocation: true\n" in stream.read():
                names.append(os.path.basename(os.path.dirname(path)))
    return sorted(names)


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self.dir)

    def path(self, *parts: str) -> str:
        return os.path.join(self.dir, *parts)

    def read(self, *parts: str) -> str:
        with open(self.path(*parts), encoding="utf-8") as stream:
            return stream.read()


class CodexTest(Case):
    def test_writes_every_agent_as_codex_names_it(self) -> None:
        result = host_files("codex", self.dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(sorted(os.listdir(self.dir)),
                         [f"vibes-{agent}.toml" for agent in AGENTS])

    @unittest.skipIf(sys.version_info < (3, 11), "tomllib is 3.11 or later")
    def test_each_is_valid_toml_holding_the_whole_definition(self) -> None:
        import tomllib

        host_files("codex", self.dir)
        for agent in AGENTS:
            with self.subTest(agent=agent):
                data = tomllib.loads(self.read(f"vibes-{agent}.toml"))
                self.assertEqual(set(data), {"name", "description",
                                             "developer_instructions"})
                self.assertEqual(data["name"], f"vibes:{agent}")
                with open(os.path.join(ROOT, "agents", f"{agent}.md"),
                          encoding="utf-8") as stream:
                    body = stream.read().split("\n---\n", 1)[1].lstrip("\n")
                self.assertEqual(data["developer_instructions"].rstrip("\n"),
                                 body.rstrip("\n"))

    def test_removes_its_own_stale_agents_only(self) -> None:
        host_files("codex", self.dir)
        os.rename(self.path("vibes-builder.toml"), self.path("vibes-old.toml"))
        with open(self.path("vibes-mine.toml"), "w", encoding="utf-8") as f:
            f.write('name = "mine"\n')
        result = host_files("codex", self.dir)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(os.path.exists(self.path("vibes-old.toml")))
        self.assertTrue(os.path.exists(self.path("vibes-mine.toml")))

    def test_never_overwrites_a_file_it_didnt_write(self) -> None:
        with open(self.path("vibes-builder.toml"), "w",
                  encoding="utf-8") as stream:
            stream.write('name = "builder"\n')
        result = host_files("codex", self.dir)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.read("vibes-builder.toml"), 'name = "builder"\n')


class GeminiTest(Case):
    def setUp(self) -> None:
        super().setUp()
        self.ext = self.path("ext")
        result = host_files("gemini", self.ext)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_manifest_matches_the_plugin(self) -> None:
        manifest = json.loads(self.read("ext", "gemini-extension.json"))
        with open(os.path.join(ROOT, ".claude-plugin", "plugin.json"),
                  encoding="utf-8") as stream:
            plugin = json.load(stream)
        self.assertEqual(manifest["name"], "vibes")
        self.assertEqual(manifest["version"], plugin["version"])

    def test_user_only_skills_are_commands(self) -> None:
        commands = sorted(name[:-5] for name in
                          os.listdir(self.path("ext", "commands", "vibes")))
        self.assertEqual(commands, user_only_skills())
        prompt = self.read("ext", "commands", "vibes", "vibe.toml")
        self.assertIn("{{args}}", prompt)
        self.assertIn(os.path.join(ROOT, "skills", "vibe", "SKILL.md"),
                      prompt)

    def test_skills_the_model_starts_are_skills(self) -> None:
        skills = sorted(os.listdir(self.path("ext", "skills")))
        self.assertEqual(skills, ["atomic-commits", "commit-gate",
                                  "test-driven-development"])

    def test_agents_use_gemini_clis_names_and_keys(self) -> None:
        names = sorted(os.listdir(self.path("ext", "agents")))
        self.assertEqual(names, [f"vibes-{agent}.md" for agent in AGENTS])
        for name in names:
            with self.subTest(agent=name):
                text = self.read("ext", "agents", name)
                front = text.split("\n---\n", 1)[0]
                keys = set(re.findall(r"^([a-z_]+):", front, re.MULTILINE))
                self.assertLessEqual(keys, GEMINI_AGENT_KEYS)
                self.assertRegex(front, r"\nname: vibes-[a-z0-9_-]+\n")
                tools = set(re.findall(r"^  - (\S+)$", front, re.MULTILINE))
                self.assertLessEqual(tools, GEMINI_TOOLS)

    def test_reviewers_get_no_shell(self) -> None:
        front = self.read("ext", "agents", "vibes-bug-reviewer.md")
        self.assertIn("  - write_file\n", front)
        self.assertNotIn("run_shell_command", front)

    def test_no_path_is_left_to_the_plugin_root_variable(self) -> None:
        for path in glob.glob(self.path("ext", "**", "*"), recursive=True):
            if os.path.isfile(path):
                with self.subTest(path=path), open(path,
                                                   encoding="utf-8") as f:
                    self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", f.read())

    def test_the_hooks_run_vibes_hooks(self) -> None:
        hooks = json.loads(self.read("ext", "hooks", "hooks.json"))["hooks"]
        self.assertEqual(set(hooks), {"BeforeTool", "AfterTool"})
        for event in hooks.values():
            for group in event:
                re.compile(group["matcher"])
                for hook in group["hooks"]:
                    path = hook["command"].strip("'")
                    self.assertTrue(os.access(path, os.X_OK), path)

    def test_writes_again_over_its_own_extension(self) -> None:
        with open(self.path("ext", "stale.txt"), "w", encoding="utf-8") as f:
            f.write("old\n")
        result = host_files("gemini", self.ext)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(os.path.exists(self.path("ext", "stale.txt")))

    def test_never_clears_a_directory_it_didnt_write(self) -> None:
        other = self.path("other")
        os.makedirs(other)
        with open(os.path.join(other, "keep.txt"), "w",
                  encoding="utf-8") as stream:
            stream.write("mine\n")
        self.assertEqual(host_files("gemini", other).returncode, 2)
        self.assertTrue(os.path.exists(os.path.join(other, "keep.txt")))


if __name__ == "__main__":
    unittest.main()
