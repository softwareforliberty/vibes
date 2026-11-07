# Ruby Idioms and Principles

How to write Ruby well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Ruby code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Optimise for the reader.** Code is read far more often than it's
  written. Prefer the plain, obvious version over the clever one.
- **Least surprise.** A method does what its name says, and nothing else.
  Callers shouldn't need to read its body to use it.
- **Small objects with one job each.** A class that's hard to name is doing
  too much.
- **Errors should never pass silently.** Raise them, handle them where
  something can be done, and never rescue them without a reason.
- **Be careful with metaprogramming.** It's powerful but hard to read,
  search and debug. Reach for it only when plain code would be clearly
  worse.

## Objects and modules

- **Prefer composition to inheritance.** Build objects from smaller
  collaborators passed to `initialize`. Use inheritance only for a true
  "is a" relationship.
- Use a module as a **namespace** for related classes, and as a **mixin**
  only for behaviour that several unrelated classes share.
- Keep a class's public interface small. Everything the outside world
  doesn't need is `private`.
- **Avoid global and class-level mutable state.** Globals (`$name`), class
  variables (`@@name`) and mutable constants are shared by everything,
  including tests that run one after another. Pass objects in instead.
- Group related settings into one object instead of threading many
  parameters through every call.

## Values and mutability

- **Use `Data.define` for value objects.** It creates an immutable class
  with keyword initialisation, equality and a readable `inspect`:

  ```ruby
  Point = Data.define(:x, :y)

  origin = Point.new(x: 0, y: 0)
  ```

- **Freeze constants that hold collections.** Otherwise any code can add to
  them:

  ```ruby
  ROLES = %i[admin editor viewer].freeze
  ```

- Use symbols for fixed sets of identifiers (`:admin`, `:pending`) and
  strings for text.
- Don't modify a method's arguments unless that's its stated job. Return a
  new value instead, and use `dup` before changing a copy.
- Use `fetch` to read required hash keys: `config.fetch(:host)`. A missing
  key then raises at once, instead of returning `nil` that fails later.

## Errors and exceptions

- **Raise exceptions for errors.** Don't return `nil` or `false` to signal
  failure. A caller can forget to check a return value, but an exception
  can't be ignored by accident.
- Return `nil` only when "no result" is a normal outcome, such as a lookup
  that may find nothing, and document it.
- **Rescue the most specific error you can handle.** Never rescue
  `Exception`. It also catches signals and `exit`. A bare `rescue` catches
  `StandardError`, which is still too broad for most code.
- Keep the code inside a `begin` small, so you only rescue errors from the
  line you expect to fail.
- Give each library a base error class, and derive its specific errors from
  it. Callers can then rescue everything from your library in one place:

  ```ruby
  module Billing
    Error = Class.new(StandardError)
    PaymentDeclinedError = Class.new(Error)
  end
  ```

- When you translate one error into another, raise the new one inside the
  `rescue` block. Ruby records the original as its `cause`, so it still
  appears in the backtrace.
- **Handle each error at the level that can do something about it**: retry,
  fall back, or report to the user. Lower levels let it propagate.
- **Report each error once.** Code either logs an error or raises it, not
  both, so one failure doesn't produce a cascade of messages.
- Limit retries to a fixed number of attempts, with a delay between them.
  An unbounded `retry` can loop forever.
- Convert input with the strict methods, `Integer('42')` and
  `Float('1.5')`, which raise on bad input. `'abc'.to_i` quietly returns
  `0`.

## Resources

- **Use the block form of methods that open resources**: `File.open`,
  `Dir.mktmpdir`, `Mutex#synchronize`, database transactions. The block
  releases the resource even when an error is raised:

  ```ruby
  File.open(path, 'w') do |file|
    file.write(report)
  end
  ```

- When you write a method that acquires a resource, offer the same block
  form, and release the resource in an `ensure`.
- Pass an encoding when reading text files whose encoding you know:
  `File.read(path, encoding: 'UTF-8')`.

## Iteration

- **Use the `Enumerable` methods**: `each`, `map`, `select`, `reject`,
  `find`, `sum`, `group_by`, `each_with_object`. They say what the loop is
  for. Never use `for` loops.
- Use `each_with_index` when you need the index too, and `each_slice` to
  work in batches.
- Use `lazy` for large or endless sequences, so items are processed one at
  a time instead of all at once.
- Never add or remove items in a collection while iterating over it. Build
  a new collection instead.
- Build long strings with `<<` on an unfrozen string, or `join` an array of
  parts. Repeated `+` creates a new string every time.

## Duck typing and types

- **Depend on behaviour, not class.** Call the method you need, and let the
  object decide how to respond. Avoid `is_a?` checks in business logic.
- Use `respond_to?` only at boundaries where several kinds of input are
  genuinely expected.
- Convert input you're unsure of with `Array(value)` and `String(value)`
  instead of branching on its type.
- Describe public APIs with YARD type tags. When a project needs static type
  checking, describe the types in RBS signature files, which ship with
  Ruby.

## Metaprogramming

- Prefer plain methods. Use `define_method` over string `eval` when you
  must generate methods, and never build code from strings.
- If you implement `method_missing`, also implement `respond_to_missing?`,
  and call `super` for names you don't handle. Otherwise the object lies
  about what it can do.
- Use `public_send` instead of `send`, so a dynamic call can't reach private
  methods.
- Don't monkey-patch core classes. Use a refinement, or a helper method,
  when you need extra behaviour.

## Concurrency

- Use **threads for I/O-bound work**. The global VM lock lets only one
  thread run Ruby code at a time, so threads don't speed up computation.
- **Document what protects shared data**, and guard it with a `Mutex`.
  Prefer handing data between threads with a `Queue` over sharing it.
- Deeply frozen objects (the object and everything it refers to) are safe
  to share between threads. Mutable ones aren't unless they're protected.

## Security

- **Never build SQL by string interpolation.** Pass values as query
  parameters, so the driver escapes them:

  ```ruby
  db.execute('SELECT * FROM users WHERE email = ?', [email])
  ```

- **Run commands with separate arguments, not a shell string.** Use
  `system('git', 'log', path)`. Never put input into backticks, `%x()` or a
  single-string `system` call.
- **Never load untrusted data with `Marshal.load` or `YAML.load`.** Both can
  create arbitrary objects. Use `JSON.parse` for data from outside the
  program, and `YAML.safe_load` for YAML.
- Never pass input to `eval`, `instance_eval`, `send` or `constantize`.
- Use `SecureRandom` for tokens and passwords, never `rand`. Compare secrets
  with `OpenSSL.secure_compare`, which takes the same time however much of
  the value matches.
- Expand file paths built from input, and check they stay inside the
  intended directory before you open them.

## Testable design

- **Pass dependencies in.** Take collaborators as keyword arguments to
  `initialize`, with a sensible default. Tests can then pass a fake:

  ```ruby
  def initialize(clock: Time)
    @clock = clock
  end
  ```

- Keep the core logic in methods that take values and return values. Push
  I/O to the edges of the program.
- Don't call `Time.now` deep in your logic. Pass the current time in, or
  inject a clock as above.
- Don't stub the object under test. If you need to, it's doing too much.

## Performance

- **Measure before you optimise.** Use the `Benchmark` module, or a
  profiler, to find the slow part, and optimise only that.
- Choose the right data structure first. A `Hash` or `Set` lookup takes the
  same time however large it grows, while `Array#include?` gets slower as
  the array grows.
- Load related records in one query instead of one query per record.
- **Stream large input** with `File.foreach` or `IO#each_line`, rather than
  `File.read` or `File.readlines`, which read the whole file into memory.
- Copy between files and sockets with `IO.copy_stream`, which uses the kernel's
  copy calls where it can.

## Sources

- [The Ruby Style Guide](https://rubystyle.guide/)
- [Ruby documentation: security](https://docs.ruby-lang.org/en/master/security_rdoc.html)
- [Ruby documentation: `Data`](https://docs.ruby-lang.org/en/master/Data.html)
- [RBS](https://github.com/ruby/rbs)
