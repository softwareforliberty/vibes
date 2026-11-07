# RISC-V Assembly (GNU as) Tools

The free/open source tools that lint, format and check RISC-V Assembly (GNU as)
code, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GNU as](https://sourceware.org/binutils/) (GNU Binutils), driven by [GCC](https://gcc.gnu.org/) | GPL-3.0-or-later | Linting | Preprocessing and assembling `.S` files |
| [LLVM](https://llvm.org/): Clang's integrated assembler and `llvm-mc` | Apache-2.0 WITH LLVM-exception | Linting | Assembling with Clang, and inspecting encodings |
| [checksec](https://github.com/slimm609/checksec) | BSD-3-Clause | Auditing | Checking that ELF programs keep NX, PIE and RELRO |
| `readelf`, `objdump` (GNU Binutils) | GPL-3.0-or-later | Auditing, Code quality | Inspecting linked programs, and reviewing disassembly |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [QEMU](https://www.qemu.org/) (`drcov` plugin) | GPL-2.0 | Code quality | Logging which code the tests execute, for coverage review |
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
# RV64, with GCC and GNU as
riscv64-linux-gnu-gcc -c -g -march=rv64gc -mabi=lp64d \
    -Wa,--fatal-warnings -o buf.o buf.S

# RV64, with Clang
clang -c -g --target=riscv64-linux-gnu -march=rv64gc -mabi=lp64d \
    -Wa,--fatal-warnings -o buf.o buf.S

# RV32 bare metal, with GCC and GNU as
riscv64-unknown-elf-gcc -c -g -march=rv32imac -mabi=ilp32 \
    -Wa,--fatal-warnings -o buf.o buf.S
```

- Always assemble through the compiler driver (`gcc` or `clang`), never by
  calling `as` directly. The driver runs the C preprocessor over `.S` files
  and passes the right target options.
- Set `-march` to exactly the extensions the target guarantees. The assembler
  then rejects any instruction the target doesn't have, instead of leaving it
  to fault at run time.
- Set `-mabi` to match the C code the routine links with. Mixing ABIs links
  without complaint but passes arguments in the wrong registers.
- `-Wa,--fatal-warnings` turns assembler warnings into errors, so a warning
  can't slip through a build.
- `-g` records source line information, so debuggers and profilers can map
  addresses back to assembly lines.
- To review instruction encodings, disassemble the object with
  `objdump -d buf.o`, or assemble preprocessed source with
  `llvm-mc --triple=riscv64 --show-encoding`.

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
jscpd --format nasm --formats-exts "nasm:S" --min-tokens 50 --exit-code 1 src
```

jscpd has no format for GNU as, so `--formats-exts` reads `.S` files with its
`nasm` grammar. Duplicate detection compares token sequences, so repeated
instruction sequences are still found.

### Coverage

Compiler coverage (`gcov`, `llvm-cov`) only instruments C, so it can't see
inside an assembly routine. Measure the routines' coverage from the C test
harness (see [Testing](idioms.md#testing)) under a binary-instrumentation
tool instead. It maps each executed instruction back to its source line
through the debug information the assembler records.

No maintained FOSS coverage tool fully supports RISC-V yet: DynamoRIO's
RISC-V port is still preliminary. The closest check is QEMU's `drcov`
plugin, which logs the address of every block the tests execute under
emulation. Compare those addresses with `objdump -d` to find routines and
branches that no test reaches.

### Mutation testing

universalmutator makes small changes to the code, such as turning `bge` into
`bgt`, and runs the tests against each one. A change the tests still pass, a
surviving mutant, is behaviour no test pins down. No maintained mutation
testing tool is written for RISC-V assembly. universalmutator works on any
language, because it rewrites the source text with regular expressions, so it's
only as good as its rules.

[`universalmutator.rules`](universalmutator.rules) holds the rules for RISC-V.
They move and flip the condition of each branch and set-if instruction, swap
`add` and `sub`, change immediates by one, and delete instructions. They leave
comments, directives and labels alone, since changing those only breaks the
build or changes nothing. Pass it with `--only`: the built-in rules are written
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
cc='riscv64-linux-gnu-gcc -c -march=rv64gc -mabi=lp64d -Wa,--fatal-warnings'
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
  C test harness, under `qemu-riscv64` when the machine isn't RISC-V. It must
  rebuild from source, since each mutant replaces the file on disk.
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
$ diff src/grade.S .mutants/src/grade.S/grade.mutant.12.S
11c11
< 	bge	a0, t0, .Lgrade_p
---
> 	bgt	a0, t0, .Lgrade_p
```

Read it as a missing test: here, `t0` holds the pass mark, 50, and no test
passes exactly 50, so the boundary isn't pinned down. Write the test that fails
on the mutant, not one that just runs the line. A mutant that can't change
behaviour needs no test; the threshold allows for it.

## Sources

- [universalmutator](https://github.com/agroce/universalmutator)
- [universalmutator on PyPI](https://pypi.org/project/universalmutator/1.14.1/)
