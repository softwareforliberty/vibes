# YAML Idioms and Principles

How to write YAML well. [coding-style.md](coding-style.md) covers how YAML
looks. This guide covers how to write YAML that every parser reads the way you
meant it. Every example follows the style guide.

## Principles

- **YAML is data, not logic.** Keep files to plain values and structure. Once
  a file needs conditions, loops or computed values, generate it from code
  instead.
- **Be explicit about types.** YAML guesses the type of every unquoted value.
  A file is only correct if every parser guesses the same way, so quote
  anything that could be guessed wrong.
- **Write for the oldest parser that will read it.** Many widely used parsers
  still follow YAML 1.1, whose guessing rules differ from YAML 1.2. A file
  must mean the same thing under both.
- **Validate on load.** Check every file against a schema before using it,
  so a typo fails loudly instead of silently becoming a default.

## Implicit typing traps

An unquoted value's type depends on the parser's schema. These are the
values that YAML 1.1 and YAML 1.2 parsers read differently, or that surprise
people under both:

| Written | YAML 1.1 reads it as | YAML 1.2 reads it as | Write instead |
| --- | --- | --- | --- |
| `no`, `yes`, `on`, `off`, `y`, `n` | Boolean | String | `"no"`, or `false` if a boolean is meant |
| `NO` (Norway's country code) | `false` | String | `"NO"` |
| `0755` | Octal number 493 | Decimal number 755 | `"0755"`, or the decimal value |
| `1.10` | Float 1.1 | Float 1.1 | `"1.10"` for a version string |
| `1e3` | String | Float 1000 | `1000`, or `"1e3"` for a string |
| `22:22` | Base-60 number 1342 | String | `"22:22"` |
| `2024-05-01` | Date (in many parsers) | String | `"2024-05-01"` for a string |
| `~`, `null`, empty value | Null | Null | `null`, or `""` for an empty string |

- **Quote every string that could look like a number, boolean, date or
  null.** Version numbers, postal codes, phone numbers, country codes, IDs
  with leading zeros and time-of-day values are the usual victims.
- **Don't rely on an empty value meaning anything.** It's null, not an empty
  string. Write `null` or `""` so the intent is clear.
- **Write booleans only as `true` and `false`.** They're booleans under every
  schema.
- yamllint's `truthy`, `octal-values` and `float-values` rules catch most of
  these (see the [style guide's config](tools.md#recommended-setup)).

## Strings

- Prefer plain, unquoted strings where they're unambiguous. They're the
  easiest to read.
- When a string needs quotes, use double quotes. Only double-quoted strings
  support escape sequences such as `\n` and `\t`. The one exception is a
  string that itself contains double quotes, which takes single quotes (see
  [Values](coding-style.md#values)).
- Never rely on YAML to strip or keep the spaces at either end of a plain
  string. Quote a string whose leading or trailing spaces matter.

## Multi-line strings

Use a block scalar for any string longer than a line or containing line
breaks. The indicator after the key decides what happens to the line breaks:

| Indicator | Line breaks inside the text | Final line break |
| --- | --- | --- |
| `\|` | Kept | One kept |
| `\|-` | Kept | Removed |
| `\|+` | Kept | All trailing ones kept |
| `>` | Folded into spaces | One kept |
| `>-` | Folded into spaces | Removed |

- Use **`|`** (literal) when line breaks matter: scripts, certificates,
  formatted text.
- Use **`>`** (folded) for long prose that should read as one paragraph.
- Add **`-`** when the value must not end with a newline, such as a name or
  a single-line command:

  ```yaml
  ---
  description: >-
    Collects metrics from every node and forwards them to the central store
    once a minute.
  banner: |
    Welcome.
    Maintenance runs every Sunday at 02:00 UTC.
  ```

- Avoid `+`. Trailing blank lines are invisible in review, and keeping them
  is almost never intended.

## Anchors, aliases and merge keys

- **Use anchors (`&`) and aliases (`*`) sparingly**, to avoid repeating a
  large block. Every alias makes the reader jump to another part of the file.
- Define an anchor before it's used, and only once. Remove anchors nothing
  refers to.
- **Don't use the `<<` merge key in files that must be portable.** It comes
  from YAML 1.1's optional types and isn't part of YAML 1.2, so some parsers
  reject it and others treat it as an ordinary key. Repeat the values, or
  generate the file, instead.
- When a file needs heavy reuse, it has outgrown YAML. Generate it from code
  or a configuration language instead.

## Duplicate keys

- **Never repeat a key in the same mapping.** The specification requires
  keys to be unique, but most parsers silently keep only the last value. The
  first value disappears without an error.
- yamllint's `key-duplicates` rule catches this. Run it on every file.

## Loading YAML safely

- **Always use a parser's safe loader** for YAML you didn't write yourself.
  Full loaders can build arbitrary objects from tags such as
  `!!python/object`, which lets a crafted file run code. In Python, use
  `yaml.safe_load()`, never `yaml.load()` with the full loader.
- **Don't write language-specific tags** (`!!python/...`, `!ruby/object`).
  They tie the file to one language and only work with an unsafe loader.
- **Limit alias expansion.** A small file can use nested aliases to expand
  into billions of nodes (the "billion laughs" attack). Use a parser that
  limits alias expansion or document size when loading untrusted input.
- Treat YAML from outside the program as untrusted input, like any other.

## Schemas and validation

- **Validate every file against a schema** when it's loaded, and fail on
  unknown keys. A misspelled key is otherwise silently ignored, and its
  default quietly used.
- Describe the schema with **JSON Schema**. YAML's data model maps onto
  JSON's, so the same schema validates both, and editors can use it for
  completion and inline errors.
- Keep the schema next to the code that reads the files, and version them
  together.

## Keeping YAML as data

- **Don't template YAML with text substitution.** String templating can't
  see YAML's structure, so a substituted value with a colon, quote or
  newline silently changes the document. Build the data in code, then
  serialise it with a YAML library.
- Keep long scripts and queries out of YAML. Put them in their own files, so
  they get their own syntax highlighting, linting and tests, and reference
  them by path.
- Keep secrets out of YAML files. Reference them from a secret store or the
  environment instead.

## Sources

- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/)
- [YAML 1.1 language-independent types](https://yaml.org/type/)
- [yamllint rules](https://yamllint.readthedocs.io/en/stable/rules.html)
- [PyYAML documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [JSON Schema](https://json-schema.org/)
