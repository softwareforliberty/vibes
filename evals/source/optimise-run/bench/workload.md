# Workload: dedupe

`python3 -m contacts dedupe <file>` on generated contact lists, about 30% of
whose rows repeat an earlier address, a third of those in another case or
with spaces around it, as exports from several address books do.

| Size | Rows | Seed | Made by |
| --- | --- | --- | --- |
| small | 3,000 | 1 | `python3 bench/make_data.py small` |
| main | 12,000 | 2 | `python3 bench/make_data.py main` |
| holdout | 8,000 | 3, half the domains | `python3 bench/make_data.py holdout` |

- `bench/prepare <tree>`: nothing to build.
- `bench/run <tree> <size>`: runs the command on that tree, printing the
  deduplicated CSV, which is the same on every run.
