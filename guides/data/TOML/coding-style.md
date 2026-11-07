# TOML Coding Style

A general-purpose style for TOML files. It builds on the
[TOML 1.0.0 specification](https://toml.io/en/v1.0.0) and the formatting that
[Taplo](https://taplo.tamasfe.dev/) can enforce (see [Sources](#sources)). It
covers TOML itself, not the schema of any one tool that reads it.

This guide covers how TOML looks. For how to structure TOML files (tables,
arrays of tables, dates, flat configuration and schema validation), see
[idioms.md](idioms.md).

The tools that check TOML code are listed in [tools.md](tools.md).

## Language baseline

Write **TOML 1.0.0**. TOML 1.1.0 adds multi-line inline tables, trailing
commas in inline tables, new string escapes and times without seconds, but
many parsers still read only 1.0. A file that uses none of those features
means the same thing to every parser.

## Files

- Name TOML files with the **`.toml`** extension.
- Encode files in **UTF-8**, which the specification requires, without a
  byte order mark.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

## Layout

### Indentation and line length

- Don't indent keys or table headers. Tables are defined by their headers,
  not by indentation, and flat files diff cleanly.
- Indent the items of a multi-line array with **2 spaces**.
- **80 columns** is the limit. An array that doesn't fit goes on several
  lines, one item per line, with a trailing comma after the last item:

  ```toml
  allowed_origins = [
    "https://app.example.com",
    "https://admin.example.com",
    "https://status.example.com",
  ]
  ```

### Blank lines

- Put one blank line before every table header, so each table stands apart.
- Use at most one blank line in a row anywhere else, to separate groups of
  related keys.

### Order

- Put a table's own keys before any of its sub-tables. A key written after a
  sub-table's header belongs to that sub-table, so misplaced keys silently
  change meaning.
- Put the root keys first, then each table in the order a reader needs them.
- Order keys for the reader: identity first (such as `name` or `id`), then the
  rest in logical groups. Don't sort alphabetically when that splits related
  keys apart.

## Keys

- Write keys as **bare keys** wherever they can be: letters, digits, `_` and
  `-` only.
- When you define the format, name keys in **`snake_case`**. When a consumer
  defines it, use the consumer's names exactly.
- Quote a key only when it can't be bare, for example a hostname used as a
  key. Use double quotes.
- Put one space on each side of `=`: `port = 8080`.
- Use dotted keys (`server.port = 8080`) only for one or two values, never as
  a replacement for a table. A table header shows the structure at a glance.

## Values

### Strings

- Write strings in **double quotes** (basic strings) by default.
- Use single quotes (literal strings) for a string that contains backslashes
  or double quotes, such as a Windows path or a regular expression, so it
  needs no escaping: `pattern = '\d+\.\d+'`.
- Use `"""` for multi-line text, and `'''` for multi-line text that contains
  backslashes.

### Numbers and booleans

- Write integers in decimal, and use `_` to group the digits of large
  numbers: `max_connections = 1_000`, `size_bytes = 104_857_600`.
- Write bit masks and other values that are naturally hexadecimal with `0x`:
  `mode = 0x1ff`.
- Write floats with digits on both sides of the decimal point: `0.5`, not
  `.5`, which TOML doesn't allow anyway.
- Write booleans only as `true` and `false`.

### Dates and times

- Write a point in time as an **offset date-time in UTC**:
  `started_at = 2026-01-01T09:30:00Z`.
- Write a calendar date as a local date: `birth_date = 2026-01-01`.
- Use a `T` between the date and the time, not a space, so the value reads
  the same as in other ISO 8601 data.

### Arrays and inline tables

- Keep an array to one type of value. Mixed arrays are valid TOML but surprise
  most readers and many programs.
- A short array stays on one line: `ports = [8080, 8443]`.
- Use an inline table only for a small group of values that fits on one line:
  `owner = { name = "Platform team", email = "platform@example.com" }`.
  Anything bigger becomes a table.

## Comments

- Start a comment with `#` followed by one space: `# Retry policy`.
- Put one space between a value and a trailing comment:
  `timeout = 30 # seconds`.
- Put a comment that sits on its own line directly above the key or table it
  describes.
- Comments explain **why** a value is what it is, not what the key already
  says. `# seconds` and `# matches the upstream default` are useful;
  `# the port` is not.
- Write a TODO as `# TODO: <issue link> - <what needs doing>`. The link gives
  the context and an owner.

## Generated and third-party files

Generated TOML and vendored third-party files keep their own format and are
excluded from the formatter, so regenerating or updating them stays a clean
replacement.

## Sources

This guide starts from the TOML specification and borrows from:

- [TOML 1.0.0 specification](https://toml.io/en/v1.0.0)
- [TOML releases](https://github.com/toml-lang/toml/releases)
- [Taplo formatter options](https://taplo.tamasfe.dev/configuration/formatter-options.html)
