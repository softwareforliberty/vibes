# x86 Assembly (NASM) Tools

The free/open source tools that lint, format and check x86 Assembly (NASM)
code, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [NASM](https://www.nasm.us/) 2.15 or later | BSD-2-Clause | Linting | Assembling, and linting through its warning classes |
| [checksec](https://github.com/slimm609/checksec) | BSD-3-Clause | Auditing | Checking that ELF programs keep NX, PIE and RELRO |
| `readelf`, `objdump` (GNU Binutils) | GPLv3 | Auditing, Code quality | Inspecting linked programs, and reviewing disassembly |
| `llvm-readobj` (LLVM) | Apache-2.0 WITH LLVM-exception | Auditing | Checking Windows images for DEP, ASLR and unwind data |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [kcov](https://github.com/SimonKagstrom/kcov) | GPL-2.0 | Code quality | Measuring line coverage of the tests on Linux |
| [DynamoRIO](https://dynamorio.org/) (drcov) | BSD-3-Clause | Code quality | Measuring line coverage of the tests on Linux and Windows |

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Assembler warnings

Assembler warnings are the lint gate. Code must assemble with **no warnings**
using at least these flags:

```sh
# 64-bit ELF (Linux, BSD)
nasm -f elf64 -g -F dwarf -w+all -w+error -o buf.o buf.asm

# 32-bit ELF
nasm -f elf32 -g -F dwarf -w+all -w+error -o buf.o buf.asm

# 64-bit Windows
nasm -f win64 -g -F cv8 -w+all -w+error -o buf.obj buf.asm
```

- `-w+all` turns on every warning class, and `-w+error` turns warnings into
  errors, so a warning can't slip through a build.
- `-g` with the format's debug format (`dwarf` or `cv8`) lets debuggers and
  profilers map addresses back to source lines.
- When a warning is a deliberate exception, turn it off for those lines only,
  with `[warning push]`, `[warning -<class>]` and `[warning pop]`, plus a
  comment explaining why. Never turn a warning off for the whole build.
- When reviewing instruction encodings, generate a listing with
  `-l buf.lst`.

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
[linker script tools](../Linker-GNU-ld/tools.md#security-analysis).

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
objdump -d --no-show-raw-insn build/buf.o
```

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format nasm --min-tokens 50 --exitCode 1 src
```

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

On Linux and Windows, DynamoRIO's drcov records the executed code, and
drcov2lcov turns its logs into an lcov report:

```sh
drrun -t drcov -- build/tests
drcov2lcov -dir . -output build/coverage.info -src_filter src
```
