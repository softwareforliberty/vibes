# Clojure Idioms and Principles

How to write Clojure well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Clojure code correct, simple and maintainable. Every example follows the
style guide.

## Principles

- **Data first.** Represent information as plain maps, vectors and sets.
  Generic data works with every function in the core library, and is easy to
  print, test and send over the wire.
- **Pure functions in the core, side effects at the edges.** A function that
  only turns inputs into outputs can be tested at the REPL with no setup.
- **Values don't change.** Immutable collections can be shared freely, and
  "updating" one returns a new value.
- **Validate at the boundaries.** Check data where it enters the system, then
  trust it inside.
- **Small, composable functions.** Prefer many short functions over one long
  one; they combine with `comp`, threading macros and higher-order functions.
- **Simple over easy.** Choose the design with the fewest interleaved
  concerns, even if another is quicker to type.

## Data modelling

- Use **maps with namespace-qualified keywords** for entities:
  `{:order/id 42 :order/lines [...]}`. Qualified keys stay unambiguous when
  maps from different domains are merged.
- Use a `defrecord` only when you need fast field access or to implement a
  protocol on the type. Plain maps are the default.
- Keep keys flat and predictable. Don't change a value's shape depending on
  where it came from.
- Represent absent data by **leaving the key out**, not by storing `nil`
  against it. Then `contains?` and `(:key m)` agree.

## Functions

- Write functions that take data and return data. Pass dependencies (a
  database, a clock) in as arguments, so tests can substitute them.
- Keep functions short. A function that needs a long `let` with many steps is
  usually several functions.
- Name side-effecting functions with a trailing `!` (see
  [Naming](coding-style.md#naming)), so callers know what's pure.
- Use multi-arity functions to provide defaults instead of optional
  positional arguments. For many options, take a single map.

## Collections

- Use the core sequence functions (`map`, `filter`, `reduce`, `group-by`)
  instead of explicit loops.
- Use `mapv` and `filterv`, or `into []`, when you need a vector. Lazy
  sequences are the default result of `map` and `filter`.
- **Never let laziness escape a side effect.** A lazy `map` over an effectful
  function may never run, or run outside a `with-open` or binding. Use
  `run!` or `doseq` for side effects, and `doall` when a lazy result must be
  realised now.
- Use transducers (`transduce`, `into` with an xform) for long pipelines over
  large data, so no intermediate sequences are built.
- Use sets as predicates and keywords as functions: `(filter #{:paid}
  states)`, `(map :price lines)`.

## State and concurrency

- Keep mutable state in as few places as possible, behind reference types.
- Use an **atom** for independent state, and update it with a pure function
  through `swap!`. The function may be retried, so it must have no side
  effects.
- Use refs and transactions only when several pieces of state must change
  together.
- Prefer passing values between threads (through queues or `core.async`
  channels) to sharing state.
- Don't use dynamic vars to pass ordinary arguments. Rebinding is
  thread-local and invisible at the call site; use them only for genuinely
  ambient context.

## Namespaces and dependencies

- Keep each namespace focused on one area, and avoid circular requires; they
  fail at load time.
- Keep a namespace's public API small. Make helpers private with `defn-`.
- Don't redefine core functions in a namespace. If a name must shadow a core
  one, exclude it explicitly with `(:refer-clojure :exclude [...])`.
- Pin every dependency in `deps.edn` to an exact version. The resolved
  classpath, and so the dependency audit, then doesn't change between
  builds.

## Validation at boundaries

- Describe external data (requests, files, messages) with **malli** schemas
  or **clojure.spec** specs, and validate it where it enters the system.
- Return or throw a clear error that names the invalid fields, instead of
  letting bad data fail deep inside the program.
- Inside the system, trust validated data and don't re-check it in every
  function.
- Read untrusted EDN with `clojure.edn/read-string`, never
  `clojure.core/read-string`, and never `eval` input. The core reader can run
  code embedded in the text.

## Errors

- Throw `ex-info` with a message and a data map for errors:
  `(throw (ex-info "Order not found" {:order/id id}))`. The data makes the
  error inspectable without parsing the message.
- Catch exceptions only where you can handle them, and use `ex-data` to
  decide what to do.
- Don't catch `Throwable` or `Error`; they include problems the program
  can't recover from.
- For expected failures in a pipeline, return data that describes the failure
  rather than throwing, when callers need to handle it as a normal case.

## Resources

- Open resources with `with-open`, so they're closed even when an exception
  is thrown.
- Start and stop long-lived components (connection pools, servers) through
  one lifecycle library or a single start/stop function, never as a side
  effect of loading a namespace.

## Java interop

- **Avoid reflection.** Add type hints where the compiler can't infer a Java
  type, and turn on `(set! *warn-on-reflection* true)` in every namespace
  that calls Java. Reflective calls are slow and hide type errors until run
  time.
- Wrap Java APIs in small Clojure functions at the boundary, and convert
  `null` results and checked exceptions there.

## Macros

- Write a function, not a macro, unless you need to control evaluation or
  introduce syntax. Functions compose; macros don't.
- Keep macros thin: do the work in a function and have the macro call it.
- Use `gensym`s (`x#`) for every local a macro introduces, so it can't
  capture the caller's names.

## REPL-driven development

- Build and test code by evaluating it in a running REPL as you write it.
- Keep exploratory code in `(comment ...)` blocks, and move anything worth
  keeping into tests.
- Make namespaces safe to reload: no side effects at load time, and `defonce`
  for state that must survive a reload.

## Testing

- Test pure functions with plain data in `clojure.test`.
- Use property-based tests (`test.check`) for functions with laws, such as
  round-tripping parsers and serialisers.
- Generate test data from your malli schemas or specs, so tests cover the
  shapes the boundary accepts.

## Sources

- [Clojure rationale](https://clojure.org/about/rationale)
- [The Clojure Style Guide](https://guide.clojure.style/)
- [Clojure reference: transducers](https://clojure.org/reference/transducers)
- [Clojure reference: Java interop](https://clojure.org/reference/java_interop)
- [malli](https://github.com/metosin/malli)
- [clojure.spec guide](https://clojure.org/guides/spec)
