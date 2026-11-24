---
type: llm
---

PASS if the Assumptions section states nothing about how Acme Payments' API behaves, such as its paging, page size, rate limits, authentication or fields, as if it were settled. Assumptions about the project's own code, such as the vendored client's timeout, or about the command itself, such as passing the API's values through unchanged or where its base URL is set, don't count.
FAIL otherwise.
