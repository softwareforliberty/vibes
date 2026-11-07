# x86 Assembly (MASM) Coding Style

A general-purpose coding style for x86 and x86-64 assembly written in the
Microsoft Macro Assembler (MASM) language, in Intel syntax, as accepted by
MASM-compatible assemblers. It builds on Microsoft's MASM reference and the
conventions of long-lived Windows systems code, and it matches the
[C coding style](../C/coding-style.md) wherever the two meet (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (calling
conventions, register preservation, interfacing with C and other idioms), see
[idioms.md](idioms.md).

The tools that check x86 Assembly (MASM) code are listed in [tools.md](tools.md).

## Language baseline

Write MASM-language source that assembles unchanged with both **UASM** and
**JWasm**, the two assemblers in [tools.md](tools.md). Never rely on an
extension that only one of them accepts.

Use only instructions that every CPU the program supports is guaranteed to
have: the same baseline the C code is compiled for. Use a newer extension only
behind a runtime check that picks a fallback on CPUs without it.

## Files

- Assembly sources use `.asm`. Shared definitions (constants, macros, struct
  layouts) go in `.inc` files.
- One module per file. A module that C code calls has a C header with the same
  base name (`buf.asm` with `buf.h`).
- Keep 32-bit and 64-bit code in separate files (see
  [Supporting both word sizes](idioms.md#supporting-both-word-sizes)).
- Lay out each file in this order, with one blank line between sections:
  1. A header comment describing the module.
  2. Processor and model directives (32-bit only: `.686`, `.XMM`,
     `.MODEL FLAT, C`).
  3. `OPTION` directives.
  4. `INCLUDE` lines.
  5. Constants, structs and macros private to the file.
  6. `PUBLIC`, `EXTERN` and `PROTO` declarations.
  7. Data sections (`.CONST`, `.DATA`, `.DATA?`).
  8. The `.CODE` section.
  9. `END`.
- Every `.inc` file has an include guard, built the same way as a C header
  guard: the file's path, uppercased, with `/` and `.` turned into `_`. For
  example, `"buf.inc"` becomes `BUF_INC`:

  ```masm
  IFNDEF BUF_INC
  BUF_INC	EQU	1

  ...

  ENDIF ; BUF_INC
  ```

## Layout

### Columns

Assembly reads like a table. Keep four columns, separated by tabs that are
**8 columns wide**:

| Column | Starts at | Holds |
| --- | --- | --- |
| Label | 0 | Labels, procedure and struct names, and file-level and assembly-time directives (`OPTION`, `INCLUDE`, `PUBLIC`, `EXTERN`, `.CODE`, `IF`/`ENDIF`, `FOR`/`ENDM`) |
| Mnemonic | 8 (one tab) | The instruction, directive or macro name |
| Operands | 16 (two tabs) | The operands |
| Comment | 40 (five tabs) where it fits | The trailing comment |

```masm
buf_sum	PROC
	xor	eax, eax		; sum = 0
	test	rdx, rdx
	jz	done			; empty array: return 0
next_item:
	add	rax, [rcx]
	add	rcx, 8
	dec	rdx
	jnz	next_item
done:
	ret
buf_sum	ENDP
```

- Indent with tabs. Never use spaces for indentation.
- A procedure's name sits in the label column, with `PROC` and `ENDP` one tab
  after it.
- A code label goes on its own line, so the instruction column stays
  straight no matter how long the label is.
- A data label shares its line with the data it names
  (`msg_hello BYTE ...`), so the name and its storage read as one
  declaration.
- Directives that emit or align storage, and the unwind directives that
  annotate a prologue (`.PUSHREG`, `.ALLOCSTACK`, `.SETFRAME`, `.ENDPROLOG`),
  go in the mnemonic column, like instructions.
- A mnemonic or directive too long for its column is followed by one tab, and
  its operands start at the next tab stop.
- When the operands run past column 40, put the comment one tab after them
  instead of breaking the line.

### Line length and spacing

- **80 columns** is the preferred limit. You may go up to **100** only when
  that clearly reads better and hides nothing.
- Never break user-visible strings across lines, so they stay greppable.
- Put one blank line between procedures. Inside a procedure, use single blank
  lines to separate logical steps.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### Operands

- Put a space after each comma: `mov rax, rbx`.
- Inside a memory operand, put spaces around `+` and `-` but not around `*`:
  `[rbx + rcx*8 + 16]`. The scale stays visually attached to its register.
- Write the base register first, then the index, then the displacement.
- Give a memory operand an explicit size (`BYTE PTR`, `WORD PTR`,
  `DWORD PTR`, `QWORD PTR`) whenever no register operand implies it:
  `mov DWORD PTR [rcx], 0`.

## Case and literals

- Write instructions and registers in **lowercase**: `mov`, `rax`.
- Write directives, operators and type names in **uppercase**: `PROC`,
  `.CODE`, `QWORD PTR`, `OFFSET`. The case difference separates what the
  assembler does at assembly time from the instructions the CPU runs.
- Write hexadecimal with an `h` suffix and uppercase digits, with a leading
  `0` when the number starts with a letter: `0FFh`, `0FFFF0000h`, `1000h`.
  MASM needs the `0` to tell a number from a name.
- Write binary with a `b` suffix: `10100001b`.
- MASM strings have no escape sequences. Add control characters as numbers
  after the string: `"hello", 13, 10`.

## Naming

- Labels and symbols use `snake_case`.
- **Global** symbols are descriptive and start with their module's prefix,
  exactly like the C names they implement: `buf_sum`, `ctx_switch`.
- **Local** labels are labels inside a `PROC`, written with a single colon.
  MASM scopes them to their procedure, so they need no prefix. Name them for
  what happens there or why the code jumps there: `next_item`, `done`,
  `err_unmap`. Don't use numbered labels like `l1` and `l2`.
- Don't use anonymous labels (`@@`, jumped to as `@B` or `@F`). They say
  nothing about where a jump goes. Never make a label global with a double
  colon (`label::`); export procedures with `PUBLIC` instead.
- Constants and macros are `UPPER_SNAKE_CASE`: `PAGE_SIZE`, `SAVE_REGS`. An
  uppercase macro name tells the reader that the line expands to more than
  one instruction.
- Struct names and their fields use `snake_case`, matching the C struct they
  mirror. A field's offset is written `struct.field`: `pipe.head`.

### Reserved names

- Never define symbols that start with `__` or with `_` followed by a capital
  letter. C reserves those names for the compiler and the C library, and
  assembly symbols share C's namespace.
- Don't start names with `@` or `?`. MASM uses `@` for its predefined symbols
  (`@@`, `@WordSize`), and `?` starts C++ decorated names.
- Don't use MASM reserved words as names. Common traps are `c`, `name`,
  `size`, `length`, `type`, `mask` and `width`.

## Constants and data

- Define numeric constants with `EQU`: `PAGE_SIZE EQU 4096`. An `EQU`
  constant can't be redefined, and it shows up in listings.
- Use `TEXTEQU` only for text substitution, such as register aliases.
- Don't use magic numbers. Name each constant, and add a comment explaining
  the size you chose for each limit.
- Describe data that C also uses with `STRUCT` and `ENDS`, with the fields
  indented one tab. Add a comment naming the C struct it must match:

  ```masm
  ; Must match struct pipe in pipe.h.
  pipe	STRUCT
  	head	DWORD	?
  	tail	DWORD	?
  	count	DWORD	?
  pipe	ENDS
  ```

- Address a field through its offset: `mov eax, [rcx + pipe.head]`.
- Declare data with the type names `BYTE`, `WORD`, `DWORD` and `QWORD`, not
  `DB`, `DW`, `DD` and `DQ`. MASM records the type with the label and checks
  operand sizes against it.
- Put each piece of data in the section that matches its use: constants in
  `.CONST`, initialised data in `.DATA`, zeroed data in `.DATA?`.
- Declare one data item per line:

  ```masm
  .CONST
  msg_hello	BYTE	"hello", 10
  MSG_HELLO_LEN	EQU	$ - msg_hello
  ```

## Directives and sections

- Use the simplified section directives `.CODE`, `.DATA`, `.DATA?` and
  `.CONST`. Write a full `SEGMENT` definition only when you need a section
  they can't describe, such as one with more alignment.
- Start every file with `OPTION CASEMAP:NONE`, so symbol names keep their
  case and match the C names they implement.
- Follow it with `OPTION PROC:PRIVATE`, so procedures are private to the file
  unless a `PUBLIC` line exports them. Only a module's API is visible outside
  it.
- Put `PUBLIC`, `EXTERN` and `PROTO` declarations near the top of the file, so
  a module's interface can be read without scrolling.
- In 32-bit code, start with the processor directives and
  `.MODEL FLAT, C`, which sets the flat memory model and the C calling
  convention as the default.
- End every file with `END`.
- **Don't use the high-level control directives** (`.IF`, `.ELSEIF`,
  `.WHILE`, `.REPEAT`, `.BREAK`). They hide the branches they generate, and
  `ml64` doesn't support them.
- **Stick to the MASM language.** UASM and JWasm add extensions, such as
  `INVOKE` in 64-bit code, that other MASM assemblers reject. Avoiding them
  keeps code portable between assemblers.

## Macros

- Keep macros small, and use them to remove repetition. Don't use them to
  build a private language.
- Declare every label inside a macro with `LOCAL`, so each expansion gets its
  own labels.
- Mark required parameters with `:REQ`, so a missing argument is an error
  instead of an empty expansion.
- A macro must not jump to a label outside itself, and must not depend on a
  register holding a magic value. Pass what it needs as parameters.
- Document every macro with a comment that gives its parameters and every
  register it changes.
- Indent a macro's body like any other code:

  ```masm
  ; ZERO_REGS reg, ... - Zero each register in the list.
  ZERO_REGS	MACRO	regs:VARARG
  FOR reg, <regs>
  	xor	reg, reg
  ENDM
  ENDM
  ```

## Comments

- Comments start with `;`. A comment on its own line sits at the indentation
  of the code it describes. A trailing comment sits in the comment column.
- Comments explain **what** a block does and **why**. Don't restate the
  instruction. `; skip the header` helps, and `; add 8 to rcx` doesn't.
- Don't use `COMMENT` blocks. A run of `;` lines reads the same in every
  editor and survives copying.
- Every file starts with a comment describing the module.
- Every procedure starts with a header comment that gives its register-level
  contract. If C code calls the procedure, the C header's prototype carries
  the API documentation (see the [C coding style](../C/coding-style.md#api-documentation)),
  and this header adds the register details:

  ```masm
  ;
  ; buf_sum - Sum an array of 64-bit integers.
  ;
  ; In:		rcx = pointer to the array
  ;		rdx = number of elements
  ; Out:		rax = sum
  ; Clobbers:	rcx, rdx, flags
  ;
  ```

- After a long conditional-assembly block, add a comment naming the
  condition: `ENDIF ; BUF_DEBUG`.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [Microsoft Macro Assembler reference](https://learn.microsoft.com/en-us/cpp/assembler/masm/microsoft-macro-assembler-reference)
- [UASM](https://github.com/Terraspace/UASM)
- [JWasm manual](https://baron-von-riedesel.github.io/JWasm/Html/Manual.html)
- [C coding style](../C/coding-style.md), for the conventions shared with C
