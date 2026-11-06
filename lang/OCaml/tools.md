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

## Config files

These files are drop-in templates: copy them into the project root.

| File | Read by |
| --- | --- |
| [.editorconfig](.editorconfig) | Every editor and IDE, through EditorConfig |
| [.ocamlformat](.ocamlformat) | ocamlformat |
| [dune-project](dune-project) | dune (merge into the project's `dune-project`) |
| [dune](dune) | dune: warning flags and bisect_ppx instrumentation |
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
`dune` file. The template also enables coverage instrumentation (see
[Coverage](#coverage)):

```lisp
; Template: the env stanza goes in the project's root dune file, and the
; instrumentation field in every library's own dune file.

(env
 (dev
  (flags
   (:standard -w @a-40-41-42-44-45))))

(library
 (name app)
 (instrumentation
  (backend bisect_ppx)))
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
