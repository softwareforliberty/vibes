# Go Coding Style

A general-purpose coding style for Go projects. It builds on
[Effective Go](https://go.dev/doc/effective_go),
[Go Code Review Comments](https://go.dev/wiki/CodeReviewComments) and the
[Google Go Style Guide](https://google.github.io/styleguide/go/) (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (errors,
context, interfaces, concurrency and other idioms), see [idioms.md](idioms.md).

The tools that check Go code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Go 1.22**. That version gives each loop iteration
its own copy of the loop variable, and adds `range` over integers, both of
which this guide relies on. Set it with the `go` directive in `go.mod`.

## Layout

### Formatting

- **`gofmt` owns layout.** It indents with tabs, aligns comments and fields,
  and settles every spacing question. Don't hand-format code it will
  rewrite, and don't argue with its output in review.
- `goimports` runs on top of `gofmt` and also maintains the import block.

### Line length

- Go has no fixed line limit, and `gofmt` never wraps lines. Keep lines
  readable, at roughly **100 columns**, by naming things well and extracting
  values, not by splitting at arbitrary points.
- Don't split a function signature or call just because it's long. If it's
  too long to read, it probably takes too many parameters (see
  [idioms](idioms.md#functions-and-apis)).
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8, LF line endings, and end every file with a newline. `gofmt`
  removes trailing whitespace.
- File names are lowercase, with underscores between words:
  `http_server.go`. Tests live beside the code in `_test.go` files.
- Order a file's contents: package comment, `package` clause, imports, then
  constants, variables, types and functions. Keep a type's methods together,
  right after the type.

### Blank lines

- Use single blank lines inside functions, sparingly, to separate logical
  steps.
- Don't start or end a block with a blank line.

## Packages and imports

- Package names are **short, lowercase, single words**: `json`, `httputil`.
  No underscores or mixed caps. The name is part of every call site, so it
  should read well there.
- Don't name packages `util`, `common`, `helpers` or `misc`. They say
  nothing about what's inside and grow without limit.
- Imports come in two groups separated by a blank line: the standard
  library first, then everything else. `goimports` sorts each group.

  ```go
  import (
  	"context"
  	"fmt"

  	"example.com/shop/internal/order"
  )
  ```

- Rename an import only to resolve a name clash.
- Don't use dot imports (`import . "pkg"`). They hide where names come
  from.
- Blank imports (`import _ "pkg"`) are only for their side effects, and
  belong in `main` packages or tests, where the side effect is chosen
  deliberately.

## Naming

- Use **MixedCaps**: `parseHeader`, `MaxRetries`. Never underscores in Go
  names, and never ALL_CAPS for constants.
- A name starting with a capital letter is exported. Export only what other
  packages need.
- **Initialisms keep one case throughout**: `userID`, `ServeHTTP`, `urlPath`,
  `XMLParser`. Mixed forms like `UserId` or `Url` are wrong.
- **Don't repeat the package name.** Callers write `order.New`, not
  `order.NewOrder`, and `bytes.Buffer`, not `bytes.ByteBuffer`.
- **Getters have no `Get` prefix.** A field `owner` has the getter `Owner()`
  and the setter `SetOwner()`.
- One-method interfaces are named for the method plus `-er`: `Reader`,
  `Closer`, `Stringer`.
- **Receivers** are one or two letters that abbreviate the type, and the same
  in every method: `func (s *Server)`. Never `this` or `self`.
- **Local names are short when their scope is short.** `i`, `n`, `b` and
  `err` are right for a few lines. Longer-lived names get longer.
- Error variables start with `Err` (`ErrNotFound`), and error types end with
  `Error` (`NotFoundError`).

## Declarations

- Use `:=` inside functions when you have a value to assign. Use `var x T`
  when you want the zero value, so the intent is visible:

  ```go
  var buf bytes.Buffer
  count := len(items)
  ```

- Group related constants in one block, and use `iota` for enumerations:

  ```go
  type State int

  const (
  	StateIdle State = iota
  	StateRunning
  	StateStopped
  )
  ```

- Name struct fields in composite literals for types from other packages:
  `http.Server{Addr: ":8080"}`. Positional literals break when the type
  gains a field.
- Use named results only when they document something, such as two values of
  the same type. Don't use bare `return` except in very short functions.

## Control flow

- **Handle errors and edge cases first, and return early.** The main path
  then stays at the left margin:

  ```go
  	f, err := os.Open(path)
  	if err != nil {
  		return fmt.Errorf("open config: %w", err)
  	}
  	defer f.Close()
  ```

- Don't use `else` after a block that ends in `return`, `break` or
  `continue`.
- Scope a value to its check when it's only needed there:
  `if err := save(o); err != nil {`.
- A `switch` doesn't fall through, so don't add `break`. Use `fallthrough`
  only with a comment explaining why.

## Errors

- Error strings are **lowercase and have no trailing punctuation**. They're
  usually wrapped into a longer message: `"open config: permission denied"`.
- When you add context, say what was being done, not that it failed:
  `fmt.Errorf("load user %d: %w", id, err)`, not `"failed to load user"`.

## Comments

- Every exported name has a **doc comment**: a full sentence that starts with
  the name.

  ```go
  // Retry calls fn until it succeeds or ctx is cancelled, waiting longer
  // after each failure.
  func Retry(ctx context.Context, fn func() error) error {
  ```

- Every package has one package comment, in the file named after the
  package or in `doc.go`: `// Package order manages customer orders.`
- Comments explain **why**, not what. The code already says what.
- Mark deprecated API with a paragraph starting `Deprecated:` in its doc
  comment, naming the replacement.
- Use `//` comments. Save `/* */` for temporarily disabling large blocks
  while debugging, and don't commit them.

## Generics

- Use type parameters when they remove real duplication, such as a container
  or an algorithm that works on many types. Don't reach for them before you
  have two concrete uses.
- Name type parameters with a single capital letter (`T`, `K`, `V`), or a
  short word when that reads better (`Key`).
- Prefer an ordinary interface parameter when the function only calls methods
  on the value.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from Effective Go and borrows from:

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
- [Google Go Style Guide](https://google.github.io/styleguide/go/)
- [Go Doc Comments](https://go.dev/doc/comment)
- [Go 1.22 release notes](https://go.dev/doc/go1.22) (loop variables and
  range over integers)
