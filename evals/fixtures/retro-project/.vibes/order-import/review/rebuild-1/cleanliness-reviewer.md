VERDICT: CHANGES REQUESTED

FINDINGS
- [MAJOR] invoices/importer.py:22: a debug `print(order)` is left in. Why: it writes to standard output on every call. Fix: remove it.
