# CMake Tools

The free/open source tools that lint, format and check CMake code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [CMake](https://cmake.org/) 3.24 or later | BSD-3-Clause | Linting, Code quality | Configuring and building, linting through its own warnings, and tracing configure runs |
| [gersemi](https://github.com/BlankSpruce/gersemi) | MPL-2.0 | Formatting | Formatting `CMakeLists.txt` and `.cmake` files |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.gersemirc`](.gersemirc) | gersemi |
| [`CMakePresets.json`](CMakePresets.json) | CMake and CTest |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## CMake warnings

CMake's own warnings are the lint gate. A project must configure with **no
warnings** using:

```sh
cmake --preset dev
```

The `dev` and `ci` presets in [`CMakePresets.json`](CMakePresets.json) turn
the checks on, so every developer and CI run gets the same ones:

- `"uninitialized": true` under `warnings` reports variables that are read
  before they're set, which is almost always a typo. It only warns, so CI
  fails the build when the output contains `CMake Warning`.
- `"dev": true` under `errors` turns warnings meant for project authors into
  errors, such as policy warnings and misused commands.
- `"deprecated": true` under `errors` turns uses of deprecated features into
  errors, so they get fixed before a CMake release removes them.
- Set these in the presets rather than on the command line. CMake 4.4
  renamed the command-line options (`--warn-uninitialized` became
  `-Wuninitialized`, and `-Werror=dev` became `-Werror=author`), but a
  version 5 presets file works the same in every CMake from 3.24 on.

## Formatting

gersemi formats every CMake file. Check formatting in CI with:

```sh
gersemi --check --diff .
```

Commit a `.gersemirc` at the repository root so every editor and CI run uses
the same settings:

```yaml
---
line_length: 80
indent: 4
```

Formatting is the formatter's job. Where this guide and gersemi's output could
disagree on layout, gersemi wins, so reviews never argue about whitespace.

## Auditing

### Security analysis

No maintained FOSS static analyser understands CMake. Configure and build
steps can run commands and download code, so review every `execute_process`,
`file(DOWNLOAD)`, `ExternalProject_Add` and `FetchContent_Declare` call when
it's added or changed. Give every downloaded archive a `URL_HASH`, so CMake
rejects a file that has changed since it was pinned.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `conan.lock` and checks every pinned
version against the OSV database.

```sh
osv-scanner scan source -r .
```

OSV-Scanner also checks git submodules and vendored C and C++ sources by
commit. It can't read `FetchContent_Declare` calls, so pin each fetched
dependency to an exact version (see [Dependencies](idioms.md#dependencies)),
and check that version against the [OSV database](https://osv.dev/) whenever
it changes.

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

No maintained FOSS tool measures complexity in CMake code, and lizard doesn't
read it. The closest check is review: keep each `function()` short enough to
read at once, and split it when it isn't.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format cmake --min-tokens 50 --exitCode 1 .
```

### Coverage

No maintained FOSS tool measures coverage of CMake code. The closest check is
CMake's trace, which records every command a configure run executes. Compare
the traces of your presets to find `if()` branches that no preset reaches:

```sh
cmake --preset dev --trace-expand --trace-redirect=build/cmake-trace.txt
```
