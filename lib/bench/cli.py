"""bench's commands.

    bench run --out <dir> --a <tree> --b <tree> [--pairs N] [--max-pairs N]
              [--noise <dir>] [--measure M] [--warmup N] [--repeat N]
              [--min-time S] [--seed N] [--timeout S] [--no-output-check]
              -- <harness command, naming the tree as {tree}>
    bench import --out <dir> --a <file[#n]> --b <file[#n]> [--measure M]
    bench tests --out <dir> --tree <tree> [--timeout S] -- <test command>
    bench compare --out <dir>
    bench verdict --out <dir> [--noise <dir>] [--measure M]
                  [--higher-is-better] [--guard M=PCT]... [--floor PCT]

Each prints only numbers and fixed text, never the harness's output, which
goes to the measurement's run.log.
"""

from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
from typing import Dict, List, Optional, Sequence, Tuple

from . import samples, stats, verdict
from .runner import HarnessFailed, Runner, environment
from .samples import Sample

EXTEND_BY = 5


def main(argv: Optional[Sequence[str]] = None) -> int:
    options, command = _split(list(argv or []))
    args = _parser().parse_args(options)
    args.argv = command
    try:
        return args.handler(args)
    except (HarnessFailed, OSError, ValueError, KeyError,
            subprocess.SubprocessError) as error:
        print(f"bench: {error}", file=sys.stderr)
        return 2


def _split(argv: List[str]) -> Tuple[List[str], List[str]]:
    """The options, and the command after --, which argparse can't take."""
    if "--" in argv:
        index = argv.index("--")
        return argv[:index], argv[index + 1:]
    return argv, []


def _command(args: argparse.Namespace) -> List[str]:
    if not args.argv:
        raise ValueError("give the command after --")
    return list(args.argv)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bench")
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("run")
    run.add_argument("--out", required=True)
    run.add_argument("--a", required=True)
    run.add_argument("--b", required=True)
    run.add_argument("--pairs", type=int, default=10)
    run.add_argument("--max-pairs", type=int, default=30)
    run.add_argument("--noise")
    run.add_argument("--measure", default="wall")
    run.add_argument("--higher-is-better", action="store_true")
    run.add_argument("--warmup", type=int, default=1)
    run.add_argument("--repeat", type=int)
    run.add_argument("--min-time", type=float, default=0.1)
    run.add_argument("--seed", type=int, default=1)
    run.add_argument("--timeout", type=float, default=600)
    run.add_argument("--no-output-check", action="store_true")
    run.set_defaults(handler=_run)

    imported = commands.add_parser("import")
    imported.add_argument("--out", required=True)
    imported.add_argument("--a", required=True)
    imported.add_argument("--b", required=True)
    imported.add_argument("--measure", default="wall")
    imported.set_defaults(handler=_import)

    tests = commands.add_parser("tests")
    tests.add_argument("--out", required=True)
    tests.add_argument("--tree", required=True)
    tests.add_argument("--timeout", type=float, default=3600)
    tests.set_defaults(handler=_tests)

    compare = commands.add_parser("compare")
    compare.add_argument("--out", required=True)
    compare.set_defaults(handler=_compare)

    decide = commands.add_parser("verdict")
    decide.add_argument("--out", required=True)
    decide.add_argument("--noise")
    decide.add_argument("--measure", default="wall")
    decide.add_argument("--higher-is-better", action="store_true")
    decide.add_argument("--guard", action="append", default=[])
    decide.add_argument("--floor", type=float, default=2.0)
    decide.set_defaults(handler=_verdict)
    return parser


def _fresh(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)
    if os.path.exists(os.path.join(directory, samples.SAMPLES)):
        raise ValueError(f"{directory} already holds a measurement: use a "
                         f"new directory")


def _run(args: argparse.Namespace) -> int:
    _fresh(args.out)
    trees = {"a": os.path.abspath(args.a), "b": os.path.abspath(args.b)}
    for tree in trees.values():
        if not os.path.isdir(tree):
            raise ValueError(f"no such tree: {tree}")
    found_environment = environment()
    with open(os.path.join(args.out, "run.log"), "w",
              encoding="utf-8") as log:
        runner = Runner(_command(args), trees, args.timeout, log)
        taken: List[Sample] = []
        broken: List[str] = []
        repeat = args.repeat
        try:
            calibrated = runner.calibrate(args.warmup, args.min_time)
            repeat = repeat or calibrated
            # A side b that prints something else is broken, so it isn't
            # worth timing.
            if not args.no_output_check:
                broken += _output_problems(runner)
            if not broken:
                taken = _until_clear(args, runner, repeat)
        except HarnessFailed as error:
            if runner.sides["a"].failures:
                raise
            broken.append(f"{error}; see run.log")
        if not args.no_output_check and not broken:
            broken += _output_problems(runner)
        samples.write_samples(args.out, taken)
        _write_run(args, trees, repeat, runner, broken, found_environment)
    print(f"bench: {_pairs(taken)} pairs, {repeat or 0} runs per sample")
    for warning in found_environment["warnings"]:  # type: ignore[union-attr]
        print(f"bench: warning: {warning}")
    if broken:
        print("bench: side b is broken: run bench verdict for why")
    return 0


def _until_clear(args: argparse.Namespace, runner: Runner,
                 repeat: int) -> List[Sample]:
    """Takes the pairs asked for, then more, up to the maximum, while the
    interval is too wide to tell a change of the minimum effect from
    noise."""
    generator = random.Random(args.seed)
    effect = verdict.min_effect(verdict.noise(args.noise, args.measure))
    taken = runner.pairs(0, args.pairs, repeat, generator)
    while _pairs(taken) < args.max_pairs:
        a, b = samples.by_measure(taken)[args.measure]
        if stats.paired(a, b).half_width <= effect:
            break
        taken += runner.pairs(_pairs(taken), EXTEND_BY, repeat, generator)
    return taken


def _pairs(taken: List[Sample]) -> int:
    return len({sample.pair for sample in taken})


def _output_problems(runner: Runner) -> List[str]:
    a = set(runner.sides["a"].hashes)
    b = set(runner.sides["b"].hashes)
    if len(a) > 1:
        raise ValueError("side a's output varies from run to run: make the "
                         "harness print the same output each time, or use "
                         "--no-output-check")
    if a != b:
        return ["side b's output differs from side a's"]
    return []


def _write_run(args: argparse.Namespace, trees: Dict[str, str], repeat,
               runner: Runner, broken: List[str],
               found_environment: Dict[str, object]) -> None:
    samples.write_json(args.out, samples.RUN, {
        "command": runner.command, "trees": trees, "paired": True,
        "repeat": repeat, "seed": args.seed,
        "output_checked": not args.no_output_check,
        "failures": {side: runner.sides[side].failures
                     for side in runner.sides},
        "broken": broken, "environment": found_environment})


def _import(args: argparse.Namespace) -> int:
    _fresh(args.out)
    taken = [Sample(index, side, args.measure, value)
             for side, spec in (("a", args.a), ("b", args.b))
             for index, value in enumerate(samples.read_values(spec))]
    samples.write_samples(args.out, taken)
    samples.write_json(args.out, samples.RUN, {
        "command": None, "sources": {"a": args.a, "b": args.b},
        "paired": False, "broken": [], "environment": environment()})
    print(f"bench: imported {sum(1 for s in taken if s.side == 'a')} and "
          f"{sum(1 for s in taken if s.side == 'b')} samples")
    return 0


def _tests(args: argparse.Namespace) -> int:
    os.makedirs(args.out, exist_ok=True)
    tree = os.path.abspath(args.tree)
    with open(os.path.join(args.out, "tests.log"), "w",
              encoding="utf-8") as log:
        try:
            status = subprocess.run(_command(args), cwd=tree, stdout=log,
                                    stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL,
                                    timeout=args.timeout,
                                    check=False).returncode
        except subprocess.TimeoutExpired:
            status = -1
            log.write(f"\nbench: timed out after {args.timeout:.0f}s\n")
    samples.write_json(args.out, samples.TESTS, {
        "command": _command(args), "tree": tree, "status": status,
        "passed": status == 0})
    print(f"bench: tests {'passed' if status == 0 else 'FAILED'} "
          f"(exit {status})")
    return 0


def _compare(args: argparse.Namespace) -> int:
    for measure in verdict.measures(args.out):
        found = verdict.interval(args.out, measure)
        print(f"bench: {measure}: b/a {found.ratio:.4f} (95% CI "
              f"{found.low:.4f} to {found.high:.4f}), {found.count} pairs")
    return 0


def _verdict(args: argparse.Namespace) -> int:
    guards = {}
    for guard in args.guard:
        measure, _, limit = guard.partition("=")
        if not limit:
            raise ValueError(f"a guard is MEASURE=PERCENT, not {guard}")
        guards[measure] = float(limit.rstrip("%")) / 100
    found = verdict.decide(args.out, args.noise, args.measure,
                           args.higher_is_better, guards, args.floor / 100)
    samples.write_json(args.out, "verdict.json", found.data)
    print(f"bench: {found.line}")
    return 0
