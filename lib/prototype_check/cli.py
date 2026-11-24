"""prototype-check's command.

    prototype-check <prototype.html>

Checks a logic prototype, the single HTML file /vibes:prototype builds,
keeps the rules that make it worth having:

- it loads nothing from outside, so it opens by double-click and survives
  being emailed: no script, style sheet, image or font fetched from a URL,
  no @import, and no fetch, XMLHttpRequest or WebSocket;
- its logic sits in one <script id="logic"> block that never touches the
  page, so the rules it proves can be read on their own: no document,
  window, event listeners or browser storage;
- it states its question, in an element with id="question";
- it has at least two scenarios, elements with a data-scenario attribute,
  each with steps, elements with a data-step attribute.

Prints `PROTOTYPE OK: <n> scenarios, <m> steps` and exits 0, or
`PROTOTYPE PROBLEMS:` and a line for each, and exits 1. Exits 2 on an
error.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from typing import List, Optional, Sequence, Tuple

# Attributes that fetch from a URL when they name one.
FETCHING = {"src", "href", "srcset", "data", "poster", "action"}
URL = re.compile(r"^\s*(https?:)?//", re.IGNORECASE)
REMOTE_CODE = re.compile(
    r"@import|url\(\s*['\"]?\s*(https?:)?//|\bfetch\s*\(|XMLHttpRequest"
    r"|\bWebSocket\b|\bEventSource\b|\bimport\s*\(", re.IGNORECASE)
PAGE = re.compile(
    r"\b(document|window|globalThis|localStorage|sessionStorage|indexedDB"
    r"|navigator|alert|addEventListener|innerHTML|querySelector\w*)\b")


class _Prototype(HTMLParser):
    """Collects what the rules need from the page."""

    def __init__(self) -> None:
        self._stack: List[str] = []
        super().__init__(convert_charrefs=True)
        self.outside: List[str] = []
        self.logic: List[str] = []
        self.texts: List[Tuple[str, str]] = []
        self.question = ""
        self.scenarios: List[List[str]] = []
        self._open: List[str] = []
        self._in_question = 0
        self._scenario_depth: List[int] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = {name: value or "" for name, value in attrs}
        for name, value in values.items():
            if name in FETCHING and URL.match(value) \
                    and not (tag == "a" and name == "href"):
                self.outside.append(f"<{tag} {name}=\"{value}\">")
        kind = "logic" if tag == "script" and values.get("id") == "logic" \
            else tag
        if tag in ("script", "style"):
            self._open.append(kind)
        if values.get("id") == "question":
            self._in_question = len(self._stack) + 1
        if "data-scenario" in values:
            self.scenarios.append([])
            self._scenario_depth.append(len(self._stack) + 1)
        if "data-step" in values and self.scenarios and self._scenario_depth:
            self.scenarios[-1].append(values["data-step"])
        if tag not in _VOID:
            self._stack.append(tag)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._open:
            self._open.pop()
        depth = len(self._stack)
        if self._in_question and depth <= self._in_question:
            self._in_question = 0
        if self._scenario_depth and depth <= self._scenario_depth[-1]:
            self._scenario_depth.pop()
        if self._stack and tag in self._stack:
            while self._stack and self._stack.pop() != tag:
                pass

    def handle_data(self, data: str) -> None:
        where = self._open[-1] if self._open else "text"
        if where == "logic":
            self.logic.append(data)
        if where in ("logic", "script", "style"):
            self.texts.append((where, data))
        if self._in_question and where == "text":
            self.question += data

    def reset(self) -> None:
        # HTMLParser.__init__ calls reset, so the stack of open elements is
        # cleared here too.
        super().reset()
        self._stack = []


# Elements that never have an end tag.
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
         "link", "meta", "source", "track", "wbr"}


def problems(html: str) -> Tuple[List[str], int, int]:
    """The rules the page breaks, and its scenario and step counts."""
    page = _Prototype()
    page.feed(html)
    page.close()
    found = [f"loads from outside: {what}" for what in page.outside]
    for where, text in page.texts:
        for match in REMOTE_CODE.finditer(text):
            found.append(f"loads from outside: {match.group(0)} in a "
                         f"{'script' if where != 'style' else 'style'}")
    if not page.logic:
        found.append('no logic block: put the logic in <script id="logic">')
    for match in PAGE.finditer("".join(page.logic)):
        found.append(f"the logic touches the page: {match.group(0)}")
    if not page.question.strip():
        found.append('no question: state it in an element with id="question"')
    if len(page.scenarios) < 2:
        found.append("fewer than two scenarios: mark each with data-scenario")
    for number, steps in enumerate(page.scenarios, start=1):
        if not steps:
            found.append(f"a scenario with no steps: scenario {number} has no "
                         "data-step element")
    return found, len(page.scenarios), sum(map(len, page.scenarios))


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv or [])
    if len(args) != 1:
        print("usage: prototype-check <prototype.html>", file=sys.stderr)
        return 2
    try:
        with open(args[0], encoding="utf-8") as stream:
            html = stream.read()
    except (OSError, UnicodeDecodeError) as error:
        print(f"prototype-check: {error}", file=sys.stderr)
        return 2
    found, scenarios, steps = problems(html)
    if found:
        print("PROTOTYPE PROBLEMS:")
        for problem in found:
            print(f"- {problem}")
        return 1
    print(f"PROTOTYPE OK: {scenarios} scenarios, {steps} steps")
    return 0
