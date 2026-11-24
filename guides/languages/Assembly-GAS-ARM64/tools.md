# ARM64 Assembly (GNU as) Tools

The free/open source tools that lint, format and check ARM64 Assembly (GNU as)
code, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GNU as](https://sourceware.org/binutils/) (GNU Binutils), driven by [GCC](https://gcc.gnu.org/) | GPL-3.0-or-later | Linting | Preprocessing and assembling `.S` files on Linux and BSD |
| [LLVM](https://llvm.org/): Clang's integrated assembler and `llvm-mc` | Apache-2.0 WITH LLVM-exception | Linting | Assembling on Apple platforms and with Clang, and inspecting encodings |
| [checksec](https://github.com/slimm609/checksec) | BSD-3-Clause | Auditing | Checking that ELF programs keep NX, PIE and RELRO |
| `readelf`, `objdump`, `ld`, `objcopy`, `nm` (GNU Binutils) | GPL-3.0-or-later | Auditing, Code quality | Inspecting linked programs and their BTI and PAC notes, reviewing disassembly, and enforcing the layers |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [kcov](https://github.com/SimonKagstrom/kcov) | GPL-2.0 | Code quality | Measuring line coverage of the tests on Linux |
| [DynamoRIO](https://dynamorio.org/) (drcov) | BSD-3-Clause | Code quality | Measuring line coverage of the tests on Linux |
| [universalmutator](https://github.com/agroce/universalmutator) | Apache-2.0 | Code quality | Mutation testing |

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
# Linux and BSD, with GCC and GNU as
aarch64-linux-gnu-gcc -c -g -mbranch-protection=standard \
    -Wa,--fatal-warnings -o buf.o buf.S

# Apple platforms, with Clang
clang -c -g -arch arm64 -Wa,--fatal-warnings -o buf.o buf.S
```

- Always assemble through the compiler driver (`gcc` or `clang`), never by
  calling `as` directly. The driver runs the C preprocessor over `.S` files
  and passes the right target options.
- `-Wa,--fatal-warnings` turns assembler warnings into errors, so a warning
  can't slip through a build.
- `-g` records source line information, so debuggers and profilers can map
  addresses back to assembly lines.
- `-mbranch-protection=standard` turns on the branch-protection macros that
  the [function macros](idioms.md#a-shared-header) use (see
  [Branch protection](idioms.md#branch-protection)).
- To review instruction encodings, disassemble the object with
  `objdump -d buf.o`, or assemble preprocessed source with
  `llvm-mc --triple=aarch64 --show-encoding`.

## Auditing

### Security analysis

No maintained FOSS static analyser reads assembly source, so audit the linked
program instead. One assembly object can turn off a protection for the whole
program it's linked into.

On ELF, run checksec on every program or shared library that links the
assembly, and check that NX, PIE and full RELRO are all enabled. An object
without the non-executable stack marker makes the whole stack executable, so
also fail the build when the stack segment is executable:

```sh
checksec file build/app
if readelf -lW build/app | grep -q 'GNU_STACK.*RWE'; then
  echo 'build/app has an executable stack' >&2
  exit 1
fi
```

Bare-metal images have no PIE or RELRO, so check only that no segment is
both writable and executable, as described in the
[linker script tools](../../build/Linker-GNU-ld/tools.md#security-analysis).

The linker turns on BTI and PAC for a program only if every object carries
the GNU property note for them (see
[Branch protection](idioms.md#branch-protection)). One assembly file without
the note turns both off for the whole program, so also check the note on the
linked program:

```sh
readelf -n build/app | grep -q 'AArch64 feature: BTI, PAC'
```

These checks read ELF only. On Apple platforms, Apple's toolchain applies the
equivalent protections, and no FOSS tool audits Mach-O programs for them.

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
objdump -d --no-show-raw-insn build/buf.o
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format armasm --formats-exts "armasm:S" --min-tokens 50 \
    --exit-code 1 src
```

jscpd has no format for GNU as, so `--formats-exts` reads `.S` files with its
`armasm` grammar. Duplicate detection compares token sequences, so repeated
instruction sequences are still found.

### Coverage

Compiler coverage (`gcov`, `llvm-cov`) only instruments C, so it can't see
inside an assembly routine. Measure the routines' coverage from the C test
harness (see [Testing](idioms.md#testing)) under a binary-instrumentation
tool instead. It maps each executed instruction back to its source line
through the debug information the assembler records.

On Linux, kcov runs the tests and writes HTML and Cobertura reports:

```sh
kcov --include-path=src build/coverage build/tests
```

On Linux, DynamoRIO's drcov records the executed code, and drcov2lcov turns
its logs into an lcov report:

```sh
drrun -t drcov -- build/tests
drcov2lcov -dir . -output build/coverage.info -src_filter src
```

Neither tool runs on Apple platforms. Measure coverage on Linux AArch64,
which builds the same source.

### Mutation testing

universalmutator makes small changes to the code, such as turning `b.ge` into
`b.gt`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. No maintained mutation
testing tool is written for ARM64 assembly. universalmutator works on any
language, because it rewrites the source text with regular expressions, so it's
only as good as its rules.

[`universalmutator.rules`](universalmutator.rules) holds the rules for ARM64.
They move and flip the condition of each branch, `csel`, `cset` and `ccmp`,
swap `cbz` and `cbnz`, swap `add` and `sub`, change immediates by one, and
delete instructions. They leave comments, directives and labels alone, since
changing those only breaks the build or changes nothing. Pass it with `--only`:
the built-in rules are written for C-like languages, and add mutants that can't
compile or can't change anything.

A full run is slow, so `scripts/audit` mutates only the source files changed
since the base branch. For each file, `mutate` writes the mutants that still
compile, and `analyze_mutants` copies each one over the file in turn, runs the
tests, and puts the file back. The last line fails when the tests kill fewer
than 80% of the mutants:

```sh
rm -rf .mutants
mkdir .mutants
cc='aarch64-linux-gnu-gcc -c -mbranch-protection=standard -Wa,--fatal-warnings'
files=$(git diff --name-only --diff-filter=d origin/main... -- 'src/*.S')
for f in $files; do
  d=.mutants/$f
  mkdir -p "$d"
  mutate "$f" --only universalmutator.rules --mutantDir "$d" \
    --cmd "$cc -o $d/check.o $f"
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
  counted as a kill. `cc` is the assembler command from
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
$ diff src/grade.S .mutants/src/grade.S/grade.mutant.11.S
11c11
< 	b.ge	.Lgrade_p
---
> 	b.gt	.Lgrade_p
```

Read it as a missing test: here, the branch to the pass grade follows
`cmp w0, #50`, and no test passes exactly 50, so the boundary isn't pinned
down. Write the test that fails on the mutant, not one that just runs the line.
A mutant that can't change behaviour needs no test; the threshold allows for
it.

### Architecture

The linker enforces the layers, as the
[architecture guide](../../../architecture/README.md#enforce-it) asks, with
`ld`, `objcopy` and `nm` from GNU Binutils. Assembly has no modules: `.globl`
makes a symbol visible to every object in the program. A layer's own files
call each other through global symbols, so `.globl` can't mark the layer's
boundary. Nor can `.hidden`: it keeps a symbol out of a shared library's
exports, but every object linked into that library or program still sees it.

Instead, build each layer as one object that exports only its entry points.
Keep each layer's sources in its own directory under `src`, and list its
entry points in an `exports.txt` beside them, one symbol per line. `#` starts
a comment. The layer names are examples: replace them with the layers in the
project's `design.md`. `src/core/exports.txt`:

```text
# The core's entry points, declared in src/core/price.h.
price_parse
```

The build assembles each layer's files, joins them into one object with a
partial link (`ld -r`), and has `objcopy` make every other global symbol
local. It clears each layer's directory first, so an object left over from a
deleted file can't slip in:

```sh
for layer in core adapters cli; do
  rm -rf "build/$layer"
  mkdir -p "build/$layer"
  for f in "src/$layer"/*.S; do
    aarch64-linux-gnu-gcc -c -g -mbranch-protection=standard \
      -Wa,--fatal-warnings -o "build/$layer/$(basename "$f" .S).o" "$f"
  done
  aarch64-linux-gnu-ld -r -o "build/$layer.o" "build/$layer"/*.o
  aarch64-linux-gnu-objcopy \
    --keep-global-symbols="src/$layer/exports.txt" "build/$layer.o"
done
```

Link the program from the layer objects. Link each layer's tests as their
own program, with that layer's object alone, so they see only its entry
points, as callers do:

```sh
aarch64-linux-gnu-gcc -mbranch-protection=standard -o build/app \
  build/cli.o build/adapters.o build/core.o
aarch64-linux-gnu-gcc -mbranch-protection=standard -o build/core_tests \
  tests/core/*.c build/core.o
```

The core's own files still share `digit_value`, because the partial link
joins them before `objcopy` hides it. An edge or a core test that uses it
fails to link, and the linker names the symbol and where it's used:
``undefined reference to `digit_value'``. The partial link keeps each
object's GNU property note, so BTI and PAC stay on (see
[Security analysis](#security-analysis)).

The core's tests link the core alone, so they also fail when the core uses
an edge. To fail with the rule's name, `scripts/check` also checks the layer
objects, after the loop above and before linking: no symbol the core leaves
undefined may be one an edge defines.

```sh
aarch64-linux-gnu-nm -u build/core/* | awk 'NF > 1 {print $NF}' |
  sort -u >build/core.uses
for edge in adapters cli; do
  aarch64-linux-gnu-nm -g --defined-only "build/$edge"/* |
    awk 'NF > 1 {print $NF}' | sort -u |
    comm -12 build/core.uses - >build/core.breach
  if [ -s build/core.breach ]; then
    sed "s/^/the core must not use $edge: /" build/core.breach >&2
    exit 1
  fi
done
```

A breach prints each symbol, such as
`the core must not use adapters: console_write`. To prove it bites, add a
core file that refers to an edge, and keep it as
`scripts/breaches/core-uses-edge.patch`:

```text
Rule: the core never uses an edge
Fails with: the core must not use adapters: console_write
diff --git a/src/core/leak.S b/src/core/leak.S
new file mode 100644
index 0000000..71c2e56
--- /dev/null
+++ b/src/core/leak.S
@@ -0,0 +1,8 @@
+/* leak.S - Breach: the core refers to an edge. */
+
+	.data
+leak:	.quad	console_write
+
+#ifdef __ELF__
+	.section	.note.GNU-stack, "", %progbits
+#endif /* __ELF__ */
```

Prove the entry points the same way, with a file such as
`src/adapters/peek.S` that refers to `digit_value`. It fails with
``undefined reference to `digit_value'``.

These commands read ELF, and were checked only there. On Apple platforms,
every symbol carries a leading underscore and the tools take other flags, so
run the check on the Linux AArch64 build, which assembles the same source.

The linker checks names, not addresses. An entry point that hands out the
address of an internal routine or table, a file that reaches into another
layer's data at a fixed offset, and a file that includes another layer's
private header for its constants and macros all pass, so review must catch
them. When existing code must use an internal symbol, add it to that layer's
`exports.txt`, with a comment naming the breach and how to fix it. That
opens it to every caller: the linker can't exempt a single one. This was
checked with GNU Binutils 2.44.

## Sources

- [universalmutator](https://github.com/agroce/universalmutator)
- [universalmutator on PyPI](https://pypi.org/project/universalmutator/1.14.1/)
- [GNU ld: command-line options](https://sourceware.org/binutils/docs/ld/Options.html),
  for partial linking with `-r`
- [GNU objcopy](https://sourceware.org/binutils/docs/binutils/objcopy.html)
- [GNU nm](https://sourceware.org/binutils/docs/binutils/nm.html)
