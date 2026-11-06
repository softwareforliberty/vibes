# Julia Tools

The free/open source tools that lint, format and check Julia code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [JuliaFormatter.jl](https://github.com/domluna/JuliaFormatter.jl) | MIT | Formatting | Formatting code to the Blue style |
| [JET.jl](https://github.com/aviatesk/JET.jl) | MIT | Linting | Finding type errors and type instability without running the code |
| [Aqua.jl](https://github.com/JuliaTesting/Aqua.jl) | MIT | Linting, Code quality | Checking ambiguities, type piracy, compat entries and stale dependencies |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Coverage.jl](https://github.com/JuliaCI/Coverage.jl) | MIT | Code quality | Measuring test coverage |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.JuliaFormatter.toml`](.JuliaFormatter.toml) | JuliaFormatter.jl |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`.opengrep/julia.yaml`](.opengrep/julia.yaml) | Opengrep |

## Configuration

Put the formatter settings in `.JuliaFormatter.toml` at the project root:

```toml
style = "blue"
```

Code must be formatted and pass the quality tests with **no failures**:

```sh
julia -e 'using JuliaFormatter; format(".", overwrite=false) || exit(1)'
julia --project -e 'using Pkg; Pkg.test()'
```

Run JET and Aqua from the test suite, in `test/runtests.jl`, so every test
run checks them:

```julia
using Aqua
using JET
using Surveys
using Test

@testset "code quality" begin
    Aqua.test_all(Surveys)
    JET.test_package(Surveys; target_modules=(Surveys,))
end
```

- JuliaFormatter owns layout. Don't hand-format code it will rewrite.
- `JET.test_package` reports calls that can't succeed and undefined names,
  without running the code. It doesn't report type instability: check
  suspect functions for that with JET's `@report_opt` (see
  [idioms.md](idioms.md)).
- `target_modules` keeps only the errors JET finds in the package's own
  code. Without it, JET also reports problems deep inside Base, such as
  every `convert` a struct's default constructor might call.
- Aqua checks for method ambiguities, type piracy, missing `[compat]`
  entries and unused dependencies, which are the package rules in
  [idioms.md](idioms.md).

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

Opengrep's Julia support is experimental. The starter rules in
[`.opengrep/julia.yaml`](.opengrep/julia.yaml) cover the unsafe calls in the
[security idioms](idioms.md#security), such as `eval(Meta.parse(...))` and
`deserialize()`; test them against known examples before relying on them.

### Dependency vulnerabilities

OSV-Scanner doesn't list Julia's `Manifest.toml` among its supported
lockfiles, and no other maintained FOSS tool checks Julia packages against
known vulnerabilities. Commit `Manifest.toml` for applications, keep every
dependency's `[compat]` entry current, and follow the security advisories of
the packages you depend on.

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

lizard doesn't support Julia, and no other maintained FOSS tool measures
Julia function complexity. Review long functions by hand, and split any
function longer than 60 lines or with deeply nested branches.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format julia --min-tokens 50 --exitCode 1 src
```

### Dead code

Aqua's stale-dependency check, part of `Aqua.test_all()`, fails when a
package declares a dependency it never loads. No FOSS tool finds unused
functions, so check that every internal function has a caller before keeping
it.

### Coverage

Measure line coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

```sh
julia --project -e 'using Pkg; Pkg.test(coverage=true)'
julia -e 'using Coverage
    covered, total = get_summary(process_folder("src"))
    println("coverage: ", round(100 * covered / total; digits=1), "%")
    covered / total >= 0.8 || exit(1)'
```
