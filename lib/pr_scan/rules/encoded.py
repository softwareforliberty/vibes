"""Encoded payloads in text: base64, hex, escapes, byte arrays, char codes."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterator

from ..escape import excerpt
from ..model import HIGH, REVIEW, Context, Finding
from .common import added, severity_for

BASE64 = re.compile(r"[A-Za-z0-9+/_-]{100,}={0,2}")
HEX = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{160,}(?![0-9a-fA-F])")
ESCAPES = re.compile(r"(?:\\x[0-9a-fA-F]{2}){16,}|(?:\\[0-7]{3}){16,}|"
                     r"(?:\\u[0-9a-fA-F]{4}){12,}|(?:%[0-9a-fA-F]{2}){24,}")
BYTE = re.compile(r"\b0x[0-9a-fA-F]{2}\b")
DECIMAL_BYTES = re.compile(r"(?:\b(?:25[0-5]|2[0-4]\d|1?\d?\d)\s*,\s*){48,}")
CHAR_CODES = re.compile(r"(?:\bchr\s*\(\s*\d+\s*\).*){4,}|"
                        r"fromCharCode\s*\(\s*\d+\s*,|"
                        r"join\s*\(\s*map\s*\(\s*chr\b|"
                        r"\bpack\s*\(\s*['\"][CcH]\*?['\"]|"
                        r"\[::-1\]\s*\)|\.reverse\(\)\s*\.join\(",
                        re.IGNORECASE)
# The base64 of compressed data or executables, by its first bytes.
ENCODED_MAGIC = re.compile(r"H4sI|/Td6WFo|KLUv/|QlpoO|f0VMR|TVqQAA|N3q8ryc|"
                           r"UEsDB|XQAAA|eJz[a-zA-Z0-9+/]{20}|"
                           r"eNo[a-zA-Z0-9+/]{20}")
STRING = re.compile(r"\"([^\"\\]{40,})\"|'([^'\\]{40,})'")
NOT_SECRET = re.compile(r"[/ .:]|^[a-z_]+$|^[A-Z_]+$")


def entropy(text: str) -> float:
    counts = Counter(text)
    total = len(text)
    return -sum(c / total * math.log2(c / total) for c in counts.values())


def check(ctx: Context) -> Iterator[Finding]:
    risky = ("build", "ci", "source", "agent-config", "gate")
    for change, number, text in added(ctx):
        severity = severity_for(change, risky, REVIEW)
        for match in BASE64.finditer(text):
            if entropy(match.group()) >= 4.5:
                yield Finding(severity, "encoded-base64", change.path, number,
                              f"a {len(match.group())}-character base64-like "
                              f"run: {excerpt(match.group(), 60)}")
                break
        if HEX.search(text):
            yield Finding(severity, "encoded-hex", change.path, number,
                          f"a long hex run: {excerpt(text, 60)}")
        if ESCAPES.search(text):
            yield Finding(HIGH, "encoded-escapes", change.path, number,
                          f"a long run of escaped bytes: {excerpt(text, 60)}")
        if DECIMAL_BYTES.search(text):
            yield Finding(REVIEW, "encoded-byte-array", change.path, number,
                          f"a long array of byte values: {excerpt(text, 60)}")
        if CHAR_CODES.search(text):
            yield Finding(HIGH, "encoded-char-codes", change.path, number,
                          f"a string built from character codes or "
                          f"reversed: {excerpt(text)}")
        if ENCODED_MAGIC.search(text) and "docs" not in change.classes:
            yield Finding(HIGH, "encoded-magic", change.path, number,
                          f"text that starts like encoded compressed data "
                          f"or an executable: {excerpt(text, 60)}")
        for match in STRING.finditer(text):
            literal = match.group(1) or match.group(2)
            if not NOT_SECRET.search(literal) and entropy(literal) >= 4.8:
                yield Finding(REVIEW, "encoded-high-entropy", change.path,
                              number, f"a random-looking string: "
                              f"{excerpt(literal, 60)}")
                break
    for change in ctx.text_files():
        count = sum(len(BYTE.findall(text)) for _, text in change.added())
        if count >= 256:
            yield Finding(REVIEW, "encoded-byte-array", change.path, 0,
                          f"{count} hex byte values added: embedded data, "
                          f"such as a font or firmware, needs its source "
                          f"and how it was made")
