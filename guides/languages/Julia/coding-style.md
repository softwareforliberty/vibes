# Julia Coding Style

A general-purpose coding style for Julia projects. It builds on the
[style guide in the Julia manual](https://docs.julialang.org/en/v1/manual/style-guide/)
and on [Blue](https://github.com/JuliaDiff/BlueStyle), the community style
that JuliaFormatter applies with `style = "blue"` (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (type
stability, multiple dispatch, packages and other idioms), see
[idioms.md](idioms.md).

The tools that check Julia code are listed in [tools.md](tools.md).

## Language baseline

Code targets **Julia 1.10 or later**. 1.10 is the long-term support release,
so it's the oldest version most users and CI systems still run.

## Files

- A package's main file is named after its module: `src/Surveys.jl` holds
  `module Surveys`. Other files use `snake_case.jl` and are `include`d from it.
- Use UTF-8 and LF line endings, and end every file with a newline.

## Layout

### Indentation

- Indent with **4 spaces**. Never use tabs.
- Don't indent the body of a `module`. Every line in the file would gain an
  indent that tells the reader nothing.
- Close every block with `end` at the indentation of the line that opened it.

### Line length

- Keep lines to **92 columns**. That's Blue's limit, and JuliaFormatter wraps
  to it.
- Never break a user-visible string across lines, so it stays greppable.

### Wrapping

When a call or signature doesn't fit, JuliaFormatter moves the arguments to
one line of their own, indented one level, with the closing parenthesis on
its own line. When they still don't fit, it puts each argument on its own
line:

```julia
by_region = summarise_responses(
    survey_responses;
    group=:region,
    weights=:response_weight,
    min_responses=10,
    missing_values=:skip,
)
```

### One thing per line

- One statement per line. Never join statements with `;`.
- Leave one blank line between functions, and none at the start or end of a
  block.

## Spacing

- Put spaces around binary operators and `=`: `total = price * quantity`.
  Leave out the spaces around `^`, `:` in ranges, and `.` in field access.
- Leave out the spaces around `=` in keyword arguments and default values,
  both in signatures and calls: `group=:region`. Blue style writes them this
  way, and JuliaFormatter enforces it.
- Put a space after every comma, and none just inside parentheses or
  brackets.
- Separate keyword arguments from positional ones with `;` in signatures:
  `function summarise_responses(responses; group=:region)`.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Modules and types | `UpperCamelCase` | `Surveys`, `ResponseTable` |
| Functions and variables | `snake_case` | `summarise_responses`, `n_rows` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_WEIGHT` |
| Mutating functions | Name ends in `!` | `normalise!`, `push_row!` |

- When you add a method to a Base function, keep Base's name exactly
  (`isempty`, `haskey`). The point of the method is that callers already know
  the name.
- Use ASCII for names in a public API. Unicode symbols are fine inside a
  function's maths, but callers shouldn't need a special input method to call
  your code.

## Functions

- Use the short form only for one-line functions:
  `area(r::Circle) = π * r.radius^2`.
- In long-form functions, end with an explicit `return`. A reader can then
  see what the function returns without tracing the last expression of every
  branch.
- Annotate argument types to choose a method, not to document them. Annotate
  with the most general type that works, such as `AbstractVector{<:Real}`
  instead of `Vector{Float64}`, so the function works for every suitable
  type.

## Imports

- Import names explicitly: `using DataFrames: DataFrame, groupby`. Every name
  in a file then has a visible source.
- Use `import Base: show` only for functions you're adding methods to.
- Put all `using` and `import` lines at the top of the module.

## Strings

Strings use double quotes, which is the only option in Julia. Use `"""` for
multi-line strings and docstrings, and `$` interpolation instead of
concatenation: `"read $(n_rows) rows"`.

## Comments and docstrings

- Start each comment with `# ` and write it as a sentence. Explain **why**,
  not **what**.
- Document every exported function and type with a docstring directly above
  it. Start with the signature, indented four spaces, then a one-line
  summary:

  ```julia
  """
      summarise_responses(responses; group=:region)

  Summarise survey responses, with one row per value of `group`.
  """
  function summarise_responses(responses; group=:region)
      ...
  end
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [Julia manual: Style Guide](https://docs.julialang.org/en/v1/manual/style-guide/)
- [Julia manual: Documentation](https://docs.julialang.org/en/v1/manual/documentation/)
- [Blue: a style guide for Julia](https://github.com/JuliaDiff/BlueStyle)
- [JuliaFormatter documentation](https://domluna.github.io/JuliaFormatter.jl/stable/)
