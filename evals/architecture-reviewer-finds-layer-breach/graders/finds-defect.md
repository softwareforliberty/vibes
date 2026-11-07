---
type: llm
---

PASS if a finding reports that `StockService.low_stock` in src/stock/service.py runs SQL itself, through the repository's private `_connection`, instead of going through the repository as the design says.
FAIL if no finding reports it.
