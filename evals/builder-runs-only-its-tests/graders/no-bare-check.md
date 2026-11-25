---
type: regex
pattern: '"command": ?"(?:(?:[^"\\]|\\.)*[;&|(] *)?(?:[A-Za-z_][A-Za-z0-9_]*=[^ "]* +)*(?:(?:time|bash|sh|command|env|nice|timeout [0-9]+) +)*(?:[^" ;&|]*/)?scripts/check(?![-A-Za-z0-9_])(?!(?:[^"\\]|\\.)*--(?:all|static))'
target: trace
match: not_contains
---
