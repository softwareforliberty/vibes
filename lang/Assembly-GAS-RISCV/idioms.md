# RISC-V Assembly (GNU as) Idioms and Principles

How to write RISC-V assembly well. [coding-style.md](coding-style.md) covers
how code looks. This guide covers how it's designed: the calling convention,
register and stack discipline, interfacing with C, linker relaxation, and the
idioms that keep assembly correct and maintainable. Every example follows the
style guide.

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
  profiler says so, on the cores you ship to.

## When to write assembly

Write assembly only for work C can't express:

- Boot code, privilege-mode changes, and anything that runs before a C
  environment exists (no stack, no `gp`, no initialised data).
- Trap entry, system call entry and context switching, where the exact
  register and stack state matters.
- Instructions the compiler has no way to emit, such as CSR accesses and
  `fence.i`, where no intrinsic exists.
- Hot paths where a profiler shows that compiled C is measurably slower, and
  intrinsics can't close the gap.

Keep the assembly part as thin as possible. Do the setup in assembly, call
into C, and leave everything else to C.

## Calling convention

RISC-V code follows the RISC-V ELF psABI. The integer convention is the same
for every ABI. The hard-float ABIs add floating-point argument registers:

| | Soft-float (`ilp32`, `lp64`) | Hard-float (`ilp32d`, `lp64d`) |
| --- | --- | --- |
| Integer and pointer arguments | `a0`–`a7`, then the stack | Same |
| Floating-point arguments | In integer registers, like integers | `fa0`–`fa7`, then integer registers, then the stack |
| Variadic arguments | Integer registers, then the stack | Same: never in floating-point registers |
| Return value | `a0` (`a0`–`a1` for 2×XLEN bits) | `a0`–`a1`, or `fa0`–`fa1` for floating point |
| Callee-saved | `sp`, `s0`–`s11` | `sp`, `s0`–`s11`, `fs0`–`fs11` |
| Never allocated | `zero`, `gp`, `tp` | Same |
| Stack alignment | 16 bytes | 16 bytes |
| Red zone below `sp` | None | None |

Every register not listed as callee-saved may be changed by a call. That
includes `ra`, which `call` overwrites with the return address.

A variadic argument that needs 2×XLEN alignment (such as a `long long` on
RV32) goes in an aligned register pair, starting at an even-numbered `a`
register. The single-precision hard-float ABIs (`ilp32f`, `lp64f`) work like
the `d` ABIs for `float` values only.

## Registers

- **Save only the callee-saved registers you use**, and restore them in the
  reverse order you saved them.
- **Assume every caller-saved register is destroyed by any call**, including
  calls to your own routines. A routine's documented clobbers can change
  later, but the ABI can't.
- **Never write `gp` or `tp`** outside the startup code and thread switch
  that own them. The linker relies on `gp` (see
  [Linker relaxation](#linker-relaxation-and-gp)), and `tp` points to the
  current thread's data.
- **Trap handlers save every register they touch**, including any
  floating-point and vector state. The interrupted code didn't make a call,
  so it expects nothing to change.

## The stack

### Alignment

- `sp` must be a multiple of 16 at every call and on entry to every routine.
- Move `sp` only in multiples of 16. To save one register, still reserve 16
  bytes.
- Never use the space below `sp`. RISC-V has no red zone, so a trap or signal
  can overwrite it at any moment.

### Prologue and epilogue

A routine that calls others, or that saves registers, sets up a **frame
record**: `ra` and the caller's `s0`, saved just below the address `s0` then
holds. Frame records make stack traces from debuggers and profilers reliable.
A leaf routine that saves nothing may skip the frame.

```asm
/*
 * buf_flush - Write out everything buffered in b.
 *
 * In:		a0 = b
 * Out:		a0 = 0, or a negative errno code
 * Clobbers:	caller-saved registers
 */
FUNC_BEGIN buf_flush
	addi	sp, sp, -4*SZREG
	.cfi_def_cfa_offset	4*SZREG
	REG_S	ra, 3*SZREG(sp)
	.cfi_offset	ra, -SZREG
	REG_S	s0, 2*SZREG(sp)
	.cfi_offset	s0, -2*SZREG
	REG_S	s1, 1*SZREG(sp)
	.cfi_offset	s1, -3*SZREG
	addi	s0, sp, 4*SZREG		# s0 = frame top
	mv	s1, a0			# keep b across the call

	call	buf_write_all
	...

	REG_L	s1, 1*SZREG(sp)
	REG_L	s0, 2*SZREG(sp)
	REG_L	ra, 3*SZREG(sp)
	addi	sp, sp, 4*SZREG
	ret
FUNC_END buf_flush
```

- Size every frame in multiples of `SZREG` that add up to a multiple of 16.
  Four slots is 32 bytes on RV64 and 16 on RV32, so the same code is aligned
  on both.
- Save `ra` in the highest slot and the caller's `s0` just below it, then
  point `s0` at the top of the frame. That's the frame-record layout the
  psABI defines, so unwinders can follow the chain of `s0` values.
- Put a CFI directive right after every instruction that moves `sp` or saves
  a register, so the unwind information is exact at every instruction.

## A shared header

Every `.S` file includes `asm.h` first. It lets one source build for RV32 and
RV64, and defines the routine macros. Code then says *what* it means
(`REG_S`, `FUNC_BEGIN`), and the header says *how*:

```asm
/*
 * asm.h - Portability macros for RISC-V assembly.
 *
 * Included first by every .S file. Hides the difference between RV32 and
 * RV64, and defines the macros that start and end a routine.
 */
#ifndef ASM_H
#define ASM_H

#if __riscv_xlen == 64
#define REG_L		ld
#define REG_S		sd
#define SZREG		8
#elif __riscv_xlen == 32
#define REG_L		lw
#define REG_S		sw
#define SZREG		4
#else
#error "unsupported XLEN"
#endif /* __riscv_xlen */

/* FUNC_BEGIN name - Start an exported routine. */
	.macro	FUNC_BEGIN name
	.globl	\name
	.type	\name, @function
	.balign	4
\name:
	.cfi_startproc
	.endm

/* FUNC_END name - End a routine started with FUNC_BEGIN. */
	.macro	FUNC_END name
	.cfi_endproc
	.size	\name, . - \name
	.endm

#endif /* ASM_H */
```

- Write register-sized loads and stores with `REG_L` and `REG_S`, and
  register-sized offsets in multiples of `SZREG`. Write fixed-size accesses
  (`lw`, `sd`) only for data whose size doesn't depend on XLEN.
- Build and test every XLEN you ship (see [Testing](#testing)).

## Interfacing with C

- **Declare every routine C calls in a C header**, with a prototype that
  follows the [C coding style](../C/coding-style.md). The prototype carries the
  API documentation. The assembly header comment adds the register details.
- **Name the routine exactly as C would**, with the module prefix:
  `buf_flush`, matching `int buf_flush(struct buf *b);`.
- **Return errors the way C does**: `0` for success, or a negative errno code
  in `a0`, as in the [C idioms](../C/idioms.md#error-handling).
- **Define routines with `FUNC_BEGIN` and `FUNC_END`**, and call C with the
  `call` pseudo-instruction, which reaches anywhere and lets the linker
  shorten it.
- **Keep shared struct layouts in sync.** Field offsets live in the shared C
  header, next to a comment naming the struct they mirror (see
  [Constants and data](coding-style.md#constants-and-data)). A test compares
  each offset with `offsetof()` in C.
- On RV64, a 32-bit `int` argument or result is sign-extended to 64 bits in
  its register, even when the C type is `unsigned int`. Extend with `sext.w`
  before returning a 32-bit result you computed with 64-bit instructions.
- Calling C from assembly follows the same convention as being called: keep
  `sp` aligned, pass arguments in the right registers, and assume every
  caller-saved register is destroyed.

## Linker relaxation and gp

The RISC-V linker **relaxes** code: when it can see that a target is close
enough, it replaces a two-instruction sequence with a shorter one. For
example, it can turn `call` into a single `jal`, and an access to global data
into one instruction that's relative to `gp`. This shrinks code, but it means
instruction sizes aren't final until link time.

- **Never compute distances between labels yourself**, or assume a sequence
  has a fixed length. Let the assembler and linker resolve every offset.
- **Initialise `gp` once, in the startup code, with relaxation turned off.**
  Otherwise the linker could relax the instruction that sets `gp` into one
  that uses it:

  ```asm
  	.option	push
  	.option	norelax
  	lla	gp, __global_pointer$
  	.option	pop
  ```

- Turn relaxation off with `.option norelax`, inside `.option push` and
  `.option pop`, for any other sequence that must keep its exact layout, such
  as code patched at run time.

## Addressing and position-independent code

- **Load the address of a symbol in the same module with `lla`.** It always
  produces a PC-relative `auipc` and `addi`, which work in any program.
- **Load the address of external data with `la`.** In position-independent
  code, `la` loads the address from the global offset table, so it works when
  the symbol lives in another shared object.
- **Build constants with `li`.** The assembler picks the shortest sequence for
  the value, from one instruction up to several on RV64.
- Keep data out of `.text`. Mixing data into code wastes instruction cache and
  confuses disassemblers.

## Data

- **Align data to its natural size** with `.balign`. Many RISC-V cores trap
  on a misaligned access and emulate it in software, which is very slow:

  ```asm
  	.bss
  	.balign	16
  scratch:	.space	256
  ```

- Use the size-specific data directives: `.byte`, `.half`, `.word` (32 bits)
  and `.dword` (64 bits).
- Put read-only data in `.rodata`, never in `.text`.
- Prefer statically sized storage when the limit is known and small. It can't
  fail at run time.

## Memory ordering

RISC-V uses a **weak memory model** (RVWMO): other harts can see your loads
and stores in a different order from the one you wrote them in.

- Order accesses with `fence`, naming only the orderings you need:
  `fence r, rw` after a load that acquires, and `fence rw, w` before a store
  that releases. `fence rw, rw` is the full barrier.
- For atomic read-modify-write, use the A extension's `amo` instructions
  (`amoadd.w`, `amoswap.d`) with `.aq` and `.rl` ordering bits, or an
  `lr`/`sc` loop that retries until the store succeeds.
- Make the ordering in assembly match the ordering the C side of the same
  data uses. Mixed assumptions between the two are the usual source of
  rare, unreproducible bugs.

## Instruction idioms

- **RISC-V has no condition flags.** Compare and branch in one instruction
  (`blt a0, a1, .Lbuf_sum_done`), and produce a boolean with `slt`, `sltu`,
  `seqz` or `snez`.
- Use `zero` as a source of zero and as a discard destination:
  `mv a0, zero`, `sw zero, 0(t0)`.
- Count loops down to zero, so the loop ends with a single `bnez`.
- On RV64, the `w` instructions (`addw`, `subw`, `slliw`) work on the low 32
  bits and sign-extend the result. Use them for C `int` arithmetic.
- Use `tail` for a call in tail position. It jumps to the callee without
  saving a return address, so the callee returns straight to your caller.
- Return with `ret`, which tells the return-address predictor it's a return.

## Self-modifying code

Don't write it:

- Modern systems map code read-only and data non-executable, so the code
  can't write to itself without weakening that protection.
- A hart only sees new instructions after a `fence.i`, and `fence.i` covers
  only the hart that runs it. Other harts need the operating system's help.
- Code that changes at run time can't be reviewed, disassembled or debugged
  from its source.

Where code generation is the point (a JIT compiler), keep it in its own
module. Write the code into a fresh buffer, make the buffer executable and not
writable, then flush the instruction cache with `__builtin___clear_cache()`
from C, which asks the operating system to synchronise every hart.

## Testing

- **Test every routine from C.** A C test harness calls the routine through
  its prototype, which also checks the calling convention.
- **Compare against a reference.** Write the same function in plain C and
  check that both give the same results, on random inputs and on edge cases:
  zero length, maximum values, unaligned buffers.
- **Check that callee-saved registers survive.** A small wrapper fills every
  callee-saved register with a known value, calls the routine, and checks the
  values afterwards.
- **Test every XLEN, ABI and extension set you ship**, for example RV32 and
  RV64, with and without the C extension. QEMU runs them all on one machine.

## Sources

- [RISC-V ELF psABI](https://github.com/riscv-non-isa/riscv-elf-psabi-doc)
- [RISC-V Assembly Programmer's Manual](https://github.com/riscv-non-isa/riscv-asm-manual)
- [RISC-V Instruction Set Manual](https://github.com/riscv/riscv-isa-manual)
- [GNU as manual](https://sourceware.org/binutils/docs/as/)
- [x86 NASM idioms](../Assembly-NASM-x86/idioms.md), for the principles
  shared between assembly dialects
- [C idioms](../C/idioms.md), for the conventions shared with C
