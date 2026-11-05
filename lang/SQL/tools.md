# SQL Tools

The free/open source tools that lint, format and check SQL code, and how to run
them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [SQLFluff](https://sqlfluff.com/) | MIT | Formatting, Linting | Linting and auto-formatting SQL |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Configuration

Put this `.sqlfluff` file at the root of the project. It sets every rule in
this guide that SQLFluff can check:

```ini
[sqlfluff]
dialect = ansi
max_line_length = 80

[sqlfluff:indentation]
indent_unit = space
tab_space_size = 4

[sqlfluff:rules:capitalisation.keywords]
capitalisation_policy = upper

[sqlfluff:rules:capitalisation.identifiers]
extended_capitalisation_policy = lower

[sqlfluff:rules:capitalisation.functions]
extended_capitalisation_policy = upper
ignore_words_regex = ^[a-z][a-z0-9]*(_[a-z0-9]+)+$

[sqlfluff:rules:capitalisation.literals]
capitalisation_policy = upper

[sqlfluff:rules:capitalisation.types]
extended_capitalisation_policy = upper

[sqlfluff:rules:aliasing.table]
aliasing = explicit

[sqlfluff:rules:aliasing.column]
aliasing = explicit

[sqlfluff:rules:ambiguous.join]
fully_qualify_join_types = inner

[sqlfluff:rules:ambiguous.column_references]
group_by_and_order_by_style = explicit

[sqlfluff:rules:convention.not_equal]
preferred_not_equal_style = ansi

[sqlfluff:rules:convention.casting_style]
preferred_type_casting_style = cast

[sqlfluff:rules:convention.terminator]
require_final_semicolon = True

[sqlfluff:rules:references.quoting]
prefer_quoted_identifiers = False

[sqlfluff:rules:structure.subquery]
forbid_subquery_in = both
```

SQLFluff's `ansi` dialect doesn't parse every ISO feature (identity
columns, for example). When your SQL only ever runs on one engine, set
`dialect` to that engine instead.

## Running it

```sh
sqlfluff lint .   # report violations
sqlfluff fix .    # fix what can be fixed automatically
```

Code must pass `sqlfluff lint` with **no violations**. A rule with no
SQLFluff equivalent is checked in review.

SQLFluff can't tell built-in functions from your own, so the configuration
skips function names written in lowercase with an underscore, which is how
[your own functions](coding-style.md#case) are named. Review checks that built-in functions
with an underscore in their name, such as `ROW_NUMBER()`, are uppercase.

## Auditing

### Security analysis

No maintained FOSS tool runs security analysis on plain SQL files. SQL
injection happens where application code builds SQL strings, so
[pass values as parameters](idioms.md#security), and scan the application
code with its own language's security tools.

### Dependency vulnerabilities

SQL has no package manager, so there are no third-party dependencies
to audit.

### Secrets

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Complexity

No maintained FOSS tool measures the complexity of SQL queries. SQLFluff's
structure rules catch some of it, such as the subqueries the configuration
above forbids in `FROM` and `JOIN` clauses. Review checks the rest.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format sql --min-tokens 50 --exitCode 1 .
```

### Coverage

No FOSS tool measures test coverage of portable SQL, and no test framework
runs on every engine. Test each query and migration on the engine it will run
on, with that engine's own tools.
