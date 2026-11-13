"""Writes the pull request where reviewers can read it safely.

No file is written under its real name: each blob goes to
blobs/<sha>.txt, with hidden characters made visible, and blobs/index.tsv
maps paths to them. A CLAUDE.md, a .claude/settings.json or an .envrc in the
pull request is then never loaded by Claude Code or a shell, and a symlink
or a .. path is never followed. Claude Code loads a CLAUDE.md inside the
project as soon as an agent reads a file next to it, which this prevents.
Binaries are described in blobs/<sha>.describe.txt instead, since an image
can carry instructions an agent would read.
"""

from __future__ import annotations

import hashlib
import os
import posixpath
from typing import List, Optional, TextIO

from . import binfmt
from .escape import ascii_only, visible
from .gitio import ZERO, Change
from .model import TEXT_LIMIT, Context, FileChange, is_binary

COLUMNS = ("path", "status", "old_mode", "new_mode", "old_blob", "new_blob",
           "size", "kind", "view", "base_view", "note")


def write(ctx: Context, out: str) -> None:
    blobs = os.path.join(out, "blobs")
    os.makedirs(blobs, exist_ok=True)
    with open(os.path.join(blobs, "index.tsv"), "w", encoding="ascii") as index:
        index.write("\t".join(COLUMNS) + "\n")
        for change in ctx.files:
            _row(ctx, blobs, index, change.change, change)
        for commit, change in ctx.history_only:
            _row(ctx, blobs, index, change, None,
                 note=f"history only: added in {commit.sha[:12]}")
    raw = ctx.git.run("diff", "--no-ext-diff", "--no-textconv", "--no-color",
                      "--full-index", "-M", ctx.base, ctx.head)
    with open(os.path.join(out, "diff.patch"), "w", encoding="utf-8") as patch:
        patch.write(visible(raw.decode("utf-8", "replace")))
    with open(os.path.join(out, "files.txt"), "w", encoding="ascii") as files:
        for change in ctx.files:
            files.write(ascii_only(change.path) + "\n")


def _row(ctx: Context, blobs: str, index: TextIO, change: Change,
         loaded: Optional[FileChange], note: str = "") -> None:
    mode = change.new_mode
    kind, view, base_view, size = "deleted", "-", "-", 0
    if change.status != "D":
        if mode == "160000":
            kind = "submodule"
            note = note or f"points at commit {change.new_sha}"
        else:
            data = ctx.git.blob(change.new_sha)
            size = len(data)
            if mode == "120000":
                kind = "symlink"
                note = note or "target " + ascii_only(
                    data.decode("utf-8", "replace"), 200)
            elif is_binary(data):
                kind = "binary"
                view = _describe(blobs, change, data)
            else:
                kind = "text"
                view = _text(blobs, change.new_sha, data)
                if len(data) > TEXT_LIMIT:
                    note = note or f"cut short at {TEXT_LIMIT} bytes"
    if change.old_sha != ZERO and change.old_mode not in ("160000", "120000"):
        old = ctx.git.blob(change.old_sha)
        if not is_binary(old):
            base_view = _text(blobs, change.old_sha, old)
    row = (ascii_only(change.path), change.status, change.old_mode,
           change.new_mode, change.old_sha, change.new_sha, str(size), kind,
           view, base_view, ascii_only(note))
    index.write("\t".join(row) + "\n")


def _text(blobs: str, sha: str, data: bytes) -> str:
    name = f"{sha}.txt"
    path = os.path.join(blobs, name)
    if not os.path.exists(path):
        text = visible(data[:TEXT_LIMIT].decode("utf-8", "replace"))
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(text)
        os.chmod(path, 0o644)
    return f"blobs/{name}"


def _describe(blobs: str, change: Change, data: bytes) -> str:
    name = f"{change.new_sha}.describe.txt"
    extension = posixpath.splitext(change.path)[1].lstrip(".")
    description = binfmt.describe(data, extension)
    lines: List[str] = [
        f"path: {ascii_only(change.path)}",
        f"kind: {description.kind or 'unknown'}",
        f"size: {len(data)} bytes",
        f"sha256: {hashlib.sha256(data).hexdigest()}",
        "",
        "anomalies:",
        *(f"  {ascii_only(a, 200)}" for a in description.anomalies or
          ["none found"]),
        "notes:",
        *(f"  {ascii_only(n, 200)}" for n in description.notes),
        "structure:",
        *(f"  {ascii_only(s, 200)}" for s in description.structure[:200]),
        "printable strings (first 40, escaped):",
        *(f"  {ascii_only(s, 120)}" for s in
          binfmt.printable_strings(data, 8)[:40]),
        "first 256 bytes:",
        *binfmt.hexdump(data[:256]),
    ]
    if len(data) > 256:
        start = max(256, len(data) - 256)
        lines += ["last 256 bytes:", *binfmt.hexdump(data[start:], start)]
    path = os.path.join(blobs, name)
    with open(path, "w", encoding="ascii") as stream:
        stream.write("\n".join(lines) + "\n")
    os.chmod(path, 0o644)
    return f"blobs/{name}"
