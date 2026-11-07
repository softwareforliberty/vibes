---
type: llm
---

PASS if the findings report at least two of these three: `name_contains` is no longer keyword-only; `typing.Optional` is used instead of `str | None`; and the public `export_low_stock_csv` has no docstring.
FAIL if no finding reports it.
