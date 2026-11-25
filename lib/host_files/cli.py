"""host-files' command.

    host-files codex <agents directory>
    host-files gemini <extension directory>

Writes what another coding agent needs to run vibes, from this checkout's
skills/ and agents/. Claude Code and Copilot CLI read the plugin as it is,
and Codex reads its skills and hooks, but not its agents, and Gemini CLI
reads extensions of its own format.

codex writes each agent as Codex's custom agent, vibes-<agent>.toml, into
the directory given, usually ~/.codex/agents or a project's .codex/agents.
Each is named vibes:<agent>, as the skills name it. Files it wrote before
for agents that no longer exist are removed; any other file is left alone.

gemini writes a Gemini CLI extension into the directory given, which must
be empty or one it wrote before:

    gemini-extension.json
    commands/vibes/<skill>.toml   a skill only the user starts, as /vibes:<skill>
    skills/<skill>/               a skill the model may start itself
    agents/vibes-<agent>.md       each agent, with Gemini CLI's tool names
    hooks/hooks.json              the vibes hooks, before and after each tool

The extension points at this checkout for the rest, so keep the checkout
where it is, and run host-files again after updating it. Prints what it
wrote. Exits 0, and 2 on an error.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
ROOT_VARIABLE = "${CLAUDE_PLUGIN_ROOT}"
# The first line of each file host-files writes, so it knows its own.
MARKER = "Written by vibes' bin/host-files"
GEMINI_MARKER_FILE = ".vibes-host-files"
# Claude Code's tool names, and Gemini CLI's for the same work.
GEMINI_TOOLS = {
    "Read": ["read_file", "read_many_files", "list_directory"],
    "Grep": ["grep_search"],
    "Glob": ["glob"],
    "Write": ["write_file"],
    "Edit": ["replace"],
    "MultiEdit": ["replace"],
    "Bash": ["run_shell_command"],
    "WebFetch": ["web_fetch"],
    "WebSearch": ["google_web_search"],
}


class Definition:
    """A skill's SKILL.md or an agent's definition: its frontmatter and
    body."""

    def __init__(self, path: Path) -> None:
        self.path = path
        text = path.read_text(encoding="utf-8")
        match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
        if not match:
            raise ValueError(f"{path}: no frontmatter")
        self.fields = frontmatter(match.group(1))
        self.body = text[match.end():].lstrip("\n")
        if "name" not in self.fields or "description" not in self.fields:
            raise ValueError(f"{path}: no name or description")

    @property
    def name(self) -> str:
        return self.fields["name"]

    @property
    def description(self) -> str:
        return self.fields["description"]

    @property
    def tools(self) -> list[str] | None:
        """The Claude Code tools it's given, or None for all of them."""
        value = self.fields.get("tools")
        if value is None:
            return None
        return [tool.strip() for tool in value.split(",") if tool.strip()]

    @property
    def user_only(self) -> bool:
        return self.fields.get("disable-model-invocation") == "true"


def frontmatter(text: str) -> dict[str, str]:
    """Reads the YAML the definitions use: `key: value`, a quoted value,
    or a folded block, `key: >-`, of indented lines."""
    fields: dict[str, str] = {}
    key = ""
    folded: list[str] | None = None
    for line in text.splitlines():
        if folded is not None and (line.startswith(" ") or not line):
            folded.append(line.strip())
            continue
        if folded is not None:
            fields[key] = " ".join(part for part in folded if part)
            folded = None
        match = re.match(r"([A-Za-z][\w-]*):\s*(.*)$", line)
        if not match:
            raise ValueError(f"unreadable frontmatter line: {line!r}")
        key, value = match.group(1), match.group(2).strip()
        if value in (">", ">-", "|", "|-"):
            folded = []
        elif len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            fields[key] = value[1:-1]
        else:
            fields[key] = value
    if folded is not None:
        fields[key] = " ".join(part for part in folded if part)
    return fields


def agents() -> list[Definition]:
    return [Definition(path) for path in sorted((ROOT / "agents").glob("*.md"))]


def skills() -> list[Definition]:
    return [Definition(path)
            for path in sorted((ROOT / "skills").glob("*/SKILL.md"))]


def toml_string(text: str) -> str:
    """A TOML basic string, on one line."""
    return json.dumps(text)


def toml_block(text: str) -> str:
    """A TOML multi-line basic string, kept readable."""
    text = text.replace("\\", "\\\\").replace('"""', '""\\"')
    if text.endswith('"'):
        text += "\n"
    return '"""\n' + text + '"""'


def write_codex(directory: Path) -> list[str]:
    directory.mkdir(parents=True, exist_ok=True)
    written = {f"vibes-{agent.name}.toml": agent for agent in agents()}
    for name in written:
        path = directory / name
        if path.exists() and not ours(path):
            raise ValueError(f"{path} exists and isn't one host-files wrote")
    lines = []
    for name, agent in written.items():
        (directory / name).write_text(
            f"# {MARKER} from agents/{agent.name}.md.\n"
            "# Run it again after updating vibes; changes here are lost.\n"
            f"name = {toml_string('vibes:' + agent.name)}\n"
            f"description = {toml_string(agent.description)}\n"
            f"developer_instructions = {toml_block(agent.body)}\n",
            encoding="utf-8")
        lines.append(f"WROTE {directory / name}")
    for path in sorted(directory.glob("vibes-*.toml")):
        if path.name not in written and ours(path):
            path.unlink()
            lines.append(f"REMOVED {path}")
    return lines


def ours(path: Path) -> bool:
    try:
        with path.open(encoding="utf-8") as stream:
            return MARKER in stream.readline()
    except (OSError, UnicodeDecodeError):
        return False


def with_root(text: str) -> str:
    return text.replace(ROOT_VARIABLE, str(ROOT))


def gemini_command(skill: Definition) -> str:
    prompt = (
        f"Run vibes' `{skill.name}` skill: read "
        f"{ROOT}/skills/{skill.name}/SKILL.md and follow it.\n\n"
        f"vibes' own folder is {ROOT}. Where the skill's paths begin with "
        "the CLAUDE_PLUGIN_ROOT variable, use that folder in its place, and "
        "give it to each vibes agent you start, on a `Vibes root:` line at "
        "the start of its brief. vibes' agents are named `vibes-<agent>` "
        "here: start one with the invoke_agent tool.\n\n"
        "The skill's arguments, which it calls $ARGUMENTS: {{args}}\n")
    return (f"# {MARKER} from skills/{skill.name}/SKILL.md.\n"
            f"description = {toml_string(skill.description)}\n"
            f"prompt = {toml_block(prompt)}\n")


def gemini_agent(agent: Definition) -> str:
    lines = ["---", f"name: vibes-{agent.name}",
             f"description: {json.dumps(agent.description)}"]
    if agent.tools is not None:
        tools: list[str] = []
        for tool in agent.tools:
            if tool not in GEMINI_TOOLS:
                raise ValueError(
                    f"agents/{agent.name}.md: no Gemini CLI tool for {tool}")
            tools += [t for t in GEMINI_TOOLS[tool] if t not in tools]
        lines.append("tools:")
        lines += [f"  - {tool}" for tool in tools]
    lines += ["---", "", f"<!-- {MARKER} from agents/{agent.name}.md. -->",
              "", with_root(agent.body)]
    return "\n".join(lines)


def gemini_hooks() -> str:
    def hook(name: str) -> dict[str, str]:
        return {"type": "command", "name": f"vibes {name}",
                "command": shlex.quote(str(ROOT / "hooks" / name))}

    shell = "^run_shell_command$"
    writes = "^(write_file|replace)$"
    return json.dumps({"hooks": {
        "BeforeTool": [
            {"matcher": shell,
             "hooks": [hook("claude_commit_gate"),
                       hook("claude_read_only_agents"),
                       hook("claude_tracker_guard"),
                       hook("claude_test_one_guard"),
                       hook("claude_check_file")]},
            {"matcher": writes,
             "hooks": [hook("claude_guide_check"),
                       hook("claude_read_only_agents"),
                       hook("claude_tracker_guard")]},
        ],
        "AfterTool": [
            {"matcher": "^(write_file|replace|run_shell_command)$",
             "hooks": [hook("claude_check_file")]},
        ],
    }}, indent=2) + "\n"


def write_gemini(directory: Path) -> list[str]:
    if directory.exists():
        entries = list(directory.iterdir())
        if entries and not (directory / GEMINI_MARKER_FILE).exists():
            raise ValueError(
                f"{directory} isn't empty and isn't an extension host-files "
                "wrote")
        for entry in entries:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    directory.mkdir(parents=True, exist_ok=True)
    plugin = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    files: dict[str, str] = {
        GEMINI_MARKER_FILE: f"{MARKER} from {ROOT}.\n",
        "gemini-extension.json": json.dumps(
            {"name": "vibes", "version": plugin["version"],
             "description": plugin["description"]}, indent=2) + "\n",
        "hooks/hooks.json": gemini_hooks(),
    }
    for skill in skills():
        if skill.user_only:
            files[f"commands/vibes/{skill.name}.toml"] = gemini_command(skill)
            continue
        source = skill.path.parent
        for path in sorted(source.rglob("*")):
            if path.is_file():
                relative = path.relative_to(source)
                files[f"skills/{skill.name}/{relative}"] = with_root(
                    path.read_text(encoding="utf-8"))
    for agent in agents():
        files[f"agents/vibes-{agent.name}.md"] = gemini_agent(agent)
    for name, text in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    counts = {kind: sum(1 for name in files if name.startswith(kind + "/"))
              for kind in ("commands", "agents")}
    skill_count = len({name.split("/")[1] for name in files
                       if name.startswith("skills/")})
    return [f"WROTE {directory}: {counts['commands']} commands, "
            f"{skill_count} skills, {counts['agents']} agents and the hooks"]


def main(argv: Sequence[str]) -> int:
    if len(argv) != 2 or argv[0] not in ("codex", "gemini"):
        print("usage: host-files codex|gemini <directory>", file=sys.stderr)
        return 2
    directory = Path(os.path.expanduser(argv[1])).absolute()
    try:
        if argv[0] == "codex":
            lines = write_codex(directory)
        else:
            lines = write_gemini(directory)
    except (OSError, ValueError) as error:
        print(f"host-files: {error}", file=sys.stderr)
        return 2
    print("\n".join(lines))
    return 0
