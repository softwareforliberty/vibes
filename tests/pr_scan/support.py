"""Builds throwaway git repositories for the scan's tests.

Fixtures are made at test time, so no payload-shaped bytes are committed to
this repository. Every payload only prints a harmless string.
"""

from __future__ import annotations

import os
import struct
import subprocess
import sys
import tempfile
import zlib
from typing import Dict, List, Optional, Union

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "lib"))

from pr_scan import cli, rules  # noqa: E402
from pr_scan.model import Finding  # noqa: E402


class Link(str):
    """A symlink's target."""


class Exec(bytes):
    """The contents of an executable file."""


class Indexed(bytes):
    """Contents added to the index only, for paths this file system can't
    hold, such as .GIT or a case collision on macOS."""


Content = Union[str, bytes, Link, Exec, Indexed, None]

ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
           GIT_AUTHOR_NAME="Base Author", GIT_AUTHOR_EMAIL="base@example.com",
           GIT_COMMITTER_NAME="Base Author",
           GIT_COMMITTER_EMAIL="base@example.com")


class Repo:
    def __init__(self, base: Dict[str, Content]) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = self._tmp.name
        self.git("init", "-q", "-b", "main")
        self.write(base)
        self.commit("Base")
        self.git("switch", "-q", "-c", "pr")

    def cleanup(self) -> None:
        self._tmp.cleanup()

    def git(self, *args: str, env: Optional[Dict[str, str]] = None) -> str:
        return subprocess.run(
            ["git", *args], cwd=self.path, env=env or ENV, check=True,
            capture_output=True, text=True).stdout

    def write(self, files: Dict[str, Content]) -> None:
        for path, content in files.items():
            full = os.path.join(self.path, path)
            if content is None:
                self.git("rm", "-q", "--", path)
                continue
            if isinstance(content, Indexed):
                sha = subprocess.run(
                    ["git", "hash-object", "-w", "--stdin"], cwd=self.path,
                    env=ENV, input=bytes(content), check=True,
                    capture_output=True).stdout.decode().strip()
                self.git("-c", "core.protectHFS=false", "-c",
                         "core.protectNTFS=false", "update-index", "--add",
                         "--cacheinfo",
                         f"100644,{sha},{path}")
                continue
            os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
            if os.path.lexists(full):
                os.remove(full)
            if isinstance(content, Link):
                os.symlink(str(content), full)
            else:
                data = content.encode() if isinstance(content, str) else content
                with open(full, "wb") as stream:
                    stream.write(data)
                os.chmod(full, 0o755 if isinstance(content, Exec) else 0o644)
            self.git("add", "-f", "--", path)

    def commit(self, message: str, author: str = "Base Author <base@example.com>"
               ) -> str:
        self.git("commit", "-q", "--allow-empty", "-m", message,
                 f"--author={author}")
        return self.git("rev-parse", "HEAD").strip()

    def scan(self, meta: Optional[Dict[str, object]] = None) -> List[Finding]:
        ctx = cli.context(self.path, "main", "pr", meta or {})
        findings = rules.run(ctx)
        return findings + cli.per_commit(ctx, findings)


def pr(base: Dict[str, Content], change: Dict[str, Content],
       message: str = "Change", meta: Optional[Dict[str, object]] = None,
       author: str = "Base Author <base@example.com>") -> List[Finding]:
    repo = Repo(base)
    try:
        repo.write(change)
        repo.commit(message, author)
        return repo.scan(meta)
    finally:
        repo.cleanup()


def chunk(kind: bytes, body: bytes) -> bytes:
    return (struct.pack(">I", len(body)) + kind + body
            + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF))


def png(width: int = 2, height: int = 2, extra: bytes = b"",
        chunks: bytes = b"", pixels: Optional[bytes] = None) -> bytes:
    rows = pixels if pixels is not None else b"".join(
        b"\0" + b"\x10\x20\x30" * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0,
                                         0))
            + chunks + chunk(b"IDAT", zlib.compress(rows))
            + chunk(b"IEND", b"") + extra)


def rules_of(findings: List[Finding], severity: str = "") -> set:
    return {f.rule for f in findings if not severity or f.severity == severity}
