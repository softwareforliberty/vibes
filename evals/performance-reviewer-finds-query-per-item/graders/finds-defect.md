---
type: llm
---

PASS if a finding reports that `find_low_stock` in src/stock/repository.py runs one query per matching item (an N+1 query), because it loads each item with `self.get`.
FAIL if no finding reports it.
