# GNU ld Linker Script Idioms and Principles

How to write linker scripts well. [coding-style.md](coding-style.md) covers
how linker scripts look. This guide covers how they're designed: when to
write one at all, memory regions, load and run addresses, symbols shared
with C, and the checks that keep an image's layout correct. Every example
follows the style guide.

## Principles

- **Don't write a linker script unless you need one.** The linker's default
  script is right for ordinary programs, and a custom script turns every
  toolchain upgrade into a review of your layout.
- **Place every section on purpose.** Every input section matches a rule in
  the script, and the link fails if one doesn't. Nothing ends up somewhere by
  accident.
- **Make the layout checkable.** Memory regions, `ASSERT`s and map files let
  the linker and reviewers catch a layout mistake at link time, instead of on
  the hardware.
- **The script and the startup code are one contract.** Every symbol the
  script defines for C or assembly is documented, and both sides change
  together.

## When to write a linker script

- **Hosted programs** (anything that runs on an operating system) use the
  toolchain's default script. Don't pass `-T` at all.
- **Freestanding images** (kernels, bootloaders, firmware) need their own
  script, because only the project knows where its memory is and what must
  go where.
- For a small change to an ordinary program, prefer something lighter than a
  full script:
  - put a function or variable in a named section with
    `__attribute__((section(".buf_init")))`, and let the default script place
    it;
  - add a fragment to the default script with `INSERT AFTER`, which both GNU
    ld and LLD support.
- To see the script the linker uses by default, run `ld --verbose`. Start a
  new script from the parts of it you need, not from a blank page.

## Memory regions

Declare the target's memory with `MEMORY`, and assign every output section to
a region:

```ld
MEMORY
{
	rom (rx)  : ORIGIN = 0x08000000, LENGTH = 256K
	ram (rwx) : ORIGIN = 0x20000000, LENGTH = 64K
}
```

- The linker reports an error when a region overflows, so an image that's
  grown too big fails to link instead of failing on the device.
- Give each region its attributes (`r`, `w`, `x`), so the script records
  what each kind of memory allows.
- Use `--print-memory-usage` in every build, so the build log shows how close
  each region is to full.

## Sections

A complete script for a firmware image that runs code from flash and data
from RAM:

```ld
/*
 * Linker script for the buf firmware image.
 *
 * Code and read-only data run from flash. Initialised data is stored in
 * flash and copied to RAM by the startup code; .bss is zeroed in RAM.
 *
 *   rom  0x08000000  256K  .text, .rodata, .ARM.exidx, load image of .data
 *   ram  0x20000000   64K  .data, .bss, stack
 */

ENTRY(reset_handler)

MEMORY
{
	rom (rx)  : ORIGIN = 0x08000000, LENGTH = 256K
	ram (rwx) : ORIGIN = 0x20000000, LENGTH = 64K
}

/* Overridable with -Wl,--defsym=stack_size=0x2000. */
PROVIDE(stack_size = 0x1000);

SECTIONS
{
	.text : {
		/* Read by the hardware; nothing references it. */
		KEEP(*(.vectors))
		*(.text .text.*)
		/* Veneers and stubs that GNU ld generates. */
		*(.glue_7 .glue_7t .vfp11_veneer .v4_bx .iplt)
	} > rom

	.rodata : {
		*(.rodata .rodata.*)
		*(.ARM.extab .ARM.extab.*)
		*(.rel.iplt)
	} > rom

	/* Unwind tables, from libgcc and any code that unwinds the stack. */
	.ARM.exidx : {
		*(.ARM.exidx .ARM.exidx.*)
	} > rom

	.data : ALIGN(4) {
		data_start = .;
		*(.data .data.*)
		*(.igot.plt)
		. = ALIGN(4);
		data_end = .;
	} > ram AT> rom
	data_load_start = LOADADDR(.data);

	.bss : ALIGN(4) {
		bss_start = .;
		*(.bss .bss.*)
		. = ALIGN(4);
		bss_end = .;
	} > ram

	.stack (NOLOAD) : ALIGN(16) {
		. += stack_size;
		stack_top = .;
	} > ram

	/*
	 * Sections that aren't loaded: toolchain notes, debug information and
	 * the symbol table. Each starts at 0, as in the default script.
	 */
	.comment 0 : { *(.comment) }
	.ARM.attributes 0 : { *(.ARM.attributes) }
	.debug_aranges 0 : { *(.debug_aranges) }
	.debug_pubnames 0 : { *(.debug_pubnames) }
	.debug_info 0 : { *(.debug_info) }
	.debug_abbrev 0 : { *(.debug_abbrev) }
	.debug_line 0 : { *(.debug_line) }
	.debug_frame 0 : { *(.debug_frame) }
	.debug_str 0 : { *(.debug_str) }
	.debug_loc 0 : { *(.debug_loc) }
	.debug_macinfo 0 : { *(.debug_macinfo) }
	.debug_pubtypes 0 : { *(.debug_pubtypes) }
	.debug_ranges 0 : { *(.debug_ranges) }
	.debug_addr 0 : { *(.debug_addr) }
	.debug_line_str 0 : { *(.debug_line_str) }
	.debug_loclists 0 : { *(.debug_loclists) }
	.debug_macro 0 : { *(.debug_macro) }
	.debug_names 0 : { *(.debug_names) }
	.debug_rnglists 0 : { *(.debug_rnglists) }
	.debug_str_offsets 0 : { *(.debug_str_offsets) }
	/* LLD reports these as orphans unless the script places them. */
	.symtab 0 : { *(.symtab) }
	.strtab 0 : { *(.strtab) }
	.shstrtab 0 : { *(.shstrtab) }

	/* Only the linker reads it; nothing in the image uses it. */
	/DISCARD/ : {
		*(.note.GNU-stack)
	}
}

ASSERT(stack_size >= 0x400, "stack_size is smaller than 1K")
```

- **Name the entry point with `ENTRY()`**, so debuggers, loaders and
  `readelf` all agree on where execution starts.
- **List the most specific patterns first.** The first rule that matches an
  input section wins, so `KEEP(*(.vectors))` must come before
  `*(.text .text.*)`.
- Combine each standard section with its numbered variants
  (`*(.text .text.*)`). `-ffunction-sections` and `-fdata-sections` put each
  function and variable in its own `.text.<name>` or `.data.<name>` section.
- **Align the start and end of any section that code copies or clears.**
  Startup code that works a word at a time needs both boundaries aligned to
  the word size.
- Mark sections that occupy memory but have no contents in the file
  `(NOLOAD)`, such as a stack or a DMA buffer, so the image doesn't carry
  zeros for them.
- **Place the sections the toolchain adds, not just your code and data.**
  With `--orphan-handling=error` (see [GNU ld and LLD](#gnu-ld-and-lld)),
  the link fails on any section without a rule: the veneers and stubs GNU ld
  generates, libgcc's unwind tables, debug information and, with LLD, the
  symbol table. Place them as the linker's default script does: generated
  code in `.text`, and sections that aren't loaded at address 0. If a
  compiler flag adds a section the script doesn't place, the error names it;
  add a rule for it.

## Load and run addresses

A section that runs from RAM but must survive power-off is **stored** in one
place and **run** from another:

- `> ram AT> rom` gives `.data` its run address in `ram` and its load address
  in `rom`.
- `LOADADDR(.data)` gives the load address, which the startup code copies
  from. Export it as a symbol (`data_load_start`) next to the section.
- `.bss` needs no load address. It has no contents, and the startup code
  zeroes it at its run address.
- Check the result in the map file, or with `readelf -l`: each loadable
  segment's `PhysAddr` is the load address and `VirtAddr` the run address.

## Symbols shared with C and assembly

- A linker symbol is **an address with no storage behind it**. Declare it in
  C as an array of `char`, and only ever use its address:

  ```c
  extern char data_start[];
  extern char data_end[];
  extern char data_load_start[];
  extern char bss_start[];
  extern char bss_end[];

  static void startup_init_memory(void)
  {
  	size_t data_len = (uintptr_t)data_end - (uintptr_t)data_start;
  	size_t bss_len = (uintptr_t)bss_end - (uintptr_t)bss_start;

  	memcpy(data_start, data_load_start, data_len);
  	memset(bss_start, 0, bss_len);
  }
  ```

  Declaring it as an array means `data_start` already *is* the address. A
  declaration such as `extern int data_start;` invites code to read the
  "variable", which reads whatever happens to be at that address.
- **Convert to `uintptr_t` before subtracting or comparing** two linker
  symbols. In C, subtracting or comparing pointers into different objects is
  undefined behaviour, and the compiler treats each symbol as a separate
  object.
- Declare every symbol the script defines in one C header, next to the code
  that uses them, with a comment pointing back to the script.
- Assembly uses the same symbols directly by name, for example
  `leaq bss_start(%rip), %rdi` in x86-64 GNU as.
- **Use `PROVIDE()` for symbols the build may override**, such as a stack
  size. `PROVIDE` defines the symbol only when something references it and
  nothing else defines it, so `-Wl,--defsym` or an object file can replace
  the default.
- In shared libraries and position-independent executables, use `HIDDEN()`
  or `PROVIDE_HIDDEN()` for symbols that are only for the image's own code,
  so they aren't exported to other modules.

## Garbage collection and KEEP

- Link with `-Wl,--gc-sections` (and compile with `-ffunction-sections
  -fdata-sections`) to drop functions and data that nothing references.
- **Wrap in `KEEP()` every section that's used without being referenced**:
  vector tables read by hardware, tables the code finds through start and end
  symbols, and `.init_array`. Without `KEEP`, garbage collection removes them
  and the image links cleanly but doesn't work.
- Keep the `KEEP` list short. Every entry is a section the linker can never
  remove, used or not.

## Discarding sections

- Discard a section with `/DISCARD/` only when you know nothing in the image
  needs it, such as `.note.GNU-stack`, which only the linker reads.
- Don't discard debug information or `.comment` to silence an orphan error.
  They aren't loaded, so they cost nothing on the target, and debuggers read
  them from the ELF file. Place them at address 0 instead.
- Never discard `.init_array`, `.fini_array`, `.eh_frame` or `.ARM.exidx`
  from an image that runs constructors or unwinds the stack. The link
  succeeds, and the failure appears at run time.

## Layout checks

- **Check every layout assumption with `ASSERT`**, so a violation stops the
  link with a clear message:

  ```ld
  ASSERT(ADDR(.text) == ORIGIN(rom), "vector table must be at the start of rom")
  ASSERT(stack_size % 16 == 0, "stack_size must be a multiple of 16")
  ```

- Write each message so it says what's wrong, the way an error from C code
  would.
- Treat a change to the map file as a change to review. A section moving or
  growing unexpectedly is a bug report waiting to happen.

## GNU ld and LLD

- LLD implements most of GNU ld's script language, but it places orphan
  sections differently and doesn't support every command. Link with
  `--orphan-handling=error` so neither linker gets to guess.
- LLD also reports the symbol table sections (`.symtab`, `.strtab` and
  `.shstrtab`) as orphans, so a script for both linkers places them at
  address 0. GNU ld accepts the same rules.
- If a project supports both linkers, link with both in CI and compare the
  map files or `readelf -S` output.
- Use only commands documented by both linkers in a script meant for both.

## Build integration

- Make the script a dependency of the link step, so editing it relinks the
  image. In Make, list it as a prerequisite of the image (see the
  [Make idioms](../Make/idioms.md)). In CMake, add it to the executable's
  `LINK_DEPENDS` property (see the [CMake idioms](../CMake/idioms.md)).
- Generate a preprocessed script (`<name>.ld.S`) into the build directory,
  never into the source tree.
- Keep the map file from every CI build, so a layout regression can be
  traced to the commit that caused it.

## Sources

- [GNU ld manual](https://sourceware.org/binutils/docs/ld/), especially
  [Linker Scripts](https://sourceware.org/binutils/docs/ld/Scripts.html) and
  [Command-line Options](https://sourceware.org/binutils/docs/ld/Options.html)
- [LLD documentation](https://lld.llvm.org/), including its
  [linker script notes](https://lld.llvm.org/ELF/linker_script.html)
