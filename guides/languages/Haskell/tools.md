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
| [universalmutator](https://github.com/agroce/universalmutator) | Apache-2.0 | Code quality | Mutation testing |

## Config files

These files are drop-in templates: copy them into the project root.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor and IDE, through EditorConfig |
| [fourmolu.yaml](fourmolu.yaml) | Fourmolu |
| [.hlint.yaml](.hlint.yaml) | HLint |
| [weeder.toml](weeder.toml) | Weeder |
| [project.cabal](project.cabal) | Cabal and GHC (merge into the package's `.cabal` file) |
| [.jscpd.json](.jscpd.json) | jscpd |
| [universalmutator.rules](universalmutator.rules) | universalmutator |

## Formatting

Fourmolu owns layout. Check formatting in CI, and fix it locally with
`--mode inplace`:

```sh
fourmolu --mode check $(git ls-files '*.hs')
```

Put the settings in `fourmolu.yaml` at the project root:

```yaml
---
indentation: 4
column-limit: 80
comma-style: leading
import-export-style: leading
haddock-style: single-line
unicode: never
```

## Compiler warnings

Compiler warnings are the main lint gate. Code must build with **no
warnings** using at least these flags. Put them, with the language
settings from [coding-style.md](coding-style.md#language-baseline), in a
`common` stanza that every component of the `.cabal` file imports:

```cabal
cabal-version: 3.0
-- Template: merge these settings into your package's .cabal file. Every
-- component imports the shared stanza, so they all build the same way.
name:          project
version:       0.1.0.0

common shared
    build-depends:      base >=4.18 && <5
    default-language:   GHC2021
    default-extensions:
        DerivingStrategies
        DuplicateRecordFields
        LambdaCase
        OverloadedRecordDot
        OverloadedStrings
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

library
    import:          shared
    hs-source-dirs:  src
    exposed-modules: Project
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
---
# Partial and unsafe functions are banned everywhere. A module that has a
# real reason to call one lists itself in that function's `within`.
- functions:
    - name: head
      within: []
    - name: tail
      within: []
    - name: init
      within: []
    - name: last
      within: []
    - name: "!!"
      within: []
    - name: fromJust
      within: []
    - name: read
      within: []
    - name: undefined
      within: []
    - name: unsafePerformIO
      within: []
    - name: unsafeCoerce
      within: []
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
jscpd --format haskell --min-tokens 50 --exit-code 1 src
```

### Dead code

GHC's `-Wunused-top-binds` (part of `-Wall`) finds unused definitions inside
a module. Weeder finds definitions that are exported but never used
anywhere in the program. It reads the `.hie` files GHC writes, so build with
`-fwrite-ide-info` first. Build the tests too, so code they use isn't
reported:

```sh
cabal build all --enable-tests --ghc-options=-fwrite-ide-info
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

hpc reports the share of expressions the tests evaluated. Cabal writes
only an HTML report, so run `hpc report` on the test suite's `.tix` file,
then check its summary line. The check also fails when there's no summary:

```sh
cabal test all --enable-coverage
tix=$(find dist-newstyle -path '*/vanilla/tix/*' -name '*.tix')
mix=$(find dist-newstyle -type d -path '*/vanilla/mix' | sed 's/^/--hpcdir=/')
hpc report "$tix" $mix | tee coverage.txt
awk '/expressions used/ { seen = 1; sub(/%/, "", $1); if ($1 < 80) bad = 1 }
     END { exit bad || !seen }' coverage.txt
```

This reads one test suite. With more than one, merge their `.tix` files
with `hpc sum` first.

### Mutation testing

universalmutator makes small changes to the code, such as turning `>=` into
`>`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. No Haskell-specific tool
qualifies: MuCheck has had no release since 2023, and sydtest's mutation
testing isn't under an OSI-approved licence. universalmutator works on any
language, because it rewrites the source text with regular expressions, so it's
only as good as its rules.

[`universalmutator.rules`](universalmutator.rules) holds the rules for Haskell.
They move each comparison's boundary, flip `==`, `/=`, `&&`, `||`, `True`,
`False`, `min` and `max`, drop `not`, and change arithmetic and numbers by one.
They leave comments, imports and type signatures alone, since changing those
only breaks the build. Pass it with `--only`: the built-in rules are written
for C-like languages, and add mutants that can't compile or can't change
anything.

A full run is slow, so `scripts/audit` mutates only the source files changed
since the base branch. For each file, `mutate` writes the mutants that still
compile, and `analyze_mutants` copies each one over the file in turn, runs the
tests, and puts the file back. The last line fails when the tests kill fewer
than 80% of the mutants:

```sh
rm -rf .mutants
mkdir .mutants
files=$(git diff --name-only --diff-filter=d origin/main... -- 'src/*.hs')
for f in $files; do
  d=.mutants/$f
  mkdir -p "$d"
  mutate "$f" --only universalmutator.rules --mutantDir "$d" \
    --cmd 'cabal build -v0 all'
  analyze_mutants "$f" 'cabal test -v0 all' --mutantDir "$d" \
    --prefix "$d/run"
done
killed=$(find .mutants -name run.killed.txt -exec cat {} + | wc -l)
total=$(find .mutants -name 'run.*killed.txt' -exec cat {} + | wc -l)
echo "Mutation score: $killed of $total mutants killed"
[ "$((killed * 100))" -ge "$((total * 80))" ]
```

Install it with pip, pinned to the version this guide was checked with:

```sh
pip install universalmutator==1.14.1
```

- `cabal build` and `cabal test` rebuild from source, which each mutant needs,
  since it replaces the file on disk.
- `--cmd` drops the mutants GHC rejects, so a type error isn't counted as a
  kill. Each check is a build, which is why only changed files run. Name the
  file in `--cmd`, not the `MUTANT` placeholder, which crashes version 1.14.1.
- A test run that takes longer than 30 seconds is stopped and counted as a
  kill. If the build and tests take longer, give `analyze_mutants` a larger
  `--timeout`.
- Run it on a clean working tree, and add `.mutants/` to `.gitignore`. If a run
  is interrupted, `git status` shows a file it left mutated.

80% is the same bar as coverage. Some mutants can't change what the code does,
so 100% is rarely reachable; 80% leaves room for them and still fails a change
whose tests check little.

`.mutants/<file>/run.notkilled.txt` lists the survivors of each file. Compare
one with the source to see what changed:

```text
$ diff src/Grade.hs .mutants/src/Grade.hs/Grade.mutant.5.hs
8c8
<     | score >= 50 = 'P' -- the pass mark, 50
---
>     | score > 50 = 'P' -- the pass mark, 50
```

Read it as a missing test: here, no test passes exactly 50, so the boundary
isn't pinned down. Write the test that fails on the mutant, not one that just
runs the line. A mutant that can't change behaviour needs no test; the
threshold allows for it.

### Architecture

The build enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, so no
extra tool is needed. Make each layer its own library component in the
`.cabal` file. A component can import modules only from the libraries in its
`build-depends`, so a core that imports an edge fails to compile, and Cabal
rejects any dependency cycle between components.

Name each layer's library, and list the layers it may use as
`<package>:<library>`. Each component imports the `shared` stanza from the
[template](#compiler-warnings). The names are examples: replace them with the
layers in the project's `design.md`.

```cabal
-- The core depends on no other layer.
library core
    import:          shared
    hs-source-dirs:  core
    exposed-modules: App.Core.Greeting

-- Each edge depends only on the core.
library adapters
    import:          shared
    hs-source-dirs:  adapters
    exposed-modules: App.Adapters.Console
    build-depends:   app:core

-- The program wires the layers together, so it depends on them all.
executable app
    import:         shared
    hs-source-dirs: cli
    main-is:        Main.hs
    build-depends:  app:core, app:adapters
```

A breach fails the build: GHC reports that the edge's module is in a hidden
package, and Cabal reports a dependency cycle if the core lists an edge in
its `build-depends`:

```sh
cabal build all --ghc-options=-Werror
```

## Sources

- [universalmutator](https://github.com/agroce/universalmutator)
- [universalmutator on PyPI](https://pypi.org/project/universalmutator/1.14.1/)
