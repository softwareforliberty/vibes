"""repro's command.

    repro run --out <dir> [--runs N] [--timeout S] [--tree <dir>] -- <command>

Runs the command N times, 5 by default, in the tree, the current directory
by default, one run after another. Each run's output goes to
<out>/run-<n>.log, and the results to <out>/summary.json. Prints one line:

    RED 5/5 failed, median 1.4s
    GREEN 0/5 failed, median 1.2s
    FLAKY 3/5 failed, median 1.3s
    CAN'T TELL 2/5 couldn't tell, median 0.8s

A run fails when the command exits 1 to 127 other than 125, as git bisect
run counts a bad commit. It can't tell when it exits 125, is killed by a
signal, or runs out of time; any such run makes the verdict CAN'T TELL.
The line ends with SLOW when the median is over 30 seconds, too slow for a
debugging loop. Exits 0 for any verdict and 2 on an error.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import time
from typing import List, Optional, Sequence, Tuple

CANT_TELL = 125
CANT_TELL_OUTCOME = "can't tell"
SLOW_SECONDS = 30.0


def main(argv: Optional[Sequence[str]] = None) -> int:
    options, command = _split(list(argv or []))
    parser = argparse.ArgumentParser(prog="repro")
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--out", required=True)
    run.add_argument("--runs", type=int, default=5)
    run.add_argument("--timeout", type=float, default=60)
    run.add_argument("--tree", default=".")
    args = parser.parse_args(options)
    try:
        if not command:
            raise ValueError("give the command after --")
        if args.runs < 1:
            raise ValueError("--runs must be at least 1")
        if not os.path.isdir(args.tree):
            raise ValueError(f"no directory {args.tree}")
        print(_run(args.out, args.runs, args.timeout, args.tree, command))
    except (OSError, ValueError) as error:
        print(f"repro: {error}", file=sys.stderr)
        return 2
    return 0


def _split(argv: List[str]) -> Tuple[List[str], List[str]]:
    """The options, and the command after --, which argparse can't take."""
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def outcome(code: Optional[int]) -> str:
    """failed, passed or can't tell, for a run's exit status, or None for a
    run that ran out of time."""
    if code is None or code < 0 or code == CANT_TELL or code > 127:
        return CANT_TELL_OUTCOME
    return "passed" if code == 0 else "failed"


def verdict(outcomes: List[str]) -> str:
    if CANT_TELL_OUTCOME in outcomes:
        return "CAN'T TELL"
    failed = outcomes.count("failed")
    if failed == len(outcomes):
        return "RED"
    return "GREEN" if failed == 0 else "FLAKY"


def _run(out: str, runs: int, timeout: float, tree: str,
         command: List[str]) -> str:
    os.makedirs(out, exist_ok=True)
    results = []
    for number in range(1, runs + 1):
        log = os.path.join(out, f"run-{number}.log")
        start = time.monotonic()
        with open(log, "w", encoding="utf-8") as stream:
            try:
                code: Optional[int] = subprocess.run(
                    command, cwd=tree, stdout=stream,
                    stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                    timeout=timeout, check=False).returncode
            except subprocess.TimeoutExpired:
                code = None
                stream.write(f"\nrepro: timed out after {timeout:g}s\n")
        seconds = time.monotonic() - start
        results.append({"run": number, "exit": code,
                        "seconds": round(seconds, 3),
                        "outcome": outcome(code)})
    outcomes = [result["outcome"] for result in results]
    median = statistics.median(result["seconds"] for result in results)
    found = verdict(outcomes)
    if found == "CAN'T TELL":
        count = f"{outcomes.count(CANT_TELL_OUTCOME)}/{runs} couldn't tell"
    else:
        count = f"{outcomes.count('failed')}/{runs} failed"
    line = f"{found} {count}, median {median:.1f}s"
    if median > SLOW_SECONDS:
        line += " SLOW"
    with open(os.path.join(out, "summary.json"), "w",
              encoding="utf-8") as stream:
        json.dump({"command": command, "tree": os.path.abspath(tree),
                   "verdict": found, "median_seconds": round(median, 3),
                   "runs": results}, stream, indent=2)
        stream.write("\n")
    return line
