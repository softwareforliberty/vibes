# Elixir Tools

The free/open source tools that lint, format and check Elixir code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [Elixir](https://elixir-lang.org/) compiler and Mix | Apache-2.0 | Formatting, Linting, Code quality | Formatting, compiler warnings, and test coverage |
| [Credo](https://github.com/rrrene/credo) | MIT | Linting, Code quality | Linting style, design and complexity |
| [Dialyxir](https://github.com/jeremyjh/dialyxir) | Apache-2.0 | Linting | Running Dialyzer's type analysis from Mix |
| [mix_audit](https://github.com/mirego/mix_audit) | BSD-3-Clause | Auditing | Checking dependencies against Elixir security advisories |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

## Config files

These files are drop-in templates: copy them into the project root.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor and IDE, through EditorConfig |
| [.formatter.exs](.formatter.exs) | `mix format` |
| [.credo.exs](.credo.exs) | Credo |
| [mix.exs](mix.exs) | Mix: Dialyxir flags, coverage minimum and tool dependencies (merge into the project's `mix.exs`) |
| [.opengrep/elixir.yaml](.opengrep/elixir.yaml) | Opengrep |
| [.jscpd.json](.jscpd.json) | jscpd |

## Formatting

`mix format` owns layout. Check formatting in CI, and fix it locally by
running `mix format` without the flag:

```sh
mix format --check-formatted
```

Keep `.formatter.exs` at the project root with the default line length:

```elixir
[
  inputs: ["{mix,.formatter}.exs", "{config,lib,test}/**/*.{ex,exs}"]
]
```

## Compiler warnings

Compiler warnings are the first lint gate. Turn them into errors in CI
rather than in `mix.exs`, so a newer Elixir with new warnings doesn't break a
user's build:

```sh
mix compile --warnings-as-errors
```

## Linting

Credo checks style, design and readability. Run it in strict mode, which
includes the low-priority checks:

```sh
mix credo --strict
```

Dialyzer checks the `@spec`s against how functions are actually called.
Cache the analysis between CI runs, because building it from scratch is
slow:

```sh
mix dialyzer
```

Dialyzer's warning flags, the coverage minimum and the tool dependencies
live in `mix.exs`:

```elixir
# Template: merge these settings into your project's mix.exs.
defmodule MyApp.MixProject do
  use Mix.Project

  def project do
    [
      app: :my_app,
      version: "0.1.0",
      elixir: "~> 1.17",
      deps: deps(),
      dialyzer: [
        flags: [:error_handling, :extra_return, :missing_return, :unknown, :unmatched_returns]
      ],
      test_coverage: [summary: [threshold: 80]]
    ]
  end

  defp deps do
    [
      {:credo, "~> 1.7", only: [:dev, :test], runtime: false},
      {:dialyxir, "~> 1.4", only: [:dev, :test], runtime: false},
      {:mix_audit, "~> 2.1", only: [:dev, :test], runtime: false}
    ]
  end
end
```

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

The starter rules in [.opengrep/elixir.yaml](.opengrep/elixir.yaml) flag the
calls the idioms forbid on untrusted input: `String.to_atom/1`,
`Code.eval_string/1` and `:erlang.binary_to_term/1` without the `:safe`
option. Add rules as the project finds new risks.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `mix.lock` and checks every pinned version
against the OSV database.

```sh
osv-scanner scan source -r .
```

mix_audit checks the same lockfile against the Elixir security advisories
database, and `mix hex.audit` reports dependencies their authors have
retired:

```sh
mix deps.audit
mix hex.audit
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

lizard doesn't support Elixir, so Credo measures complexity instead. Set its
limits in `.credo.exs` to match the other languages: a cyclomatic complexity
of at most 10 per function.

```elixir
%{
  configs: [
    %{
      name: "default",
      checks: %{
        extra: [
          {Credo.Check.Refactor.CyclomaticComplexity, [max_complexity: 10]}
        ]
      }
    }
  ]
}
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format elixir --min-tokens 50 --exitCode 1 lib
```

### Dead code

The compiler warns about unused variables, aliases, imports and private
functions, so `--warnings-as-errors` fails the build on them. No maintained
FOSS tool finds unused public functions across a project; the closest check
is `mix xref callers` on a function you suspect is unused.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

The minimum is set in `mix.exs` with
`test_coverage: [summary: [threshold: 80]]` (see the template under
[Linting](#linting)). `mix test --cover` exits with status 3 when coverage
is below it:

```sh
mix test --cover
```
