# x86 Assembly (MASM) Tools

The free/open source tools that lint, format and check x86 Assembly (MASM)
code, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

Microsoft's own assemblers, `ml` and `ml64`, are proprietary, so they aren't
listed here. The open-source assemblers below accept the MASM language.

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [UASM](https://github.com/Terraspace/UASM) | Sybase Open Watcom Public License 1.0 | Linting | Assembling 32- and 64-bit code, and linting through its warnings |
| [JWasm](https://github.com/Baron-von-Riedesel/JWasm) | Sybase Open Watcom Public License 1.0 | Linting | A second assembler, to check that code doesn't depend on one assembler's extensions |
| [llvm-ml](https://llvm.org/) (part of LLVM) | Apache-2.0 with LLVM exception | Linting | A MASM-compatible assembler that covers part of the MASM language |
| `llvm-readobj`, `llvm-objdump`, `llvm-nm` (LLVM) | Apache-2.0 WITH LLVM-exception | Auditing, Code quality | Checking Windows images for DEP, ASLR and unwind data, reviewing disassembly, and checking the layers |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [DynamoRIO](https://dynamorio.org/) (drcov) | BSD-3-Clause | Code quality | Measuring line coverage of the tests on Windows |
| [universalmutator](https://github.com/agroce/universalmutator) | Apache-2.0 | Code quality | Mutation testing |

The Sybase Open Watcom Public License is OSI-approved. The FSF and Debian
don't consider it free, because it requires publishing changes even when the
changed program is only used privately. Projects that accept only FSF-free
tools can use llvm-ml, after checking that it supports every feature their
code uses. Today it can't assemble code that follows this guide: llvm-ml
rejects `PROC` parameter lists, and the `OPTION CASEMAP:NONE` and
`OPTION PROC:PRIVATE` lines that the
[coding style](coding-style.md#directives-and-sections) puts at the top of
every file.

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.jscpd.json`](.jscpd.json) | jscpd |
| [`universalmutator.rules`](universalmutator.rules) | universalmutator |

## Assembler warnings

Assembler warnings are the lint gate. Code must assemble with **no warnings**
using at least these flags:

```sh
# 64-bit Windows (COFF)
uasm -win64 -Zi -W3 -WX buf.asm

# 32-bit Windows (COFF)
uasm -coff -Zi -W3 -WX buf.asm
```

- `-W3` raises the warning level, and `-WX` turns warnings into errors, so a
  warning can't slip through a build.
- `-Zi` emits debug information, so debuggers and profilers can map addresses
  back to source lines.
- When a warning fires, change the code so it no longer triggers. Never lower
  the warning level for the whole build.
- When reviewing instruction encodings, generate a listing with `-Fl`.

## Auditing

### Security analysis

No maintained FOSS static analyser reads assembly source, so audit the linked
program instead. One assembly object can turn off a protection for the whole
program it's linked into.

On Windows, check that the linked image opts in to DEP and ASLR, and that
every routine that needs unwind data has it:

```sh
llvm-readobj --file-headers build/app.exe
llvm-readobj --unwind build/buf.obj
```

The file headers' DLL characteristics must include `NX_COMPAT`,
`DYNAMIC_BASE` and `HIGH_ENTROPY_VA`. The unwind listing must have an entry
for every routine that calls others or changes `rsp`, or exceptions and
debuggers can't walk the stack through it.

### Dependency vulnerabilities

Assembly has no package manager, so there are no third-party dependencies to
audit.

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

No maintained FOSS tool measures complexity in assembly, and lizard doesn't
read it. The closest check is the disassembly, which shows each routine's
length and every branch for review:

```sh
llvm-objdump -d --no-show-raw-insn build/buf.obj
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format nasm --min-tokens 50 --exit-code 1 src
```

jscpd has no format for MASM, so it reads `.asm` files with its `nasm`
grammar. Duplicate detection compares token sequences, so repeated
instruction sequences are still found.

### Coverage

Compiler coverage (`gcov`, `llvm-cov`) only instruments C, so it can't see
inside an assembly routine. Measure the routines' coverage from the C test
harness (see [Testing](idioms.md#testing)) under a binary-instrumentation
tool instead. It maps each executed instruction back to its source line
through the debug information the assembler records.

On Windows, DynamoRIO's drcov records the executed code, and drcov2lcov turns
its logs into an lcov report:

```sh
drrun -t drcov -- build/tests.exe
drcov2lcov -dir . -output build/coverage.info -src_filter src
```

### Mutation testing

universalmutator makes small changes to the code, such as turning `jge` into
`jg`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. No maintained mutation
testing tool is written for x86 assembly. universalmutator works on any
language, because it rewrites the source text with regular expressions, so it's
only as good as its rules.

[`universalmutator.rules`](universalmutator.rules) holds the rules for x86.
They move and flip the condition of each jump, `setcc` and `cmovcc`, swap `add`
and `sub` and `inc` and `dec`, change immediates by one, and delete
instructions. They leave comments, directives and labels alone, since changing
those only breaks the build or changes nothing. Pass it with `--only`: the
built-in rules are written for C-like languages, and add mutants that can't
compile or can't change anything.

A full run is slow, so `scripts/audit` mutates only the source files changed
since the base branch. For each file, `mutate` writes the mutants that still
compile, and `analyze_mutants` copies each one over the file in turn, runs the
tests, and puts the file back. The last line fails when the tests kill fewer
than 80% of the mutants:

```sh
rm -rf .mutants
mkdir .mutants
files=$(git diff --name-only --diff-filter=d origin/main... -- 'src/*.asm')
for f in $files; do
  d=.mutants/$f
  mkdir -p "$d"
  mutate "$f" --only universalmutator.rules --mutantDir "$d" \
    --cmd "uasm -win64 -W3 -WX -Fo $d/check.obj $f"
  analyze_mutants "$f" 'make test' --mutantDir "$d" --prefix "$d/run"
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

- Replace `make test` with the project's test command that builds and runs the
  C test harness. It must rebuild from source, since each mutant replaces the
  file on disk.
- `--cmd` drops the mutants that don't assemble, so a build failure isn't
  counted as a kill. It uses UASM with the flags from
  [Assembler warnings](#assembler-warnings). Name the file in `--cmd`, not the
  `MUTANT` placeholder, which crashes version 1.14.1.
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
$ diff src/grade.asm .mutants/src/grade.asm/grade.mutant.4.asm
11c11
< 	jge	grade_a
---
> 	jg	grade_a
```

Read it as a missing test: here, the jump to the top grade follows
`cmp ecx, 90`, and no test passes exactly 90, so the boundary isn't pinned
down. Write the test that fails on the mutant, not one that just runs the line.
A mutant that can't change behaviour needs no test; the threshold allows for
it.

### Architecture

An architecture test in `scripts/check` enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, with
`llvm-nm`. Assembly has no modules, and `OPTION PROC:PRIVATE` hides a
procedure only from other files. A layer's own files call each other through
`PUBLIC` symbols, and `EXTERN` reaches a `PUBLIC` symbol in any file, so
`PUBLIC` can't mark the layer's boundary. Nor can the linker: Microsoft's
`link` and `lld-link` can't join a layer's objects into one with a partial
link, and GNU ld's partial link drops the CodeView debug information that
`-Zi` writes.

Instead, check which symbols each object uses. Keep each layer's sources in
its own directory under `src`, and list its entry points in an
`exports.txt` beside them, one symbol per line. `#` starts a comment. The
layer names are examples: replace them with the layers in the project's
`design.md`. `src/core/exports.txt`:

```text
# The core's entry points, declared in src/core/price.h.
price_parse
```

The build assembles each layer's files into its own directory. It clears
the directory first, so an object left over from a deleted file can't slip
in. Compile the tests into `build/tests` too, so the check covers them:

```sh
for layer in core adapters cli; do
  rm -rf "build/$layer"
  mkdir -p "build/$layer"
  for f in "src/$layer"/*.asm; do
    uasm -win64 -Zi -W3 -WX -Fo "build/$layer/$(basename "$f" .asm).obj" \
      "$f"
  done
done
```

`scripts/check` then checks the objects, before linking. First, the core
never uses an edge: no symbol the core leaves undefined may be one an edge
defines.

```sh
llvm-nm -u build/core/* | awk 'NF > 1 {print $NF}' | sort -u \
  >build/core.uses
for edge in adapters cli; do
  llvm-nm -g --defined-only "build/$edge"/* | awk 'NF > 1 {print $NF}' |
    sort -u | comm -12 build/core.uses - >build/core.breach
  if [ -s build/core.breach ]; then
    sed "s/^/the core must not use $edge: /" build/core.breach >&2
    exit 1
  fi
done
```

A breach prints each symbol, such as
`the core must not use adapters: console_write`.

Second, code outside a layer, and the layer's tests, use only its entry
points. The check lists each layer's internal symbols, its `PUBLIC` ones
that aren't in `exports.txt`, and fails when any object outside the layer
uses one:

```sh
: >build/breaches.txt
for layer in core adapters cli; do
  awk 'NF && $1 !~ /^#/ {print $1}' "src/$layer/exports.txt" | sort -u \
    >"build/$layer.exports"
  llvm-nm -g --defined-only "build/$layer"/* | awk 'NF > 1 {print $NF}' |
    sort -u | comm -23 - "build/$layer.exports" >"build/$layer.internal"
done
for obj in build/*/*; do
  owner=${obj#build/}
  owner=${owner%%/*}
  for layer in core adapters cli; do
    if [ "$layer" != "$owner" ]; then
      llvm-nm -u "$obj" | awk 'NF > 1 {print $NF}' | sort -u |
        comm -12 - "build/$layer.internal" |
        sed "s|.*|$obj uses &, internal to $layer|" >>build/breaches.txt
    fi
  done
done
if [ -s build/breaches.txt ]; then
  cat build/breaches.txt >&2
  exit 1
fi
```

A breach names the object and the symbol, such as
`build/adapters/peek.obj uses digit_value, internal to core`. The core's
own files still share `digit_value`, because the check only looks outside
the layer. In 32-bit code, list each name in `exports.txt` as `llvm-nm`
prints it, with its decoration, such as `_price_parse`.

To prove the first check bites, add a core file that refers to an edge, and
keep it as `scripts/breaches/core-uses-edge.patch`:

```text
Rule: the core never uses an edge
Fails with: the core must not use adapters: console_write
diff --git a/src/core/leak.asm b/src/core/leak.asm
new file mode 100644
index 0000000..2b51cb8
--- /dev/null
+++ b/src/core/leak.asm
@@ -0,0 +1,11 @@
+; leak.asm - Breach: the core refers to an edge.
+
+OPTION	CASEMAP:NONE
+OPTION	PROC:PRIVATE
+
+EXTERN	console_write:PROC
+
+.DATA
+leak	QWORD	console_write
+
+END
```

Prove the second the same way, with a file such as `src/adapters/peek.asm`
that refers to `digit_value`. It fails with
`build/adapters/peek.obj uses digit_value, internal to core`.

The check reads names, not addresses. An entry point that hands out the
address of an internal procedure or table, a file that reaches into another
layer's data at a fixed offset, and a file that includes another layer's
private `.inc` file for its constants and macros all pass, so review must
catch them. When existing code must use an internal symbol, add it to that
layer's `exports.txt`, with a comment naming the breach and how to fix it.
That opens it to every caller: the check can't exempt a single one. This
was checked with UASM 2.59, JWasm 2.21 and LLVM 19.

## Sources

- [universalmutator](https://github.com/agroce/universalmutator)
- [universalmutator on PyPI](https://pypi.org/project/universalmutator/1.14.1/)
- [llvm-nm](https://llvm.org/docs/CommandGuide/llvm-nm.html)
