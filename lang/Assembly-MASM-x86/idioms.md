# x86 Assembly (MASM) Idioms and Principles

How to write x86 and x86-64 assembly well in the MASM language.
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
most often in MASM code:

| | Microsoft x64 (64-bit Windows) | 32-bit cdecl (C functions) | 32-bit stdcall (Windows API) |
| --- | --- | --- | --- |
| Integer and pointer arguments | `rcx`, `rdx`, `r8`, `r9`, then the stack | All on the stack, pushed right to left | All on the stack, pushed right to left |
| Floating-point arguments | `xmm0`–`xmm3`, sharing positions with the integer registers | On the stack | On the stack |
| Return value | `rax`, `xmm0` for floating point | `eax` (and `edx` for 64 bits), `st0` for floating point | `eax` (and `edx` for 64 bits), `st0` for floating point |
| Callee-saved | `rbx`, `rbp`, `rdi`, `rsi`, `r12`–`r15`, `xmm6`–`xmm15` | `ebx`, `esi`, `edi`, `ebp` | `ebx`, `esi`, `edi`, `ebp` |
| Stack alignment at `call` | 16 bytes | 4 bytes | 4 bytes |
| Stack cleanup | Caller | Caller | Callee (`ret n`) |
| Caller-reserved space | 32 bytes of shadow space above the return address | None | None |
| Name decoration | None | `_name` | `_name@n`, where `n` is the bytes of arguments |

Every register not listed as callee-saved may be changed by a call. That
includes the flags.

On all three conventions, the direction flag (`DF`) is clear on entry to a
routine and must be clear again when it returns or calls another routine.

If you assemble for Linux or BSD (UASM can produce ELF objects), follow the
System V AMD64 convention instead. It passes arguments in `rdi`, `rsi`, `rdx`,
`rcx`, `r8` and `r9`, and only `rbx`, `rbp` and `r12`–`r15` are callee-saved.

### Name decoration

In 32-bit code, let the assembler decorate names. `.MODEL FLAT, C` makes C
the default, and a procedure or prototype can name another convention
(`STDCALL`). The assembler then adds `_` or `_name@n` itself. Never write
decorated names by hand: they break when an argument list changes.

### Supporting both word sizes

Keep 32-bit and 64-bit code in separate files. The two differ in almost
everything a routine touches: argument passing, callee-saved registers, the
`.MODEL` directive, unwind data, and which directives the assembler supports.
A file that tries to serve both ends up mostly conditional assembly. Test
every build you ship.

## Registers

- **Save only the callee-saved registers you use**, and restore them in the
  reverse order you saved them.
- **Assume every caller-saved register and the flags are destroyed by any
  `call`**, including calls to your own routines. A routine's documented
  clobbers can change later, but the ABI can't.
- **Interrupt and exception handlers save every register they touch**,
  including the flags and any SIMD state. The interrupted code didn't make a
  call, so it expects nothing to change.
- In 32-bit code, list the callee-saved registers a procedure uses in its
  `USES` clause (`buf_copy PROC USES ebx esi, ...`). MASM then saves them in
  the prologue and restores them before every `ret`, so no exit path can
  forget one.

## The stack

### Alignment

- In 64-bit code, `rsp` must be a multiple of 16 at every `call`. On entry to
  a routine it's therefore 8 bytes past a multiple of 16, because `call`
  pushed the return address.
- Count every `push` and every `sub rsp` between entry and a `call`, and make
  them add up so the stack is aligned at the call. Misalignment often shows up
  only later, as a crash in a SIMD instruction deep inside a library.
- Keep stack adjustments in multiples of the stack slot size: 8 bytes in
  64-bit code, 4 in 32-bit code.

### Prologue and epilogue

A routine that calls others, or that needs stack space, sets up a frame with
`rbp` (`ebp` in 32-bit code). Frame pointers make stack traces from debuggers
and profilers reliable. A leaf routine that needs no stack may skip the
frame.

**In 64-bit code, every routine that calls others or changes `rsp` is a
`PROC FRAME`** and describes its prologue with unwind directives. Windows
uses this unwind data to walk the stack for exceptions and debuggers. The
unwinder expects the prologue in a fixed order: push the callee-saved
registers, then allocate the stack, then set the frame pointer.
`.ENDPROLOG` marks where the prologue ends. The caller reserves 32 bytes of
shadow space for the callee to use, so `sub rsp` reserves it before each
call:

```masm
; int buf_flush(struct buf *b)
buf_flush	PROC	FRAME
	push	rbp
	.PUSHREG	rbp
	push	rbx			; rsp is now 8 past a multiple of 16
	.PUSHREG	rbx
	sub	rsp, 40			; 32 bytes of shadow space + 8 to realign
	.ALLOCSTACK	40
	lea	rbp, [rsp + 32]		; frame pointer above the shadow space
	.SETFRAME	rbp, 32
	.ENDPROLOG
	mov	rbx, rcx		; keep b across the call
	...
	call	buf_write_all
	...
	add	rsp, 40
	pop	rbx
	pop	rbp
	ret
buf_flush	ENDP
```

The epilogue undoes the prologue in reverse with only `add rsp`, `pop` and
`ret`. The unwinder recognises an epilogue by those instructions, so don't
mix others into it.

**In 32-bit code, name a procedure's parameters on its `PROC` line** and
refer to them by name. MASM then generates the frame and the matching
epilogue, and for `STDCALL` procedures it emits the right `ret n`:

```masm
; int add3(int x, int y, int z)
add3	PROC	x:DWORD, y:DWORD, z:DWORD
	mov	eax, x
	add	eax, y
	add	eax, z
	ret
add3	ENDP
```

## Interfacing with C

- **Declare every routine C calls in a C header**, with a prototype that
  follows the [C coding style](../C/coding-style.md). The prototype carries the
  API documentation. The assembly header comment adds the register details.
- **Name the routine exactly as C would**, with the module prefix:
  `buf_flush`, matching `int buf_flush(struct buf *b);`.
- **Return errors the way C does**: `0` for success, or a negative errno code
  in `eax`/`rax`, as in the [C idioms](../C/idioms.md#error-handling). Never
  report results through the flags across the C boundary.
- Export procedures with `PUBLIC`, and import C symbols with `EXTERN`:

  ```masm
  PUBLIC	buf_flush
  EXTERN	buf_write_all:PROC
  ```

- **Write calls out explicitly in 64-bit code.** `ml64` has no `INVOKE`, and
  an explicit call shows the argument registers, shadow space and stack
  alignment that the ABI requires.
- **In 32-bit code, declare every routine you call with `PROTO`**, giving
  its convention and parameters, and call it with `INVOKE`. The assembler
  then checks the argument count and pushes the arguments in the right order:

  ```masm
  buf_write_all	PROTO	C :DWORD

  	INVOKE	buf_write_all, ebx
  ```

- **Keep shared struct layouts in sync.** Every `STRUCT` that mirrors a C
  struct names that struct in a comment (see
  [Constants and data](coding-style.md#constants-and-data)). A test compares
  each offset with `offsetof()` in C.
- Calling C from assembly follows the same convention as being called: align
  the stack, pass arguments in the right registers or slots, and assume every
  caller-saved register is destroyed.

## Data

- **Align data to its natural size**, or more where the instructions using it
  require it. SSE aligned loads need 16 bytes, and AVX aligned loads need 32.
  Use `ALIGN`:

  ```masm
  .DATA?
  	ALIGN	16
  scratch	BYTE	256 DUP (?)
  ```

- `ALIGN` can't exceed the alignment of the section it's in. When you need
  more than a simplified section gives, define the section yourself with
  `SEGMENT ALIGN(n)`.
- Put read-only data in `.CONST`, never in `.CODE`. Mixing data into code
  wastes instruction cache and can confuse disassemblers and branch
  predictors.
- Prefer statically sized storage when the limit is known and small. It can't
  fail at run time.

## Addressing

- In 64-bit code, MASM addresses labels relative to `rip`, so code is
  position-independent as written. Load addresses with `lea rcx, msg_hello`,
  not `mov rcx, OFFSET msg_hello`. The `lea` form is RIP-relative and
  shorter. The `mov` form embeds an absolute address that the loader must
  relocate.
- Windows links calls to DLL functions through import thunks, so a plain
  `call` to an imported function works.

## Instruction idioms

- Zero a register with `xor eax, eax`. It's shorter than `mov`, and CPUs
  recognise it as having no dependency on the old value.
- Writing a 32-bit register zeroes the upper half of its 64-bit register, so
  `mov eax, 1` sets all of `rax` with a shorter encoding than `mov rax, 1`.
  Writing an 8-bit or 16-bit register leaves the rest unchanged.
- Test for zero with `test rax, rax`, not `cmp rax, 0`. It's shorter and sets
  the same flags for the following jump.
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
- **Test every word size you ship.** A routine that works in 64-bit code says
  nothing about its 32-bit counterpart.
- **Assemble with a second assembler** in continuous integration. Building
  with both UASM and JWasm (or llvm-ml) catches code that depends on one
  assembler's behaviour.

## Sources

- [Microsoft Macro Assembler reference](https://learn.microsoft.com/en-us/cpp/assembler/masm/microsoft-macro-assembler-reference)
- [Microsoft x64 calling convention](https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention)
- [Microsoft x64 prolog and epilog](https://learn.microsoft.com/en-us/cpp/build/prolog-and-epilog)
- [Microsoft argument passing and naming conventions (32-bit)](https://learn.microsoft.com/en-us/cpp/cpp/argument-passing-and-naming-conventions)
- [Agner Fog, *Calling conventions for different C++ compilers and operating systems*](https://www.agner.org/optimize/calling_conventions.pdf)
- [Agner Fog, *Instruction tables*](https://www.agner.org/optimize/instruction_tables.pdf)
- [C idioms](../C/idioms.md), for the conventions shared with C
