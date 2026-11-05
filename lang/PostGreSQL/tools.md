# PostgreSQL Tools

The free/open source tools that lint, format and check PostgreSQL code, and how
to run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [SQLFluff](https://sqlfluff.com/) | MIT | Formatting, Linting | Linting and auto-formatting SQL |
| [Squawk](https://github.com/sbdchd/squawk) | Apache-2.0 | Linting | Checking migrations for changes that lock tables or break running code |
| [plpgsql_check](https://github.com/okbob/plpgsql_check) | MIT | Linting, Auditing, Code quality | Checking PL/pgSQL functions, and measuring their test coverage |
| [pgTAP](https://pgtap.org/) | PostgreSQL | Code quality | Unit-testing schemas, queries and functions |
| [pg_prove](https://metacpan.org/pod/pg_prove) | Artistic-1.0 or GPL-1.0+ | Code quality | Running pgTAP tests |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Configuration

Put this `.sqlfluff` file at the root of the project. It sets every rule in
this guide that SQLFluff can check:

```ini
[sqlfluff]
dialect = postgres
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
## Migration safety

Squawk checks migration files for changes that take long locks or break code
that's still running, the risks described in
[Migrations](idioms.md#migrations). Run it on every new migration, and fix
each warning before the migration ships:

```sh
squawk migrations/*.sql
```

## Function checks

PostgreSQL only checks a PL/pgSQL function body properly when the function
first runs. plpgsql_check checks it ahead of time, and reports references to
missing tables and columns, type mismatches and unused variables. Install it
in the test database, and check every function in CI:

```sql
CREATE EXTENSION plpgsql_check;

SELECT plpgsql_check_function('customer_merge(BIGINT, BIGINT)');
```

## Auditing

### Security analysis

No maintained FOSS tool runs security analysis on plain SQL files. SQL
injection happens where application code builds SQL strings, so
[pass values as parameters](idioms.md#security), and scan the application
code with its own language's security tools.

For PL/pgSQL functions, plpgsql_check's security warnings flag dynamic SQL
in `EXECUTE` statements that's open to injection:

```sql
SELECT plpgsql_check_function(
    'customer_merge(BIGINT, BIGINT)',
    security_warnings => TRUE
);
```

### Dependency vulnerabilities

PostgreSQL has no package manager, so there are no third-party dependencies
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

Write unit tests for the schema, queries and functions with pgTAP, and run
them against a test database with pg_prove. pg_prove exits with an error when
any test fails:

```sh
pg_prove -d app_test tests/*.sql
```

For PL/pgSQL functions, plpgsql_check also measures statement coverage. In
the test server's `postgresql.conf`, preload it and turn its profiler on, so
it keeps coverage data across the separate sessions pg_prove opens:

```ini
shared_preload_libraries = 'plpgsql_check'
plpgsql_check.profiler = on
```

After the tests, read each function's coverage:

```sql
SELECT plpgsql_coverage_statements('customer_merge(BIGINT, BIGINT)');
```
