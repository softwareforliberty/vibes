"""Helpers the rule families share."""

from __future__ import annotations

import re
from typing import Iterable, Iterator, Pattern, Tuple

from ..escape import excerpt
from ..model import HIGH, Context, FileChange, Finding

Line = Tuple[FileChange, int, str]


def added(ctx: Context, *wanted: str) -> Iterator[Line]:
    """Every line the pull request adds to a text file of the given kinds."""
    for change in ctx.changed(*wanted):
        for number, text in change.added():
            yield change, number, text


def removed(ctx: Context, *wanted: str) -> Iterator[Line]:
    for change in ctx.changed(*wanted):
        for number, text in change.removed():
            yield change, number, text


def matching(lines: Iterable[Line], pattern: Pattern[str], severity: str,
             rule: str, message: str) -> Iterator[Finding]:
    """A finding for each line that matches, quoting the line."""
    for change, number, text in lines:
        if pattern.search(text):
            yield Finding(severity, rule, change.path, number,
                          f"{message}: {excerpt(text)}")


def severity_for(change: FileChange, high: Tuple[str, ...],
                 otherwise: str) -> str:
    """HIGH for files of the given kinds, the other severity elsewhere."""
    return HIGH if set(change.classes) & set(high) else otherwise


def regex(*alternatives: str, flags: int = 0) -> Pattern[str]:
    return re.compile("|".join(f"(?:{a})" for a in alternatives), flags)


URL = re.compile(r"\b(?:https?|ftp|git|ssh|wss?|sftp|rsync)://"
                 r"(?:[^\s/@'\"<>`]*@)?([^\s/:'\"<>`?#)\]}]+)", re.IGNORECASE)


def hosts(text: str) -> Iterator[str]:
    for match in URL.finditer(text):
        yield match.group(1).lower().rstrip(".")
