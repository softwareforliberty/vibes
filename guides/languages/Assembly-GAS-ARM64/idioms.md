# ARM64 Assembly (GNU as) Idioms and Principles

How to write AArch64 assembly well. [coding-style.md](coding-style.md) covers
how code looks. This guide covers how it's designed: the calling convention,
register and stack discipline, interfacing with C, portability between ELF and
Apple platforms, and the idioms that keep assembly correct and maintainable.
Every example follows the style guide.

## Principles

- **Write as little assembly as possible.** Assembly is hard to read, hard to
  review and tied to one architecture. Every line of it needs a reason C
  couldn't do the job.
- **Follow the ABI exactly.** The calling convention is a contract with every
  compiler and caller. An ABI violation often works until an unrelated change
  exposes it.
- **Every routine has a written contract.** Its inputs, outputs, clobbered
  registers and stack use are documented in its header comment (see
  [Comments](coding-style.md#comments)).
- **One routine, one job.** Small routines with one entry point and a clear
  exit are far easier to verify than long fall-through code.
- **Measure before you optimise.** Hand-written assembly is only faster if a
  profiler says so, on the CPUs you ship to.

## When to write assembly

Write assembly only for work C can't express:

- Boot code, exception-level changes, and anything that runs before a C
  environment exists (no stack, no initialised data).
- Exception vectors, system call entry and context switching, where the exact
  register and stack state matters.
- Instructions the compiler has no way to emit, and no intrinsic for.
- Hot paths where a profiler shows that compiled C is measurably slower, and
  intrinsics (`<arm_neon.h>`) can't close the gap.

Keep the assembly part as thin as possible. Do the setup in assembly, call
into C, and leave everything else to C.

## Calling convention

AArch64 code follows the Procedure Call Standard for the Arm 64-bit
Architecture (AAPCS64). Apple platforms use it with a few differences:

| | AAPCS64 (Linux, BSD) | Apple arm64 |
| --- | --- | --- |
| Integer and pointer arguments | `x0`–`x7`, then the stack | Same |
| Floating-point and SIMD arguments | `v0`–`v7`, then the stack | Same |
| Variadic arguments | Registers, like any other argument | Always on the stack, in 8-byte slots |
| Return value | `x0` (`x0`–`x1` for 128 bits), `v0` for floating point; `x8` points to memory for large structs | Same |
| Callee-saved | `x19`–`x28`, `x29`, `sp`, and the low 64 bits of `v8`–`v15` (`d8`–`d15`) | Same |
| `x18` | Platform register; its use depends on the OS | Reserved; never touch it |
| Frame pointer `x29` | Optional for leaf routines | Must always point to a valid frame record |
| Stack alignment | 16 bytes, at all times | Same |
| Red zone below `sp` | None | 128 bytes |
| C symbol names | Unchanged: `buf_sum` | Prefixed with `_`: `_buf_sum` |

Every register not listed as callee-saved may be changed by a call. That
includes `x30` (which `bl` overwrites with the return address), `x16` and
`x17`, the high halves of `v8`–`v15`, and the condition flags.

## Registers

- **Save only the callee-saved registers you use**, and restore them in the
  reverse order you saved them. Save and restore them in pairs with `stp` and
  `ldp`.
- **Assume every caller-saved register and the flags are destroyed by any
  call**, including calls to your own routines. A routine's documented
  clobbers can change later, but the ABI can't.
- **Never use `x18`.** Apple and Windows reserve it, and Linux kernels may use
  it for the shadow call stack. Code that leaves it alone runs everywhere.
- **Don't keep values in `x16` or `x17` across a branch to another routine.**
  The linker may insert a veneer or PLT stub on the way that uses them.
- **Exception handlers save every register they touch**, including the flags
  and any SIMD state. The interrupted code didn't make a call, so it expects
  nothing to change.

## The stack

### Alignment

- `sp` must be a multiple of 16 whenever it's used to access memory, not only
  at calls. The CPU can be configured to fault on a misaligned `sp`.
- Move `sp` only in multiples of 16. To save one register, still reserve 16
  bytes.
- Don't use the space below `sp`. Only Apple platforms guarantee a red zone,
  and kernel and exception code can never use one.

### Prologue and epilogue

A routine that calls others, or that saves registers, sets up a **frame
record**: `x29` and `x30` stored as a pair, with `x29` pointing at them.
Frame records make stack traces from debuggers and profilers reliable. A leaf
routine that saves nothing may skip the frame, except on Apple platforms.

```asm
/*
 * buf_flush - Write out everything buffered in b.
 *
 * In:		x0 = b
 * Out:		x0 = 0, or a negative errno code
 * Clobbers:	caller-saved registers, flags
 */
FUNC_BEGIN buf_flush
	PAC_SIGN
	stp	x29, x30, [sp, #-32]!
	.cfi_def_cfa_offset	32
	.cfi_offset	x29, -32
	.cfi_offset	x30, -24
	mov	x29, sp
	str	x19, [sp, #16]
	.cfi_offset	x19, -16
	mov	x19, x0			// keep b across the call

	bl	SYM(buf_write_all)
	...

	ldr	x19, [sp, #16]
	ldp	x29, x30, [sp], #32
	PAC_AUTH
	ret
FUNC_END buf_flush
```

- Allocate the whole frame with the first `stp` (pre-index), so the frame
  record sits at the bottom of the frame and `sp` stays aligned throughout.
- Put a CFI directive right after every instruction that moves `sp` or saves
  a register, so the unwind information is exact at every instruction.

## A shared header

Every `.S` file includes `asm.h` first. It hides the differences between ELF
and Mach-O, and adds branch protection when the build asks for it. Code then
says *what* it means (`FUNC_BEGIN`, `SYM()`, `PAGE()`), and the header says
*how* on each platform:

```asm
/*
 * asm.h - Portability macros for AArch64 assembly.
 *
 * Included first by every .S file. Hides the differences between ELF
 * (Linux, BSD) and Mach-O (Apple platforms), and adds branch protection
 * when the build enables it.
 */
#ifndef ASM_H
#define ASM_H

#if defined(__APPLE__)
#define SYM(name)	_##name
#define LOCAL(name)	L##name
#define PAGE(sym)	sym@PAGE
#define PAGEOFF(sym)	sym@PAGEOFF
#define GOTPAGE(sym)	sym@GOTPAGE
#define GOTPAGEOFF(sym)	sym@GOTPAGEOFF
#define RODATA_SECTION	.section __TEXT,__const
#elif defined(__ELF__)
#define SYM(name)	name
#define LOCAL(name)	.L##name
#define PAGE(sym)	sym
#define PAGEOFF(sym)	:lo12:sym
#define GOTPAGE(sym)	:got:sym
#define GOTPAGEOFF(sym)	:got_lo12:sym
#define RODATA_SECTION	.section .rodata
#else
#error "unsupported object format"
#endif

/* BTI_C - Mark an indirect-call landing pad, when BTI is enabled. */
	.macro	BTI_C
#if defined(__ARM_FEATURE_BTI_DEFAULT)
	hint	#34			// bti c
#endif
	.endm

/* PAC_SIGN - Sign x30 with the A key, when return signing is enabled. */
	.macro	PAC_SIGN
#if defined(__ARM_FEATURE_PAC_DEFAULT)
	hint	#25			// paciasp
	.cfi_negate_ra_state
#endif
	.endm

/* PAC_AUTH - Check x30's signature before returning. */
	.macro	PAC_AUTH
#if defined(__ARM_FEATURE_PAC_DEFAULT)
	hint	#29			// autiasp
	.cfi_negate_ra_state
#endif
	.endm

#if defined(__APPLE__)
/* FUNC_BEGIN name - Start an exported routine. */
	.macro	FUNC_BEGIN name
	.globl	_\name
	.balign	4
_\name:
	.cfi_startproc
	BTI_C
	.endm

/* FUNC_END name - End a routine started with FUNC_BEGIN. */
	.macro	FUNC_END name
	.cfi_endproc
	.endm
#else
/* FUNC_BEGIN name - Start an exported routine. */
	.macro	FUNC_BEGIN name
	.globl	\name
	.type	\name, %function
	.balign	4
\name:
	.cfi_startproc
	BTI_C
	.endm

/* FUNC_END name - End a routine started with FUNC_BEGIN. */
	.macro	FUNC_END name
	.cfi_endproc
	.size	\name, . - \name
	.endm
#endif /* __APPLE__ */

#endif /* ASM_H */
```

The `hint` encodings run as no-ops on CPUs without the feature, and every
assembler accepts them whatever architecture version it targets.

## Branch protection

Armv8.3 and Armv8.5 added two hardware defences against code-reuse attacks.
Support both on Linux by building with `-mbranch-protection=standard`, which
turns the macros above on:

- **Pointer authentication (PAC)** signs the return address in `x30` before
  it's saved to the stack, and checks the signature before `ret`. A
  corrupted return address then faults instead of jumping. Call `PAC_SIGN`
  first in every routine that saves `x30`, and `PAC_AUTH` just before its
  `ret`.
- **Branch target identification (BTI)** faults on an indirect branch to an
  instruction that isn't a landing pad. `FUNC_BEGIN` starts every exported
  routine with `bti c`, because C may call it through a function pointer.
  Code that jumps through a register (`br`) to a label in the same file needs
  `bti j` at that label.
- On ELF, the linker only enables BTI for a program if every object in it is
  marked as compatible. Mark each object built with branch protection with a
  GNU property note that lists the features it was built with, and add it to
  `asm.h` so no file can forget it:

  ```asm
  #if defined(__ARM_FEATURE_BTI_DEFAULT)
  #define PROPERTY_BTI	1
  #else
  #define PROPERTY_BTI	0
  #endif
  #if defined(__ARM_FEATURE_PAC_DEFAULT)
  #define PROPERTY_PAC	2
  #else
  #define PROPERTY_PAC	0
  #endif
  #define PROPERTY_BITS	(PROPERTY_BTI | PROPERTY_PAC)

  #if defined(__ELF__) && PROPERTY_BITS
  	.pushsection	.note.gnu.property, "a"
  	.balign	8
  	.word	4			// name size
  	.word	16			// descriptor size
  	.word	5			// NT_GNU_PROPERTY_TYPE_0
  	.asciz	"GNU"
  	.word	0xC0000000		// GNU_PROPERTY_AARCH64_FEATURE_1_AND
  	.word	4			// property size
  	.word	PROPERTY_BITS		// bit 0 = BTI, bit 1 = PAC
  	.word	0			// padding
  	.popsection
  #endif /* __ELF__ && PROPERTY_BITS */
  ```

The macros above use the A key, which is what `-mbranch-protection=standard`
selects. Apple's arm64e uses its own pointer-authentication scheme. Follow
Apple's documentation when targeting it.

## Interfacing with C

- **Declare every routine C calls in a C header**, with a prototype that
  follows the [C coding style](../C/coding-style.md). The prototype carries the
  API documentation. The assembly header comment adds the register details.
- **Name the routine exactly as C would**, with the module prefix:
  `buf_flush`, matching `int buf_flush(struct buf *b);`.
- **Return errors the way C does**: `0` for success, or a negative errno code
  in `w0`/`x0`, as in the [C idioms](../C/idioms.md#error-handling). Never
  report results through the flags across the C boundary.
- **Define routines with `FUNC_BEGIN` and `FUNC_END`**, and refer to C symbols
  with `SYM()`: `bl SYM(memcpy)`. The source then stays the same on every
  platform.
- **Keep shared struct layouts in sync.** Field offsets live in the shared C
  header, next to a comment naming the struct they mirror (see
  [Constants and data](coding-style.md#constants-and-data)). A test compares
  each offset with `offsetof()` in C.
- Calling C from assembly follows the same convention as being called: keep
  `sp` aligned, pass arguments in the right registers, and assume every
  caller-saved register is destroyed.

## Apple platforms

Most of Apple's differences are handled by `asm.h`. The rest need care in the
code itself:

- **Leave `x18` alone**, and **keep `x29` pointing at a valid frame record**
  at all times, even in leaf routines that call nothing.
- **Pass variadic arguments on the stack**, never in registers, when calling a
  variadic C function such as `printf`.
- **Write local labels with `LOCAL()`**. Mach-O treats only `L`-prefixed
  labels as assembler-local. A `.L` label would stay in the symbol table, and
  crash reports would blame it instead of the routine it's in.
- **Don't write ELF-only directives** (`.type`, `.size`, `.section .rodata`)
  outside `asm.h`.

## Addressing and position-independent code

- **Write all code position-independent.** Shared libraries require it,
  executables are usually built as position-independent (PIE), and Apple
  platforms require it.
- **Form addresses with `adrp` and `add`**, which reach anything within
  ±4 GiB of the code:

  ```asm
  	adrp	x0, PAGE(msg_hello)
  	add	x0, x0, PAGEOFF(msg_hello)
  ```

- **Load the address of external data from the global offset table:**

  ```asm
  	adrp	x0, GOTPAGE(SYM(shared_counter))
  	ldr	x0, [x0, GOTPAGEOFF(SYM(shared_counter))]
  ```

- **Build constants with `mov`**, or with `movz` and `movk` when one
  instruction can't encode the value. Don't use `ldr x0, =value`: it puts a
  literal pool of data into `.text`, and for an address it needs a relocation
  that position-independent code can't have.

## Data

- **Align data to its natural size**, or more where the instructions using it
  require it, with `.balign`. Aligned `ldp`/`stp` and SIMD loads run fastest
  at their natural alignment:

  ```asm
  	.bss
  	.balign	16
  scratch:	.space	256
  ```

- Put read-only data in a read-only section, never in `.text`. Mixing data
  into code wastes instruction cache and confuses disassemblers.
- Prefer statically sized storage when the limit is known and small. It can't
  fail at run time.

## Memory ordering

AArch64 is **weakly ordered**: other cores can see your loads and stores in a
different order from the one you wrote them in. x86 hides most of this; ARM64
doesn't.

- Use acquire loads (`ldar`) and release stores (`stlr`) for the flags and
  pointers that publish data to another core. They match C's
  `memory_order_acquire` and `memory_order_release`.
- Use `dmb ish` only where you need a full barrier between ordinary accesses.
- For atomic read-modify-write, use the LSE instructions (`ldadd`, `cas`,
  `swp`) when the target guarantees Armv8.1 or later. Otherwise use an
  exclusive `ldaxr`/`stlxr` loop that retries until the store succeeds.
- Make the ordering in assembly match the ordering the C side of the same
  data uses. Mixed assumptions between the two are the usual source of
  rare, unreproducible bugs.

## Instruction idioms

- Use `xzr` and `wzr` for zero: `mov x0, xzr`, `str xzr, [x1]`. No register
  needs clearing first.
- Writing a 32-bit `w` register zeroes the upper half of its `x` register, so
  `mov w0, #1` sets all of `x0`.
- Test for zero and branch in one instruction with `cbz`/`cbnz`, and test a
  single bit with `tbz`/`tbnz`.
- Let the loop's arithmetic set the flags: `subs x1, x1, #1` followed by
  `b.ne`, rather than a separate `cmp`.
- Load and store registers in pairs with `ldp` and `stp`. One instruction
  moves 16 bytes, and it keeps `sp` adjustments in 16-byte steps.
- Use `csel`, `csinc` and `cset` instead of short branches. Branch-free code
  can't be mispredicted.
- Return with `ret`, which uses `x30` and tells the branch predictor it's a
  return. Never return with `br x30`.

## Self-modifying code

Don't write it:

- Modern systems map code read-only and data non-executable, so the code
  can't write to itself without weakening that protection.
- ARM64 keeps separate instruction and data caches. New code only runs
  correctly after explicit cache maintenance, which is easy to get wrong.
- Code that changes at run time can't be reviewed, disassembled or debugged
  from its source.

Where code generation is the point (a JIT compiler), keep it in its own
module. Write the code into a fresh buffer, make the buffer executable and not
writable, then flush the instruction cache with `__builtin___clear_cache()`
from C before running it. On Apple platforms, use `MAP_JIT` memory and
Apple's write-protection APIs.

## Testing

- **Test every routine from C.** A C test harness calls the routine through
  its prototype, which also checks the calling convention.
- **Compare against a reference.** Write the same function in plain C and
  check that both give the same results, on random inputs and on edge cases:
  zero length, maximum values, unaligned buffers.
- **Check that callee-saved registers survive.** A small wrapper fills every
  callee-saved register with a known value, calls the routine, and checks the
  values afterwards.
- **Test every platform you ship**: ELF and Apple, with and without branch
  protection, on hardware or an emulator that enforces BTI and PAC.

## Sources

- [Procedure Call Standard for the Arm 64-bit Architecture (AAPCS64)](https://github.com/ARM-software/abi-aa/blob/main/aapcs64/aapcs64.rst)
- [Apple, *Writing ARM64 code for Apple platforms*](https://developer.apple.com/documentation/xcode/writing-arm64-code-for-apple-platforms)
- [Arm C Language Extensions (ACLE)](https://github.com/ARM-software/acle), for the branch-protection feature macros
- [ELF for the Arm 64-bit Architecture](https://github.com/ARM-software/abi-aa/blob/main/aaelf64/aaelf64.rst), for the GNU property note
- [GNU as manual](https://sourceware.org/binutils/docs/as/)
- [x86 NASM idioms](../Assembly-NASM-x86/idioms.md), for the principles
  shared between assembly dialects
- [C idioms](../C/idioms.md), for the conventions shared with C
