"""capacity's commands: how many vibes builders this machine can run at
once for this project, measured and cached.

    capacity measure --cache <file> --as single|pair --tree <dir> [--tree <dir>] -- <command>
    capacity decide --cache <file>
    capacity check --cache <file>
    capacity lower --cache <file> --to <n> --reason <text>

Run each from the repository's root. A builder's cost is roughly one run of
the project's gate, scripts/check, so `measure` runs a command in one
worktree, or in two at once, sampling every second the memory of its
processes and of any Docker containers it starts, and records the wall
time, the CPU time and the peaks in the cache. `decide` works out how many
builders fit: what memory and CPU allow, never more than 4, and 1 when two
at once ran little faster than one after the other. `check` prints
`BUILDERS <n>` from the cache, lowered to what's free now, or
`MEASURE: <why>` when the cache is missing or stale: the machine, the
project's gate or the project's size changed, or it's over 30 days old.
`lower` records a lower number, such as after a builder ran out of memory.

Exits 0, 3 when `check` says to measure, and 2 on an error.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Sequence, Tuple

CEILING = 4
HEADROOM = 0.75  # of the memory a pool has, the share builders may use
MAX_AGE_DAYS = 30
GROWTH = 0.25  # how much the project may grow before measuring again
INTERVAL = 1.0
NEED_MEASURE = 3
UNITS = {"b": 1, "kb": 1000, "kib": 1024, "mb": 1000 ** 2, "mib": 1024 ** 2,
         "gb": 1000 ** 3, "gib": 1024 ** 3, "tb": 1000 ** 4, "tib": 1024 ** 4}


def _run(*args: str) -> Optional[str]:
    """A command's output, or None when it fails or isn't installed."""
    try:
        done = subprocess.run(args, capture_output=True, text=True,
                              timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout if done.returncode == 0 else None


def size(text: str) -> int:
    """Bytes in a size such as `12.5MiB` or `1.2GB`."""
    match = re.match(r"\s*([\d.]+)\s*([A-Za-z]*)", text)
    if not match:
        return 0
    return int(float(match.group(1)) * UNITS.get(match.group(2).lower(), 1))


def docker_info() -> Optional[Dict[str, int]]:
    """The CPUs and memory Docker's engine has, when it's running."""
    out = _run("docker", "info", "--format", "{{.NCPU}} {{.MemTotal}}")
    if not out or len(out.split()) != 2:
        return None
    cpus, memory = out.split()
    return {"cpus": int(cpus), "memory": int(memory)}


def machine() -> Dict[str, Any]:
    """What this machine has, and has free now."""
    total = free = 0
    if sys.platform == "darwin":
        total = int(_run("sysctl", "-n", "hw.memsize") or 0)
        vm = _run("vm_stat") or ""
        page = int((re.search(r"page size of (\d+)", vm) or [0, 4096])[1])
        pages = sum(int(n) for n in re.findall(
            r"Pages (?:free|inactive|speculative):\s+(\d+)", vm))
        free = pages * page
    else:
        try:
            with open("/proc/meminfo", encoding="utf-8") as stream:
                info = dict(line.split(":", 1) for line in stream)
            total = size(info["MemTotal"].strip().replace(" kB", "KiB"))
            free = size(info["MemAvailable"].strip().replace(" kB", "KiB"))
        except (OSError, KeyError, ValueError):
            pass
    return {"os": f"{platform.system()} {platform.machine()}",
            "cpus": os.cpu_count() or 1, "memory": total, "free": free,
            "disk_free": shutil.disk_usage(".").free,
            "docker": docker_info()}


def fingerprint(info: Dict[str, Any]) -> Dict[str, Any]:
    """The parts of the machine that change what fits."""
    return {"os": info["os"], "cpus": info["cpus"], "memory": info["memory"],
            "docker": info["docker"]}


def project() -> Dict[str, Any]:
    """The project's gate and size."""
    try:
        with open("scripts/check", "rb") as stream:
            gate = hashlib.sha256(stream.read()).hexdigest()[:16]
    except OSError:
        gate = ""
    files = [f for f in (_run("git", "ls-files", "-z") or "").split("\0") if f]
    total = sum(os.path.getsize(f) for f in files if os.path.isfile(f))
    return {"gate": gate, "files": len(files), "bytes": total}


def tree_memory(roots: List[int]) -> int:
    """The memory, in bytes, of the processes under each root."""
    out = _run("ps", "-A", "-o", "pid=,ppid=,rss=") or ""
    children: Dict[int, List[int]] = {}
    rss: Dict[int, int] = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            pid, ppid, kib = map(int, parts)
            children.setdefault(ppid, []).append(pid)
            rss[pid] = kib * 1024
    total, seen, todo = 0, set(), list(roots)
    while todo:
        pid = todo.pop()
        if pid in seen:
            continue
        seen.add(pid)
        total += rss.get(pid, 0)
        todo.extend(children.get(pid, []))
    return total


def docker_stats() -> Dict[str, Tuple[float, int]]:
    """Each running container's CPU percentage and memory."""
    out = _run("docker", "stats", "--no-stream", "--format",
               "{{.ID}}\t{{.CPUPerc}}\t{{.MemUsage}}") or ""
    stats: Dict[str, Tuple[float, int]] = {}
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) == 3:
            cpu = float(parts[1].rstrip("%") or 0)
            stats[parts[0]] = (cpu, size(parts[2].split("/")[0]))
    return stats


def measure(trees: List[str], command: List[str]) -> Dict[str, Any]:
    """Runs the command in each tree at once, sampling as it runs."""
    use_docker = docker_info() is not None
    before = set(docker_stats()) if use_docker else set()
    peaks = {"memory": 0, "docker_memory": 0}
    docker_cpu = [0.0]
    done = threading.Event()

    def sample_processes(pids: List[int]) -> None:
        while not done.wait(INTERVAL):
            peaks["memory"] = max(peaks["memory"], tree_memory(pids))

    def sample_docker() -> None:
        last = time.monotonic()
        while not done.is_set():
            stats = {k: v for k, v in docker_stats().items()
                     if k not in before}
            now = time.monotonic()
            docker_cpu[0] += sum(c for c, _ in stats.values()) / 100 * (
                now - last)
            last = now
            peaks["docker_memory"] = max(peaks["docker_memory"],
                                         sum(m for _, m in stats.values()))
            done.wait(INTERVAL)

    start = time.monotonic()
    procs = [subprocess.Popen(command, cwd=tree, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL) for tree in trees]
    threads = [threading.Thread(target=sample_processes,
                                args=([p.pid for p in procs],), daemon=True)]
    if use_docker:
        threads.append(threading.Thread(target=sample_docker, daemon=True))
    for thread in threads:
        thread.start()
    runs = []
    for tree, proc in zip(trees, procs):
        _, status, usage = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status) \
            if hasattr(os, "waitstatus_to_exitcode") else status >> 8
        runs.append({"tree": tree, "exit": proc.returncode,
                     "wall": round(time.monotonic() - start, 2),
                     "cpu": round(usage.ru_utime + usage.ru_stime, 2)})
    done.set()
    for thread in threads:
        thread.join(timeout=10)
    return {"runs": runs, "memory": peaks["memory"],
            "docker_memory": peaks["docker_memory"],
            "docker_cpu": round(docker_cpu[0], 2)}


def decide(cache: Dict[str, Any]) -> Tuple[int, List[str]]:
    """How many builders fit, and why."""
    single = cache.get("single")
    if not single:
        return 1, ["not measured yet"]
    info = cache["machine"]
    wall = max(single["runs"][0]["wall"], 0.01)
    limits: List[Tuple[int, str]] = [
        (CEILING, f"the ceiling of {CEILING}")]
    if single["memory"]:
        limits.append((math.floor(info["memory"] * HEADROOM
                                  / single["memory"]), "memory"))
    host_cores = single["runs"][0]["cpu"] / wall
    if host_cores >= 0.5:
        limits.append((math.floor(info["cpus"] / host_cores), "CPU"))
    docker = info.get("docker")
    if docker and single.get("docker_memory"):
        limits.append((math.floor(docker["memory"] * HEADROOM
                                  / single["docker_memory"]),
                       "Docker's memory"))
    docker_cores = single.get("docker_cpu", 0) / wall
    if docker and docker_cores >= 0.5:
        limits.append((math.floor(docker["cpus"] / docker_cores),
                       "Docker's CPUs"))
    builders, why = min(limits)
    builders = max(1, builders)
    reasons = [f"{name} allows {n}" for n, name in limits]
    pair = cache.get("pair")
    if pair:
        speedup = 2 * wall / max(max(r["wall"] for r in pair["runs"]), 0.01)
        reasons.append(f"two at once ran {speedup:.2f} times as fast as "
                       "one after the other")
        if speedup < 1.2:
            builders = 1
        elif speedup < 1.5:
            builders = min(builders, 2)
    lowered = cache.get("lowered")
    if lowered:
        builders = min(builders, lowered["to"])
        reasons.append(f"lowered to {lowered['to']}: {lowered['reason']}")
    reasons.insert(0, f"{builders} builders; limited by {why}" if builders > 1
                   else "1 builder")
    return builders, reasons


def stale(cache: Dict[str, Any], info: Dict[str, Any],
          now: Dict[str, Any]) -> Optional[str]:
    """Why the cache must be measured again, or None."""
    if "builders" not in cache or not cache.get("pair"):
        return "not measured yet"
    if cache.get("fingerprint") != fingerprint(info):
        return "the machine changed"
    then = cache["project"]
    if then["gate"] != now["gate"]:
        return "scripts/check changed"
    for key in ("files", "bytes"):
        if then[key] and now[key] > then[key] * (1 + GROWTH):
            return f"the project grew: {key} up from {then[key]} to {now[key]}"
    measured = datetime.datetime.fromisoformat(cache["measured_at"])
    if (datetime.datetime.now(datetime.timezone.utc) - measured).days \
            > MAX_AGE_DAYS:
        return f"it was measured over {MAX_AGE_DAYS} days ago"
    return None


def _load(path: str) -> Dict[str, Any]:
    try:
        with open(path, encoding="utf-8") as stream:
            return json.load(stream)
    except FileNotFoundError:
        return {}


def _save(path: str, cache: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(cache, stream, indent=2)
        stream.write("\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = list(argv or [])
    command: List[str] = []
    if "--" in args:
        command = args[args.index("--") + 1:]
        args = args[:args.index("--")]
    parser = argparse.ArgumentParser(prog="capacity")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("measure", "decide", "check", "lower"):
        sub = commands.add_parser(name)
        sub.add_argument("--cache", required=True)
        if name == "measure":
            sub.add_argument("--as", dest="kind", required=True,
                             choices=("single", "pair"))
            sub.add_argument("--tree", action="append", required=True)
        if name == "lower":
            sub.add_argument("--to", type=int, required=True)
            sub.add_argument("--reason", required=True)
    try:
        options = parser.parse_args(args)
    except SystemExit:
        return 2
    try:
        cache = _load(options.cache)
    except (OSError, ValueError) as error:
        print(f"capacity: {error}", file=sys.stderr)
        return 2
    if options.command == "measure":
        trees = options.tree
        if not command or len(trees) != (1 if options.kind == "single" else 2):
            print("capacity: give a command, and one tree for single or "
                  "two for pair", file=sys.stderr)
            return 2
        if any(not os.path.isdir(tree) for tree in trees):
            print("capacity: no such tree", file=sys.stderr)
            return 2
        info = machine()
        result = measure(trees, command)
        cache.update({"machine": info, "fingerprint": fingerprint(info),
                      "project": project(), options.kind: result,
                      "measured_at": datetime.datetime.now(
                          datetime.timezone.utc).isoformat(
                              timespec="seconds")})
        cache.pop("lowered", None)
        _save(options.cache, cache)
        walls = ", ".join(f"{r['wall']}s exit {r['exit']}"
                          for r in result["runs"])
        print(f"MEASURED {options.kind}: {walls}; memory "
              f"{result['memory'] // 2 ** 20} MiB, Docker "
              f"{result['docker_memory'] // 2 ** 20} MiB")
        return 0
    if options.command == "decide":
        if not cache.get("single"):
            print("capacity: measure a single run first", file=sys.stderr)
            return 2
        builders, reasons = decide(cache)
        cache["builders"] = builders
        _save(options.cache, cache)
        print(f"BUILDERS {builders}")
        for reason in reasons:
            print(f"- {reason}")
        return 0
    if options.command == "lower":
        cache["lowered"] = {"to": max(1, options.to),
                            "reason": options.reason}
        cache["builders"] = min(cache.get("builders", 1), max(1, options.to))
        _save(options.cache, cache)
        print(f"BUILDERS {cache['builders']}")
        return 0
    info = machine()
    why = stale(cache, info, project()) if cache else "not measured yet"
    if why:
        print(f"MEASURE: {why}")
        return NEED_MEASURE
    builders = cache["builders"]
    per_builder = cache["single"]["memory"]
    now = builders
    if per_builder and info["free"]:
        now = max(1, min(builders, math.floor(info["free"] * 0.9
                                              / per_builder)))
    print(f"BUILDERS {builders}" + (f", {now} now: memory is in use"
                                    if now < builders else ""))
    return 0
