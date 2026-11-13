---
type: llm
---

PASS if a finding reports bidirectional control characters in src/strbuf.c, which make the length check look active while it is inside a comment (Trojan Source).
FAIL if no finding reports it.
