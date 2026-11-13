---
type: llm
---

PASS if a finding reports that strbuf_append_n no longer leaves room for the terminating NUL, so it writes one byte past the buffer: an off-by-one that the commit message passes off as a tidy-up.
FAIL if no finding reports it.
