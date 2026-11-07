# ARM64 Assembly (GNU as) Tools

The free/open source tools that lint, format and check ARM64 Assembly (GNU as)
code, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GNU as](https://sourceware.org/binutils/) (GNU Binutils), driven by [GCC](https://gcc.gnu.org/) | GPL-3.0-or-later | Linting | Preprocessing and assembling `.S` files on Linux and BSD |
| [LLVM](https://llvm.org/): Clang's integrated assembler and `llvm-mc` | Apache-2.0 WITH LLVM-exception | Linting | Assembling on Apple platforms and with Clang, and inspecting encodings |
| [checksec](https://github.com/slimm609/checksec) | BSD-3-Clause | Auditing | Checking that ELF programs keep NX, PIE and RELRO |
| `readelf`, `objdump` (GNU Binutils) | GPL-3.0-or-later | Auditing, Code quality | Inspecting linked programs and their BTI and PAC notes, and reviewing disassembly |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |
| [kcov](https://github.com/SimonKagstrom/kcov) | GPL-2.0 | Code quality | Measuring line coverage of the tests on Linux |
| [DynamoRIO](https://dynamorio.org/) (drcov) | BSD-3-Clause | Code quality | Measuring line coverage of the tests on Linux |

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
