# Haskell Tools

The free/open source tools that lint, format and check Haskell code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GHC](https://www.haskell.org/ghc/) | BSD-3-Clause | Linting | Compiling, and linting through its warning flags |
| [Fourmolu](https://fourmolu.github.io/) | BSD-3-Clause | Formatting | Formatting source files |
| [HLint](https://github.com/ndmitchell/hlint) | BSD-3-Clause | Linting, Auditing | Suggesting simpler code, and banning unsafe functions |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [OSV-Scanner](https://github.com/google/osv-scanner) | Apache-2.0 | Auditing | Checking dependencies against known vulnerabilities |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [Weeder](https://github.com/ocharles/weeder) | BSD-3-Clause | Code quality | Finding unused code |
| [hpc](https://hackage.haskell.org/package/hpc) | BSD-3-Clause | Code quality | Measuring test coverage (ships with GHC) |

## Formatting

Fourmolu owns layout. Check formatting in CI, and fix it locally with
`--mode inplace`:

```sh
fourmolu --mode check $(git ls-files '*.hs')
```

Put the settings in `fourmolu.yaml` at the project root:

```yaml
indentation: 4
column-limit: 80
comma-style: leading
import-export-style: diff-friendly
haddock-style: multi-line
unicode: never
```

## Compiler warnings

Compiler warnings are the main lint gate. Code must build with **no
warnings** using at least these flags, set in every component of the
`.cabal` file:

```cabal
ghc-options:
    -Wall
    -Wcompat
    -Widentities
    -Wincomplete-record-updates
    -Wincomplete-uni-patterns
    -Wmissing-export-lists
    -Wpartial-fields
    -Wredundant-constraints
    -Wunused-packages
```

Turn warnings into errors in CI rather than in the `.cabal` file, so a
newer GHC with new warnings doesn't break a user's build:

```sh
cabal build all --ghc-options=-Werror
```

## Linting

HLint suggests simpler code and enforces the bans in
[idioms.md](idioms.md#totality). Run it on every source directory:

```sh
hlint src app test
```

Put the settings in `.hlint.yaml`. The `functions` list bans partial and
unsafe functions everywhere:

```yaml
- functions:
    - {name: head, within: []}
    - {name: tail, within: []}
    - {name: init, within: []}
    - {name: last, within: []}
    - {name: "!!", within: []}
    - {name: fromJust, within: []}
    - {name: read, within: []}
    - {name: undefined, within: []}
    - {name: unsafePerformIO, within: []}
    - {name: unsafeCoerce, within: []}
```

A module that has a real reason to call one of these lists itself in that
function's `within`, so every exception is visible in one file.

## Auditing

### Security analysis

No maintained FOSS security analyser supports Haskell; Opengrep doesn't
parse it. The closest check is HLint's function bans above, which block the
calls that bypass the type system (`unsafePerformIO`, `unsafeCoerce`).
Review every use of `System.Process` and of raw SQL strings by hand.

### Dependency vulnerabilities

Commit the lockfile, and fail the build when any dependency has a known
vulnerability. OSV-Scanner reads `cabal.project.freeze` and
`stack.yaml.lock` and checks every pinned version against the OSV database.

```sh
osv-scanner scan source -r .
```

Generate `cabal.project.freeze` with `cabal freeze`, and regenerate it
whenever the dependencies change.

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

No maintained FOSS tool measures function complexity for Haskell; lizard
doesn't support it. The closest check is review against the indentation and
function-size rules in [coding-style.md](coding-style.md#functions), plus
HLint's suggestions, which often shorten deep expressions.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format haskell --min-tokens 50 --exitCode 1 src
```

### Dead code

GHC's `-Wunused-top-binds` (part of `-Wall`) finds unused definitions inside
a module. Weeder finds definitions that are exported but never used
anywhere in the program. It reads the `.hie` files GHC writes, so build with
`-fwrite-ide-info` first:

```sh
cabal build all --ghc-options=-fwrite-ide-info
weeder
```

Tell Weeder where the program starts in `weeder.toml`:

```toml
roots = ["^Main.main$"]
type-class-roots = true
```

### Coverage

Measure expression coverage on every test run, and fail the build when it
falls below 80%. Raise the minimum as coverage grows; never lower it to make
a build pass.

hpc reports the share of expressions the tests evaluated. It has no
minimum of its own, so check its summary line:

```sh
cabal test all --enable-coverage | tee test.log
awk '/expressions used/ { sub(/%/, "", $1); if ($1 < 80) bad = 1 }
     END { exit bad }' test.log
```
