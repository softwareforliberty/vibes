# MySQL Tools

The free/open source tools that lint, format and check MySQL code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [SQLFluff](https://sqlfluff.com/) | MIT | Formatting, Linting | Linting and auto-formatting SQL |
| [Skeema](https://www.skeema.io/) | Apache-2.0 | Linting | Linting table definitions against a MySQL server |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

These files are in this directory, ready to copy to the root of a project:

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Editors and IDEs |
| [.sqlfluff](.sqlfluff) | SQLFluff |
| [.jscpd.json](.jscpd.json) | jscpd |

## Configuration

Put this [.sqlfluff](.sqlfluff) file at the root of the project. It sets
every rule in this guide that SQLFluff can check:

```ini
[sqlfluff]
dialect = mysql
max_line_length = 80
templater = placeholder

[sqlfluff:templater:placeholder]
param_style = question_mark

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
case_sensitive = False

[sqlfluff:rules:structure.subquery]
forbid_subquery_in = both
```

## Running it

```sh
sqlfluff lint .   # report violations
sqlfluff fix .    # fix what can be fixed automatically
```

Code must pass `sqlfluff lint` with **no violations**. A rule with no
SQLFluff equivalent is checked in review.

The configuration reads `?` as a query parameter, the placeholder MySQL
uses, so files of [parameterised queries](idioms.md#security) parse.
SQLFluff lints each `?` as a number.

SQLFluff can't tell built-in functions from your own, so the configuration
skips function names written in lowercase with an underscore, which is how
[your own functions](coding-style.md#case) are named. Review checks that
built-in functions with an underscore in their name, such as `ROW_NUMBER()`,
are uppercase.
## Schema linting

Skeema lints table definitions by running them on a MySQL server, so it
catches problems that depend on how MySQL reads a definition, which SQLFluff
can't see. In CI, apply the migrations to an empty server, export the
resulting schema with `skeema init`, then lint it with the checks that match
[idioms.md](idioms.md):

```sh
skeema init -h 127.0.0.1 -u ci --dir schema
cd schema
skeema lint --lint-pk=error --lint-has-enum=error \
    --allow-engine=innodb --lint-engine=error \
    --allow-charset=utf8mb4 --lint-charset=error
```

## Auditing

### Security analysis

No maintained FOSS tool runs security analysis on plain SQL files. SQL
injection happens where application code builds SQL strings, so
[pass values as parameters](idioms.md#security), and scan the application
code with its own language's security tools.

### Dependency vulnerabilities

MySQL has no package manager, so there are no third-party dependencies
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

No maintained FOSS tool unit-tests SQL inside MySQL or measures its coverage.
Test queries, stored routines and migrations from the application's test
suite, against a real MySQL server of the version you deploy.
