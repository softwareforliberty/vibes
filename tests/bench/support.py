"""Shared set-up for bench's tests: lib/ on the path, and measurement
directories written from made-up samples."""

from __future__ import annotations

import os
import sys
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "lib"))
BENCH = os.path.join(ROOT, "bin", "bench")

from bench import samples  # noqa: E402
from bench.samples import Sample  # noqa: E402


def measurement(directory: str, a: List[float], b: List[float],
                measure: str = "wall", broken: Optional[List[str]] = None,
                extra: Optional[Dict[str, List[List[float]]]] = None) -> str:
    """Writes a paired measurement of a against b."""
    taken = []
    for pair, (x, y) in enumerate(zip(a, b)):
        taken += [Sample(pair, "a", measure, x), Sample(pair, "b", measure, y)]
    for name, (xs, ys) in (extra or {}).items():
        for pair, (x, y) in enumerate(zip(xs, ys)):
            taken += [Sample(pair, "a", name, x), Sample(pair, "b", name, y)]
    os.makedirs(directory, exist_ok=True)
    samples.write_samples(directory, taken)
    samples.write_json(directory, samples.RUN,
                       {"paired": True, "broken": broken or []})
    return directory
