# XML Tools

The free/open source tools that lint, format and check XML code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [xmllint](https://gitlab.gnome.org/GNOME/libxml2) (libxml2) | MIT | Formatting, Linting, Auditing | Formatting, checking well-formedness and validating against XSD or RELAX NG schemas |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Recommended setup

Every XML file must be well-formed and match `xmllint --format` exactly.
Run this from the repository root:

```sh
for f in $(git ls-files '*.xml'); do
  xmllint --format --nonet "$f" | diff -u "$f" - || exit 1
done
```

- `xmllint --format` indents with 2 spaces, writes empty elements as
  `<name/>`, and leaves mixed content alone, as the
  [style guide](coding-style.md#layout) asks.
- A file that isn't well-formed fails to parse, so the same loop is the
  well-formedness check.
- `--nonet` stops xmllint fetching anything from the network, as the
  [safe-reading rules](idioms.md#reading-xml-safely) require.
- To fix a file's layout, write the formatted output back over it:
  `xmllint --format --nonet --output file.xml file.xml`.

## Schema validation

Validate every document against its schema, as the
[validation rules](idioms.md#schemas-and-validation) require. Use the schema
from the repository, never the one a document names:

```sh
xmllint --noout --nonet --relaxng schemas/order.rng orders/*.xml
xmllint --noout --nonet --schema schemas/order.xsd orders/*.xml
```

Use `--relaxng` for a RELAX NG schema and `--schema` for an XML Schema.

## Auditing

### Security analysis

No maintained FOSS tool runs security analysis on XML files. Almost every
XML attack needs a DTD, so fail the build when any XML file in the repository
declares a `DOCTYPE`:

```sh
! git grep -l '<!DOCTYPE' -- '*.xml'
```

The real defence is in the code that parses XML: review every parser it
creates against the [safe-reading rules](idioms.md#reading-xml-safely), and
scan that code with its own language's security tools. Never run xmllint
with `--noent`, `--dtdvalid` or `--huge` on a document you didn't write.

### Dependency vulnerabilities

XML has no package manager, so there are no third-party dependencies to
audit. Keep the schemas a format uses in the repository, so validation never
downloads them.

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

XML has no functions, so there's no complexity to measure.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format markup --min-tokens 50 --exitCode 1 .
```

### Coverage

XML has no executable code, so there's no coverage to measure.
