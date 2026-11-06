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
| `llvm-readobj`, `llvm-objdump` (LLVM) | Apache-2.0 WITH LLVM-exception | Auditing, Code quality | Checking Windows images for DEP, ASLR and unwind data, and reviewing disassembly |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [DynamoRIO](https://dynamorio.org/) (drcov) | BSD-3-Clause | Code quality | Measuring line coverage of the tests on Windows |

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
