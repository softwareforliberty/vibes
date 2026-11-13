"""Characters that hide or disguise code: Trojan Source, invisible text,
homoglyphs, overprinting and code pushed off the screen."""

from __future__ import annotations

import re
import unicodedata
from typing import Iterator

from ..escape import BIDI, INVISIBLE, TAGS, VARIATION_SELECTORS, excerpt
from ..model import HIGH, REVIEW, Context, Finding
from .common import added, severity_for

CODE = ("source", "build", "ci", "agent-config", "gate", "git-meta")
IDENTIFIER = re.compile(r"[^\W\d]\w*")
# Letters from other scripts that look like Latin ones.
CONFUSABLE = set("аеорсухіјѕԁԛԝАВЕКМНОРСТХІЈЅԜαοερτυνικχΑΒΕΖΗΙΚΜΝΟΡΤΥΧ"
                 "ɑɡɩɪʏ")
OFFSCREEN = re.compile(r"\S[ \t]{80,}\S")


def script(char: str) -> str:
    name = unicodedata.name(char, "")
    return name.split(" ")[0] if name else "UNKNOWN"


def check(ctx: Context) -> Iterator[Finding]:
    for change in ctx.text_files():
        raw = change.new()
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            yield Finding(REVIEW, "unicode-not-utf8", change.path, 0,
                          "not valid UTF-8: read it as bytes")
        if raw.startswith(b"\xef\xbb\xbf") and "source" in change.classes:
            yield Finding(REVIEW, "unicode-bom", change.path, 1,
                          "starts with a byte order mark")
    for change, number, text in added(ctx):
        codes = [ord(char) for char in text]
        if number == 1 and codes[:1] == [0xFEFF]:
            codes = codes[1:]
        if any(code in BIDI for code in codes):
            yield Finding(HIGH, "unicode-bidi", change.path, number,
                          f"bidirectional control characters, which make "
                          f"code display differently from how it runs "
                          f"(Trojan Source): {excerpt(text)}")
        tags = [code for code in codes if code in TAGS]
        if tags:
            hidden = "".join(chr(code - 0xE0000) for code in tags
                             if 0x20 <= code - 0xE0000 < 0x7F)
            yield Finding(HIGH, "unicode-tags", change.path, number,
                          f"invisible tag characters spelling "
                          f"{excerpt(hidden, 60)}: hidden text agents read "
                          f"but people don't see")
        if any(code in INVISIBLE for code in codes):
            yield Finding(severity_for(change, CODE, REVIEW),
                          "unicode-invisible", change.path, number,
                          f"zero-width or invisible characters: "
                          f"{excerpt(text)}")
        selectors = [code for code in codes if code in VARIATION_SELECTORS]
        if len(selectors) > 2 or any(code >= 0xE0100 for code in selectors):
            yield Finding(HIGH, "unicode-variation-selectors", change.path,
                          number, f"{len(selectors)} variation selectors, "
                          f"which can smuggle hidden data: {excerpt(text)}")
        if any((code < 0x20 and code not in (0x09, 0x0C, 0x0D))
               or 0x7F <= code < 0xA0 for code in codes):
            yield Finding(HIGH, "unicode-control", change.path, number,
                          f"control characters: {excerpt(text)}")
        if "\r" in text.rstrip("\r"):
            yield Finding(HIGH, "unicode-overprint", change.path, number,
                          f"a carriage return mid-line, which overprints "
                          f"what came before it on a terminal: "
                          f"{excerpt(text)}")
        if OFFSCREEN.search(text):
            yield Finding(severity_for(change, CODE, REVIEW),
                          "unicode-offscreen", change.path, number,
                          f"a long run of spaces that pushes code off the "
                          f"screen: {excerpt(text.strip()[-60:])}")
        if len(text) > 1000 and set(change.classes) & set(CODE):
            yield Finding(REVIEW, "unicode-long-line", change.path, number,
                          f"a {len(text)}-character line: minified or "
                          f"generated code can't be reviewed")
        if set(change.classes) & set(CODE):
            yield from _identifiers(change, number, text)


def _identifiers(change, number: int, text: str) -> Iterator[Finding]:
    for word in IDENTIFIER.findall(text):
        if word.isascii():
            continue
        letters = [char for char in word if char.isalpha()]
        scripts = {script(char) for char in letters}
        if any(char.isascii() for char in letters) and len(scripts) > 1:
            yield Finding(HIGH, "unicode-mixed-script", change.path, number,
                          f"a word mixing scripts {sorted(scripts)}, which "
                          f"can pass for another name: {excerpt(word)}")
            return
        if letters and all(char in CONFUSABLE for char in letters):
            yield Finding(HIGH, "unicode-confusable", change.path, number,
                          f"a word made of letters that look like Latin "
                          f"ones: {excerpt(word)}")
            return
