# ARM64 Assembly (GNU as) Coding Style

A general-purpose coding style for AArch64 assembly, written for the GNU
assembler and Clang's integrated assembler. It builds on the GNU as manual,
the Arm architecture's own assembly syntax and the conventions of long-lived
FOSS systems code. It matches the [C coding style](../C/coding-style.md) and
the [x86 NASM style](../Assembly-NASM-x86/coding-style.md) wherever they meet
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(calling conventions, register and stack discipline, interfacing with C and
other idioms), see [idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [GNU as](https://sourceware.org/binutils/) (GNU Binutils), driven by [GCC](https://gcc.gnu.org/) | GPL-3.0-or-later | Preprocessing and assembling `.S` files on Linux and BSD |
| [LLVM](https://llvm.org/): Clang's integrated assembler and `llvm-mc` | Apache-2.0 WITH LLVM-exception | Assembling on Apple platforms and with Clang, and inspecting encodings |

### Assembler warnings

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

## Files

- Assembly sources use `.S` (uppercase), so the C preprocessor runs first.
  That gives you `#include`, `#define` and conditional assembly, and lets C
  and assembly share one header.
- One module per file. A module that C code calls has a C header with the same
  base name (`buf.S` with `buf.h`).
- Constants, field offsets and macros that both languages use live in a C
  header. Wrap the parts only C can read in `#ifndef __ASSEMBLER__`.
- Every header has an include guard, built as the
  [C style](../C/coding-style.md#headers-and-includes) describes:
  `"buf.h"` becomes `BUF_H`.
- Lay out each file in this order, with one blank line between sections:
  1. A header comment describing the module.
  2. `#include` lines, starting with the shared `asm.h` (see
     [A shared header](idioms.md#a-shared-header)).
  3. Constants and macros private to the file.
  4. Data sections (`.data`, `.bss`, read-only data).
  5. The `.text` section.
  6. On ELF targets, the non-executable stack marker (see
     [Directives and sections](#directives-and-sections)).

## Layout

### Columns

Assembly reads like a table. Keep four columns, separated by tabs that are
**8 columns wide**:

| Column | Starts at | Holds |
| --- | --- | --- |
| Label | 0 | Labels, macro invocations that open or close a routine, and preprocessor lines |
| Mnemonic | 8 (one tab) | The instruction, directive or macro name |
| Operands | 16 (two tabs) | The operands |
| Comment | 40 (five tabs) where it fits | The trailing comment |

```asm
FUNC_BEGIN buf_sum
	mov	x2, x0			// keep the array pointer
	mov	x0, xzr			// sum = 0
	cbz	x1, .Lbuf_sum_done	// empty array: return 0
.Lbuf_sum_loop:
	ldr	x3, [x2], #8
	add	x0, x0, x3
	subs	x1, x1, #1
	b.ne	.Lbuf_sum_loop
.Lbuf_sum_done:
	ret
FUNC_END buf_sum
```

- Indent with tabs. Never use spaces for indentation.
- A code label goes on its own line, so the instruction column stays
  straight no matter how long the label is.
- A data label shares its line with the data it names
  (`msg_hello: .asciz "hello\n"`), so the name and its storage read as one
  declaration.
- Directives that emit or align storage (`.quad`, `.asciz`, `.balign`) go in
  the mnemonic column, like instructions.
- When the operands run past column 40, put the comment one tab after them
  instead of breaking the line.

### Line length and spacing

- **80 columns** is the preferred limit. You may go up to **100** only when
  that clearly reads better and hides nothing.
- Never break user-visible strings across lines, so they stay greppable.
- Put one blank line between routines. Inside a routine, use single blank
  lines to separate logical steps.
- One instruction per line. Never use `;` to put several on one line: GNU as
  reads it as a separator, but Apple's assembler reads it as a comment.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### Operands

- Put a space after each comma: `add x0, x0, x3`.
- Write every immediate with `#`: `add x0, x0, #1`, `[sp, #16]`. Arm's own
  syntax uses it, and it marks a constant at a glance.
- Write memory operands without spaces inside the brackets, in the forms the
  architecture defines: `[x0]`, `[x0, #16]`, `[x0, x1, lsl #3]`, and the
  pre-index `[sp, #-16]!` and post-index `[x2], #8` forms.

## Case and literals

- Write mnemonics, registers, condition codes and directives in
  **lowercase**: `ldr`, `x0`, `b.ne`, `.balign`. Both assemblers accept
  either case, and lowercase is easier to read.
- Use the architectural register names: `x0`–`x30`, `w0`–`w30`, `sp`, `xzr`
  and `wzr`. Write `x29` and `x30`, not the `fp` and `lr` aliases, so each
  register has one name everywhere.
- Write hexadecimal with a `0x` prefix and uppercase digits: `#0xFF`,
  `#0xFFFF0000`.
- Write binary with a `0b` prefix: `#0b1010`.
- GNU as has no digit separator, so give long numbers a name with a comment
  instead of writing them inline (see [Constants and data](#constants-and-data)).

## Naming

- Labels and symbols use `snake_case`.
- **Global** symbols are descriptive and start with their module's prefix,
  exactly like the C names they implement: `buf_sum`, `ctx_switch`.
- **Local** labels start with `.L`, so they stay out of the symbol table and
  debuggers don't mistake them for routines. A local label is visible in the
  whole file, so give it the routine's name followed by what happens there or
  why the code jumps there: `.Lbuf_sum_loop`, `.Lbuf_flush_err_unlock`. Don't
  use numbered labels like `1:` outside macros.
- Source that also builds for Apple platforms writes local labels with the
  `LOCAL()` macro, `LOCAL(buf_sum_loop)`, which supplies the prefix Mach-O
  treats as local (see [Apple platforms](idioms.md#apple-platforms)).
- Constants and macros are `UPPER_SNAKE_CASE`: `PAGE_SIZE`, `FUNC_BEGIN`. An
  uppercase macro name tells the reader that the line expands to more than
  one instruction.
- Field offsets shared with C use the struct's name as a prefix: `PIPE_HEAD`,
  `PIPE_TAIL`.

### Reserved names

- Never define symbols that start with `__` or with `_` followed by a capital
  letter. C reserves those names for the compiler and the C library, and
  assembly symbols share C's namespace.
- The `.L` prefix belongs to assembler-local labels. Use it only for them.

## Constants and data

- Put constants that C also uses in the shared C header, as `#define`s.
- Define constants private to one file with `.equ`: `.equ RING_SLOTS, 64`.
  An `.equ` is evaluated once, and it shows up in listings.
- Don't use magic numbers. Name each constant, and add a comment explaining
  the size you chose for each limit.
- Describe data that C also uses with field offsets in the shared header, and
  add a comment naming the C struct they must match:

  ```c
  /* Field offsets of struct pipe; must match struct pipe in pipe.h. */
  #define PIPE_HEAD	0
  #define PIPE_TAIL	4
  #define PIPE_COUNT	8
  ```

- Put each piece of data in the section that matches its use: constants in
  read-only data, initialised data in `.data`, zeroed data in `.bss`.
- Declare one data item per line:

  ```asm
  	RODATA_SECTION
  msg_hello:	.asciz	"hello\n"
  ```

## Directives and sections

- Write `.globl` (not `.global`) to export a symbol.
- Align with `.balign`, which always takes a byte count. Never use `.align`,
  whose argument means bytes on some targets and a power of two on others.
- Start and end every routine with the `FUNC_BEGIN` and `FUNC_END` macros
  from the shared header (see [A shared header](idioms.md#a-shared-header)).
  They export the symbol, give it its type and size on ELF, align it, and open
  and close its call-frame information. A routine written this way has its
  interface declared in its C header, so the file doesn't repeat it.
- Use the CFI directives (`.cfi_def_cfa_offset`, `.cfi_offset`) whenever a
  routine moves `sp` or saves a register, so debuggers and unwinders can walk
  the stack through it.
- On ELF targets, every file ends with the non-executable stack marker:

  ```asm
  #ifdef __ELF__
  	.section	.note.GNU-stack, "", %progbits
  #endif /* __ELF__ */
  ```

  Without it, the linker may assume the object needs an executable stack.

## Macros

- Keep macros small, and use them to remove repetition. Don't use them to
  build a private language.
- Use `.macro` and `.endm` for macros that expand to instructions, and
  `#define` only for constants and simple text substitution.
- Labels inside a `.macro` end in `\@`, so each expansion gets its own:
  `.Lzero_loop\@`.
- A macro must not jump to a label outside itself, and must not depend on a
  register holding a magic value. Pass what it needs as parameters.
- Document every macro with a comment that gives its parameters and every
  register it changes.
- Indent a macro's body like any other code:

  ```asm
  /* ZERO_PAIR a, b - Zero two registers. */
  	.macro	ZERO_PAIR a, b
  	mov	\a, xzr
  	mov	\b, xzr
  	.endm
  ```

## Comments

- A comment on its own line uses `/* ... */`, at the indentation of the code
  it describes. It's the one form that both the preprocessor and every GNU as
  target accept.
- A trailing comment uses `//` and sits in the comment column. `//` is the
  line comment on AArch64 for both GNU as and Clang.
- Comments on preprocessor lines use `/* ... */`: `#endif /* __ELF__ */`.
- Comments explain **what** a block does and **why**. Don't restate the
  instruction. `// skip the header` helps, and `// add 8 to x2` doesn't.
- Every file starts with a comment describing the module.
- Every routine starts with a header comment that gives its register-level
  contract. If C code calls the routine, the C header's prototype carries the
  API documentation (see the [C coding style](../C/coding-style.md#api-documentation)),
  and this header adds the register details:

  ```asm
  /*
   * buf_sum - Sum an array of 64-bit integers.
   *
   * In:		x0 = pointer to the array
   *		x1 = number of elements
   * Out:		x0 = sum
   * Clobbers:	x1, x2, x3, flags
   */
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [GNU as manual](https://sourceware.org/binutils/docs/as/), including the
  [AArch64-dependent features](https://sourceware.org/binutils/docs/as/AArch64_002dDependent.html)
- [Arm A64 instruction set reference](https://developer.arm.com/documentation/ddi0602/latest)
- [x86 NASM coding style](../Assembly-NASM-x86/coding-style.md), for the
  layout shared between assembly dialects
- [C coding style](../C/coding-style.md), for the conventions shared with C
