# GNU ld Linker Script Coding Style

A general-purpose coding style for linker scripts written for
[GNU ld](https://sourceware.org/binutils/docs/ld/), which also link with
[LLD](https://lld.llvm.org/). It builds on the GNU ld manual and matches the
[C coding style](../C/coding-style.md) and the assembly guides wherever they
meet (see [Sources](#sources)).

This guide covers how linker scripts look. For when to write one and how to
structure it (memory regions, load and run addresses, symbols shared with C
and other idioms), see [idioms.md](idioms.md).

The tools that check GNU ld Linker Script code are listed in [tools.md](tools.md).

## Language baseline

Write for **GNU ld 2.39 or later**, and keep every script linking with **LLD 17
or later**. GNU ld 2.39 added the `--warn-rwx-segments` and `--warn-execstack`
warnings, and LLD 17 added `--print-memory-usage`, which the tools rely on.

## Files

- Name a linker script after the image it links, with a `.ld` extension:
  `kernel.ld`, `firmware.ld`. One script per output image.
- A script that needs constants shared with C or assembly is written as
  `<name>.ld.S` and run through the C preprocessor into the build directory:

  ```sh
  gcc -E -P -x assembler-with-cpp -o build/kernel.ld kernel.ld.S
  ```

  `-x assembler-with-cpp` defines `__ASSEMBLER__`, so shared headers hide
  their C-only parts exactly as they do for assembly files. `-P` drops the
  line markers the linker can't read.

## Layout

### Indentation and line length

- Indent with **tabs, 8 columns wide**. Never indent with spaces.
- **80 columns** is the preferred limit. You may go up to **100** only when
  that clearly reads better and hides nothing.
- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

### Braces

- Top-level commands that take a block (`MEMORY`, `SECTIONS`, `PHDRS`) put
  the opening brace **at the start of the next line**, like a C function:

  ```ld
  SECTIONS
  {
  	...
  }
  ```

- Output section descriptions put the opening brace **last on the line**, like
  a C block. The closing brace goes on its own line, followed by the region
  assignments:

  ```ld
  	.data : ALIGN(4) {
  		data_start = .;
  		*(.data .data.*)
  		data_end = .;
  	} > ram AT> rom
  ```

- Separate output section descriptions with one blank line.
- Write the sections that aren't loaded (debug information, notes, the
  symbol table) one per line, as a block with no blank lines, the way the
  linker's default script does. Each holds one input pattern and starts at
  address 0:

  ```ld
  	.debug_info 0 : { *(.debug_info) }
  	.debug_abbrev 0 : { *(.debug_abbrev) }
  ```

### Statements and spacing

- End every assignment with `;`: `. = ALIGN(4096);`. GNU ld requires it in
  most places, and writing it everywhere means never having to remember
  where.
- Put one space on each side of `=`, `+=` and other operators, and on each
  side of the `:` in an output section description: `.text : {`.
- Put the memory region assignments (`> ram`, `AT> rom`) after the closing
  brace, separated by single spaces.
- List several input section patterns in one statement where they belong
  together: `*(.text .text.*)`.

## Case and literals

- Write **commands and keywords in uppercase**: `SECTIONS`, `MEMORY`,
  `ENTRY`, `ALIGN`, `KEEP`, `ASSERT`. That's how the GNU ld manual writes
  them, and it separates them from names you choose.
- Write hexadecimal with a `0x` prefix and uppercase digits: `0x08000000`,
  `0xFFFF0000`.
- Write sizes with the `K` and `M` suffixes: `LENGTH = 256K`.

## Naming

- Everything you name (symbols, memory regions) uses `snake_case`.
- Name memory regions after what they are: `rom`, `ram`, `sram`, `flash`.
- **Name boundary symbols as `<thing>_start` and `<thing>_end`**:
  `bss_start` and `bss_end`, `kernel_image_start` and `kernel_image_end`.
  Name a load address `<thing>_load_start`, and a size `<thing>_size`.
- In a script that links part of a larger system, prefix symbols with the
  image or module name, so they can't clash with symbols from C code.
- **Never define symbols that start with `__` or with `_` followed by a
  capital letter**, or any new symbol that starts with `_`. C reserves those
  names for the compiler and the C library, and linker symbols share C's
  namespace. Referring to symbols the toolchain itself defines, such as
  `__bss_start` in a default script, is fine.
- Name custom input sections with a leading dot and the module's prefix:
  `.buf_init`.

## Comments

- Use `/* ... */` comments. Linker scripts don't support `//` or `#`
  comments.
- Write multi-line comments with a column of asterisks, and put the
  delimiters on their own lines, as in C.
- **Start every script with a block comment describing the image's layout**:
  each memory region, its address and size, and what lives in it. The layout
  is the reason the script exists, and the comment lets a reader check the
  script against it:

  ```ld
  /*
   * Linker script for the buf firmware image.
   *
   *   rom  0x08000000  256K  .text, .rodata, .ARM.exidx, load image of .data
   *   ram  0x20000000   64K  .data, .bss, stack
   */
  ```

- Comment every `KEEP`, `/DISCARD/` and hard-coded address with the reason
  for it. These are the lines most likely to break the image when changed.

## Third-party code

Linker scripts from vendors (for example, a chip vendor's startup files)
keep their upstream style and are not reformatted, so updates from upstream
stay easy to merge.

## Sources

This guide builds on:

- [GNU ld manual: Linker Scripts](https://sourceware.org/binutils/docs/ld/Scripts.html)
- [LLD documentation](https://lld.llvm.org/), including its
  [linker script notes](https://lld.llvm.org/ELF/linker_script.html)
