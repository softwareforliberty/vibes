# Go Tools

The free/open source tools that lint, format and check Go code, and how to run
them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [gofmt](https://pkg.go.dev/cmd/gofmt) | BSD-3-Clause | Formatting | Formatting, as part of the Go distribution |
| [goimports](https://pkg.go.dev/golang.org/x/tools/cmd/goimports) | BSD-3-Clause | Formatting | Formatting plus maintaining the import block |
| [go vet](https://pkg.go.dev/cmd/vet) | BSD-3-Clause | Linting | Finding suspicious constructs, as part of the Go distribution |
| [golangci-lint](https://golangci-lint.run/) | GPL-3.0 | Linting, Auditing | Running staticcheck, gosec and other linters in one pass |
| [staticcheck](https://staticcheck.dev/) | MIT | Linting, Code quality | Finding bugs, simplifications and unused code |
| [gosec](https://github.com/securego/gosec) | Apache-2.0 | Auditing | Finding security problems in Go source |
| [govulncheck](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck) | BSD-3-Clause | Auditing | Finding known vulnerabilities in code you actually call |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [deadcode](https://pkg.go.dev/golang.org/x/tools/cmd/deadcode) | BSD-3-Clause | Code quality | Finding functions no program path can reach |
| [go test](https://pkg.go.dev/cmd/go#hdr-Test_packages) | BSD-3-Clause | Code quality | Running tests, the race detector and coverage |

## Config files

Copy these files into the project root. Each one matches the settings this
guide describes.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, including GoLand's import settings |
| [`.golangci.yml`](.golangci.yml) | golangci-lint |
| [`.opengrep/go.yaml`](.opengrep/go.yaml) | Opengrep: starter rules for the [security idioms](idioms.md#security) |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Formatting

`gofmt` owns layout, and `goimports` adds import maintenance on top. Code must
come out of both unchanged:

```sh
gofmt -l .
goimports -l .
```

Both commands list the files they would change, so CI fails when either
prints anything. Run them with `-w` to fix the files.

## Linting

Code must pass `go vet` and golangci-lint with **no findings**:

```sh
go vet ./...
golangci-lint run ./...
```

Put the golangci-lint settings in `.golangci.yml`:

```yaml
---
version: "2"

linters:
  default: standard
  enable:
    - bodyclose
    - errorlint
    - gosec
    - misspell
    - revive

formatters:
  enable:
    - gofmt
    - goimports
```

- The `standard` set includes `errcheck`, `govet`, `ineffassign`,
  `staticcheck` and `unused`. `errorlint` enforces the
  [error inspection rules](idioms.md#errors), and `bodyclose` the rule on
  closing HTTP response bodies.
- Disable a finding only on the line it applies to, with a reason:
  `//nolint:gosec // path is a fixed constant`.

Run every test under the race detector as part of linting. A data race is a
bug even when the tests pass:

```sh
go test -race ./...
```

## Auditing

### Security analysis

gosec runs as part of golangci-lint (see [Linting](#linting)). It finds
unsafe calls such as SQL built with string formatting, shell commands with
user input, weak cryptography and files created with loose permissions.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

### Dependency vulnerabilities

govulncheck checks the Go vulnerability database and reports only the
vulnerabilities in functions your code can actually reach, so its findings
need action:

```sh
govulncheck ./...
```

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `go.mod` and checks every pinned version
against the OSV database.

```sh
osv-scanner scan source -r .
```

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

Fail the build on any function with a cyclomatic complexity over 10 or more
than 60 lines of code. A function past either limit is hard to test and
should be split.

```sh
lizard -l go -C 10 -L 60 -w .
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format go --min-tokens 50 --exit-code 1 .
```

### Dead code

The `unused` linter in golangci-lint finds unexported code nothing uses.
deadcode goes further: it builds the call graph from `main` and reports every
function no path can reach, exported or not. Run it with `-test` so code only
tests use isn't reported:

```sh
deadcode -test ./...
```

deadcode only sees one build configuration at a time, so check a finding
against other operating systems and build tags before deleting the code.

### Coverage

Measure statement coverage on every test run, and fail the build when it
falls below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```sh
go test -race -covermode=atomic -coverprofile=cover.out ./...
go tool cover -func=cover.out | awk '/^total:/ { if ($3 + 0 < 80) exit 1 }'
```

`go test` measures statements, not branches, and has no built-in minimum, so
the second line fails the build when the total is under 80%.
