---
type: llm
---

PASS if a finding reports that `export_low_stock_csv` in src/stock/report.py leaves the file open when writing raises, because it calls `close()` itself instead of using `with`.
FAIL if no finding reports it.
