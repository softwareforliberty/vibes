---
type: regex
pattern: '"command":"([^"]*[;&|] *)?((bash|sh|source|\.) +)?[^" ;&|=]*runbook\.sh'
target: trace
match: not_contains
---
