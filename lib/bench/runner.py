"""Runs a benchmark harness against two trees, in interleaved pairs.

Each pair runs side a and side b once each, in an order a seeded random
generator picks, so drift such as a laptop warming up or a backup starting
falls on both sides alike. Every run of the harness is waited for with
wait4, which gives that run's own CPU time and peak memory.
"""

from __future__ import annotations

import hashlib
import math
import os
import platform
import random
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, TextIO

from .samples import Sample

TREE = "{tree}"
SIDES = ("a", "b")
MAX_REPEAT = 100


@dataclass
class Execution:
    wall: float
    user: float
    sys: float
    rss_kib: float
    status: int
    output: bytes


@dataclass
class Side:
    """What one side's runs printed and how many failed."""

    hashes: List[str] = field(default_factory=list)
    failures: int = 0


class HarnessFailed(RuntimeError):
    pass


def command_for(command: Sequence[str], tree: str) -> List[str]:
    return [part.replace(TREE, tree) for part in command]


def execute(argv: Sequence[str], env: Dict[str, str], timeout: float,
            log: TextIO) -> Execution:
    """Runs one command, capturing its output to a file rather than a pipe,
    so a chatty harness can't block on a full pipe."""
    with tempfile.TemporaryFile() as output:
        start = time.perf_counter()
        process = subprocess.Popen(list(argv), stdout=output, stderr=log,
                                   stdin=subprocess.DEVNULL, env=env)
        timer = threading.Timer(timeout, process.kill)
        timer.start()
        try:
            _, status, usage = os.wait4(process.pid, 0)
        finally:
            timer.cancel()
        wall = time.perf_counter() - start
        process.returncode = os.waitstatus_to_exitcode(status)
        output.seek(0)
        text = output.read()
    # ru_maxrss is in bytes on macOS and in KiB on Linux.
    rss = usage.ru_maxrss / 1024 if platform.system() == "Darwin" \
        else float(usage.ru_maxrss)
    return Execution(wall, usage.ru_utime, usage.ru_stime, rss,
                     process.returncode, text)


def metrics(output: bytes) -> Dict[str, float]:
    """The `metric <name> <value>` lines a harness printed."""
    found = {}
    for line in output.decode("utf-8", "replace").splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[0] == "metric":
            try:
                found[parts[1]] = float(parts[2])
            except ValueError:
                continue
    return found


def output_hash(output: bytes) -> str:
    """A hash of what the harness printed, other than its metric lines,
    which vary from run to run."""
    kept = [line for line in output.splitlines()
            if not line.startswith(b"metric ")]
    return hashlib.sha256(b"\n".join(kept)).hexdigest()


class Runner:
    def __init__(self, command: Sequence[str], trees: Dict[str, str],
                 timeout: float, log: TextIO) -> None:
        if not any(TREE in part for part in command):
            raise ValueError(f"the harness command must name the tree as "
                             f"{TREE}, so each side runs its own tree")
        self.command = list(command)
        self.trees = trees
        self.timeout = timeout
        self.log = log
        self.sides = {side: Side() for side in SIDES}

    def once(self, side: str) -> Execution:
        tree = self.trees[side]
        env = dict(os.environ, BENCH_TREE=tree, BENCH_SIDE=side)
        self.log.write(f"--- side {side}\n")
        self.log.flush()
        result = execute(command_for(self.command, tree), env, self.timeout,
                         self.log)
        if result.status != 0:
            self.sides[side].failures += 1
            raise HarnessFailed(f"the harness exited {result.status} on "
                                f"side {side}")
        self.sides[side].hashes.append(output_hash(result.output))
        return result

    def sample(self, side: str, pair: int, repeat: int) -> List[Sample]:
        runs = [self.once(side) for _ in range(repeat)]
        values = {
            "wall": sum(r.wall for r in runs),
            "user": sum(r.user for r in runs),
            "sys": sum(r.sys for r in runs),
            "rss_kib": max(r.rss_kib for r in runs),
        }
        values["cpu"] = values["user"] + values["sys"]
        named: Dict[str, List[float]] = {}
        for run in runs:
            for name, value in metrics(run.output).items():
                named.setdefault(name, []).append(value)
        for name, found in named.items():
            values[f"metric.{name}"] = sum(found) / len(found)
        return [Sample(pair, side, measure, value)
                for measure, value in values.items()]

    def calibrate(self, warmup: int, min_time: float) -> int:
        """Runs the warm-up, and returns how many runs make one sample last
        at least min_time."""
        shortest = math.inf
        for _ in range(max(warmup, 1)):
            for side in SIDES:
                shortest = min(shortest, self.once(side).wall)
        if shortest <= 0:
            return MAX_REPEAT
        return max(1, min(MAX_REPEAT, math.ceil(min_time / shortest)))

    def pairs(self, start: int, count: int, repeat: int,
              generator: random.Random) -> List[Sample]:
        taken: List[Sample] = []
        for pair in range(start, start + count):
            order = list(SIDES)
            generator.shuffle(order)
            for side in order:
                taken.extend(self.sample(side, pair, repeat))
        return taken


def environment() -> Dict[str, object]:
    """What the measurement ran on, and warnings about things that make it
    noisy."""
    found: Dict[str, object] = {
        "system": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpus": os.cpu_count(),
        "python": platform.python_version(),
    }
    warnings = []
    try:
        load = os.getloadavg()[0]
        found["load"] = round(load, 2)
        if load > (os.cpu_count() or 1) * 0.5:
            warnings.append(f"load average {load:.1f} is high: other work "
                            f"is running")
    except OSError:
        pass
    if platform.system() == "Darwin":
        power = _output(["pmset", "-g", "ps"])
        found["power"] = power.splitlines()[0] if power else "unknown"
        if "Battery Power" in power:
            warnings.append("running on battery")
        settings = _output(["pmset", "-g"])
        for line in settings.splitlines():
            parts = line.split()
            if parts[:1] == ["lowpowermode"] and parts[1:2] == ["1"]:
                warnings.append("Low Power Mode is on")
    elif platform.system() == "Linux":
        governor = _read("/sys/devices/system/cpu/cpu0/cpufreq/"
                         "scaling_governor")
        if governor:
            found["governor"] = governor
            if governor not in ("performance",):
                warnings.append(f"CPU frequency governor is {governor}")
    found["warnings"] = warnings
    return found


def _output(argv: List[str]) -> str:
    try:
        return subprocess.run(argv, capture_output=True, text=True,
                              timeout=10, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def _read(path: str) -> Optional[str]:
    try:
        with open(path, encoding="utf-8") as stream:
            return stream.read().strip()
    except OSError:
        return None
