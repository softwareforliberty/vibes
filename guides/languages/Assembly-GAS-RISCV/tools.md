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
