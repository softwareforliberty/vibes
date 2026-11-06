# TOML Tools

The free/open source tools that lint, format and check TOML code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Taplo](https://taplo.tamasfe.dev/) | MIT | Formatting, Linting | Formatting TOML and checking its syntax |
| [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) | Apache-2.0 | Linting, Auditing | Validating files against their JSON Schema |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.taplo.toml`](.taplo.toml) | Taplo |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Recommended setup

Format and lint every TOML file. Files must pass with **no errors**:

```sh
taplo fmt --check
taplo lint
```

Run `taplo fmt` without `--check` to fix the formatting in place.

Configure Taplo with `.taplo.toml` at the repository root:

```toml
include = ["**/*.toml"]

[formatting]
align_comments = false
align_entries = false
allowed_blank_lines = 1
array_auto_collapse = true
array_auto_expand = true
array_trailing_comma = true
column_width = 80
compact_arrays = true
indent_entries = false
indent_string = "  "
indent_tables = false
reorder_keys = false
trailing_newline = true
```

- `array_auto_expand` and `array_auto_collapse` put an array on one line when
  it fits in 80 columns, and one item per line, with a trailing comma, when it
  doesn't.
- `reorder_keys = false` keeps keys in the order the
  [style guide](coding-style.md#order) asks for, instead of sorting them.
- Taplo can't check that a table header has a blank line before it, or that
  a table's keys come before its sub-tables. Review checks those.
- The file follows its own rules, so it's a working example of this style.

## Schema validation

Validate every file against its JSON Schema, as the
[validation rules](idioms.md#schemas-and-validation) require. A file can pass
Taplo and still hold a misspelled key or a value of the wrong type; only the
schema catches those.

```sh
check-jsonschema --schemafile schemas/settings.schema.json config/*.toml
```

- Set `"additionalProperties": false` in the schema, so an unknown key fails
  validation instead of being silently ignored.
- Run the same check in the program that loads the files. The tool catches
  mistakes before a commit; the program must still refuse a bad file at run
  time.

## Auditing

### Security analysis

No maintained FOSS tool runs security analysis on TOML files, and Opengrep
doesn't support TOML. TOML parsers only build plain values, so the risks are
in what the program does with them: schema validation rejects any value the
program doesn't expect.

### Dependency vulnerabilities

TOML has no package manager, so there are no third-party dependencies to
audit.

### Secrets

TOML files often hold configuration, which makes them a common place for a
committed password or API key. Keep secrets out of them and load secrets
from the environment or a secret store instead.

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Complexity

TOML has no functions, so there's no complexity to measure.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format toml --min-tokens 50 --exit-code 1 .
```

### Coverage

TOML has no executable code, so there's no coverage to measure.
