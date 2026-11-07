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
| [Gremlins](https://gremlins.dev/) | Apache-2.0 | Code quality | Mutation testing |
| [go-arch-lint](https://github.com/fe3dback/go-arch-lint) | MIT | Code quality | Enforcing the dependency rules between the project's layers |

## Config files

Copy these files into the project root. Each one matches the settings this
guide describes.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, including GoLand's import settings |
| [`.golangci.yml`](.golangci.yml) | golangci-lint |
| [`.opengrep/go.yaml`](.opengrep/go.yaml) | Opengrep: starter rules for the [security idioms](idioms.md#security) |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.gremlins.yaml`](.gremlins.yaml) | Gremlins |

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

### Mutation testing

Gremlins makes small changes to the code, such as turning `>` into `>=`,
and runs the tests against each one. A change the tests still pass, a
`LIVED` mutant, is behaviour no test pins down. A full run is slow, so
`scripts/audit` tests only the mutants in lines changed since the base
branch:

```sh
if ! git diff --quiet --merge-base origin/main -- '*.go'; then
  mutants=$(GOFLAGS=-count=1 gremlins unleash --dry-run \
    --diff origin/main --output-statuses rc) || exit
  case $mutants in
  *RUNNABLE* | *'NOT COVERED'*)
    GOFLAGS=-count=1 gremlins unleash --diff origin/main \
      --output-statuses lkctv
    ;;
  esac
fi
```

- [`.gremlins.yaml`](.gremlins.yaml) makes the run fail unless both the
  test efficacy, the share of tested mutants the tests kill, and the
  mutant coverage, the share of mutants any test reaches, are over 80%.
  That's the same bar as coverage. Some mutants can't be killed, because
  they don't change what the code does, so 100% is rarely reachable; 80%
  leaves room for them and still fails a change whose tests check little.
  Gremlins 0.6.0 ignores the `--threshold-*` flags, so they're set there.
- `GOFLAGS=-count=1` turns off Go's test cache. Gremlins times each mutant
  against its first test run, and a cached run takes no time, so without
  it every mutant times out on the second run, and a timed-out mutant
  counts against neither minimum.
- Gremlins tests every mutant when the diff is empty, and fails with 0%
  when the changed lines hold no mutant, as in a change to comments or
  tests only. So the first line skips the run when no Go file changed, and
  the dry run lists the mutants in the change without testing them: the
  real run happens only when there are some. If the build or the tests
  fail, the dry run does too, and so does the command.
- `--diff` compares with the point the branch left `origin/main`. Replace
  it with the project's base branch, and fetch that first.
- Gremlins 0.6.0 counts a mutant that doesn't compile as killed, so treat a
  high score on code with few tests with suspicion.
- Install it with
  `go install github.com/go-gremlins/gremlins/cmd/gremlins@v0.6.0`, the
  version this guide was checked with. Building it needs Go 1.25 or later.

Gremlins prints each mutant's status, kind and place:

```text
       LIVED CONDITIONALS_BOUNDARY at price.go:14:12
      KILLED CONDITIONALS_NEGATION at price.go:14:12
```

Read a `LIVED` mutant as a missing test: here, `>` became `>=` and the
tests still passed, because no test passes a weight of exactly 5. Write the
test that fails on the mutant, not one that just runs the line.
`NOT COVERED` means no test reaches the line at all. Gremlins 0.6.0 has
no way to mark a mutant that can't change behaviour; leave it, and let
the 80% absorb it.

### Architecture

Make the build and go-arch-lint enforce the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks. The Go
compiler already rejects import cycles between packages, so go-arch-lint only
has to check which way each import points: it fails the build when a package
imports a layer it may not use.

Install it with `go install github.com/fe3dback/go-arch-lint@v1.19.1`, and
run it from the module root, where it reads `.go-arch-lint.yml`. It exits 1
on a breach, and names the file and line of each forbidden import:

```sh
go-arch-lint check
```

An example `.go-arch-lint.yml` for a core with two edges. The package names
are examples: replace them with the layers in the project's `design.md`.

```yaml
---
version: 3
components:
  core:
    in: internal/core/**
  adapters:
    in: internal/adapters/**
  cli:
    in: internal/cli/**
  main:
    in: cmd/**
deps:
  adapters:
    mayDependOn:
      - core
  cli:
    mayDependOn:
      - core
  main:
    anyProjectDeps: true
```

- `core` has no entry under `deps`, so it may import no other component. An
  import of `internal/adapters` or `internal/cli` fails the check.
- Each edge may import the core, and `main`, which builds and wires the
  parts, may import any of them.
- An import of a third-party module fails too, until the module is listed
  under `vendors` and the components that need it name it in `canUse`. The
  standard library is always allowed.

## Sources

- [Gremlins: unleash command](https://gremlins.dev/latest/usage/commands/unleash/)
- [Gremlins: configuration](https://gremlins.dev/latest/usage/configuration/)
- [Gremlins issue 267: every mutant times out on a second run](https://github.com/go-gremlins/gremlins/issues/267)
- [Gremlins pull request 281: threshold flags ignored](https://github.com/go-gremlins/gremlins/pull/281)
