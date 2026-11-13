"""Reads a repository through git, without running anything it contains.

Every call goes through Git.run, which turns off hooks, the file system
monitor, external diff programs, textconv, LFS smudging, submodules and
signature checks, so no filter, driver or hook from the repository or the
pull request runs. Only tree-to-tree commands are used: never checkout,
worktree or archive.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

CONFIG = (
    "-c", "core.hooksPath=/dev/null",
    "-c", "core.fsmonitor=false",
    "-c", "core.quotePath=false",
    "-c", "diff.external=",
    "-c", "log.showSignature=false",
    "-c", "protocol.file.allow=never",
    "-c", "protocol.ext.allow=never",
    "-c", "submodule.recurse=false",
    "-c", "fetch.recurseSubmodules=false",
)
# Environment variables that would point git at other programs or settings.
DROPPED = ("GIT_EXTERNAL_DIFF", "GIT_DIFF_OPTS", "GIT_CONFIG_PARAMETERS",
           "GIT_CONFIG_COUNT", "GIT_EXEC_PATH", "GIT_ASKPASS", "SSH_ASKPASS",
           "GIT_SSH", "GIT_SSH_COMMAND", "GIT_PAGER", "PAGER")
ZERO = "0" * 40


def environment() -> Dict[str, str]:
    env = {key: value for key, value in os.environ.items()
           if key not in DROPPED}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_TERMINAL_PROMPT="0",
               GIT_LFS_SKIP_SMUDGE="1", GIT_PAGER="cat", LC_ALL="C")
    return env


@dataclass(frozen=True)
class Change:
    """One file changed between two trees, from git diff-tree --raw."""

    status: str
    path: str
    old_path: Optional[str]
    old_mode: str
    new_mode: str
    old_sha: str
    new_sha: str
    score: int


@dataclass(frozen=True)
class Commit:
    sha: str
    parents: Tuple[str, ...]
    author_name: str
    author_email: str
    author_date: str
    committer_name: str
    committer_email: str
    committer_date: str
    message: str


class Git:
    def __init__(self, repo: str) -> None:
        self.repo = repo
        self.env = environment()
        self._blobs: Dict[str, bytes] = {}

    def run(self, *args: str, check: bool = True) -> bytes:
        result = subprocess.run(  # noqa: S603
            ["git", *CONFIG, *args], cwd=self.repo, env=self.env,
            stdin=subprocess.DEVNULL, capture_output=True, check=False,
        )
        if check and result.returncode != 0:
            message = result.stderr.decode("utf-8", "replace").strip()
            raise RuntimeError(f"git {args[0]} failed: {message}")
        return result.stdout

    def rev(self, name: str) -> str:
        return self.run("rev-parse", "--verify", "--quiet",
                        f"{name}^{{commit}}").decode().strip()

    def merge_base(self, base: str, head: str) -> str:
        return self.run("merge-base", base, head).decode().strip()

    def diff(self, old: str, new: str) -> List[Change]:
        raw = self.run("diff-tree", "-r", "-z", "-M", "--no-ext-diff",
                       "--no-textconv", "--full-index", old, new)
        return parse_raw(raw)

    def commit_changes(self, commit: Commit) -> List[Change]:
        """The changes a commit makes against its first parent."""
        if commit.parents:
            return self.diff(commit.parents[0], commit.sha)
        raw = self.run("diff-tree", "-r", "-z", "--root", "--no-commit-id",
                       "--no-ext-diff", "--no-textconv", "--full-index",
                       commit.sha)
        return parse_raw(raw)

    def commits(self, base: str, head: str) -> List[Commit]:
        shas = self.run("rev-list", "--reverse", "--topo-order",
                        f"{base}..{head}").decode().split()
        return [self.commit(sha) for sha in shas]

    def commit(self, sha: str) -> Commit:
        fields = self.run(
            "show", "-s", "--no-mailmap",
            "--format=%H%x00%P%x00%an%x00%ae%x00%aI%x00%cn%x00%ce%x00%cI%x00%B",
            sha,
        ).decode("utf-8", "replace").split("\0", 8)
        return Commit(fields[0], tuple(fields[1].split()), *fields[2:8],
                      fields[8].rstrip("\n"))

    def tree(self, commit: str) -> Dict[str, Tuple[str, str]]:
        """Every path in a commit's tree, with its mode and object."""
        entries: Dict[str, Tuple[str, str]] = {}
        raw = self.run("ls-tree", "-r", "-z", "--full-tree", commit)
        for record in raw.split(b"\0"):
            if not record:
                continue
            meta, _, path = record.partition(b"\t")
            mode, _, sha = meta.decode().split(" ")
            entries[path.decode("utf-8", "surrogateescape")] = (mode, sha)
        return entries

    def blob(self, sha: str) -> bytes:
        if sha == ZERO:
            return b""
        if sha not in self._blobs:
            self._blobs[sha] = self.run("cat-file", "blob", sha)
        return self._blobs[sha]

    def grep(self, commit: str, needle: str,
             paths: Tuple[str, ...] = ()) -> List[str]:
        """The paths in a commit whose text contains the needle."""
        out = self.run("grep", "-I", "-z", "-l", "-F", "--no-textconv",
                       "-e", needle, commit, "--", *paths, check=False)
        prefix = f"{commit}:"
        return [path.decode("utf-8", "surrogateescape")[len(prefix):]
                for path in out.split(b"\0") if path]


def parse_raw(raw: bytes) -> List[Change]:
    """Parses diff-tree -z --raw output."""
    parts = raw.split(b"\0")
    changes: List[Change] = []
    index = 0
    while index < len(parts) and parts[index].startswith(b":"):
        old_mode, new_mode, old_sha, new_sha, status = (
            parts[index][1:].decode().split(" "))
        letter = status[0]
        score = int(status[1:]) if status[1:] else 0
        first = parts[index + 1].decode("utf-8", "surrogateescape")
        if letter in "RC":
            second = parts[index + 2].decode("utf-8", "surrogateescape")
            changes.append(Change(letter, second, first, old_mode, new_mode,
                                  old_sha, new_sha, score))
            index += 3
        else:
            changes.append(Change(letter, first, None, old_mode, new_mode,
                                  old_sha, new_sha, score))
            index += 2
    return changes


def iter_lines(data: bytes) -> Iterator[Tuple[int, str]]:
    text = data.decode("utf-8", "replace")
    for number, line in enumerate(text.split("\n"), start=1):
        yield number, line
