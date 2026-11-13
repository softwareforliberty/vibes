# Baseline profile: dedupe

## Workload

`python3 -m contacts dedupe` on generated contact lists, as
`bench/workload.md` describes: small (3,000 rows), main (12,000 rows) and
holdout (8,000 rows). Commands: `bench/run <tree> <size>`.

## Environment

macOS 27.0.1, arm64, 10 CPUs, Python 3.15.2, on mains power.

## Tools

- cProfile and pstats (Python 3.15.2):
  `python3 -m cProfile -o profile/baseline/main.prof -m contacts dedupe bench/data/main.csv`
- Missing: py-spy needs sudo on macOS; pyinstrument isn't installed and
  would show the same picture with less overhead.

## Time

| Size | Wall | CPU | Peak memory |
| --- | --- | --- | --- |
| small | 0.09 s | 0.08 s | 14 MiB |
| main | 1.21 s | 1.19 s | 19 MiB |
| holdout | 0.55 s | 0.54 s | 17 MiB |

Four times the rows takes thirteen times as long: the work grows with the
square of the rows.

## Hot spots

| Rank | Function | File:line | Self % | Inclusive % | What it does |
| --- | --- | --- | --- | --- | --- |
| 1 | `_is_seen` | contacts/dedupe.py:22 | 91.8 | 91.8 | Scans the list of addresses seen so far, once per row |
| 2 | `dedupe` | contacts/dedupe.py:9 | 2.9 | 96.4 | The loop over the rows |
| 3 | `csv.DictReader.__next__` | csv.py | 2.1 | 2.6 | Reads the rows |
| 4 | `normalise` | contacts/dedupe.py:4 | 1.2 | 1.7 | Strips and lower-cases each address |
| 5 | `csv.DictWriter.writerows` | csv.py | 0.9 | 1.0 | Writes the kept rows |
| 6 | `header` | contacts/summary.py:13 | 0.0 | 0.0 | Not called by dedupe |

## The task's focus

The task names the dedupe command: it is 96.4% of the time.

## Notes

No I/O wait: CPU time is within 2% of wall time. Memory is flat.
