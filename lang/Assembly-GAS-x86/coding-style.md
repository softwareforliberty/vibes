# x86 Assembly (GNU as) Coding Style

A general-purpose coding style for x86 and x86-64 assembly written for the
[GNU assembler](https://sourceware.org/binutils/docs/as/) (`as`), in AT&T
syntax, in `.S` files run through the C preprocessor. It builds on the GNU as
manual and the conventions of long-lived FOSS systems code such as the Linux
kernel, and it matches the [C coding style](../C/coding-style.md) wherever the
two meet (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (calling
conventions, register preservation, interfacing with C and other idioms), see
[idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [GNU as](https://sourceware.org/binutils/) (GNU Binutils) | GPLv3 | Assembling, and linting through its warnings |
| [GCC](https://gcc.gnu.org/) | GPLv3 | Running the C preprocessor over `.S` files and driving `as` |

### Assembler warnings

Assembler warnings are the lint gate. Code must assemble with **no warnings**
using at least these flags:

```sh
# 64-bit ELF (Linux, BSD)
gcc -c -g -Wall -Werror -Wa,--fatal-warnings -o buf.o buf.S

# 32-bit ELF
gcc -m32 -c -g -Wall -Werror -Wa,--fatal-warnings -o buf.o buf.S

# 64-bit Windows (MinGW-w64)
x86_64-w64-mingw32-gcc -c -g -Wall -Werror -Wa,--fatal-warnings -o buf.o buf.S
```

- `-Wa,--fatal-warnings` makes the assembler treat warnings as errors, and
  `-Wall -Werror` does the same for the preprocessor, so a warning can't slip
  through a build.
- `-g` emits debug information, so debuggers and profilers can map addresses
  back to source lines.
- GNU as can't silence a warning for a few lines only. When a warning fires,
  change the code so it no longer triggers. Never turn warnings off for the
  whole build.
- When reviewing instruction encodings, generate a listing with
  `-Wa,-adhln=buf.lst`.

## Syntax

- Write **AT&T syntax**: the syntax of GNU toolchains, compiler output
  (`gcc -S`) and most FOSS systems code. GNU as also accepts Intel syntax
  through `.intel_syntax noprefix`. Pick one syntax for a whole project, and
  never switch syntax inside a file.
- Operands go **source first, destination last**: `movq %rsi, %rdi` copies
  `%rsi` into `%rdi`.
- Registers take a `%` prefix (`%rax`), and immediates take a `$` prefix
  (`$8`, `$PAGE_SIZE`).

## Files

- Hand-written assembly sources use `.S` (uppercase), so the compiler driver
  runs the C preprocessor over them. Lowercase `.s` is for compiler output,
  which isn't preprocessed.
- One module per file. A module that C code calls has a C header with the same
  base name (`buf.S` with `buf.h`).
- **Share definitions with C through C headers.** Constants and annotation
  macros that both languages use live in a `.h` file. Wrap the parts only C
  can read (prototypes, struct definitions) in `#ifndef __ASSEMBLER__`, which
  the compiler defines while preprocessing assembly:

  ```c
  #ifndef BUF_H
  #define BUF_H

  #define BUF_MAX_SIZE	4096	// largest buffer buf_alloc() hands out

  #ifndef __ASSEMBLER__
  #include <stddef.h>
  #include <stdint.h>

  uint64_t buf_sum(const uint64_t *items, size_t n);
  #endif

  #endif // BUF_H
  ```

- Shared headers follow the [C coding style](../C/coding-style.md) in full,
  including its header guards: the file's path, uppercased, with `/` and `.`
  turned into `_`.
- Lay out each `.S` file in this order, with one blank line between sections:
  1. A header comment describing the module.
  2. `#include` lines.
  3. Constants and macros private to the file.
  4. `.extern` declarations.
  5. Data sections (`.rodata`, `.data`, `.bss`).
  6. The `.text` section.
  7. The non-executable stack marker (see
     [Directives and sections](#directives-and-sections)).

## Layout

### Columns

Assembly reads like a table. Keep four columns, separated by tabs that are
**8 columns wide**:

| Column | Starts at | Holds |
| --- | --- | --- |
| Label | 0 | Labels, `FUNC_START`/`FUNC_END` lines, file-level directives (`.text`, `.section`, `.extern`, `.equ`, `.macro`, `.endm`) and preprocessor lines |
| Mnemonic | 8 (one tab) | The instruction, directive or macro name |
| Operands | 16 (two tabs) | The operands |
| Comment | 40 (five tabs) where it fits | The trailing comment |

```gas
FUNC_START(buf_sum)
	xorl	%eax, %eax		// sum = 0
	testq	%rsi, %rsi
	jz	.Lbuf_sum_done		// empty array: return 0
.Lbuf_sum_loop:
	addq	(%rdi), %rax
	addq	$8, %rdi
	decq	%rsi
	jnz	.Lbuf_sum_loop
.Lbuf_sum_done:
	ret
FUNC_END(buf_sum)
```

- Indent with tabs. Never use spaces for indentation.
- A code label goes on its own line, so the instruction column stays
  straight no matter how long the label is.
- A data label shares its line with the data it names
  (`msg_hello: .ascii ...`), so the name and its storage read as one
  declaration.
- Directives that emit or align storage (`.byte`, `.quad`, `.skip`,
  `.balign`) and directives that annotate code (`.cfi_*`, `.seh_*`) go in the
  mnemonic column, like instructions.
- A mnemonic or directive too long for its column is followed by one tab, and
  its operands start at the next tab stop.
- When the operands run past column 40, put the comment one tab after them
  instead of breaking the line.

### Line length and spacing

- **80 columns** is the preferred limit. You may go up to **100** only when
  that clearly reads better and hides nothing.
- Never break user-visible strings across lines, so they stay greppable.
- Put one blank line between routines. Inside a routine, use single blank
  lines to separate logical steps.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.
- Write one instruction per line. In x86 GNU as, `;` separates statements on
  one line; use it only inside preprocessor macros, which must fit on one
  line.

### Operands

- Put a space after each comma that separates operands: `movq %rax, %rbx`.
- Write memory operands with **no spaces inside the parentheses**:
  `16(%rbx,%rcx,8)`. The commas inside belong to one operand, and leaving out
  the spaces keeps them visually separate from the operand separators.
- Give every instruction that has size variants an **explicit size suffix**:
  `movq`, `movl`, `movw`, `movb`. The suffix states the operand size in the
  instruction itself, and the assembler rejects a suffix that doesn't match a
  register operand, which catches mistakes.

## Case and literals

- Write mnemonics, registers and directives in **lowercase**: `movq`, `%rax`,
  `.section`. GNU as accepts lowercase everywhere, and it's easier to read.
- Write hexadecimal with a `0x` prefix and uppercase digits: `0xFF`,
  `0xFFFF0000`.
- Write binary with a `0b` prefix: `0b10100001`.
- Write strings with double quotes and C escapes: `"line\n"`.

## Naming

- Labels and symbols use `snake_case`.
- **Global** symbols are descriptive and start with their module's prefix,
  exactly like the C names they implement: `buf_sum`, `ctx_switch`.
- **Local** labels start with `.L`, then the routine's name, then what happens
  there or why the code jumps there: `.Lbuf_sum_loop`, `.Lbuf_flush_err`.
  The `.L` prefix keeps the label out of the symbol table. GNU as has no
  per-routine label scope, so the routine's name keeps labels unique within
  the file.
- Use numeric labels (`1:`, jumped to as `1b` or `1f`) only inside macros,
  where each expansion needs its own labels. Elsewhere, `1f` says nothing
  about where the jump goes.
- Constants and macros are `UPPER_SNAKE_CASE`: `PAGE_SIZE`, `SAVE_REGS`. An
  uppercase macro name tells the reader that the line expands to more than
  one instruction.
- Name structure field offsets with the struct's name as a prefix:
  `PIPE_HEAD`, `PIPE_TAIL`.

### Reserved names

- Never define symbols that start with `__` or with `_` followed by a capital
  letter. C reserves those names for the compiler and the C library, and
  assembly symbols share C's namespace.
- The `.L` prefix is reserved for local labels. Never start a global symbol
  with `.`.

## Constants and data

- Define numeric constants private to the file with `.equ`:
  `.equ PAGE_SHIFT, 12`. An `.equ` constant shows up as a symbol in debuggers
  and listings.
- Define constants that C also uses with `#define` in the shared C header, so
  both languages read one definition.
- Don't use magic numbers. Name each constant, and add a comment explaining
  the size you chose for each limit.
- Describe data that C also uses with offset constants, and add a comment
  naming the C struct they must match. Generate them from C where you can
  (see [Keep shared struct layouts in sync](idioms.md#interfacing-with-c)):

  ```c
  /* Must match struct pipe in pipe.h. */
  #define PIPE_HEAD	0
  #define PIPE_TAIL	4
  #define PIPE_COUNT	8
  ```

- Put each piece of data in the section that matches its use: constants in
  `.rodata`, initialised data in `.data`, zeroed data in `.bss`.
- Use `.byte`, `.short`, `.long` and `.quad` for 8-, 16-, 32- and 64-bit data.
  Avoid `.word` and `.int`, whose sizes differ between targets.
- Declare one data item per line:

  ```gas
  .section .rodata
  msg_hello:	.ascii	"hello\n"
  .equ	MSG_HELLO_LEN, . - msg_hello
  ```

## Directives and sections

- Use `.text`, `.data` and `.bss` for the standard sections, and
  `.section .rodata` for read-only data.
- Align with `.balign`, which always takes a byte count. Avoid `.align`,
  whose argument means bytes on some targets and a power of two on others.
- **Wrap every routine in `FUNC_START(name)` and `FUNC_END(name)`.** Define
  the pair once, in a shared header, for each object format your project
  builds. On ELF they mark the symbol global, give it a type and size, align
  it, and open and close its call-frame information:

  ```c
  #define FUNC_START(name)		\
  	.globl	name;			\
  	.type	name, @function;	\
  	.balign	16;			\
  	name:				\
  	.cfi_startproc

  #define FUNC_END(name)			\
  	.cfi_endproc;			\
  	.size	name, . - name
  ```

  A second pair without `.globl` covers routines private to the file. On
  Windows (PE), the same macros expand to `.seh_proc` and `.seh_endproc`
  instead. The type, size and frame information let debuggers, profilers and
  the dynamic linker treat each routine correctly, and the macros keep that
  boilerplate in one place.
- List the symbols a module uses from elsewhere with `.extern`, near the top
  of the file. GNU as treats undefined symbols as external anyway, but the
  list shows a module's dependencies without reading every routine.
- On ELF targets, every file ends with the non-executable stack marker:

  ```gas
  .section .note.GNU-stack, "", @progbits
  ```

  Without it, the linker may assume the object needs an executable stack.

## Macros

- Use GNU as `.macro` for instruction sequences. Use preprocessor `#define`
  only for constants and for short annotation wrappers such as `FUNC_START`.
  A preprocessor macro collapses onto one line, so its statements need `;`
  separators, and an error in it is reported against a single line.
- Keep macros small, and use them to remove repetition. Don't use them to
  build a private language.
- Labels inside a macro are numeric (`1:`), so each expansion gets its own
  labels.
- A macro must not jump to a label outside itself, and must not depend on a
  register holding a magic value. Pass what it needs as parameters.
- Document every macro with a comment that gives its parameters and every
  register it changes.
- Indent a macro's body like any other code:

  ```gas
  /* ZERO_REGS reg, ... - Zero each 32-bit register in the list. */
  .macro ZERO_REGS regs:vararg
  .irp reg, \regs
  	xorl	\reg, \reg
  .endr
  .endm
  ```

## Comments

- A comment that sits on its own line or lines uses `/* ... */`. A short note
  at the end of a line uses `//`. The preprocessor strips both before the
  assembler runs, and they match the comment rules for C.
- Don't use `#` comments in `.S` files. A `#` at the start of a line is a
  preprocessor directive, and `#` inside a `#define` is the stringify
  operator.
- `;` separates statements in x86 GNU as. It never starts a comment.
- A comment on its own line sits at the indentation of the code it describes.
  A trailing comment sits in the comment column.
- Comments explain **what** a block does and **why**. Don't restate the
  instruction. `// skip the header` helps, and `// add 8 to rdi` doesn't.
- Every file starts with a comment describing the module.
- Every routine starts with a header comment that gives its register-level
  contract. If C code calls the routine, the C header's prototype carries the
  API documentation (see the [C coding style](../C/coding-style.md#api-documentation)),
  and this header adds the register details:

  ```gas
  /*
   * buf_sum - Sum an array of 64-bit integers.
   *
   * In:		%rdi = pointer to the array
   *		%rsi = number of elements
   * Out:		%rax = sum
   * Clobbers:	%rdi, %rsi, flags
   */
  ```

- After a long conditional block, add a comment naming the condition:
  `#endif // _WIN64`.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [GNU as manual](https://sourceware.org/binutils/docs/as/)
- [GCC manual: options controlling the kind of output](https://gcc.gnu.org/onlinedocs/gcc/Overall-Options.html)
  (preprocessing `.S` files)
- [Linux kernel x86 sources](https://github.com/torvalds/linux/tree/master/arch/x86),
  as an example of long-lived AT&T-syntax assembly
- [C coding style](../C/coding-style.md), for the conventions shared with C
