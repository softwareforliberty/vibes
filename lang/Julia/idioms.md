# Julia Idioms and Principles

How to write Julia well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Julia code correct, fast and maintainable. Every example follows the
style guide.

## Principles

- **Write generic code.** A function written against abstract types and
  interfaces works for types its author never saw. Multiple dispatch is what
  makes that possible.
- **Keep code type-stable.** The compiler generates fast code when it can
  predict every value's type. Most Julia performance problems are type
  instability.
- **Put code in functions.** Code at the top level of a script runs in
  global scope, which is slow and hard to test.
- **Fail loudly.** Throw a specific exception the moment something is wrong.
- **Pin your environment.** Every result should be reproducible from a
  `Project.toml` and a `Manifest.toml`.

## Type stability

- A function's return type must depend only on its argument types, never on
  their values. A function that returns `0` in one branch and `0.0` in
  another forces every caller onto a slow path:

  ```julia
  function safe_ratio(a::Float64, b::Float64)
      if iszero(b)
          return zero(a)
      end
      return a / b
  end
  ```

- Give struct fields concrete types, using type parameters when the type
  varies. A field typed `Real` or `Any` makes every access dynamic:

  ```julia
  struct Measurement{T<:Real}
      value::T
      error::T
  end
  ```

- Avoid containers of abstract types such as `Vector{Any}` or `Vector{Real}`.
  Use `Vector{Float64}`, or a type parameter.
- Check suspect functions with `@code_warntype`, or JET's `@report_opt`.

## Multiple dispatch

- **Use methods instead of type checks.** A chain of `if x isa ...` branches
  is a dispatch table written by hand, and nobody else can extend it:

  ```julia
  area(c::Circle) = π * c.radius^2
  area(s::Square) = s.side^2
  ```

- Define methods against abstract types and interfaces (`AbstractVector`,
  iteration, indexing), so they work for every type that implements them.
- **Never commit type piracy.** Don't add methods to a function you don't own
  for types you don't own, such as `Base.:+(::Vector, ::String)`. It changes
  the behaviour of unrelated code that loads your package.
- Avoid method ambiguities: two methods where neither is more specific than
  the other. Aqua.jl's tests report them.

## Globals and constants

- **Never use non-constant globals in performance-critical code.** Their type
  can change at any time, so every use is dynamic. Pass values as arguments,
  or declare them `const`.
- Wrap a script's work in a `main()` function and call it at the end.

## Mutation

- A function that changes one of its arguments ends in `!`, and the mutated
  argument comes first: `sort!(scores)`.
- Provide the non-mutating version alongside it where it's useful. It copies
  the argument and calls the mutating one: `normalise(v) = normalise!(copy(v))`.
- Make structs immutable by default. Use `mutable struct` only when instances
  must change after construction, because immutable values are easier to
  reason about and often faster.

## Errors

- Throw the most specific exception type that fits: `ArgumentError` for bad
  arguments, `DomainError` for values outside a function's domain,
  `KeyError` for missing keys.
- Define your own exception types for errors callers should handle:

  ```julia
  struct SurveyNotFound <: Exception
      path::String
  end
  ```

- Catch only the exceptions you can handle, and rethrow the rest. A
  `catch` block that handles everything hides bugs.
- Use `@assert` for internal invariants only, never to validate input. The
  manual warns that assertions may be disabled at some optimisation levels.

## Resources

- Use the `do`-block form, which closes the resource on every path:

  ```julia
  open(path) do io
      return read_responses(io)
  end
  ```

- Use `try`/`finally` for cleanup the `do` form doesn't cover.

## Missing values

- Use `nothing` for "no value" (a search that found nothing), and `missing`
  for a missing data value that should propagate through calculations.
- Test with `isnothing(x)` and `ismissing(x)`, or `x === nothing`. Never use
  `==`: `missing == missing` is `missing`, not `true`.

## Packages and environments

- Every project has its own environment, with a `Project.toml`. Never install
  packages into the global environment for project work.
- **Commit `Manifest.toml` for applications**, so every machine uses the same
  versions. Don't commit it for packages, which must work across a range of
  versions.
- Give every dependency a `[compat]` entry in `Project.toml`. Without one, a
  new major version of a dependency can break your package without warning.
- Never call `Pkg.add()` from package or script code. Dependencies are
  declared, not installed at run time.

## Security

- **Never evaluate code built from strings**, such as
  `eval(Meta.parse(input))`. Anyone who controls the string controls the
  program.
- **Never `deserialize()` data from an untrusted source.** The
  `Serialization` format can construct arbitrary objects. Exchange data as
  CSV, JSON or Arrow instead.
- Run external programs with backtick commands and interpolation:
  `` run(`convert $(input) $(output)`) ``. Julia passes each value as a
  separate argument without a shell, so it can't inject commands.
- `include()` only files that are part of your own code.

## Concurrency

- Start tasks with `Threads.@spawn`, and wait for them with `fetch()` or
  `wait()`.
- **Never index per-thread storage by `Threads.threadid()`.** Tasks can move
  between threads, so the index can change partway through.
- Protect shared mutable state with a `ReentrantLock`, or use atomics.

## Performance

- Measure before optimising, with BenchmarkTools.jl's `@btime`, which
  repeats the call and excludes compilation.
- Pre-allocate outputs, and use mutating functions in hot loops.
- Use broadcasting (`y .= a .* x .+ b`) to fuse operations into one loop with
  no temporaries.
- Use views (`@views`) instead of slices when you only read part of an array.

## Sources

- [Julia manual: Performance Tips](https://docs.julialang.org/en/v1/manual/performance-tips/)
- [Julia manual: Style Guide](https://docs.julialang.org/en/v1/manual/style-guide/)
- [Julia manual: Methods](https://docs.julialang.org/en/v1/manual/methods/)
  (ambiguities and type piracy)
- [Julia manual: Multi-Threading](https://docs.julialang.org/en/v1/manual/multi-threading/)
- [Pkg.jl documentation](https://pkgdocs.julialang.org/)
