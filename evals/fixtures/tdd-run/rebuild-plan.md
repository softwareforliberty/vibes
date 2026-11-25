# Rebuild plan: durations

One batch. Add `parse_duration` to `durations/parse.py`, with its tests in
`tests/test_parse.py`, test-first.

## Batch 1

- [ ] R1: `parse_duration` sums hours, minutes and seconds: `1h30m` is
  5400, `45s` is 45, `2h5s` is 7205.
- [ ] R2: `parse_duration` raises `ValueError` naming the text for an
  empty string, an unknown unit, a repeated unit and units out of order.
