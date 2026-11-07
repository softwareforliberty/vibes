---
type: llm
---

PASS if a finding reports that `find_low_stock` in src/stock/repository.py includes items whose quantity equals the threshold, because it compares with `<=` where the spec says below the threshold.
FAIL if no finding reports it.
