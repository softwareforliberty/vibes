# C Coding Style

A general-purpose coding style for C projects. It builds on the
[Linux kernel coding style](https://www.kernel.org/doc/html/latest/process/coding-style.html),
and fills the gaps from other long-lived FOSS C projects and the C and POSIX
standards (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(ownership, error handling, memory safety and other idioms), see
[idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [GCC](https://gcc.gnu.org/) | GPLv3 | Compiling C, and linting through its warning flags |

### Compiler warnings

Compiler warnings are the lint gate. Code must build with **no warnings**
using at least these flags:

```sh
gcc -std=c99 -Wall -Wextra -Wvla
```

- The baseline language is **C99**. Compiler extensions are limited to
  `__attribute__` and `__asm__` (see
  [Inline assembly and attributes](#inline-assembly-and-attributes)).
- `-Wextra` turns on `-Wimplicit-fallthrough`, which enforces the
  [`fallthrough` rule](#switch).
- `-Wvla` enforces the [no variable-length arrays](#language-usage) rule.

## Layout

### Indentation

- Indent with **tabs, 8 columns wide**. Never indent with spaces.
- Don't nest more than **3 levels** deep inside a function. Deeper code should
  be split into helper functions.
- Continuation lines line up with the open parenthesis. Use tabs first, then
  spaces to finish the alignment:

  ```c
  	ret = buf_copy_range(dst, src, offset,
  			     len);
  ```

- When you break an expression, leave the operator at the end of the line,
  not at the start of the next one.

### Line length

- **80 columns** is the preferred limit. You may go up to **100** only when
  that clearly reads better and hides nothing.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Whitespace

- No trailing whitespace.
- Don't use more than one blank line in a row.
- Use LF line endings, and end every file with a newline.

### One thing per line

- One statement per line. The body of an `if`, `for` or `while` always goes on
  the next line, even when it's short:

  ```c
  	if (!p)
  		return -ENOMEM;
  ```

- One assignment per line. Don't chain assignments like `a = b = 0;`.
- Don't use commas to avoid using braces.

## Braces

- Functions put the opening brace **at the start of the next line**:

  ```c
  int pipe_new(void)
  {
  	...
  }
  ```

- Every other block (`if`, `switch`, `for`, `while`, `do`) puts the opening
  brace **last on the line**. The closing brace goes on its own line, unless an
  `else` or a do-loop's `while` follows it:

  ```c
  	if (x == y) {
  		...
  	} else if (x > y) {
  		...
  	} else {
  		...
  	}

  	do {
  		...
  	} while (cond);
  ```

- Leave out braces when the body is a single statement.
- If **any** branch of an `if`/`else` chain needs braces, **every** branch gets
  them.
- A loop whose body is more than one simple statement gets braces. That
  includes a loop whose only statement is a multi-line `if`.

## Spacing

- Put a space after these keywords: `if`, `switch`, `case`, `for`, `do`,
  `while`.
- Don't put a space after `sizeof`, `__attribute__` or `__asm__`. Always use
  parentheses with `sizeof`: `sizeof(*p)`.
- No spaces just inside parentheses: `if (x)`, not `if ( x )`.
- Put one space on each side of binary and ternary operators.
- No space after a unary operator (`&`, `*`, `!`, `~`, `-`, prefix `++`/`--`).
  No space before postfix `++`/`--`. No space around `.` or `->`.
- No space after a cast: `(uint32_t)n`.
- The `*` sticks to the name, not the type: `char *s`, `const char *name`,
  `(char *)p`.

## Naming

- Use lowercase with underscores (`snake_case`). Don't use CamelCase or
  Hungarian notation.
- **Global** names (non-static functions and variables) are descriptive and
  start with their module's prefix: `buf_alloc()`, `pipe_close()`,
  `mutex_trylock()`.
- **Local** names are short where the meaning is obvious: `i`, `n`, `tmp`, `p`.
- Constants, macros that define constants, and enum labels are
  `UPPER_SNAKE_CASE`: `BUF_MAX_SIZE`, `CMD_WRITE`.
- Function-like macros are `UPPER_SNAKE_CASE` too (`ARRAY_SIZE`). The only
  exception is a macro that behaves exactly like a function, evaluating each
  argument once with no hidden effects. It may be lowercase, like
  `container_of`.
- Label `goto` targets with what the jump does or why it exists:
  `out_free_buffer:`, `err_unlock:`. Don't use labels like `err1:` and `err2:`.
- Use inclusive terms. Say primary/secondary, controller/device or
  leader/follower instead of master/slave, and allowlist/denylist instead of
  whitelist/blacklist. The only exceptions are names fixed by an existing ABI,
  protocol or hardware spec.

### Reserved identifiers

- Never declare names that start with `__`, or with `_` followed by a capital
  letter. Never declare file-scope names that start with `_`. The C standard
  reserves these for the compiler and the C library.
- Never declare type names ending in `_t`. POSIX reserves the suffix, and the
  [typedef rule](#typedefs) means you don't need it.
- These rules cover names you *declare*. Using the compiler's own keywords,
  such as `__attribute__` and `__asm__`, is fine.
- **Exception:** code that implements the C library itself may use reserved
  names. It's the implementation they are reserved for.

## Typedefs

- **Don't typedef structs or pointers.** Write `struct mutex *m`, not
  `mutex_t *m`. The `struct` keyword tells the reader what they're dealing
  with.
- For an **opaque type**, declare the struct in the header and define it only
  in the `.c` file:

  ```c
  /* pipe.h */
  struct pipe;

  struct pipe *pipe_get(int id);
  ```

- For sized integers, use the `<stdint.h>` types (`uint32_t`, …). Don't create
  your own integer aliases.

## Declarations

- Declare each variable **where it's first needed**, in the narrowest scope
  that works, and initialise it in the declaration where you can. Declare loop
  counters in the `for`: `for (int i = 0; i < n; i++)`. Small scopes and
  initialised variables avoid uninitialised-variable bugs.
- One declaration per line. Don't use commas to declare several variables:

  ```c
  	uint32_t head;		// index of the next read
  	uint32_t tail;		// index of the next write
  ```

- Don't initialise `static` or global variables to `0`, `NULL` or `false`.
  C already zeroes them.
- Use **designated initialisers** to initialise structs:
  `struct foo f = { .len = 0, .buf = NULL };`.
- Tabs may line up the values in a block of `#define`s, or the names in a
  struct.

## Functions

- Keep functions short and focused on one thing. A function should fit in one
  or two 80×24 screens. The more complex it is, the shorter it should be.
- Use at most **5–10 local variables**.
- Separate functions with one blank line.
- In prototypes, keep the return type on the same line as the name, and always
  name the parameters.
- Don't put `extern` on function declarations.
- Make every function and file-scope variable that isn't part of the
  module's API `static`.
- Add `const` to pointer parameters the function doesn't write through.

### Return values

- A function named as an **action** (`pipe_attach`, `file_write`) returns an
  `int`: `0` for success, or a **negative errno code** (`-ENOMEM`, `-EINVAL`)
  for failure.
- A function named as a **predicate** (`list_is_empty`, `file_is_open`)
  returns `bool`.
- A function that **computes a value** returns it directly. If it returns a
  pointer, `NULL` means failure. A count or size returns either the value or a
  negative errno code.
- `return` is not a function, so don't put parentheses around its value.

### Centralised cleanup with goto

When a function acquires several resources, use `goto` to jump to a shared
cleanup tail. Release resources in reverse order. Give each cleanup step its
own label so that no path frees something it didn't take. Labels start in
column 0:

```c
int pipe_open(void)
{
	struct pipe *p = malloc(sizeof(*p));
	if (!p)
		return -ENOMEM;

	int ret = pipe_register(p);
	if (ret)
		goto err_free_pipe;

	return 0;

err_free_pipe:
	free(p);
	return ret;
}
```

### Inline functions

- Don't mark a function `inline` if it has more than about 3 lines, unless one
  argument is a compile-time constant that lets the body fold away.
- Don't mark a `static` function that's called only once as `inline`. The
  compiler inlines it on its own.
- A `static inline` function in a header is better than a function-like
  macro.

## Statements and expressions

- Write `if (!p)` and `if (p)`. Don't use `==` or `!=` to compare pointers to
  `NULL`, or integers to `0` or `'\0'`. Ordering tests such as
  `if (ret < 0)` are fine.
- Never compare a `bool` to `true` or `false`.
- Don't put assignments inside an `if` condition:

  ```c
  	struct pipe *p = malloc(sizeof(*p));
  	if (!p)
  		return -ENOMEM;
  ```

- Use `NULL` for null pointers, never `0`.

### Switch

Line up the `case` labels with the `switch`, without indenting them. Mark every
intentional fall-through with `fallthrough;`, which is defined once in a shared
header (`#define fallthrough __attribute__((__fallthrough__))`). The compiler
warns about any fall-through that isn't marked.

```c
	switch (cmd) {
	case CMD_WRITE_ERR:
		redirect_to_stderr(f);
		fallthrough;
	case CMD_WRITE:
		ret = do_write(f);
		break;
	default:
		ret = -EINVAL;
		break;
	}
```

## Language usage

- Use `bool`, `true` and `false` from `<stdbool.h>`. Don't use `1` and `0` for
  truth values, and don't use `!!` to convert to `bool`. Use `bool` in a struct
  only where the struct's size and layout don't matter. Otherwise use a
  1-bit bitfield, or a `flags` word.
- Use fixed-width `<stdint.h>` types for anything with a defined size
  (file and wire formats, hardware registers). Use `size_t` for object sizes,
  and plain `int` for everything else.
- Write unsigned and long literal suffixes in uppercase: `0xFFFFFFFFU`,
  `1UL << n`. A lowercase `l` looks too much like `1`.
- Don't use **variable-length arrays**. Their size isn't known until run time,
  and an array that's too big for the stack overflows without any error.
- Make conversions explicit with a cast whenever you narrow a value, or
  convert between integers and pointers.
- Don't use magic numbers. Name each constant, and add a comment explaining
  the size you chose for each limit.

### Memory allocation

- Get the size from the pointer, not the type name: `p = malloc(sizeof(*p));`
  for one object, or `p = calloc(n, sizeof(*p));` for an array. `calloc`
  checks that `n * size` doesn't overflow.
- Don't cast the `void *` that an allocator returns.

## Macros and constants

- For a set of related constants, prefer an `enum` to a list of `#define`s.
- Wrap a macro with several statements in `do { ... } while (0)`.
- Put parentheses around every macro argument, and around the whole value of
  any macro that's an expression: `#define BITMAP_WORDS (MAX_ITEMS / 32)`.
- Macros must not change control flow (no hidden `return` or `goto`), must not
  depend on a local variable with a magic name, and must not use an argument
  as an l-value.
- Name the locals declared inside a macro after the macro, with a trailing
  underscore, so they can't clash with the caller's names (`ret_`).
- Turn a macro with unused parameters into a `static inline` function.
- Don't redefine common helpers in each file. Define them once in a shared
  header, for example
  `#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))`.

## Headers and includes

- Every header has an include guard. Don't use `#pragma once`. Build the guard
  from the header's path relative to its include directory, uppercased, with
  `/` and `.` turned into `_`. For example, `"buf.h"` becomes `BUF_H`, and
  `"net/socket.h"` becomes `NET_SOCKET_H`.
- Each `.c` file directly includes the headers that declare everything it
  uses. Don't rely on other headers pulling them in. Each header includes
  what it needs, so it compiles on its own.
- Order the includes in two groups with a blank line between them. First the
  `<...>` system headers, then the `"..."` project headers. Sort each group
  alphabetically, except that `<sys/types.h>` comes first among the system
  headers when you need it.

  ```c
  #include <stddef.h>
  #include <stdint.h>

  #include "buf.h"
  #include "pipe.h"
  #include "sync.h"
  ```

- Keep `#if` and `#ifdef` out of `.c` files where you can. Put the condition
  in a header that provides no-op stubs. Prefer `if (CONSTANT)` in ordinary C
  to `#ifdef`, so both branches are still compiled.
- After an `#endif` that closes more than a few lines, add a comment naming
  the condition: `#endif // CONFIG_NET`.

## Comments

- A comment that sits on its own line or lines uses `/* ... */`. A short note
  at the end of a line of code uses `//`.
- Write multi-line comments with a column of asterisks, and put the
  delimiters on their own lines:

  ```c
  /*
   * The table is sized for the worst case, so the hot path never has
   * to allocate or check for growth.
   */
  ```

- Comments explain **what** the code does and **why**, not **how**. Put them
  at the top of the function, not inside the body. Inside the body, only add
  short notes that flag something subtle.
- Short trailing comments are fine on declarations, struct members and
  `#define`s: `int refs;  // owner + attached readers; freed at 0`.
- Every header starts with a block comment describing the module.

### API documentation

Document every non-static function with a
[kernel-doc](https://www.kernel.org/doc/html/latest/doc-guide/kernel-doc.html)
style comment directly above its **prototype in the header**. The header is
where someone using the API reads its contract. Don't repeat the comment on the
definition.

Document public structs above their definition in the header. Static functions
may be documented the same way, above their definition in the `.c` file. Don't
write boilerplate that only repeats the signature.

```c
/**
 * buf_alloc() - Allocate a zeroed buffer.
 * @len: Size of the buffer in bytes.
 *
 * The buffer is owned by the caller and must be released with buf_free().
 *
 * Context: Safe to call from any thread.
 * Return: The new buffer, or NULL when memory is exhausted.
 */
struct buf *buf_alloc(size_t len);
```

## Inline assembly and attributes

- Don't use inline assembly where C can do the job. Wrap repeated assembly in
  small helper functions, and move large routines into separate assembly
  files.
- Write `__asm__`, not `asm`. `asm` only exists in GNU language modes, but
  `__asm__` also compiles under `-std=c99` and `-pedantic`, so headers stay
  usable by any code that includes them.
- Only add `volatile` when the assembly has side effects the compiler can't
  see. Put each instruction in its own quoted string, and end every string
  except the last with `\n\t`:

  ```c
  	__asm__ volatile("cli\n\t"
  			 "hlt"
  			 : : : "memory");
  ```

- Write attributes out in full, as `__attribute__((noreturn))` or
  `__attribute__((aligned(16)))`. Don't wrap them in macros with reserved
  names like `__packed`. The one wrapper this guide allows is `fallthrough`
  (see [Switch](#switch)), whose name isn't reserved.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

This guide starts from the Linux kernel coding style and borrows from:

- [Linux kernel coding style](https://www.kernel.org/doc/html/latest/process/coding-style.html)
- [Linux checkpatch](https://www.kernel.org/doc/html/latest/dev-tools/checkpatch.html)
- [Linux kernel-doc guide](https://www.kernel.org/doc/html/latest/doc-guide/kernel-doc.html)
- [Git CodingGuidelines](https://github.com/git/git/blob/master/Documentation/CodingGuidelines)
- [FreeBSD style(9)](https://man.freebsd.org/cgi/man.cgi?query=style&sektion=9)
- ISO C, §7.1.3 (reserved identifiers), and POSIX.1, System Interfaces §2.2.2
  (the reserved `_t` suffix)
