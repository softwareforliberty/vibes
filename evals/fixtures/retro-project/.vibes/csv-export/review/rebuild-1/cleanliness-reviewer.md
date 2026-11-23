VERDICT: CHANGES REQUESTED

FINDINGS
- [MAJOR] invoices/export.py:14: a debug `print(rows)` is left in. Why: it writes to standard output on every call. Fix: remove it.
