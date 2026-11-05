# C Idioms and Principles

How to write C well. [coding-style.md](coding-style.md) covers how code looks.
This guide covers how it's designed: the idioms and principles that keep C
code correct, safe and maintainable. Every example follows the style guide.

## Principles

- **Clarity beats cleverness.** Code is read far more often than it's
  written. Prefer the obvious version unless profiling proves it too slow.
- **Every resource has exactly one owner.** Memory, file descriptors, locks:
  someone is responsible for releasing each one, and the code makes clear who.
- **Fail early and loudly.** Check every result where it happens, and report
  errors to a caller who can act on them.
- **Make wrong code look wrong.** Consistent naming, pairing and ownership
  conventions turn a missed cleanup or an unchecked error into something a
  reviewer can spot.
- **Keep scope small.** Give variables, functions and state the narrowest
  visibility that works.
- **Never invoke undefined behaviour.** "It works on my compiler" isn't
  correctness. An optimising compiler is free to assume undefined behaviour
  never happens.

## Modules and encapsulation

- A module is a header (`buf.h`) plus a source file (`buf.c`). Every name the
  module exports starts with its prefix: `buf_alloc()`, `buf_free()`,
  `BUF_MAX_SIZE`.
- The header is the module's contract. Put only the public API there.
  Everything else in the `.c` file is `static`.
- Hide a struct's layout unless callers truly need to reach into its fields.
  Use an [opaque struct](coding-style.md#typedefs) and give callers access
  through functions.
- **Avoid global mutable state.** Pass a context struct to the functions that
  need it. A module that must keep state keeps it `static` inside its `.c`
  file and exposes it only through its API.
- Group a module's settings into one struct instead of threading many
  parameters through every call.

## Ownership and lifetimes

### Paired functions

Every function that acquires a resource has a matching function that releases
it, and the pair's names show it:

| Acquire | Release | Meaning |
| --- | --- | --- |
| `foo_create()` | `foo_destroy()` | Allocates and frees the object itself |
| `foo_init()` | `foo_cleanup()` | Sets up and tears down an object in memory the caller owns |
| `foo_get()` | `foo_put()` | Takes and drops a reference to a shared object |
| `foo_lock()` | `foo_unlock()` | Acquires and releases a lock |

- Release functions accept `NULL` and do nothing, just like `free()`. Cleanup
  paths can then call them without checking first.
- Release resources in the reverse order you acquired them. Use
  [centralised cleanup with goto](coding-style.md#centralised-cleanup-with-goto).

### Transfers and borrowing

- **Document ownership in the API comment.** Say whether the caller owns the
  returned object ("must be released with `buf_free()`") and whether a
  function takes over a pointer it's given.
- A `const` pointer parameter is a **borrow**. The function reads the object
  during the call and doesn't keep the pointer afterwards.
- A function that keeps a pointer beyond the call says so, and the caller
  must keep the object alive that long, or hand over a reference.
- Never return a pointer to a local (stack) variable.

### Reference counting

Use reference counting when several owners share an object and none of them
clearly outlives the others:

- `foo_get()` increments the count and returns the object. `foo_put()`
  decrements it, and frees the object when it reaches zero.
- Whoever stores a pointer takes a reference, and drops it when the pointer
  is discarded.
- Make the count atomic, or protect it with a lock, if more than one thread
  can touch it.

### Dangling pointers

- After freeing memory that something longer-lived still points to (a struct
  field or a global), set that pointer to `NULL`.
- Don't keep pointers into a buffer that can move. After `realloc()`, any
  pointer into the old block is invalid.

## Error handling

- **Check every return value that can report an error.** Mark functions whose
  result must not be ignored with `__attribute__((warn_unused_result))`.
- **Propagate errors unchanged.** Pass a callee's error code up to your
  caller, instead of replacing it with a generic failure.
- **Handle each error at the level that can do something about it**: retry,
  fall back, or report to the user. Lower levels return the error.
- **Report each error once.** A function either logs an error or returns it,
  not both, so one failure doesn't produce a cascade of messages.
- When a result can't share the return value with an error code (for
  example, a full-range `uint64_t`), return the error and write the result
  through a pointer parameter that comes last:

  ```c
  int counter_read(const struct counter *c, uint64_t *value);
  ```

- Leave outputs untouched on failure, unless the API comment says otherwise.
  Callers shouldn't have to guess what state a failed call left behind.

### Errors versus bugs

- An **error** is something that can happen in a correct program: a missing
  file, a full disk, bad input. Handle it with an error return.
- A **bug** is a broken assumption inside the program, such as a NULL
  argument where the contract forbids one. Catch it with `assert()`.
- Never use `assert()` to validate input from outside the program. Asserts
  vanish when `NDEBUG` is defined.
- An asserted expression must have no side effects, for the same reason.
  `assert(list_pop(l))` stops popping in release builds.

## Memory

- **Check every allocation.** `malloc()`, `calloc()` and `realloc()` can all
  return `NULL`.
- **Check for size overflow before allocating.** `calloc()` does this for
  you. When you multiply sizes yourself, check first:

  ```c
  	if (n > SIZE_MAX / sizeof(*v->items))
  		return -EOVERFLOW;
  ```

- **Never assign `realloc()` straight back to its argument.** If it fails, the
  original block leaks. Use a temporary:

  ```c
  	void *tmp = realloc(v->items, new_cap * sizeof(*v->items));
  	if (!tmp)
  		return -ENOMEM;

  	v->items = tmp;
  	v->cap = new_cap;
  ```

- **Zero-initialise structs** with `= { 0 }` or a designated initialiser, so
  no field starts out holding garbage.
- Prefer fixed-size, statically sized storage when the limit is known and
  small. It can't fail at run time and can't leak.
- Free memory in the module that allocated it. If a module hands out objects,
  it also provides the function that frees them.

## Buffers and strings

- **Pass a pointer and its size together.** Any function that writes into a
  buffer takes the buffer's size, and the size parameter comes right after
  the pointer:

  ```c
  int path_join(char *dst, size_t dst_size, const char *dir, const char *name);
  ```

- **Never use `gets()`, `sprintf()`, `strcat()` or `strcpy()` on data you
  don't control.** Use `snprintf()`, and check its return value for
  truncation:

  ```c
  	int n = snprintf(dst, dst_size, "%s/%s", dir, name);
  	if (n < 0 || (size_t)n >= dst_size)
  		return -ENAMETOOLONG;
  ```

- Don't use `strncpy()` as a "safe `strcpy()`". It doesn't null-terminate on
  truncation, and it pads the rest of the buffer with zeros.
- Never pass data you don't control as a format string. Write
  `printf("%s", msg)`, never `printf(msg)`.
- Treat raw bytes as `unsigned char` or `uint8_t`. Whether plain `char` is
  signed varies between platforms.
- Pass a value through `(unsigned char)` before handing it to the `<ctype.h>`
  functions (`isalpha()`, `toupper()`, …). A negative `char` is undefined
  behaviour there.

## Integers

- Use `size_t` for sizes, counts and indexes into memory. Mixing it with a
  signed `int` invites sign-conversion bugs, which `-Wextra` warns about.
- **Check for overflow before the arithmetic, not after.** Signed overflow is
  undefined behaviour, so a check that runs afterwards may be optimised away:

  ```c
  	if (b > 0 && a > INT_MAX - b)
  		return -EOVERFLOW;

  	int sum = a + b;
  ```

- Do bit manipulation on unsigned types. Shifting a negative value, or
  shifting into the sign bit, is undefined or implementation-defined.
- Never shift by a negative amount, or by the type's width or more.
- Don't assume the size of `int` or `long`. When the size matters, use a
  `<stdint.h>` type.

## Undefined behaviour

Code must never rely on undefined behaviour. The most common traps:

| Trap | Instead |
| --- | --- |
| Signed integer overflow | Check the bounds first, or use unsigned arithmetic |
| Reading an array out of bounds, including one past the end | Check the index against the length |
| Dereferencing `NULL` or a freed pointer | Check pointers, and set dangling pointers to `NULL` |
| Reading an uninitialised variable | Initialise every variable where it's declared |
| Modifying a variable twice without a sequence point (`i = i++`) | One side effect per expression |
| Reading an object through a pointer of a different type (type punning) | Copy the bytes with `memcpy()` |
| Accessing misaligned data through a cast pointer | Copy the bytes with `memcpy()` |

## Data and control flow

- **Prefer data to code.** A table of structs with designated initialisers is
  easier to read and extend than a long `if`/`else` or `switch` chain:

  ```c
  static const struct cmd cmds[] = {
  	{ .name = "get", .fn = cmd_get },
  	{ .name = "set", .fn = cmd_set },
  };
  ```

- **Use operations tables for polymorphism.** A `static const` struct of
  function pointers gives several implementations one interface, and callers
  dispatch through it:

  ```c
  struct storage_ops {
  	int (*read)(void *ctx, void *buf, size_t len);
  	int (*write)(void *ctx, const void *buf, size_t len);
  };
  ```

- **Callbacks take a `void *ctx` argument**, so callers can pass their own
  state without globals.
- **Embed list and tree nodes in your structs** (intrusive containers), and
  get back to the enclosing struct with `container_of`. This avoids a separate
  allocation for each node:

  ```c
  #define container_of(ptr, type, member) \
  	((type *)((char *)(ptr) - offsetof(type, member)))
  ```

- **Switch on enums without a `default` case** when you mean to handle every
  value. `-Wall` then warns when a new enum value is added and isn't handled.
- **Avoid `bool` parameters.** `buf_open(path, true)` doesn't say what `true`
  means at the call site. Use a flags argument with named bits, or two
  functions.
- **Return early** to handle errors and edge cases. The main path then stays
  at the shallowest indentation.

## Concurrency

- **Document what protects shared data.** Note the lock that guards each
  shared field beside it: `int count;  // protected by lock`.
- **Always take locks in the same order.** Taking them in different orders in
  different places causes deadlocks. Document the order wherever more than
  one lock is involved.
- **Keep critical sections short.** Never block (I/O, sleeping, waiting on
  another lock) while holding a lock, unless the design requires it.
- **`volatile` is not a synchronisation tool.** It makes no promises about
  atomicity or ordering between threads. Use locks or atomic operations.
- Prefer handing data between threads over sharing it. An object owned by one
  thread at a time needs no locking.

## Portability

- Convert byte order at the boundary: the moment data is read from, or
  written to, a file or the network. Inside the program, use native order.
- **Don't write structs directly to files or sockets.** Padding, alignment and
  byte order differ between platforms. Serialise each field explicitly.
- Write to the C standard, and keep platform-specific code in its own module
  behind a common interface.

## Performance

- **Measure before you optimise**, and optimise the part the profiler points
  at.
- Choose the right algorithm and data layout first. Contiguous arrays usually
  beat linked structures, because they keep the cache warm.
- Leave inlining and micro-optimisation to the compiler (see
  [inline functions](coding-style.md#inline-functions)).

## Sources

- [Linux kernel coding style](https://www.kernel.org/doc/html/latest/process/coding-style.html)
  (data structures and reference counting, function return values)
- [Git CodingGuidelines](https://github.com/git/git/blob/master/Documentation/CodingGuidelines)
- [The use of assert() in SQLite](https://www.sqlite.org/assert.html)
- [SEI CERT C Coding Standard](https://wiki.sei.cmu.edu/confluence/display/c)
