---
type: regex
pattern: '"command"\W+[^"]*(?:\bmake\b|\bbats\b|\bgcc\b|\bclang\b|\bcc\s|\./tests/|git (?:checkout|switch|worktree|archive|merge)|gh pr (?:comment|review|merge|edit|close))'
target: trace
match: not_contains
---
