"""plan-graph's command.

    plan-graph <rebuild-plan.md> [--done <batches>] [--running <batches>]

Reads the batch list at the top of a rebuild plan, under `## Batches`, where
each batch says what it waits for and what it touches:

    1. [Gate and parser](#batch-1-gate-and-parser) (9 entries)
       After: none
       Touches: scripts/check, src/parser/

`After:` names the batches it needs finished first, or `none`; without the
line, a batch waits for the one before it. `Touches:` names the files and
directories, ending in `/`, it changes; without the line, it touches
everything, so it never runs beside another. Prints:

    READY: 2, 3        the batches that can start now
    WIDTH: 2           the most batches that could ever run at once
    PROBLEMS:          two batches that could run at once but touch the
    - ...              same path, a cycle, or a batch that doesn't exist

Batches done or running are given as comma-separated numbers. Exits 0, 1
when there are problems, and 2 on an error.
"""

from __future__ import annotations

import re
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple

BATCH = re.compile(r"^(\d+)\.\s")
FIELD = re.compile(r"^\s+(?:-\s+)?(After|Touches):\s*(.*)$", re.IGNORECASE)
EVERYTHING = "*"


def parse(text: str) -> Tuple[List[int], Dict[int, Set[int]],
                               Dict[int, List[str]]]:
    """The batches in order, what each waits for, and what each touches."""
    order: List[int] = []
    after: Dict[int, Set[int]] = {}
    touches: Dict[int, List[str]] = {}
    section = re.search(r"^## Batches\s*$(.*?)(?=^## |\Z)", text,
                        re.MULTILINE | re.DOTALL)
    if not section:
        raise ValueError("no `## Batches` section")
    current: Optional[int] = None
    for line in section.group(1).splitlines():
        start = BATCH.match(line)
        if start:
            current = int(start.group(1))
            order.append(current)
            continue
        field = FIELD.match(line)
        if field and current is not None:
            name, value = field.group(1).lower(), field.group(2).strip()
            if name == "after":
                after[current] = {int(n) for n in re.findall(r"\d+", value)}
            else:
                touches[current] = [p.strip().strip("`") for p in
                                    value.split(",") if p.strip()]
    if not order:
        raise ValueError("no batches listed under `## Batches`")
    for index, batch in enumerate(order):
        after.setdefault(batch, {order[index - 1]} if index else set())
        touches.setdefault(batch, [EVERYTHING])
    return order, after, touches


def overlap(a: List[str], b: List[str]) -> Optional[str]:
    """A path both lists touch, counting a directory as everything in it."""
    for one in a:
        for other in b:
            if EVERYTHING in (one, other):
                return "everything" if one == other else (
                    other if one == EVERYTHING else one)
            if one == other or (one.endswith("/") and other.startswith(one)) \
                    or (other.endswith("/") and one.startswith(other)):
                return one if len(one) >= len(other) else other
    return None


def reach(after: Dict[int, Set[int]]) -> Dict[int, Set[int]]:
    """Every batch each one waits for, directly or not."""
    found: Dict[int, Set[int]] = {}

    def visit(batch: int, path: Tuple[int, ...]) -> Set[int]:
        if batch in path:
            raise ValueError("a cycle: " + " after ".join(
                map(str, path[path.index(batch):] + (batch,))))
        if batch not in found:
            below: Set[int] = set()
            for need in after.get(batch, set()):
                below |= {need} | visit(need, path + (batch,))
            found[batch] = below
        return found[batch]

    for batch in after:
        visit(batch, ())
    return found


def width(order: List[int], after: Dict[int, Set[int]]) -> int:
    """The most batches that run at once when each starts as soon as it
    can and all take the same time."""
    level: Dict[int, int] = {}
    for batch in order:
        level[batch] = 1 + max((level.get(n, 0) for n in after[batch]),
                               default=0)
    counts: Dict[int, int] = {}
    for value in level.values():
        counts[value] = counts.get(value, 0) + 1
    return max(counts.values())


def report(text: str, done: Set[int], running: Set[int]) -> Tuple[
        List[str], List[str]]:
    """The lines to print, and the problems found."""
    order, after, touches = parse(text)
    problems = [f"batch {batch} waits for batch {need}, which isn't listed"
                for batch in order for need in sorted(after[batch])
                if need not in order]
    if problems:
        return [], problems
    try:
        below = reach(after)
    except ValueError as error:
        return [], [str(error)]
    for index, one in enumerate(order):
        for other in order[index + 1:]:
            if one in below[other] or other in below[one]:
                continue
            path = overlap(touches[one], touches[other])
            if path:
                problems.append(f"batches {one} and {other} both touch "
                                f"{path}, and neither waits for the other")
    ready = [b for b in order if b not in done and b not in running
             and after[b] <= done
             and not any(overlap(touches[b], touches[r]) for r in running)]
    lines = [f"READY: {', '.join(map(str, ready)) or 'none'}",
             f"WIDTH: {width(order, after)}"]
    return lines, problems


def _numbers(value: str) -> Set[int]:
    return {int(n) for n in re.findall(r"\d+", value or "")}


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv or [])
    if not args or args[0].startswith("-"):
        print("usage: plan-graph <rebuild-plan.md> [--done <batches>] "
              "[--running <batches>]", file=sys.stderr)
        return 2
    path, rest = args[0], args[1:]
    options: Dict[str, str] = {}
    while rest:
        if rest[0] not in ("--done", "--running") or len(rest) < 2:
            print(f"plan-graph: unknown argument {rest[0]}", file=sys.stderr)
            return 2
        options[rest[0]] = rest[1]
        rest = rest[2:]
    try:
        with open(path, encoding="utf-8") as stream:
            text = stream.read()
        lines, problems = report(text, _numbers(options.get("--done", "")),
                                 _numbers(options.get("--running", "")))
    except (OSError, ValueError) as error:
        print(f"plan-graph: {error}", file=sys.stderr)
        return 2
    for line in lines:
        print(line)
    if problems:
        print("PROBLEMS:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    return 0
