# SQLite Tools

The free/open source tools that lint, format and check SQLite code, and how
to run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [SQLFluff](https://sqlfluff.com/) | MIT | Formatting, Linting | Linting and auto-formatting SQL |
| [SQLite shell](https://sqlite.org/cli.html) | Public domain | Linting, Auditing | Checking the migrated schema with SQLite's own checks |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

These files are in this directory, ready to copy to the root of a project:

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Editors and IDEs |
| [.sqlfluff](.sqlfluff) | SQLFluff |
| [checks/schema.sql](checks/schema.sql) | The SQLite shell, for the schema checks |
| [.jscpd.json](.jscpd.json) | jscpd |

## Configuration

Put this [.sqlfluff](.sqlfluff) file at the root of the project. It sets
every rule in this guide that SQLFluff can check:

```ini
[sqlfluff]
dialect = sqlite
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

SQLFluff can't tell built-in functions from your own, so the configuration
skips function names written in lowercase with an underscore, which is how
[your own functions](coding-style.md#case) are named. Review checks that
built-in functions with an underscore in their name, such as `ROW_NUMBER()`,
are uppercase.

## Schema checks

SQLite can check a schema itself, which catches problems SQLFluff can't see.
In CI, apply the migrations to an empty database, then run these checks
against it. Put them in [checks/schema.sql](checks/schema.sql):

```sql
PRAGMA integrity_check;
PRAGMA foreign_key_check;

SELECT name AS non_strict_table
FROM pragma_table_list
WHERE
    schema = 'main'
    AND type = 'table'
    AND strict = 0
    AND name NOT LIKE 'sqlite_%';
```

`integrity_check` prints `ok` for a sound database, and the other two print
nothing when there's nothing wrong. The last query lists every table that
isn't [`STRICT`](idioms.md#data-types). Fail the build on any other output:

```sh
test "$(sqlite3 build/check.db < checks/schema.sql)" = "ok"
```

## Auditing

### Security analysis

No maintained FOSS tool runs security analysis on plain SQL files. SQL
injection happens where application code builds SQL strings, so
[pass values as parameters](idioms.md#security), and scan the application
code with its own language's security tools. For database files that come
from outside, follow the [untrusted-file rules](idioms.md#security).

### Dependency vulnerabilities

SQLite has no package manager, so there are no third-party dependencies
to audit. The SQLite library itself is a dependency of the application, so
audit and update it with the application's own tools.

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

No maintained FOSS tool unit-tests SQL inside SQLite or measures its
coverage. Test queries, triggers and migrations from the application's test
suite, against the SQLite version you ship.
