---
type: llm
---

PASS if a finding reports SQL injection in `find_low_stock` in src/stock/repository.py, because `name_contains` (and the other values) are formatted into the SQL instead of passed as parameters.
FAIL if no finding reports it.
