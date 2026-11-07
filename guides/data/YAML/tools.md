# YAML Tools

The free/open source tools that lint, format and check YAML code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [yamllint](https://github.com/adrienverge/yamllint) | GPL-3.0 | Linting, Code quality | Syntax, layout and typing-trap checks, and unused anchors |
| [check-jsonschema](https://github.com/python-jsonschema/check-jsonschema) | Apache-2.0 | Linting, Auditing | Validating files against their JSON Schema |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.yamllint.yaml`](.yamllint.yaml) | yamllint |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/yaml.yaml`](.opengrep/yaml.yaml) | Opengrep |

## Recommended setup

Lint every YAML file. Files must pass with **no warnings**.

```sh
yamllint --strict .
```

Configure yamllint with `.yamllint.yaml` at the repository root:

```yaml
---
extends: default

rules:
  anchors:
    forbid-unused-anchors: true
  braces:
    forbid: non-empty
  brackets:
    forbid: non-empty
  empty-values:
    forbid-in-block-mappings: true
    forbid-in-flow-mappings: true
  float-values:
    forbid-inf: true
    forbid-nan: true
    require-numeral-before-decimal: true
  indentation:
    spaces: 2
    indent-sequences: true
  line-length:
    max: 80
  octal-values:
    forbid-explicit-octal: true
    forbid-implicit-octal: true
  quoted-strings:
    quote-type: double
    required: only-when-needed
    allow-quoted-quotes: true
  truthy:
    allowed-values:
      - "true"
      - "false"
    check-keys: true
```

- `--strict` makes warnings fail the run, so nothing is left as "only a
  warning".
- The `default` preset also turns on `key-duplicates`, `trailing-spaces`,
  `new-line-at-end-of-file` and `document-start`, which this guide relies on.
- The file follows its own rules, so it's a working example of this style.

## Schema validation

Validate every file against its JSON Schema, as the
[validation rules](idioms.md#schemas-and-validation) require. A file can pass
yamllint and still hold a misspelled key or a value of the wrong type; only
the schema catches those.

```sh
check-jsonschema --schemafile schemas/settings.schema.json config/*.yaml
```

- Set `"additionalProperties": false` in the schema, so an unknown key fails
  validation instead of being silently ignored.
- Run the same check in the program that loads the files. The tool catches
  mistakes before a commit; the program must still refuse a bad file at run
  time.

## Auditing

### Security analysis

YAML is data, so the main risk is a loader that turns tags into objects.
The starter rules in [`.opengrep/yaml.yaml`](.opengrep/yaml.yaml) reject
language-specific tags such as `!!python/object`; keep loaders safe, as the
[loading rules](idioms.md#loading-yaml-safely) require. Schema validation
also rejects any value the program doesn't expect.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

### Dependency vulnerabilities

YAML has no package manager, so there are no third-party dependencies to
audit.

### Secrets

YAML files often hold configuration, which makes them the most common place
for a committed password or API key. Keep secrets out of them and load
secrets from the environment or a secret store instead.

Scan the working tree and the full git history for committed secrets. A
secret that reaches history stays exposed after it's deleted, so rotate any
secret gitleaks finds, then remove it.

```sh
gitleaks git --redact
gitleaks dir --redact
```

## Code quality

### Complexity

YAML has no functions, so there's no complexity to measure.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format yaml --min-tokens 50 --exit-code 1 .
```

### Dead code

yamllint's `forbid-unused-anchors` setting, in the config above, rejects any
anchor that no alias refers to.

### Coverage

YAML has no executable code, so there's no coverage to measure.
