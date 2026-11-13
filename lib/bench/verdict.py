"""Decides whether side b is better than side a, beyond the noise.

The noise floor is the half-width of the interval an A/A run measured, the
same tree on both sides. A change counts only when its whole interval is on
one side of no change, and its size is at least the minimum effect: twice
the noise floor, and never less than the floor given, 2% by default.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from . import samples, stats

FLOOR = 0.02
IMPROVED = "IMPROVED"
REGRESSED = "REGRESSED"
NO_CHANGE = "NO CHANGE"
INCONCLUSIVE = "INCONCLUSIVE"
BROKEN = "BROKEN"


@dataclass(frozen=True)
class Verdict:
    word: str
    line: str
    data: Dict[str, object]


def interval(directory: str, measure: str) -> stats.Interval:
    """The interval of b against a for one measure of a measurement."""
    run = samples.read_json(directory, samples.RUN)
    taken = samples.read_samples(directory)
    if run.get("paired", True):
        table = samples.by_measure(taken)
        if measure not in table:
            raise ValueError(f"no {measure} samples in {directory}")
        a, b = table[measure]
        return stats.paired(a, b)
    a, b = samples.unpaired_measure(taken, measure)
    if not a or not b:
        raise ValueError(f"no {measure} samples in {directory}")
    return stats.unpaired(a, b)


def measures(directory: str) -> List[str]:
    return sorted({s.measure for s in samples.read_samples(directory)})


def noise(directory: Optional[str], measure: str) -> Optional[float]:
    if not directory:
        return None
    return interval(directory, measure).half_width


def min_effect(noise_floor: Optional[float], floor: float = FLOOR) -> float:
    return max(floor, 2 * noise_floor) if noise_floor is not None else floor


def oriented(found: stats.Interval, higher_is_better: bool) -> stats.Interval:
    """The interval with lower always better, so a throughput measure reads
    the same way as a time."""
    if not higher_is_better:
        return found
    return stats.Interval(1 / found.ratio, 1 / found.high, 1 / found.low,
                          found.count)


def broken(directory: str) -> List[str]:
    """Why side b is broken, from the run and the project's tests."""
    run = samples.read_json(directory, samples.RUN)
    reasons = [str(reason) for reason in run.get("broken", [])]
    try:
        tests = samples.read_json(directory, samples.TESTS)
    except FileNotFoundError:
        tests = {}
    if tests and not tests.get("passed"):
        reasons.append(f"the project's tests failed on side b (exit "
                       f"{tests.get('status')}; see tests.log)")
    return reasons


def percent(ratio: float) -> str:
    return f"{(ratio - 1) * 100:+.1f}%"


def decide(directory: str, noise_directory: Optional[str] = None,
           measure: str = "wall", higher_is_better: bool = False,
           guards: Optional[Dict[str, float]] = None,
           floor: float = FLOOR) -> Verdict:
    reasons = broken(directory)
    if reasons:
        return Verdict(BROKEN, f"{BROKEN}: {'; '.join(reasons)}",
                       {"verdict": BROKEN, "reasons": reasons})
    found = oriented(interval(directory, measure), higher_is_better)
    floor_found = noise(noise_directory, measure)
    effect = min_effect(floor_found, floor)
    if found.high < 1 and 1 - found.ratio >= effect:
        word = IMPROVED
    elif found.low > 1 and found.ratio - 1 >= effect:
        word = REGRESSED
    elif found.half_width > effect:
        word = INCONCLUSIVE
    else:
        word = NO_CHANGE
    direction = " (higher is better, shown as lower)" if higher_is_better \
        else ""
    noise_text = (f"noise ±{floor_found * 100:.1f}%" if floor_found
                  is not None else "noise unknown: no A/A run")
    guard_text, failed = _guards(directory, guards or {})
    line = (f"{word} {measure} {percent(found.ratio)} (95% CI "
            f"{percent(found.low)} to {percent(found.high)}){direction}, "
            f"{found.count} pairs; {noise_text}, min effect "
            f"{effect * 100:.1f}%; {guard_text}")
    return Verdict(word, line, {
        "verdict": word, "measure": measure, "ratio": found.ratio,
        "low": found.low, "high": found.high, "count": found.count,
        "noise": floor_found, "min_effect": effect,
        "guards_failed": failed})


def _guards(directory: str, guards: Dict[str, float]):
    """Each guard is a measure that may grow by at most its limit, such as
    rss_kib by 10%. One fails when it grew by more than its limit, and the
    growth is beyond the noise."""
    if not guards:
        return "no guards", []
    failed = []
    for measure, limit in sorted(guards.items()):
        found = interval(directory, measure)
        if found.ratio > 1 + limit and found.low > 1:
            failed.append(f"{measure} {percent(found.ratio)} is over its "
                          f"{limit * 100:.0f}% limit")
    if failed:
        return f"GUARD FAILED: {'; '.join(failed)}", failed
    return "guards ok", failed
