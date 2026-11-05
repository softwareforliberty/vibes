# YAML Coding Style

A general-purpose style for YAML files. It builds on the
[YAML 1.2 specification](https://yaml.org/spec/1.2.2/) and the checks that
[yamllint](https://github.com/adrienverge/yamllint) can enforce (see
[Sources](#sources)). It covers YAML itself, not the schema of any one tool
that reads it.

This guide covers how YAML looks. For how to write YAML that every parser
reads the same way (typing traps, quoting, anchors, multi-line strings and
safe loading), see [idioms.md](idioms.md).

The tools that check YAML code are listed in [tools.md](tools.md).

## Language baseline

Write **YAML 1.2** (revision 1.2.2 of the spec), in a form that YAML 1.1
parsers read the same way. Many widely used parsers still implement 1.1, which
reads values such as `yes`, `no`, `on` and `off` as booleans (see
[implicit typing traps](idioms.md#implicit-typing-traps)).

## Files

- Name YAML files with the **`.yaml`** extension, the one the YAML project
  recommends. Use `.yml` only where a tool requires it.
- Encode files in **UTF-8**, without a byte order mark.
- Start every file with the `---` document marker. It makes the start of the
  document explicit and is required anyway when a file holds several
  documents.
- Don't end documents with `...` unless a stream needs it. It adds nothing in
  a file.

## Layout

### Indentation and line length

- Indent with **2 spaces**. YAML forbids tabs for indentation.
- Indent sequence items under their key, so nesting is always visible:

  ```yaml
  ---
  servers:
    - name: alpha
      port: 8080
    - name: beta
      port: 8081
  ```

- **80 columns** is the limit. Long text goes in a
  [block scalar](idioms.md#multi-line-strings) instead of a long line.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.
- Use at most one blank line in a row, to separate groups of related keys.

### Block and flow style

- Use **block style** for every non-empty mapping and sequence. Each entry
  on its own line diffs and reviews cleanly.
- Use flow style only for empty collections: `{}` and `[]`.

## Keys

- Write keys as plain, unquoted scalars wherever they can be.
- When you define the format, name keys in **`snake_case`**. When a consumer
  defines it, use the consumer's names exactly.
- Every key in a mapping is unique. Most parsers silently keep only the last
  of two duplicates, so the first one is lost without a warning.
- Order keys for the reader: identity first (such as `name` or `id`), then
  the rest in logical groups. Don't sort alphabetically when that splits
  related keys apart.
- Put a single space after the colon, and none before it: `port: 8080`.

## Values

- Leave strings unquoted when they're unambiguously strings.
- **Quote a string with double quotes** when it needs quoting: when it would
  otherwise read as another type (`"no"`, `"1.10"`, `"0755"`), or when it
  contains characters that YAML treats specially (`: `, ` #`, or a leading
  `*`, `&`, `!`, `|`, `>`, `@` or `` ` ``). See
  [typing traps](idioms.md#implicit-typing-traps).
- When a string that needs quoting also contains double quotes, use single
  quotes so it doesn't need escaping: `'error: "disk" is full'`. A string
  that doesn't need quoting stays plain, even with quotes inside it:
  `say "hello"`.
- Write booleans only as `true` and `false`, and null only as `null`.
- Write numbers in plain decimal: `8080`, `0.5`. A float always has a digit
  before the decimal point.

## Comments

- Start a comment with `#` followed by one space: `# Retry policy`.
- Put at least two spaces between a value and a trailing comment:
  `timeout: 30  # seconds`.
- Indent a comment that sits on its own line to match the content it
  describes.
- Comments explain **why** a value is what it is, not what the key already
  says. `# seconds` and `# matches the upstream default` are useful;
  `# the port` is not.
- Write a TODO as `# TODO: <issue link> - <what needs doing>`. The link gives
  the context and an owner.

## Generated and third-party files

Generated YAML and vendored third-party files keep their own format and are
excluded from yamllint, so regenerating or updating them stays a clean
replacement.

## Sources

This guide starts from the YAML 1.2 specification and borrows from:

- [YAML 1.2.2 specification](https://yaml.org/spec/1.2.2/)
- [yamllint rules](https://yamllint.readthedocs.io/en/stable/rules.html)
- [YAML FAQ](https://yaml.org/faq.html)
