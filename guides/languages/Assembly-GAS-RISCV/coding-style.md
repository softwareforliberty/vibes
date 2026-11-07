# RISC-V Assembly (GNU as) Coding Style

A general-purpose coding style for RISC-V assembly (RV32 and RV64), written
for the GNU assembler and Clang's integrated assembler. It builds on the GNU as
manual, the RISC-V assembly programmer's manual and the conventions of
long-lived FOSS systems code. It matches the
[C coding style](../C/coding-style.md) and the
[x86 NASM style](../Assembly-NASM-x86/coding-style.md) wherever they meet (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(calling conventions, register and stack discipline, interfacing with C and
other idioms), see [idioms.md](idioms.md).

The tools that check RISC-V Assembly (GNU as) code are listed in [tools.md](tools.md).

## Language baseline

Assemble with **GNU Binutils 2.39 or later**, or a current Clang. From 2.39,
the GNU linker warns when an ELF object lacks the `.note.GNU-stack` marker this
guide requires, so a missing marker can't slip through.

Both **RV32** and **RV64** are supported. Set `-march` to exactly the
extensions the target guarantees (see
[Assembler warnings](tools.md#assembler-warnings)): the examples use RV64GC
with the `lp64d` ABI on Linux, and RV32IMAC with `ilp32` on bare-metal targets.

Use only instructions that every CPU the program supports is guaranteed to
have: the same baseline the C code is compiled for. Use a newer extension only
behind a runtime check that picks a fallback on CPUs without it.

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
  4. Data sections (`.data`, `.bss`, `.rodata`).
  5. The `.text` section.
  6. The non-executable stack marker (see
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
	mv	t0, a0			# keep the array pointer
	li	a0, 0			# sum = 0
	beqz	a1, .Lbuf_sum_done	# empty array: return 0
.Lbuf_sum_loop:
	REG_L	t1, 0(t0)
	add	a0, a0, t1
	addi	t0, t0, SZREG
	addi	a1, a1, -1
	bnez	a1, .Lbuf_sum_loop
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
- Directives that emit or align storage (`.dword`, `.asciz`, `.balign`) go
  in the mnemonic column, like instructions.
- When the operands run past column 40, put the comment one tab after them
  instead of breaking the line.

### Line length and spacing

- **80 columns** is the preferred limit. You may go up to **100** only when
  that clearly reads better and hides nothing.
- Never break user-visible strings across lines, so they stay greppable.
- Put one blank line between routines. Inside a routine, use single blank
  lines to separate logical steps.
- One instruction per line. Never use `;` to put several on one line.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### Operands

- Put a space after each comma: `add a0, a0, t1`.
- Write memory operands as `offset(register)`, with no spaces, and always
  write the offset, even when it's zero: `0(t0)`, `16(sp)`.
- Write immediates bare, without a prefix: `addi a1, a1, -1`.

## Case and literals

- Write mnemonics, registers and directives in **lowercase**: `addi`, `a0`,
  `.balign`. Both assemblers accept either case, and lowercase is easier to
  read.
- **Use the ABI register names** (`zero`, `ra`, `sp`, `gp`, `tp`, `t0`–`t6`,
  `s0`–`s11`, `a0`–`a7`, and `ft`, `fs` and `fa` for floating point), never
  `x0`–`x31` or `f0`–`f31`. The ABI name says what the register is for.
- Write `s0`, not its `fp` alias, so each register has one name everywhere.
- Write hexadecimal with a `0x` prefix and uppercase digits: `0xFF`,
  `0xFFFF0000`.
- Write binary with a `0b` prefix: `0b1010`.
- GNU as has no digit separator, so give long numbers a name with a comment
  instead of writing them inline (see [Constants and data](#constants-and-data)).

## Instructions

- **Use the standard pseudo-instructions** wherever one exists: `li`, `mv`,
  `not`, `neg`, `j`, `ret`, `call`, `tail`, `nop`, `beqz`, `bnez`. They say
  what the code means, and the assembler picks the best encoding.
- **Never write compressed `c.` mnemonics by hand.** When the target has the
  C extension, the assembler compresses eligible instructions on its own.
- Keep instruction-set changes local. Wrap every `.option` that changes how
  the assembler behaves (`norvc`, `norelax`, `arch`) in `.option push` and
  `.option pop`, so it can't leak into the code that follows:

  ```asm
  	.option	push
  	.option	norelax
  	lla	gp, __global_pointer$
  	.option	pop
  ```

## Naming

- Labels and symbols use `snake_case`.
- **Global** symbols are descriptive and start with their module's prefix,
  exactly like the C names they implement: `buf_sum`, `ctx_switch`.
- **Local** labels start with `.L`, so they stay out of the symbol table and
  debuggers don't mistake them for routines. A local label is visible in the
  whole file, so give it the routine's name followed by what happens there or
  why the code jumps there: `.Lbuf_sum_loop`, `.Lbuf_flush_err_unlock`. Don't
  use numbered labels like `1:` outside macros.
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
  `.rodata`, initialised data in `.data`, zeroed data in `.bss`.
- Declare one data item per line:

  ```asm
  	.section	.rodata
  msg_hello:	.asciz	"hello\n"
  ```

## Directives and sections

- Write `.globl` (not `.global`) to export a symbol.
- Align with `.balign`, which always takes a byte count. Never use `.align`,
  whose argument means bytes on some targets and a power of two on others.
- Start and end every routine with the `FUNC_BEGIN` and `FUNC_END` macros
  from the shared header (see [A shared header](idioms.md#a-shared-header)).
  They export the symbol, give it its type and size, align it, and open and
  close its call-frame information. A routine written this way has its
  interface declared in its C header, so the file doesn't repeat it.
- Use the CFI directives (`.cfi_def_cfa_offset`, `.cfi_offset`) whenever a
  routine moves `sp` or saves a register, so debuggers and unwinders can walk
  the stack through it.
- Every file ends with the non-executable stack marker:

  ```asm
  	.section	.note.GNU-stack, "", @progbits
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
  	li	\a, 0
  	li	\b, 0
  	.endm
  ```

## Comments

- A comment on its own line uses `/* ... */`, at the indentation of the code
  it describes. It's the one form that both the preprocessor and every GNU as
  target accept. A `#` at the start of a line would be read as a preprocessor
  directive.
- A trailing comment uses `#` and sits in the comment column. `#` is the line
  comment on RISC-V, and after an instruction the preprocessor leaves it
  alone.
- Comments on preprocessor lines use `/* ... */`:
  `#endif /* __riscv_xlen */`.
- Comments explain **what** a block does and **why**. Don't restate the
  instruction. `# skip the header` helps, and `# add 8 to t0` doesn't.
- Every file starts with a comment describing the module.
- Every routine starts with a header comment that gives its register-level
  contract. If C code calls the routine, the C header's prototype carries the
  API documentation (see the [C coding style](../C/coding-style.md#api-documentation)),
  and this header adds the register details:

  ```asm
  /*
   * buf_sum - Sum an array of register-sized integers.
   *
   * In:		a0 = pointer to the array
   *		a1 = number of elements
   * Out:		a0 = sum
   * Clobbers:	a1, t0, t1
   */
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [GNU as manual](https://sourceware.org/binutils/docs/as/), including the
  [RISC-V-dependent features](https://sourceware.org/binutils/docs/as/RISC_002dV_002dDependent.html)
- [RISC-V Assembly Programmer's Manual](https://github.com/riscv-non-isa/riscv-asm-manual)
- [x86 NASM coding style](../Assembly-NASM-x86/coding-style.md), for the
  layout shared between assembly dialects
- [C coding style](../C/coding-style.md), for the conventions shared with C
