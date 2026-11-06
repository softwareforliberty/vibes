# OS Component Architecture

How to structure the parts of an operating system: kernels and their
subsystems, device drivers, bootloaders and firmware, system services and
system libraries. Read the [rules for all software](README.md) first: a core
of logic with thin edges, dependencies pointing inward, and one owner for
each piece of state. This guide builds on them.

These components have no single request to serve and often no user
interface. They run with privilege, share hardware and memory with
everything else, handle interrupts and many threads at once, and keep their
interfaces stable for years. Their natural shapes are subsystems that drivers
plug into through tables of operations, hardware hidden behind thin layers,
explicit ownership and execution contexts, and stable interfaces at every
privilege boundary.

Where the code builds on an existing kernel or system, its own model wins,
such as the Linux driver model or the BSD and Windows driver frameworks.

## Mechanism, not policy

A lower layer provides mechanisms: what can be done. Policy, which decides
what should be done, lives higher up, in configuration or in user space where
it can. A scheduler provides priorities, and something above it sets them; a
driver can power a device down, and a power manager decides when.

This keeps privileged code small, and lets policy change without changing
it.

## Kernels and firmware

```text
system calls ─▶ interface layer ─▶ subsystem ─▶ ops table ─▶ driver
                                       │                       │
                                       ▼                       ▼
                               core services             bus, hardware
                                       │                  abstraction
                                       ▼                       │
                               architecture layer ◀────────────┘
```

| Layer | Its job | Depends on | Never depends on |
| --- | --- | --- | --- |
| Interface | Copies in and checks user input, then calls a subsystem | Subsystems | Drivers |
| Subsystem | One area's generic logic, such as block storage, networking, input or a file system | Core services, its ops tables | Particular drivers or hardware |
| Driver | One device family's side of a subsystem | Its subsystem, the bus layer | Other drivers |
| Bus and hardware abstraction | Finding devices, registers, interrupts and DMA | The architecture layer | Subsystems |
| Core services | Memory, scheduling, timers and synchronisation | The architecture layer | Subsystems, drivers |
| Architecture | One CPU family: boot, traps, the MMU and context switches | The hardware | Anything above it |

### Subsystems and drivers

- **A subsystem defines the interface its drivers implement,** usually a
  structure of function pointers: an ops table. A driver fills one in and
  registers it, and the subsystem calls through it. This is dependency
  inversion in C.
- **Ops tables stay small.** An optional operation may be left empty, and
  the subsystem then uses a default or reports it's unsupported.
- **Drivers never call each other.** Shared code goes in the subsystem or a
  library that both use.
- **The bus binds drivers to devices** through each driver's table of the
  devices it supports. A driver's probe function sets the device up, and its
  remove function tears it down in reverse order.

### Architecture-specific code

Each CPU architecture has its own directory, implementing a small interface
that the generic code calls. Generic code includes only that interface,
never an architecture's own headers, and never tests which architecture
it's built for.

### Build-time options

When an optional feature is turned off, its header provides empty inline
stubs in place of its functions, so callers compile the same either way.
Conditional compilation lives in headers and build files, never in the
middle of a function.

## Execution contexts

- **Every function documents the contexts it may run in.** Code that may
  run in interrupt or other atomic context must not sleep, wait for a
  sleeping lock, or allocate memory in a way that can sleep.
- **Interrupt handlers do the minimum:** acknowledge the device, capture
  what's needed, and defer the rest to a thread or work queue.
- **Every shared structure says which lock protects which fields.** Locks
  are taken in one documented order, and critical sections stay short. Never
  hold a spinlock across anything that can sleep.
- **Prefer data owned by one CPU or thread,** and passing messages, to
  shared data under locks. Lock-free code needs a comment that justifies it
  and states the memory ordering it relies on.
- **Shared objects are reference counted.** Each holder takes a reference
  and drops it, and the last one frees the object. Read-mostly structures
  can use deferred freeing, such as read-copy-update.

## Ownership and resources

- **Every resource has one owner:** memory, mappings, interrupts, DMA
  buffers, locks and device state. Each is set up and torn down in a
  matching pair, with teardown in reverse order.
- **Error paths unwind exactly what was set up,** in reverse, through
  cleanup labels in C, or destructors in C++ and Rust.
- **Resources are bounded.** Nothing allocates without limit because of
  outside input. Paths that mustn't fail, such as interrupt handling and
  freeing memory under pressure, use memory set aside in advance. Every
  allocation's failure is handled.
- **Stacks are small and fixed.** No large arrays on the stack, and no
  recursion without a bound.

## Privilege boundaries

Every boundary where less-trusted code calls more-trusted code is an attack
surface: user space into the kernel, a guest into a hypervisor, or an
unprivileged client into a system service.

- **Copy input in once, check the copy, then use only the copy,** so the
  caller can't change it between the check and the use. Check every size,
  index and range, and never use a caller's pointer directly.
- **Clear what you copy out,** including padding, so no stale data leaks.
- **The public interface is stable:** system calls, ioctls and their
  structures, IPC messages, on-disk formats and library binary interfaces.
  Never change it incompatibly. Extend it with size or flags fields, and
  reject unknown flags so they can be given a meaning later.
- **Public headers live apart from internal ones,** in their own
  directory, so internal interfaces stay free to change.

## System services

A system service, or daemon, runs in the background and serves other
processes.

- **An event loop sits at the edge,** waiting on its sockets, timers and
  signals through the platform's mechanism, such as `epoll`, `kqueue` or the
  framework's run loop, and dispatching to handlers. The service's logic is
  plain code that knows nothing about the loop.
- **Separate privileges.** A small privileged part does the few operations
  that need privilege, and the rest runs unprivileged, talking to it over a
  narrow interface. Drop privileges as soon as startup is done, and use the
  platform's sandbox, such as seccomp, `pledge` and `unveil`, or Capsicum.
- **Fit the service manager.** Run in the foreground, log to standard error
  or the system log, and use readiness notification and socket activation
  where the platform supports them, rather than forking into the background.
- **Handle signals in one place.** A signal handler only records the
  signal, such as through `signalfd` or a self-pipe, and the event loop acts
  on it.
- **Reload configuration safely.** Read and validate the whole new
  configuration, then switch to it, and keep the old one if it fails.
- **Keep state safe across crashes.** Write state files to a temporary file,
  flush, then rename, and make startup safe to repeat.
- **Check every client.** Every message in the versioned IPC protocol is
  validated, and the caller's identity comes from the operating system, such
  as a Unix socket's peer credentials, never from the message.

## System libraries

- **Keep the binary interface stable.** Public types are opaque, declared in
  the header and defined privately, and created and destroyed through
  functions, so their layout can change. A breaking change gets a new major
  version and library name.
- **Export only the public interface.** Hide symbols by default, and export
  the public ones through an explicit list or a linker version script.
- **A library never exits, prints or installs signal handlers.** It reports
  errors to its caller, and takes callbacks for logging or allocation when
  the caller needs control of them.
- **No hidden global state.** State lives in a context object the caller
  creates and passes in, and each function documents whether it's
  thread-safe.

## Layout

A kernel or firmware project:

```text
include/<name>/        the public interface: stable and installed
src/core/              memory, scheduling and the other core services
src/arch/<arch>/       one directory per CPU architecture
src/<subsystem>/       one directory per subsystem
src/drivers/<class>/   drivers, grouped by subsystem
tests/
```

A system service or library:

```text
include/<name>/        the public interface, for a library
src/core/              the logic, with no I/O
src/platform/<os>/     one directory per operating system
src/main.c             the event loop, setup and privilege dropping
tests/
```

## Enforce it

- **The build keeps internals private:** internal headers aren't on the
  public include path, and symbols are hidden unless exported.
- **Typical rules for checks in `scripts/check`:** generic code doesn't
  include architecture headers or test which architecture it's on; drivers
  don't include other drivers' headers; `.c` files don't test build options
  inside functions.
- **Check locking at compile time** where the compiler supports it, such as
  Clang's thread safety analysis, and validate lock order at run time in
  debug builds.
- **Check the binary interface** of every library against its last release
  in `scripts/audit`, with a tool such as libabigail's `abidiff`.

## Testing

| Part | Test with |
| --- | --- |
| Core logic | Unit tests built for the host, with hardware and kernel services behind fakes |
| Drivers | An emulated device, such as in QEMU, or a fake bus |
| Privilege boundaries and parsers | Fuzzing, such as syzkaller, libFuzzer or AFL++ |
| Error paths | Fault injection, failing allocations and calls on purpose |
| The whole system | Booting and running it in an emulator |

Build tests with the sanitizers the platform supports, such as
AddressSanitizer and UndefinedBehaviorSanitizer, or their kernel versions.
