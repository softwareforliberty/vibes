# Build: batch 1

## Entries

- **R2, R4 totals:** red run:
  `FAILED tests/test_totals.py::test_sums_each_sku_and_sorts_by_sku - ModuleNotFoundError: No module named 'reports.totals'`
- **R5 bad day:** red run:
  `FAILED tests/test_cli.py::test_rejects_a_malformed_day - ModuleNotFoundError: No module named 'reports.cli'`
- **R1, R3 file:** red run:
  `FAILED tests/test_cli.py::test_writes_the_days_file - AttributeError: module 'reports.cli' has no attribute 'main'`

## Rules proved

- `reports.totals` never imports the edges: an import of
  `reports.csv_output` in `reports/totals.py` failed with
  `reports.totals is not allowed to import reports.csv_output`.

## Slow tests

`scripts/check --all` passed at the last commit.
