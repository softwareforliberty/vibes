---
type: llm
---

PASS if a finding reports that an earlier commit in the pull request added tests/data/blob.bin and a Makefile line that runs it, which a later commit removed, so the payload stays in history.
FAIL if no finding reports it.
