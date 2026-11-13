"""A measurement's files: its samples, and what was run to take them.

A measurement directory holds:

- samples.tsv: one sample per line, as pair, side (a or b), measure and
  value. The measures are wall, user, sys and cpu in seconds, rss_kib, and
  metric.<name> for each value the harness printed as `metric <name> <v>`.
- run.json: the command, the trees, whether the samples are paired, the
  output checks, the harness failures and the environment.
- tests.json, when bench tests ran the project's tests on side b.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

SAMPLES = "samples.tsv"
RUN = "run.json"
TESTS = "tests.json"
HEADER = "pair\tside\tmeasure\tvalue"


@dataclass(frozen=True)
class Sample:
    pair: int
    side: str
    measure: str
    value: float


def write_samples(directory: str, samples: List[Sample]) -> None:
    lines = [HEADER] + [f"{s.pair}\t{s.side}\t{s.measure}\t{s.value!r}"
                        for s in samples]
    _write(os.path.join(directory, SAMPLES), "\n".join(lines) + "\n")


def read_samples(directory: str) -> List[Sample]:
    path = os.path.join(directory, SAMPLES)
    samples = []
    with open(path, encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            line = line.rstrip("\n")
            if number == 1:
                if line != HEADER:
                    raise ValueError(f"{path} isn't a bench samples file")
                continue
            if not line:
                continue
            pair, side, measure, value = line.split("\t")
            samples.append(Sample(int(pair), side, measure, float(value)))
    return samples


def by_measure(samples: List[Sample]
               ) -> Dict[str, Tuple[List[float], List[float]]]:
    """Each measure's a and b values, in pair order. A measure missing from
    one side of a pair is left out of that pair."""
    table: Dict[str, Dict[int, Dict[str, float]]] = {}
    for sample in samples:
        table.setdefault(sample.measure, {}).setdefault(
            sample.pair, {})[sample.side] = sample.value
    result = {}
    for measure, pairs in table.items():
        a = [pairs[p]["a"] for p in sorted(pairs) if len(pairs[p]) == 2]
        b = [pairs[p]["b"] for p in sorted(pairs) if len(pairs[p]) == 2]
        result[measure] = (a, b)
    return result


def unpaired_measure(samples: List[Sample], measure: str
                     ) -> Tuple[List[float], List[float]]:
    a = [s.value for s in samples if s.measure == measure and s.side == "a"]
    b = [s.value for s in samples if s.measure == measure and s.side == "b"]
    return a, b


def write_json(directory: str, name: str, data: Dict[str, object]) -> None:
    _write(os.path.join(directory, name),
           json.dumps(data, indent=2, sort_keys=True) + "\n")


def read_json(directory: str, name: str) -> Dict[str, object]:
    with open(os.path.join(directory, name), encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"{name} in {directory} isn't a JSON object")
    return data


def read_values(spec: str) -> List[float]:
    """Samples from another tool: hyperfine's JSON, as FILE or FILE#N for
    its Nth result, or a file of one number per line."""
    path, _, index = spec.partition("#")
    with open(path, encoding="utf-8") as stream:
        text = stream.read()
    if text.lstrip().startswith("{"):
        results = json.loads(text).get("results")
        if not isinstance(results, list) or not results:
            raise ValueError(f"{path} has no hyperfine results")
        result = results[int(index or 0)]
        return [float(value) for value in result["times"]]
    if index:
        raise ValueError(f"{path} isn't JSON, so #{index} means nothing")
    values = [float(line) for line in text.split() if line]
    if not values:
        raise ValueError(f"{path} holds no samples")
    return values


def _write(path: str, text: str) -> None:
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8") as stream:
        stream.write(text)
    os.replace(temporary, path)
