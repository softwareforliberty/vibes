# Spec: durations

## Summary

People type how long a task took, such as `1h30m`. `parse_duration` reads
such a duration as a number of seconds, so the report can add them up.

## Requirements

- **R1:** `parse_duration(text)` returns the seconds in `text`, which is
  one or more of a whole number of hours (`h`), minutes (`m`) and seconds
  (`s`), in that order, each at most once, such as `1h30m` (5400), `45s`
  (45) or `2h5s` (7205).
- **R2:** Any other text, such as an empty string, an unknown unit (`3d`),
  a repeated unit (`1m2m`) or units out of order (`5s1m`), raises
  `ValueError` naming the text.
