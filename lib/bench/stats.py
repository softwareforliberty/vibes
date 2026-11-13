"""Medians and bootstrap confidence intervals of the ratio between two sides.

A ratio below 1 means side b used less than side a: for time, that b is
faster. Paired samples, taken in alternating pairs, give the ratio of each
pair; unpaired ones, such as another tool's samples, the ratio of medians.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence

RESAMPLES = 10_000
SEED = 1


@dataclass(frozen=True)
class Interval:
    """A median ratio of b to a, and its 95% confidence interval."""

    ratio: float
    low: float
    high: float
    count: int

    @property
    def half_width(self) -> float:
        return (self.high - self.low) / 2


def median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("no samples")
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def _percentile(ordered: Sequence[float], fraction: float) -> float:
    position = fraction * (len(ordered) - 1)
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position
                                                                 - lower)


def _ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        raise ValueError("a sample of zero or less can't be compared")
    return numerator / denominator


def paired(a: Sequence[float], b: Sequence[float],
           resamples: int = RESAMPLES, seed: int = SEED) -> Interval:
    """The median of the pairs' ratios b/a, with a bootstrap interval."""
    if len(a) != len(b):
        raise ValueError("paired samples need the same number on each side")
    ratios = [_ratio(y, x) for x, y in zip(a, b)]
    generator = random.Random(seed)
    count = len(ratios)
    estimates = sorted(
        median([ratios[generator.randrange(count)] for _ in range(count)])
        for _ in range(resamples))
    return Interval(median(ratios), _percentile(estimates, 0.025),
                    _percentile(estimates, 0.975), count)


def unpaired(a: Sequence[float], b: Sequence[float],
             resamples: int = RESAMPLES, seed: int = SEED) -> Interval:
    """The ratio of the medians b/a, with a bootstrap interval."""
    if not a or not b:
        raise ValueError("no samples")
    generator = random.Random(seed)

    def resample(values: Sequence[float]) -> List[float]:
        return [values[generator.randrange(len(values))] for _ in values]

    estimates = sorted(_ratio(median(resample(b)), median(resample(a)))
                       for _ in range(resamples))
    return Interval(_ratio(median(b), median(a)),
                    _percentile(estimates, 0.025),
                    _percentile(estimates, 0.975), min(len(a), len(b)))
