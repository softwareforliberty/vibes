# R Coding Style

A general-purpose coding style for R projects. It builds on the
[tidyverse style guide](https://style.tidyverse.org/), which the styler and
lintr tools enforce (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(vectorisation, packages, missing values, reproducibility and other idioms),
see [idioms.md](idioms.md).

The tools that check R code are listed in [tools.md](tools.md).

## Language baseline

Code targets **R 4.2 or later**. R 4.1 added the native pipe `|>` and the
`\(x)` shorthand for anonymous functions, and R 4.2 added the `_` placeholder
for the pipe. This guide relies on all three.

## Files

- Name files in `snake_case` with a `.R` extension: `read_survey.R`. Never
  put spaces in a file name, because they break shell commands and URLs.
- In a package, group related functions in one file named after the main
  one. A file of unrelated helpers is hard to navigate.
- Use UTF-8 and LF line endings, and end every file with a newline.

## Layout

### Indentation

- Indent with **2 spaces**. Never use tabs.
- When a function call or definition doesn't fit on one line, put each
  argument on its own line, indented one level, with the closing parenthesis
  on its own line:

  ```r
  summary_table <- summarise_survey(
    responses,
    group = "region",
    weights = "weight"
  )
  ```

### Line length

- Keep lines to **80 columns**. Long lines are hard to read side by side and
  in review.
- Never break a user-visible string across lines, so it stays greppable.

### Braces

- Put `{` last on the line and `}` first on its own line. `else` goes on the
  same line as the closing brace:

  ```r
  if (n_rows == 0) {
    warning("no rows to summarise")
  } else {
    summarise_rows(rows)
  }
  ```

- A short `if` with a single-expression result may sit on one line without
  braces: `label <- if (passed) "pass" else "fail"`.
- Always use braces when the body has more than one line or has side effects.

### One thing per line

- One statement per line. Never use `;` to join statements.
- One step per line in a pipe chain, with `|>` at the end of each line:

  ```r
  results <- responses |>
    filter_complete() |>
    summarise_survey(group = "region")
  ```

## Assignment

- Assign with `<-`. Use `=` only for function arguments, so the two never get
  confused.
- Never use right assignment (`->`). Readers look for the name on the left.

## Spacing

- Put a space after every comma, never before one.
- Put spaces around infix operators (`==`, `+`, `<-`, `|>`, `~`), except the
  high-precedence ones: `::`, `:::`, `$`, `@`, `[`, `[[`, `^` and `:`.
- No space between a function name and its `(`. Put a space after `if`,
  `for` and `while`, and before `{`.
- No spaces just inside parentheses or brackets: `x[1, ]`, not `x[ 1, ]`.

## Naming

- Use lowercase `snake_case` for variables and functions. Don't use dots in
  names: `print.summary` looks like an S3 method for the `summary` class.
- Name functions with verbs (`read_survey()`) and data with nouns
  (`responses`).
- Never reuse the name of a base function or value, such as `c`, `t`, `mean`,
  `T` or `F`. Code that later calls the base version silently gets yours.
- Write `TRUE` and `FALSE` in full. `T` and `F` are ordinary variables that
  any code can reassign.

## Strings and numbers

- Use double quotes. Use single quotes only when the string contains a double
  quote: `'say "hello"'`.
- Write integer literals with `L` when an integer is required: `n <- 10L`.

## Functions

- Use `\(x)` for short anonymous functions, and `function(x)` for anything
  longer than one line.
- Use `return()` only for early returns. A function's value is its last
  expression, and an explicit `return()` at the end adds nothing.
- Put arguments without defaults first, then arguments with defaults.

## Conditions

- Use `&&` and `||` in `if` conditions, which need a single `TRUE` or
  `FALSE`. Use `&` and `|` only for element-wise operations on vectors.

## Comments

- Start each comment with `# ` and write it as a sentence. Explain **why** the
  code does something, not **what** it does.
- Document every exported function with a
  [roxygen2](https://roxygen2.r-lib.org/) block (`#'`) directly above it,
  covering what it does, each parameter, and what it returns:

  ```r
  #' Summarise survey responses by group.
  #'
  #' @param responses A data frame with one row per response.
  #' @param group Name of the column to group by.
  #' @return A data frame with one row per group.
  #' @export
  summarise_survey <- function(responses, group) {
    ...
  }
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [The tidyverse style guide](https://style.tidyverse.org/)
- [R Packages (2e)](https://r-pkgs.org/), by Hadley Wickham and Jennifer
  Bryan
- [roxygen2 documentation](https://roxygen2.r-lib.org/)
- [lintr documentation](https://lintr.r-lib.org/)
