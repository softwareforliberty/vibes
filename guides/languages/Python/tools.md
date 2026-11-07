# Python Tools

The free/open source tools that lint, format and check Python code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Ruff](https://docs.astral.sh/ruff/) | MIT | Formatting, Linting, Auditing | Formatting, import sorting, linting and security checks |
| [mypy](https://mypy-lang.org/) | MIT | Linting | Static type checking |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [pip-audit](https://github.com/pypa/pip-audit) | Apache-2.0 | Auditing | Checking installed packages against known vulnerabilities |
| [lizard](https://github.com/terryyin/lizard) | MIT | Code quality | Measuring function complexity and length |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Vulture](https://github.com/jendrikseipp/vulture) | MIT | Code quality | Finding unused code |
| [Coverage.py](https://coverage.readthedocs.io/) | Apache-2.0 | Code quality | Measuring test coverage |
| [import-linter](https://github.com/seddonym/import-linter) | BSD-2-Clause | Code quality | Enforcing the dependency rules between the project's layers |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`pyproject.toml`](pyproject.toml) | Ruff, mypy, Vulture and Coverage.py |
| [`vulture_whitelist.py`](vulture_whitelist.py) | Vulture |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/python.yaml`](.opengrep/python.yaml) | Opengrep |

## Configuration

Code must pass all three checks with **no errors or warnings**:

```sh
ruff format .
ruff check .
mypy .
```

Put the settings for every Python tool on this page in `pyproject.toml`:

```toml
# Template: merge these tool settings into the project's pyproject.toml.

[tool.ruff]
line-length = 88
target-version = "py310"

[tool.ruff.lint]
select = [
  "E", # pycodestyle errors
  "W", # pycodestyle warnings
  "F", # Pyflakes
  "I", # import sorting
  "N", # naming
  "D", # docstrings
  "UP", # modern syntax
  "B", # likely bugs
  "SIM", # simplifications
  "S", # security
  "RUF", # Ruff-specific checks
]
# Rules that conflict with the formatter.
ignore = ["W191", "E111", "E114", "E117", "D206", "D300"]

[tool.ruff.lint.pydocstyle]
convention = "google"

[tool.ruff.lint.per-file-ignores]
# pytest uses assert, and tests need no docstrings.
"tests/**" = ["S101", "D"]

[tool.mypy]
strict = true

[tool.vulture]
paths = ["src", "tests", "vulture_whitelist.py"]
# Vulture rates unused functions, classes and variables at 60%.
min_confidence = 60

[tool.coverage.run]
branch = true
source = ["src"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

- `ruff format` owns layout. Don't hand-format code it will rewrite, and
  don't argue with its output in review.

## Auditing

### Security analysis

Ruff's `S` rules, enabled in the [configuration](#configuration), are a port
of Bandit's checks. They catch the common unsafe calls: `eval()`, `pickle`
loads, `subprocess` with `shell=True`, and `yaml.load()` without a safe
loader.

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `requirements.txt`, `poetry.lock` and
`Pipfile.lock` and checks every pinned version against the OSV database.

```sh
osv-scanner scan source -r .
```

pip-audit checks the packages actually installed in the environment, which
catches anything installed outside the lockfile:

```sh
pip-audit --strict
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
lizard -l python -C 10 -L 60 -w src
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format python --min-tokens 50 --exit-code 1 src
```

### Dead code

Vulture finds unused functions, classes, variables and imports. Python is
dynamic, so it can't see every use: confirm each finding before deleting
it, and list names that are used indirectly (for example, by a framework) in
a whitelist file.

```sh
vulture
```

The paths and the confidence threshold come from `[tool.vulture]` in
`pyproject.toml`. It reads `tests` too, so code the tests use isn't
reported. The threshold is 60% because Vulture rates every unused
function, class and variable at 60%; a higher one reports only unused
imports, which Ruff already catches.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```sh
coverage run -m pytest
coverage report
```

The settings are in `[tool.coverage]` in `pyproject.toml` (see
[Configuration](#configuration)).

### Architecture

import-linter checks the imports between the project's own packages against
a set of contracts, so the core can't come to depend on its edges. It's how
Python projects
[enforce their layers](../../../architecture/README.md#enforce-it).

Install it as a development dependency, and run it in an environment where
the project itself is installed (`pip install -e .`), because it finds the
packages by importing them. It exits non-zero when any contract is broken:

```sh
lint-imports
```

It reads its contracts from `pyproject.toml`. They depend on each project's
layers, so they aren't in the template; add them to the project's own file.
The package names here are examples: replace them with the layers in the
project's `design.md`.

```toml
[tool.importlinter]
root_package = "app"

[[tool.importlinter.contracts]]
name = "The core doesn't depend on the edges"
type = "forbidden"
source_modules = ["app.core"]
forbidden_modules = ["app.adapters", "app.cli"]

[[tool.importlinter.contracts]]
name = "No import cycles between packages"
type = "acyclic_siblings"
ancestors = ["app"]
```

The `forbidden` contract also catches indirect imports, such as `app.core`
importing a module that imports `app.adapters`. The edges may import the
core. The `acyclic_siblings` contract fails when the packages under `app`
import each other in a cycle.
