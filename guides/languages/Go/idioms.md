# Go Idioms and Principles

How to write Go well. [coding-style.md](coding-style.md) covers how code looks.
This guide covers how it's designed: the idioms and principles that keep Go
code correct, safe and maintainable. Every example follows the style guide.

## Principles

- **Clear is better than clever.** Go favours plain code that any reader can
  follow. Write the obvious version unless profiling proves it too slow.
- **Errors are values.** Return them, check them where they happen, and add
  context as they travel up.
- **Make the zero value useful.** A type that works without a constructor
  is easier to use and harder to misuse.
- **Every goroutine has an owner.** Someone starts it, someone knows how it
  stops, and someone waits for it.
- **Keep scope small.** Unexport by default, and give state the narrowest
  visibility that works.

## Packages

- A package does one job, named by its package name. Organise by what the
  code does (`order`, `invoice`), not by what kind of code it is (`models`,
  `handlers`).
- Put code that other modules must not import under `internal/`. The Go
  toolchain enforces the boundary.
- **Avoid package-level mutable state.** Pass dependencies in through
  struct fields or parameters, so tests can replace them.
- **`init()` functions are a last resort.** They run on import, in an order
  that's easy to get wrong. Do setup in an explicit function `main` calls.

## Functions and APIs

- **Accept interfaces, return concrete types.** Callers get the full type,
  and you stay free to add methods without breaking anyone.
- Pass a struct when a function needs more than about four parameters, or
  several of the same type. Named fields can't be passed in the wrong
  order.
- **Don't take a `bool` parameter that changes behaviour.** `Load(path,
  true)` doesn't say what `true` means. Use two functions or an options
  struct.
- Return early on errors. Don't return a value and an error that both
  matter: if `err` isn't `nil`, the other results are meaningless unless the
  doc comment says otherwise.

## Errors

- **Check every error.** If you really mean to ignore one, assign it to `_`
  with a comment saying why.
- **Wrap errors with context** using `%w`, so callers can still inspect the
  cause:

  ```go
  	if err := store.Save(ctx, o); err != nil {
  		return fmt.Errorf("save order %s: %w", o.ID, err)
  	}
  ```

- Inspect errors with `errors.Is` and `errors.As`, never by comparing
  strings. Wrapping breaks `==`, and messages change.
- Export a **sentinel error** (`var ErrNotFound = errors.New("not found")`)
  when callers need to check for one condition. Export an **error type** when
  they need details from it. Otherwise keep errors unexported, so they don't
  become part of your API.
- **Handle each error once.** A function either logs an error or returns it,
  not both, so one failure doesn't produce a cascade of log lines.
- **Don't panic for ordinary failures.** `panic` is for bugs that mean the
  program can't continue, such as a broken invariant. A library never lets a
  panic escape to its caller.

## Context

- A function that does I/O, waits, or calls one that does takes a
  `context.Context` as its **first parameter**, named `ctx`.
- **Don't store a context in a struct.** Pass it to each call, so every
  operation has its own deadline and cancellation.
- Check `ctx.Err()` in long loops, and pass `ctx` on to every call that
  accepts one, so cancellation reaches the whole call tree.
- Use context values only for request-scoped data that crosses API
  boundaries, such as a trace ID. Never use them for optional parameters.

## Interfaces

- **Define an interface where it's used, not where it's implemented.** The
  consumer knows which methods it needs. The producer returns a concrete
  type.
- Keep interfaces small. One or two methods is normal; a large interface is
  hard to implement and hard to fake in tests.
- Don't define an interface until you have a second implementation or a
  test that needs one.

## Concurrency

- **Know how every goroutine stops** before you start it: when its input
  closes, its context is cancelled, or its work ends. A goroutine that can't
  stop is a leak.
- **The function that starts goroutines waits for them**, with a
  `sync.WaitGroup` or an errgroup. Don't fire and forget.
- **Use channels to hand off ownership, and mutexes to guard state.** A
  value sent on a channel belongs to the receiver. Shared state that several
  goroutines read and write sits behind a `sync.Mutex`, next to the fields it
  protects:

  ```go
  type Counter struct {
  	mu    sync.Mutex
  	count int // guarded by mu
  }
  ```

- **Only the sender closes a channel**, and only when no more values will be
  sent. Closing from the receiver side, or closing twice, panics.
- **Never copy a value that contains a mutex.** Pass it by pointer. `go vet`
  catches most copies.
- Prefer synchronous APIs. Let the caller add concurrency with a goroutine;
  it's much harder to take away.
- Run tests with the race detector (`go test -race`). A data race is a bug
  even when the tests pass.

## Zero values and construction

- **Design types so the zero value works**: an empty `bytes.Buffer` is ready
  to use, and a zero `sync.Mutex` is unlocked.
- When a type needs setup, give it a constructor named `New` (in a package
  with one main type) or `NewThing`, and document what the zero value does
  if it's not usable.
- A `nil` slice is a valid empty slice: `len`, `range` and `append` all work
  on it. Return `nil`, not `[]T{}`, unless the value is encoded (JSON
  encodes `nil` as `null`).

## Resources

- **Release a resource with `defer` right after acquiring it**, so every
  return path releases it.
- **Check the error from `Close` on files you write.** A failed close can
  mean the data never reached the disk:

  ```go
  func writeFile(path string, data []byte) (err error) {
  	f, err := os.Create(path)
  	if err != nil {
  		return err
  	}
  	defer func() {
  		if cerr := f.Close(); err == nil {
  			err = cerr
  		}
  	}()
  	_, err = f.Write(data)
  	return err
  }
  ```

- Always close HTTP response bodies, even when you don't read them.

## Slices and maps

- **`append` may or may not copy.** After `b := append(a, x)`, `a` and `b`
  can share memory. Copy explicitly (`slices.Clone`) before handing a slice
  to code that may change it.
- Preallocate when you know the size: `make([]T, 0, n)`.
- **Maps aren't safe for concurrent use.** Guard a shared map with a mutex.
- Don't rely on map iteration order. It's deliberately randomised.

## Modules and dependencies

- Commit both `go.mod` and `go.sum`, and run `go mod tidy` before every
  commit so they match the code.
- **Add dependencies sparingly.** Every module you import is code you ship
  and must keep patched. The standard library covers a great deal.
- A breaking change to a public module needs a new major version, which
  appears in the module path (`example.com/lib/v2`).

## Security

- **Run external programs with `os/exec`, passing arguments as a list.** It
  doesn't use a shell, so arguments can't inject commands.
- **Build SQL with placeholders**, never by formatting values into the query
  string:

  ```go
  	row := db.QueryRowContext(ctx,
  		"SELECT name FROM users WHERE id = $1", id)
  ```

- Render HTML with `html/template`, which escapes by context. Never use
  `text/template` for HTML.
- Use `crypto/rand` for anything security-related, never `math/rand`.
- Set timeouts on every `http.Server` and `http.Client`. The defaults wait
  forever.

## Testing

- **Write table-driven tests**, with one `t.Run` per case, so a failure names
  the case:

  ```go
  func TestParseSize(t *testing.T) {
  	tests := []struct {
  		in   string
  		want int64
  	}{
  		{"10", 10},
  		{"2k", 2048},
  	}
  	for _, tt := range tests {
  		t.Run(tt.in, func(t *testing.T) {
  			got, err := ParseSize(tt.in)
  			if err != nil {
  				t.Fatalf("ParseSize(%q): %v", tt.in, err)
  			}
  			if got != tt.want {
  				t.Errorf("ParseSize(%q) = %d, want %d", tt.in, got, tt.want)
  			}
  		})
  	}
  }
  ```

- Failure messages say what was called, what it returned and what was
  expected: `got X, want Y`.
- Mark test helpers with `t.Helper()`, so failures point at the caller.
- Keep test fixtures in a `testdata` directory, which the Go tool ignores.
- Fuzz parsers and decoders with Go's built-in fuzzing (`func FuzzX(f
  *testing.F)`).

## Performance

- **Measure before you optimise.** Write a benchmark, and profile with
  `pprof` to find where the time actually goes.
- Reduce allocations in hot paths: reuse buffers, preallocate slices, and
  avoid converting between `string` and `[]byte` in loops.
- **Stream large input** with `bufio.Scanner` or `bufio.Reader`, rather than
  reading the whole file into memory. A `Scanner` rejects lines over 64 KiB
  unless you raise its limit with `Buffer`.
- **Memory-map a large file that's read at random positions or many times**
  with `golang.org/x/exp/mmap`, which maps it read-only and falls back to plain
  reads where it can't. Don't map a file you read once from start to end, where
  buffered reads are as fast and simpler, or one that another process may
  shrink while it's mapped, which can crash the program.
- `io.Copy` from an `*os.File` to a file or a network connection uses the
  kernel's copy calls on Linux, so prefer it to a copy loop of your own.

## Sources

- [Effective Go](https://go.dev/doc/effective_go)
- [Go Code Review Comments](https://go.dev/wiki/CodeReviewComments)
- [Google Go Style Guide: best practices](https://google.github.io/styleguide/go/best-practices)
- [Go blog: Working with errors in Go 1.13](https://go.dev/blog/go1.13-errors)
- [Go blog: Go concurrency patterns: context](https://go.dev/blog/context)
- [Go Modules Reference](https://go.dev/ref/mod)
