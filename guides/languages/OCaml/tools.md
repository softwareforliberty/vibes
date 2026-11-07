# OCaml Tools

The free/open source tools that lint, format and check OCaml code, and how to
run them. They enforce the rules in [coding-style.md](coding-style.md) and
[idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [OCaml](https://ocaml.org/) compiler | LGPL-2.1 with linking exception | Linting, Code quality | Compiling, and linting and dead-code checks through its warnings |
| [dune](https://dune.build/) | MIT | Linting | Building, and setting the warning flags per profile |
| [ocamlformat](https://github.com/ocaml-ppx/ocamlformat) | MIT | Formatting | Formatting source files |
| [zanuda](https://github.com/Kakadu/zanuda) | LGPL-3.0-only | Linting | Linting typed source for common mistakes |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [Opengrep](https://github.com/opengrep/opengrep) | LGPL-2.1 | Auditing | Security analysis with pattern and taint rules |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [bisect_ppx](https://github.com/aantron/bisect_ppx) | MIT | Code quality | Measuring test coverage |
| [mutaml](https://github.com/jmid/mutaml) | BSD-2-Clause | Code quality | Mutation testing |

## Config files

These files are drop-in templates: copy them into the project root.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor and IDE, through EditorConfig |
| [.ocamlformat](.ocamlformat) | ocamlformat |
| [dune-project](dune-project) | dune (merge into the project's `dune-project`) |
| [dune](dune) | dune: warning flags, and bisect_ppx and mutaml instrumentation |
| [.opengrep/ocaml.yaml](.opengrep/ocaml.yaml) | Opengrep |
| [.jscpd.json](.jscpd.json) | jscpd |

## Formatting

ocamlformat owns layout. Check formatting in CI, and fix it locally with
`dune fmt`:

```sh
dune build @fmt
```

Put the settings in `.ocamlformat` at the project root. Pin the version, so
everyone formats the same way:

```ini
version = 0.27.0
profile = default
margin = 80
break-cases = fit-or-vertical
break-infix = fit-or-vertical
doc-comments = before
type-decl = sparse
```

The last four settings give the layout in [coding-style.md](coding-style.md):
every match case on its own line, every step of a `|>` chain on its own line
once the chain doesn't fit on one, doc comments before the item, and one
field or constructor per line in every type.

## Compiler warnings

Compiler warnings are the main lint gate. dune's default development
profile makes the standard warnings errors; turn on the rest in the root
`dune` file. The template also enables the instrumentation for
[coverage](#coverage) and [mutation testing](#mutation-testing):

```lisp
; Template: the env stanza goes in the project's root dune file, and the
; instrumentation fields in every library's own dune file.

(env
 (dev
  (flags
   (:standard -w @a-40-41-42-44-45))))

(library
 (name app)
 (instrumentation
  (backend bisect_ppx))
 (instrumentation
  (backend mutaml -mut-rate 100)))
```

This enables every warning except the ones about name resolution and
shadowing by `open` (40–42, 44, 45), which fire on ordinary code. It keeps
warning 4 (fragile match), which flags the catch-all `_` cases that
[idioms.md](idioms.md#pattern-matching) forbids, and warning 70 (missing
interface), which enforces an `.mli` for every module.

The release profile, which opam uses when installing, doesn't apply these
flags, so a newer compiler with new warnings doesn't break a user's build.
Build with the default profile in CI:

```sh
dune build @check @runtest
```

## Linting

zanuda reads the typed tree dune produces and reports common mistakes, such
as needless mutual recursion and single-case matches. Build first, then run
it from the project root:

```sh
dune build @check
zanuda -no-top_file_license -dir .
```

`-no-top_file_license` turns off the one lint that expects a copyright
comment at the top of every file, which this guide doesn't ask for.

## Auditing

### Security analysis

Opengrep is the open-source fork of Semgrep. Run it with rules you write, or
with rule sets under a FOSS licence. The Semgrep Registry rules are under the
Semgrep Rules License, which isn't a free/open source licence, so don't use
them.

```sh
opengrep scan --config .opengrep/ --error
```

The starter rules in [.opengrep/ocaml.yaml](.opengrep/ocaml.yaml) flag the
calls the project must not make with untrusted input: `Sys.command` and
`Unix.open_process` with a built-up command string, and `Marshal` on
external data. Add rules as the project finds new risks.

### Dependency vulnerabilities

No maintained FOSS tool checks opam dependencies against known
vulnerabilities; OSV-Scanner doesn't read opam lock files. The closest check
is to pin exact versions with `opam lock`, commit the `.opam.locked` file,
and review the pinned versions against the
[OCaml security advisories](https://github.com/ocaml/security-advisories)
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

No maintained FOSS tool measures function complexity for OCaml; lizard
doesn't support it. The closest check is review against the
function-structure rules in [coding-style.md](coding-style.md#functions),
plus zanuda's lints, which flag needlessly nested matches.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format ocaml --min-tokens 50 --exit-code 1 src
```

### Dead code

The warnings above find unused values (32), types (34), constructors (37),
record fields (69), variables (26, 27) and opens (33). Values are only
reported as unused when the `.mli` doesn't export them, which is one more
reason every module has one.

### Coverage

Measure branch coverage on every test run, and fail the build when it falls
below 80%. Raise the minimum as coverage grows; never lower it to make a
build pass.

bisect_ppx instruments every branch of `if` and `match`. Enable it in each
library's `dune` stanza:

```lisp
(library
 (name app)
 (instrumentation
  (backend bisect_ppx)))
```

It has no minimum of its own, so check its summary line. The check also
fails when there's no summary, such as when the tests didn't run:

```sh
dune runtest --instrument-with bisect_ppx --force
bisect-ppx-report summary | tee coverage.txt
awk -F'[(%]' '/Coverage:/ { seen = 1; if ($2 < 80) bad = 1 }
    END { exit bad || !seen }' coverage.txt
```

### Mutation testing

mutaml makes small changes to the code, such as turning `90` into `91` or
negating an `if`, and runs the tests against each one. A change the tests still
pass, a surviving mutant, is behaviour no test pins down. It's a ppx, like
bisect_ppx: dune builds every mutant into the program once, and each test run
switches one on, so no mutant needs a build of its own, and every mutant
type-checks.

Enable it in each library's `dune` stanza, next to bisect_ppx. `-mut-rate 100`
makes every mutant it can; the default, 50, picks a random half on each build,
so two runs wouldn't agree:

```lisp
(library
 (name app)
 (instrumentation
  (backend bisect_ppx))
 (instrumentation
  (backend mutaml -mut-rate 100)))
```

A full run is slow, so `scripts/audit` tests only the mutants in source files
changed since the base branch. mutaml has no minimum score of its own, so the
command counts the results in `mutaml-report.json`, where a status of 0 means
the tests passed and the mutant survived. The last line fails when the tests
kill fewer than 80% of the mutants:

```sh
rm -rf _build _mutations .mutants
mkdir .mutants
dune build --instrument-with mutaml test
files=$(git diff --name-only --diff-filter=d origin/main... -- 'src/*.ml')
for f in $files; do
  mutaml-runner --muts "${f%.ml}.muts" 'dune exec --no-build test/test.exe'
  mutaml-report
  cp mutaml-report.json ".mutants/$(echo "$f" | tr / -).json"
done
results=$(find .mutants -name '*.json' -exec cat {} +)
total=$(echo "$results" | grep -o '"status":[0-9]*' | wc -l)
survived=$(echo "$results" | grep -o '"status":0[,}]' | wc -l)
killed=$((total - survived))
echo "Mutation score: $killed of $total mutants killed"
[ "$((killed * 100))" -ge "$((total * 80))" ]
```

Install it with opam, pinned to the version this guide was checked with:

```sh
opam install mutaml.0.4
```

- mutaml writes files that dune doesn't track, so the command starts from an
  empty `_build`.
- Replace `test/test.exe` with the project's test executable. `--no-build` runs
  the one the first step built. Don't use a command that builds, such as
  `dune test`: mutaml writes the mutants while building, after the runner has
  looked for them.
- Add `_mutations/`, `.mutants/` and `mutaml-report.json` to `.gitignore`.

80% is the same bar as coverage. Some mutants can't change what the code does,
so 100% is rarely reachable; 80% leaves room for them and still fails a change
whose tests check little.

`mutaml-report` prints each survivor as a diff:

```text
--- src/grade.ml
+++ src/grade.ml-mutant0
@@ -1,6 +1,6 @@
 (* Grades a score out of 100. *)

 let grade score =
-  if score >= 90 then 'A'
+  if score >= 91 then 'A'
   else if score >= 50 then (* the pass mark, 50 *) 'P'
   else 'F'
```

Read it as a missing test: here, no test passes exactly 90, so the boundary
isn't pinned down. Write the test that fails on the mutant, not one that just
runs the line. A mutant that can't change behaviour needs no test; the
threshold allows for it.

### Architecture

The build enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, so no
extra tool is needed. Make each layer its own dune library. A library can use
only the libraries its `libraries` field lists, so a core that uses an edge
fails to compile, and dune rejects any dependency cycle between libraries.

Give each layer a `dune` file in its own directory. Each library also keeps
the `instrumentation` fields from the [template](#compiler-warnings). The
names are examples: replace them with the layers in the project's
`design.md`.

`lib/core/dune`:

```lisp
; The core depends on no other layer.

(library
 (name app_core))
```

`lib/adapters/dune`:

```lisp
; Each edge depends only on the core.

(library
 (name app_adapters)
 (libraries app_core))
```

`bin/dune`:

```lisp
; The program wires the layers together, so it depends on them all.

(executable
 (name main)
 (libraries app_core app_adapters))
```

A breach fails the build with `Unbound module App_adapters`, or with
`Dependency cycle between` the libraries if the core lists an edge:

```sh
dune build @check
```

## Sources

- [mutaml](https://github.com/jmid/mutaml)
- [mutaml on opam](https://ocaml.org/p/mutaml/0.4)
- [dune instrumentation](https://dune.readthedocs.io/en/stable/instrumentation.html)
