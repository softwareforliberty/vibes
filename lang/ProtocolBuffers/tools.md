# Protocol Buffers Tools

The free/open source tools that lint, format and check Protocol Buffers code,
and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Buf](https://github.com/bufbuild/buf) | Apache-2.0 | Formatting, Linting, Auditing | Formatting, linting, and detecting breaking changes |
| [protolint](https://github.com/yoheimuta/protolint) | MIT | Linting | Checking line length and import order, which Buf doesn't |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`buf.yaml`](buf.yaml) | Buf |
| [`.protolint.yaml`](.protolint.yaml) | protolint |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Recommended setup

Configure Buf with `buf.yaml` at the repository root, naming the directory
that holds the `.proto` files:

```yaml
---
version: v2
modules:
  - path: proto
lint:
  use:
    - STANDARD
    - COMMENT_ENUM
    - COMMENT_MESSAGE
    - COMMENT_RPC
    - COMMENT_SERVICE
breaking:
  use:
    - FILE
```

Every `.proto` file must pass all three checks with **no errors**:

```sh
buf format --diff --exit-code
buf lint
protolint lint proto
```

Run `buf format -w` to fix the formatting in place.

- Buf's `STANDARD` lint rules check the naming, package and file layout
  rules in the [style guide](coding-style.md#names), including the
  `_UNSPECIFIED` zero value and the `Request`/`Response` message names.
- The four `COMMENT_` rules require the comment the
  [style guide](coding-style.md#comments) asks for above every message,
  enum, service and method.
- Buf doesn't check line length or import order, so protolint runs only
  those two rules. Configure it with `.protolint.yaml`:

  ```yaml
  ---
  lint:
    rules:
      no_default: true
      add:
        - IMPORTS_SORTED
        - MAX_LINE_LENGTH
    rules_option:
      max_line_length:
        max_chars: 80
  ```

## Breaking changes

Compare every change with the schema on the main branch, and fail the build
on any change that breaks the [compatibility rules](idioms.md#compatibility):

```sh
buf breaking --against '.git#branch=main'
```

The `FILE` rule set in `buf.yaml` is Buf's strictest. It catches changes
that break generated code as well as the wire and JSON formats.

## Auditing

### Security analysis

No maintained FOSS tool runs security analysis on `.proto` files, and
Opengrep doesn't support them. Schemas hold no code, so the risks are in the
code that handles the messages: scan that code with its own language's
security tools. `buf breaking` above stops the most common schema mistake, a
change that makes old and new programs read the same data differently.

### Dependency vulnerabilities

No vulnerability database covers Protocol Buffers schema modules. Pin the
modules a schema imports in `buf.lock`, and commit it. The Protocol Buffers
runtime library is a dependency of each generated-code project, so audit and
update it with that project's own tools.

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

Protocol Buffers schemas have no functions, so there's no complexity to
measure. Buf's lint rules and review keep messages small.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format protobuf --min-tokens 50 --exit-code 1 .
```

### Coverage

Schemas have no executable code, so there's no coverage to measure. Test the
generated code through the programs that use it.
