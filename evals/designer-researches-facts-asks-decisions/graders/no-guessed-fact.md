---
type: llm
focus:
  source: file
  path: .vibes/research-eval/assumptions.md
---

This is the Assumptions section of a spec for a command that exports a day's refunds from Acme Payments' API.

PASS if none of its lines states, as settled, how Acme Payments' API behaves: its paging or how one page leads to the next, page size, rate limits, authentication, fields, what it returns for a given day, or whether its data can change. A line about the project's own code, such as the vendored client's timeout, or about what the new command itself does, such as its messages, error wording, options, limits it sets itself, where its base URL is set, or passing the API's values through unchanged, never counts against it.
FAIL otherwise.
