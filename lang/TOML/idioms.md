# TOML Idioms and Principles

How to write TOML well. [coding-style.md](coding-style.md) covers how TOML
looks. This guide covers how to structure it: the idioms that keep
configuration clear, typed and safe. Every example follows the style guide.

## Principles

- **TOML is configuration, not logic.** Keep files to plain values and
  structure. Once a file needs conditions, loops or computed values, generate
  it from code instead.
- **Keep it flat.** TOML reads best one or two levels deep. Deep nesting
  turns every value into a long chain of table headers.
- **Let the types do the work.** TOML has distinct strings, integers, floats,
  booleans and dates, and never guesses between them. Use the type that
  matches the value, so the program doesn't have to parse strings.
- **Validate on load.** Check every file against a schema before using it,
  so a typo fails loudly instead of silently becoming a default.

## Tables

TOML has three ways to write a group of values. Use each for what it does
best:

| Form | Use it for |
| --- | --- |
| Table header (`[server]`) | Any group of more than two values, or one that has its own sub-tables |
| Inline table (`owner = { name = "Platform team" }`) | A small group of values that fits on one line and is always read as one value |
| Dotted keys (`server.port = 8080`) | One or two values in a table that has no other reason to exist |

- **Define each table in one place.** TOML forbids defining a table twice,
  and spreading a table's keys across a file hides them.
- **Don't extend an inline table** later in the file. TOML forbids adding
  keys to an inline table after it's written, so a value that grows needs a
  real table.
- A table header names its full path (`[server.tls]`), so put sub-tables
  right after their parent. Readers then find related tables together.

## Arrays of tables

Use an **array of tables** (`[[...]]`) for a list of records with the same
shape:

```toml
[[listeners]]
name = "public"
port = 8080

[[listeners]]
name = "admin"
port = 9090
```

- Each `[[listeners]]` header starts a new record. It's the TOML equivalent
  of a list of objects.
- Use a plain array (`ports = [8080, 9090]`) for a list of single values.
- Give each record an identifying key such as `name`, so error messages and
  readers can point at a specific record.

## Dates and times

- **Write points in time as offset date-times in UTC**
  (`2026-01-01T09:30:00Z`). A time without an offset is ambiguous, because it
  means a different moment in every time zone.
- Use a **local date** (`2026-01-01`) for a calendar date with no time, such
  as a birthday or a release date.
- Avoid **local date-times** (`2026-01-01T09:30:00`, with no offset). Use one
  only for a wall-clock time that genuinely has no time zone, such as an alarm
  that goes off at 09:30 wherever the user is.
- Don't write dates as strings. TOML's date types are checked by the parser,
  so a malformed date fails to load instead of failing later.

## Numbers

- TOML integers are 64-bit, but programs and formats that use
  double-precision numbers (JavaScript, JSON in many parsers) lose precision
  above 2^53. **Write large identifiers as strings**, since they're names,
  not quantities.
- Don't use floats for money or other exact quantities. Use an integer in
  the smallest unit, and name the unit in the key: `price_cents = 1_999`.
- Name the unit of every quantity in its key (`timeout_seconds`,
  `size_bytes`), so the value can't be misread.

## Strings

- Prefer basic strings (`"..."`). Use literal strings (`'...'`) when the
  text contains backslashes or double quotes (see
  [Strings](coding-style.md#strings)).
- In a multi-line basic string, end a line with `\` to join it to the next
  line without a newline. Use it to wrap long prose that must be a single
  line.
- A multi-line string drops a newline that comes straight after the opening
  quotes, so the text can start on the next line.

## Schemas and validation

- **Write a schema for every TOML file your program reads.** A JSON Schema
  works for TOML, because a TOML document is a table of keys and values.
- Set `"additionalProperties": false`, so an unknown key, which is usually a
  typo, fails validation instead of being silently ignored.
- Validate in CI and in the program that loads the file. The CI check catches
  mistakes before a commit; the program must still refuse a bad file at run
  time.
- Give defaults in the program or the schema, not by copying them into every
  file. A file then only shows what it changes.

## Secrets

- **Keep secrets out of TOML files.** Configuration files are often committed
  and copied between environments. Load passwords, tokens and keys from the
  environment or a secret store instead.
- Name the environment variable in the file when a value comes from one, so
  a reader knows where it's set: `password_env = "DB_PASSWORD"`.

## Generating TOML

- Write TOML from code with a TOML library, never by joining strings. A
  library quotes and escapes every value correctly.
- Don't template TOML with a text template engine. A value containing a quote
  or a newline breaks the file, or changes what it means.

## Sources

- [TOML 1.0.0 specification](https://toml.io/en/v1.0.0)
- [JSON Schema](https://json-schema.org/)
