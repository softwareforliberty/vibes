# x86 Assembly (GNU as) Idioms and Principles

How to write x86 and x86-64 assembly well with the GNU assembler.
[coding-style.md](coding-style.md) covers how code looks. This guide covers
how it's designed: calling conventions, register and stack discipline,
interfacing with C, and the idioms that keep assembly correct and
maintainable. Every example follows the style guide.

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

- Boot code, mode switches, and anything that runs before a C environment
  exists (no stack, no initialised data).
- Interrupt and exception entry points, system call entry and context
  switching, where the exact register and stack state matters.
- Instructions the compiler has no way to emit, and no intrinsic for.
- Hot paths where a profiler shows that compiled C is measurably slower, and
  intrinsics can't close the gap.

Keep the assembly part as thin as possible. Do the setup in assembly, call
into C, and leave everything else to C.

## Calling conventions

Use the convention of the platform you're targeting. The three you'll meet
most often:

| | System V AMD64 (Linux, BSD, macOS) | Microsoft x64 (Windows) | 32-bit cdecl (System V i386, Windows) |
| --- | --- | --- | --- |
| Integer and pointer arguments | `%rdi`, `%rsi`, `%rdx`, `%rcx`, `%r8`, `%r9`, then the stack | `%rcx`, `%rdx`, `%r8`, `%r9`, then the stack | All on the stack, pushed right to left |
| Floating-point arguments | `%xmm0`–`%xmm7` | `%xmm0`–`%xmm3`, sharing positions with the integer registers | On the stack |
| Return value | `%rax` (and `%rdx` for 128 bits), `%xmm0` for floating point | `%rax`, `%xmm0` for floating point | `%eax` (and `%edx` for 64 bits), `%st(0)` for floating point |
| Callee-saved | `%rbx`, `%rbp`, `%r12`–`%r15` | `%rbx`, `%rbp`, `%rdi`, `%rsi`, `%r12`–`%r15`, `%xmm6`–`%xmm15` | `%ebx`, `%esi`, `%edi`, `%ebp` |
| Stack alignment at `call` | 16 bytes | 16 bytes | 16 bytes on System V i386; 4 bytes on Windows |
| Stack cleanup | Caller | Caller | Caller |
| Caller-reserved space | None. Leaf routines may use a 128-byte red zone below `%rsp` | 32 bytes of shadow space above the return address | None |

Every register not listed as callee-saved may be changed by a call. That
includes the flags.

On all three conventions, the direction flag (`DF`) is clear on entry to a
routine and must be clear again when it returns or calls another routine.

### Supporting more than one ABI

When one source file must build for several conventions, give the argument
registers names once, chosen at build time, and write the routine in terms of
the names. The compiler driver predefines `_WIN64` when it targets 64-bit
Windows:

```c
#ifdef _WIN64
#define ARG1	%rcx
#define ARG2	%rdx
#else
#define ARG1	%rdi
#define ARG2	%rsi
#endif
```

Test every convention you ship. The callee-saved sets differ between ABIs, so
a routine that touches `%rdi`, `%rsi` or `%xmm6`–`%xmm15` must save them on
Windows.

## Registers

- **Save only the callee-saved registers you use**, and restore them in the
  reverse order you saved them.
- **Assume every caller-saved register and the flags are destroyed by any
  `call`**, including calls to your own routines. A routine's documented
  clobbers can change later, but the ABI can't.
- **Interrupt and exception handlers save every register they touch**,
  including the flags and any SIMD state. The interrupted code didn't make a
  call, so it expects nothing to change.
- Kernel and interrupt code must not use the red zone. An interrupt pushes
  onto the stack right where the red zone lives.

## The stack

### Alignment

- At every `call`, `%rsp` (or `%esp` on System V i386) must be a multiple of
  16. On entry to a routine it's therefore 8 bytes past a multiple of 16 in
  64-bit code, because `call` pushed the return address.
- Count every `push` and every `sub` from `%rsp` between entry and a `call`,
  and make them add up so the stack is aligned at the call. Misalignment often
  shows up only later, as a crash in a SIMD instruction deep inside a library.
- Keep stack adjustments in multiples of the stack slot size: 8 bytes in
  64-bit code, 4 in 32-bit code.

### Prologue and epilogue

A routine that calls others, or that needs stack space, sets up a frame with
`%rbp`. Frame pointers make stack traces from debuggers and profilers
reliable. A leaf routine that needs no stack may skip the frame.

**Describe every stack change with call-frame information.** `FUNC_START`
and `FUNC_END` open and close it (see
[Directives and sections](coding-style.md#directives-and-sections)). Inside
the routine, follow each instruction that moves the stack or saves a register
with the matching directive. Debuggers, profilers and C++ exception unwinding
all read this data to walk the stack.

System V AMD64:

```gas
/* int buf_flush(struct buf *b) */
FUNC_START(buf_flush)
	pushq	%rbp
	.cfi_def_cfa_offset	16
	.cfi_offset	%rbp, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register	%rbp
	pushq	%rbx			// rsp is now 8 past a multiple of 16
	.cfi_offset	%rbx, -24
	pushq	%r12			// ...and aligned again
	.cfi_offset	%r12, -32
	movq	%rdi, %rbx		// keep b across the call
	...
	call	buf_write_all
	...
	popq	%r12
	popq	%rbx
	popq	%rbp
	.cfi_def_cfa	%rsp, 8
	ret
FUNC_END(buf_flush)
```

Microsoft x64. The caller reserves 32 bytes of shadow space for the callee to
use, so `subq` reserves it before each call. Windows describes the prologue
with `.seh_*` unwind directives instead of CFI, and the unwinder expects the
prologue in a fixed order: push the callee-saved registers, then allocate the
stack, then set the frame pointer. `.seh_endprologue` marks where the
prologue ends:

```gas
/* int buf_flush(struct buf *b) */
FUNC_START(buf_flush)
	pushq	%rbp
	.seh_pushreg	%rbp
	pushq	%rbx			// rsp is now 8 past a multiple of 16
	.seh_pushreg	%rbx
	subq	$40, %rsp		// 32 bytes of shadow space + 8 to realign
	.seh_stackalloc	40
	leaq	32(%rsp), %rbp		// frame pointer above the shadow space
	.seh_setframe	%rbp, 32
	.seh_endprologue
	movq	%rcx, %rbx		// keep b across the call
	...
	call	buf_write_all
	...
	addq	$40, %rsp
	popq	%rbx
	popq	%rbp
	ret
FUNC_END(buf_flush)
```

On Windows, every routine that calls others or changes `%rsp` needs unwind
data. Without it, exceptions and debuggers can't walk the stack through the
routine.

32-bit cdecl reads its arguments from the stack, above the saved `%ebp` and
the return address:

```gas
/* int add3(int a, int b, int c) */
FUNC_START(add3)
	pushl	%ebp
	.cfi_def_cfa_offset	8
	.cfi_offset	%ebp, -8
	movl	%esp, %ebp
	.cfi_def_cfa_register	%ebp
	movl	8(%ebp), %eax		// a
	addl	12(%ebp), %eax		// b
	addl	16(%ebp), %eax		// c
	popl	%ebp
	.cfi_def_cfa	%esp, 4
	ret
FUNC_END(add3)
```

## Interfacing with C

- **Declare every routine C calls in a C header**, with a prototype that
  follows the [C coding style](../C/coding-style.md). The prototype carries the
  API documentation. The assembly header comment adds the register details.
- **Name the routine exactly as C would**, with the module prefix:
  `buf_flush`, matching `int buf_flush(struct buf *b);`.
- **Return errors the way C does**: `0` for success, or a negative errno code
  in `%eax`/`%rax`, as in the [C idioms](../C/idioms.md#error-handling). Never
  report results through the flags across the C boundary.
- Export routines with `FUNC_START`, which marks them `.globl` and gives them
  a type and size. Give exported data the same treatment, so debuggers,
  profilers and the dynamic linker treat it correctly:

  ```gas
  .data
  	.globl	buf_table
  	.type	buf_table, @object
  	.balign	8
  buf_table:	.quad	0, 0
  	.size	buf_table, . - buf_table
  ```

- Some targets prefix C symbols with an underscore (32-bit Windows, and
  macOS). Write symbols without it, and add it in one place: build symbol
  names in the shared header with the compiler's predefined
  `__USER_LABEL_PREFIX__`, and have `FUNC_START` use it. The source then
  stays the same for every target:

  ```c
  #define SYM_CAT_(a, b)	a##b
  #define SYM_CAT(a, b)	SYM_CAT_(a, b)
  #define C_SYM(name)	SYM_CAT(__USER_LABEL_PREFIX__, name)
  ```

- **Keep shared struct layouts in sync.** Every set of offset constants that
  mirrors a C struct names that struct in a comment (see
  [Constants and data](coding-style.md#constants-and-data)). Best of all,
  generate the constants at build time from a small C file that uses
  `offsetof()`, so they can't drift. Otherwise, a test compares each offset
  with `offsetof()` in C.
- Calling C from assembly follows the same convention as being called: align
  the stack, pass arguments in the right registers or slots, and assume every
  caller-saved register is destroyed.

## Data

- **Align data to its natural size**, or more where the instructions using it
  require it. SSE aligned loads need 16 bytes, and AVX aligned loads need 32.
  Use `.balign`:

  ```gas
  .bss
  	.balign	16
  scratch:	.skip	256
  ```

- Put read-only data in `.rodata`, never in `.text`. Mixing data into code
  wastes instruction cache and can confuse disassemblers and branch
  predictors.
- Prefer statically sized storage when the limit is known and small. It can't
  fail at run time.

## Position-independent code

- **Write 64-bit code position-independent.** Shared libraries require it,
  executables are usually built as position-independent (PIE), and macOS
  requires it.
- Address your own data RIP-relative: `leaq msg_hello(%rip), %rdi`. Never use
  an absolute address such as `movq $msg_hello, %rdi`.
- Call external functions through the procedure linkage table, and load the
  addresses of external data from the global offset table:

  ```gas
  	call	puts@PLT
  	movq	shared_counter@GOTPCREL(%rip), %rax	// address of the variable
  ```

- Avoid writing 32-bit position-independent code by hand. It has no
  RIP-relative addressing, so it needs a register holding the GOT address
  throughout. Where you must, follow the i386 psABI's GOT scheme exactly.

## Instruction idioms

- Zero a register with `xorl %eax, %eax`. It's shorter than `movl $0, %eax`,
  and CPUs recognise it as having no dependency on the old value.
- Writing a 32-bit register zeroes the upper half of its 64-bit register, so
  `movl $1, %eax` sets all of `%rax` with a shorter encoding than
  `movq $1, %rax`. Writing an 8-bit or 16-bit register leaves the rest
  unchanged.
- Test for zero with `testq %rax, %rax`, not `cmpq $0, %rax`. It's shorter
  and sets the same flags for the following jump.
- Prefer `dec` and `jnz` to `loop`, and `push`/`mov`/`sub` to `enter`. Both
  `loop` and `enter` are slower on most current CPUs.
- If you set the direction flag with `std`, clear it with `cld` before
  returning or calling another routine.
- After using 256-bit or 512-bit registers, run `vzeroupper` before returning
  to or calling code that may use SSE. This avoids a costly state transition.
- Never assume the flags survive a `call`, or any instruction documented as
  leaving them undefined.

## Self-modifying code

Don't write it:

- Modern systems map code read-only and data non-executable, so the code
  can't write to itself without weakening that protection.
- Changing code that the CPU may already have fetched forces pipeline flushes
  and requires careful serialisation.
- Code that changes at run time can't be reviewed, disassembled or debugged
  from its source.

Where code generation is the point (a JIT compiler), keep it in its own
module. Write the code into a fresh buffer, then make the buffer executable
and not writable before running it.

## Testing

- **Test every routine from C.** A C test harness calls the routine through
  its prototype, which also checks the calling convention.
- **Compare against a reference.** Write the same function in plain C and
  check that both give the same results, on random inputs and on edge cases:
  zero length, maximum values, unaligned buffers.
- **Check that callee-saved registers survive.** A small wrapper fills every
  callee-saved register with a known value, calls the routine, and checks the
  values afterwards.
- **Test every ABI and word size you ship.** A routine that works under
  System V can still break the Windows convention.

## Sources

- [GNU as manual](https://sourceware.org/binutils/docs/as/), including its
  CFI and SEH directives
- [System V AMD64 psABI](https://gitlab.com/x86-psABIs/x86-64-ABI)
- [System V i386 psABI](https://gitlab.com/x86-psABIs/i386-ABI)
- [Microsoft x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention)
- [Microsoft x64 prolog and epilog](https://learn.microsoft.com/en-us/cpp/build/prolog-and-epilog)
- [Agner Fog, *Calling conventions for different C++ compilers and operating systems*](https://www.agner.org/optimize/calling_conventions.pdf)
- [Agner Fog, *Instruction tables*](https://www.agner.org/optimize/instruction_tables.pdf)
- [C idioms](../C/idioms.md), for the conventions shared with C
