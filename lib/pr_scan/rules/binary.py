"""Binary files: the hiding place of XZ's payload.

Every binary the pull request adds or changes is a finding: HIGH when its
contents can't be reviewed (code, archives, compressed data), when its
structure hides extra data, or when it's outside the paths .vibes-review
allows binaries in; REVIEW otherwise, since a person still has to look at it.
"""

from __future__ import annotations

import posixpath
from typing import Iterator

from .. import binfmt
from ..escape import ascii_only
from ..model import HIGH, REVIEW, Context, Finding, is_binary, matches

LFS = b"version https://git-lfs.github.com/spec/"


def a(kind: str) -> str:
    return f"an {kind}" if kind[:1] in "aeiou" else f"a {kind}"


def check(ctx: Context) -> Iterator[Finding]:
    images_changed = []
    for change in ctx.changed():
        data = change.new()
        if data.startswith(LFS):
            yield Finding(HIGH, "binary-lfs", change.path, 0,
                          "a Git LFS pointer: the real contents aren't in "
                          "the pull request, so they can't be reviewed")
            continue
        if not change.binary:
            continue
        extension = posixpath.splitext(change.path)[1].lstrip(".")
        description = binfmt.describe(data, extension)
        kind = description.kind
        for anomaly in description.anomalies:
            yield Finding(HIGH, "binary-anomaly", change.path, 0,
                          ascii_only(anomaly, 160))
        if kind is None:
            yield Finding(HIGH, "binary-unknown", change.path, 0,
                          f"a binary of no known kind, {len(data)} bytes")
        elif kind in binfmt.OPAQUE:
            yield Finding(HIGH, "binary-opaque", change.path, 0,
                          f"{a(kind)} file, {len(data)} bytes: code, an "
                          f"archive or compressed data can't be reviewed; "
                          f"ask for it to be built from source in the "
                          f"repository instead")
        elif matches(change.path, ctx.config.binary_allowed):
            yield Finding(REVIEW, "binary-changed", change.path, 0,
                          f"{a(kind)} file, {len(data)} bytes: look at it")
        else:
            yield Finding(HIGH, "binary-unexpected", change.path, 0,
                          f"{a(kind)} file, {len(data)} bytes, outside the "
                          f"paths .vibes-review allows binaries in")
        if kind in binfmt.IMAGES and ctx.is_test_data(change.path):
            images_changed.append(change)
    yield from _reference_and_checker(ctx, images_changed)
    yield from _history_only(ctx)


def _reference_and_checker(ctx: Context, images: list) -> Iterator[Finding]:
    """A reference image changed in the same pull request as code that uses it.

    Changing both at once can hide a weakened comparison.
    """
    for image in images:
        name = posixpath.basename(image.path)
        for change in ctx.text_files():
            if change is image:
                continue
            if any(name in text for _, text in change.added() +
                   change.removed()):
                yield Finding(REVIEW, "binary-reference-and-checker",
                              image.path, 0,
                              f"changed together with "
                              f"{ascii_only(change.path, 80)}, which uses it: "
                              f"check the comparison wasn't weakened")


def _history_only(ctx: Context) -> Iterator[Finding]:
    """Files that are gone by the head, and binaries replaced before it.

    Text that a later commit changed is scanned commit by commit instead.
    """
    head = ctx.head_tree()
    for commit, change in ctx.history_only:
        data = ctx.git.blob(change.new_sha)
        if change.path in head and not is_binary(data):
            continue
        what = "binary" if is_binary(data) else "file"
        yield Finding(HIGH, "binary-history-only" if what == "binary"
                      else "gitlevel-history-only", change.path, 0,
                      f"a {what} added in commit {commit.sha[:12]} and gone "
                      f"by the head: a merge that keeps the commits keeps it "
                      f"in history; read it in the snapshot, and ask for a "
                      f"squash merge")
