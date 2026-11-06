# GNU ld Linker Script Tools

The free/open source tools that lint, format and check GNU ld Linker Script
code, and how to run them. They enforce the rules in
[coding-style.md](coding-style.md) and [idioms.md](idioms.md).

| Tool | Licence | Category | Used for |
| --- | --- | --- | --- |
| [GNU ld](https://sourceware.org/binutils/) (GNU Binutils) | GPLv3 | Linting, Code quality | Linking with the script, linting through its warnings, and reporting unused sections |
| [LLD](https://lld.llvm.org/) | Apache-2.0 WITH LLVM-exception | Linting | Linking with the same script, to prove it works with both linkers |
| `readelf`, `objdump`, `nm` (GNU Binutils) | GPLv3 | Auditing | Checking the layout and segment permissions of the linked image |
| [checksec](https://github.com/slimm609/checksec) | BSD-3-Clause | Auditing | Checking that hosted ELF programs keep NX, PIE and RELRO |
| [gitleaks](https://github.com/gitleaks/gitleaks) | MIT | Auditing | Finding secrets committed to the repository |
| [jscpd](https://github.com/kucherenko/jscpd) | MIT | Code quality | Finding duplicated code |

No dedicated linter or formatter for linker scripts exists, so the linkers
themselves are the check.

## Config files

Copy these files into the repository root. Each one matches the
settings on this page.

| File | Read by |
| --- | --- |
| [`.editorconfig`](.editorconfig) | Editors and IDEs, through EditorConfig |
| [`.jscpd.json`](.jscpd.json) | jscpd |

## Linker warnings

Linker warnings are the lint gate. An image must link with **no warnings**,
and with every input section placed by the script, using at least these
flags (passed through the compiler driver):

```sh
gcc -nostdlib -T link.ld \
    -Wl,--fatal-warnings \
    -Wl,--orphan-handling=error \
    -Wl,-Map=build/image.map \
    -o build/image.elf build/start.o build/main.o
```

- `--fatal-warnings` makes the linker treat warnings as errors, so a warning
  can't slip through a build.
- `--orphan-handling=error` stops the link when an input section matches no
  rule in the script. Without it, the linker places such *orphan* sections
  wherever its own heuristics choose, and GNU ld and LLD choose differently.
- `-Map` writes a map file showing where every section and symbol ended up.
  Keep it as a build artifact, so a layout change can be reviewed.
- For scripts that declare memory regions, add `-Wl,--print-memory-usage` to
  print how full each region is after every link. LLD supports it from
  LLVM 17.
- Link with LLD as well, using `-fuse-ld=lld`, if the project claims to
  support both linkers.

## Auditing

### Security analysis

No static analyser reads linker scripts, so audit the linked image instead.
A script that puts code and writable data in one segment, or that leaves the
stack executable, removes a protection from the whole program.

GNU ld 2.39 and later can warn about both. Turn the warnings on, so
`--fatal-warnings` stops such a link:

```sh
gcc -nostdlib -T link.ld \
    -Wl,--fatal-warnings \
    -Wl,--warn-rwx-segments \
    -Wl,--warn-execstack \
    -o build/image.elf build/start.o build/main.o
```

LLD has no such warnings, so check the segments of every image, whichever
linker made it. Fail the build when any segment is readable, writable and
executable at once:

```sh
if readelf -lW build/image.elf | grep -q ' RWE '; then
  echo 'build/image.elf has a writable, executable segment' >&2
  exit 1
fi
```

For a hosted program, also run checksec and check that NX, PIE and full
RELRO are all enabled:

```sh
checksec file build/image.elf
```

### Dependency vulnerabilities

Linker scripts have no package manager, so there are no third-party
dependencies to audit.

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

Linker scripts have no functions, so complexity metrics don't apply. The map
file is the review aid: it shows where every section and symbol ended up.

### Duplication

Flag any block of 50 or more tokens that appears twice. Duplicated code gets
fixed in one place and not the other.

```sh
jscpd --format linker-script --min-tokens 50 --exitCode 1 .
```

jscpd reads `.ld` files as its `linker-script` format. It doesn't read a
preprocessed `.ld.S` script, which ends in `.S`, or the script's output in
the build directory, which `.jscpd.json` ignores. To check the output, run
jscpd on the build directory with an ignore list that leaves it in:

```sh
jscpd --format linker-script --min-tokens 50 --exit-code 1 \
    --ignore "**/node_modules/**" build
```

### Dead code

With garbage collection on (see
[Garbage collection and KEEP](idioms.md#garbage-collection-and-keep)), both
GNU ld and LLD can list every section they removed:

```sh
gcc -nostdlib -T link.ld -Wl,--gc-sections -Wl,--print-gc-sections \
    -o build/image.elf build/start.o build/main.o
```

Review the list when it changes. A function you expected to be used appears
there when nothing calls it, and a section that should be listed there but
isn't is held by an unneeded `KEEP`.

### Coverage

Linker scripts don't run, so coverage doesn't apply. The `ASSERT` checks are
their tests (see [Layout checks](idioms.md#layout-checks)): each one fails
the link when the layout breaks a rule.
