# x86 Assembly (NASM) Coding Style

A general-purpose coding style for x86 and x86-64 assembly written for
[NASM](https://www.nasm.us/), in Intel syntax. It builds on the NASM manual
and the conventions of long-lived FOSS systems code, and it matches the
[C coding style](../C/coding-style.md) wherever the two meet (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (calling
conventions, register preservation, interfacing with C and other idioms), see
[idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [NASM](https://www.nasm.us/) 2.15 or later | BSD-2-Clause | Assembling, and linting through its warning classes |

### Assembler warnings

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

## Files

- Assembly sources use `.asm`. Shared definitions (constants, macros, struct
  layouts) go in `.inc` files.
- One module per file. A module that C code calls has a C header with the same
  base name (`buf.asm` with `buf.h`).
- Lay out each file in this order, with one blank line between sections:
  1. A header comment describing the module.
  2. `bits` and `default rel` directives.
  3. `%include` lines.
  4. Constants and macros private to the file.
  5. `global` and `extern` declarations.
  6. Data sections (`.rodata`, `.data`, `.bss`).
  7. The `.text` section.
- Every `.inc` file has an include guard, built the same way as a C header
  guard: the file's path, uppercased, with `/` and `.` turned into `_`. For
  example, `"buf.inc"` becomes `BUF_INC`:

  ```nasm
  %ifndef BUF_INC
  %define BUF_INC

  ...

  %endif ; BUF_INC
  ```

## Layout

### Columns

Assembly reads like a table. Keep four columns, separated by tabs that are
**8 columns wide**:

| Column | Starts at | Holds |
| --- | --- | --- |
| Label | 0 | Labels, and file-level directives (`section`, `global`, `extern`, `bits`, `default`, and `%` preprocessor lines) |
| Mnemonic | 8 (one tab) | The instruction, directive or macro name |
| Operands | 16 (two tabs) | The operands |
| Comment | 40 (five tabs) where it fits | The trailing comment |

```nasm
buf_sum:
	xor	eax, eax		; sum = 0
	test	rsi, rsi
	jz	.done			; empty array: return 0
.loop:
	add	rax, [rdi]
	add	rdi, 8
	dec	rsi
	jnz	.loop
.done:
	ret
```

- Indent with tabs. Never use spaces for indentation.
- A code label goes on its own line, so the instruction column stays
  straight no matter how long the label is.
- A data label shares its line with the data it names (`msg_hello: db ...`),
  so the name and its storage read as one declaration.
- Directives that emit or align storage (`db`, `resb`, `align`, `alignb`)
  go in the mnemonic column, like instructions.
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

### Operands

- Put a space after each comma: `mov rax, rbx`.
- Inside a memory operand, put spaces around `+` and `-` but not around `*`:
  `[rbx + rcx*8 + 16]`. The scale stays visually attached to its register.
- Write the base register first, then the index, then the displacement.
- Give a memory operand an explicit size (`byte`, `word`, `dword`, `qword`)
  whenever no register operand implies it: `mov dword [rdi], 0`.

## Case and literals

- Write mnemonics, registers and directives in **lowercase**: `mov`, `rax`,
  `section`. NASM accepts either case, and lowercase is easier to read.
- Write hexadecimal with a `0x` prefix and uppercase digits: `0xFF`,
  `0xFFFF_0000`. One prefix style throughout avoids mixing `0FFh`, `$FF` and
  `0xFF`.
- Group the digits of long numbers with `_`: `0x0010_0000`, `1_000_000`.
- Write binary with a `0b` prefix: `0b1010_0001`.
- Use backquoted strings when you need escapes: `` `line\n` ``. Use plain
  quotes otherwise.

## Naming

- Labels and symbols use `snake_case`.
- **Global** symbols are descriptive and start with their module's prefix,
  exactly like the C names they implement: `buf_sum`, `ctx_switch`.
- **Local** labels start with `.` and say what happens there or why the code
  jumps there: `.loop`, `.done`, `.err_unmap`. Don't use numbered labels like
  `.l1` and `.l2`.
- Label every global routine and every label with a trailing `:`. A label
  without a colon can be mistaken for an instruction, and NASM warns about it.
- Constants and macros are `UPPER_SNAKE_CASE`: `PAGE_SIZE`, `SAVE_REGS`. An
  uppercase macro name tells the reader that the line expands to more than
  one instruction.
- Field offsets defined with `struc` use the struct's name as a prefix, as
  NASM does: `pipe.head`, `pipe.tail`.

### Reserved names

- Never define symbols that start with `__` or with `_` followed by a capital
  letter. C reserves those names for the compiler and the C library, and
  assembly symbols share C's namespace.
- Labels starting with `..` and `%%` have special meanings in NASM. Use them
  only for those meanings (for example, `%%` labels inside macros).

## Constants and data

- Define numeric constants with `equ`: `PAGE_SIZE equ 4096`. An `equ` is
  evaluated once, and it shows up as a symbol in debuggers and listings.
- Use `%define` only for text substitution, such as register aliases.
- Don't use magic numbers. Name each constant, and add a comment explaining
  the size you chose for each limit.
- Describe data that C also uses with `struc` and `endstruc`, with the
  fields indented one tab. Add a comment naming the C struct it must match:

  ```nasm
  ; Must match struct pipe in pipe.h.
  struc pipe
  	.head:	resd	1
  	.tail:	resd	1
  	.count:	resd	1
  endstruc
  ```

- Put each piece of data in the section that matches its use: constants in
  `.rodata`, initialised data in `.data`, zeroed data in `.bss`.
- Declare one data item per line:

  ```nasm
  section .rodata
  msg_hello:	db	`hello\n`
  MSG_HELLO_LEN	equ	$ - msg_hello
  ```

## Directives and sections

- Write `section` (not the `segment` synonym), followed by the section name:
  `section .text`.
- Put `global` and `extern` declarations near the top of the file, so a
  module's interface can be read without scrolling.
- Start every 64-bit file with `default rel`, so memory operands are
  RIP-relative unless they say otherwise (see
  [position-independent code](idioms.md#position-independent-code)).
- On ELF targets, every file includes the non-executable stack marker:

  ```nasm
  section .note.GNU-stack noalloc noexec nowrite progbits
  ```

  Without it, the linker may assume the object needs an executable stack.

## Macros

- Keep macros small, and use them to remove repetition. Don't use them to
  build a private language.
- Labels inside a macro use the `%%` prefix (`%%done`), so each expansion
  gets its own labels.
- A macro must not jump to a label outside itself, and must not depend on a
  register holding a magic value. Pass what it needs as parameters.
- Document every macro with a comment that gives its parameters and every
  register it changes.
- Indent a macro's body like any other code:

  ```nasm
  ; ZERO_REGS reg, ... - Zero each register in the list.
  %macro ZERO_REGS 1-*
  %rep %0
  	xor	%1, %1
  %rotate 1
  %endrep
  %endmacro
  ```

## Comments

- Comments start with `;`. A comment on its own line sits at the indentation
  of the code it describes. A trailing comment sits in the comment column.
- Comments explain **what** a block does and **why**. Don't restate the
  instruction. `; skip the header` helps, and `; add 8 to rdi` doesn't.
- Every file starts with a comment describing the module.
- Every routine starts with a header comment that gives its register-level
  contract. If C code calls the routine, the C header's prototype carries the
  API documentation (see the [C coding style](../C/coding-style.md#api-documentation)),
  and this header adds the register details:

  ```nasm
  ;
  ; buf_sum - Sum an array of 64-bit integers.
  ;
  ; In:		rdi = pointer to the array
  ;		rsi = number of elements
  ; Out:		rax = sum
  ; Clobbers:	rdi, rsi, flags
  ;
  ```

- After a long conditional-assembly block, add a comment naming the
  condition: `%endif ; ABI_WIN64`.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [NASM manual](https://www.nasm.us/doc/)
- [C coding style](../C/coding-style.md), for the conventions shared with C
