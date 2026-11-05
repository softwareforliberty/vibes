# R Idioms and Principles

How to write R well. [coding-style.md](coding-style.md) covers how code looks.
This guide covers how it's designed: the idioms and principles that keep R
code correct, reproducible and maintainable. Every example follows the style
guide.

## Principles

- **Write functions, not scripts.** A function has inputs, an output and a
  name, so it can be tested and reused. A script that relies on whatever is
  in the workspace can't.
- **Think in vectors.** R operates on whole vectors at once. Code that does
  the same is shorter, faster and easier to read than a loop over elements.
- **Results must be reproducible.** Anyone running the same code on the same
  data must get the same answer, including random numbers and package
  versions.
- **Fail loudly.** Signal an error the moment something is wrong, rather than
  carrying a bad value forward.
- **Leave global state as you found it.** Functions must not change options,
  the working directory or the search path for their callers.

## Functions and packages

- **Put reusable code in a package**, even an internal one. A package gives
  you documentation, tests, declared dependencies and `R CMD check`.
- **Never call `library()` or `require()` inside package code.** Declare the
  dependency in `DESCRIPTION` and call `pkg::fun()`, or import it in
  `NAMESPACE` through roxygen2's `@importFrom`.
- **Never use `attach()`.** It puts a data frame's columns on the search path,
  where they silently mask variables of the same name.
- **Never call `setwd()` or `rm(list = ls())` in shared code.** Build paths
  from a project root instead. Clearing the workspace doesn't clear loaded
  packages or options, so it gives a false sense of a clean start.
- **Pass data in through arguments.** A function that reads a global variable
  depends on code it doesn't show. Never assign to globals with `<<-`.

## Vectorisation

- Use vectorised functions and operators instead of element-by-element loops:
  `total <- price * quantity`, not a loop that multiplies one pair at a time.
- When you must loop, pre-allocate the result. Growing a vector with
  `c(result, x)` copies it on every step:

  ```r
  scores <- numeric(length(ids))
  for (i in seq_along(ids)) {
    scores[i] <- score_one(ids[i])
  }
  ```

- **Use `seq_along(x)` and `seq_len(n)`, never `1:length(x)`.** When `x` is
  empty, `1:length(x)` is `c(1, 0)`, so the loop runs twice on nothing.
- **Use `vapply()` instead of `sapply()`.** `sapply()` returns a list or a
  vector depending on its input, and `vapply()` checks the type of every
  result: `vapply(files, file.size, numeric(1))`.

## Missing values

- **Test for `NA` with `is.na()`, never `== NA`.** Any comparison with `NA`
  gives `NA`, not `TRUE` or `FALSE`.
- Decide how each function handles `NA`, and document it. Pass `na.rm = TRUE`
  only when dropping missing values is correct for the analysis, not to make
  an error go away.
- In `if` conditions, guard values that may be `NA` with `isTRUE()` or
  `isFALSE()`. `if (NA)` is an error.
- Keep `NULL` (no value at all) and `NA` (a missing value within a vector)
  distinct. Test for `NULL` with `is.null()`.

## Errors and conditions

- **Check arguments at the top of every exported function**, and stop with a
  message that names the argument and what was wrong:

  ```r
  if (!is.data.frame(responses)) {
    stop("`responses` must be a data frame, not ", class(responses)[1])
  }
  ```

- Give errors a class when callers may want to handle them, so they can catch
  that error and nothing else:
  `stop(errorCondition("survey file not found", class = "survey_not_found"))`.
- Use `warning()` for results that are usable but suspect, and `message()`
  for progress notes. Never use `print()` or `cat()` for either, because
  callers can't suppress them.
- Handle conditions with `tryCatch()` and catch the specific class you
  expect. A handler for every error hides bugs.

## Cleanup and global state

- **Restore anything you change with `on.exit(..., add = TRUE)`**, so it's
  restored even when the function fails:

  ```r
  old <- options(digits = 3)
  on.exit(options(old), add = TRUE)
  ```

- Close every connection you open in the same function, with `on.exit()`.

## Reproducibility

- **Lock package versions with renv.** Commit `renv.lock`, so every machine
  and every CI run uses the same versions.
- **Set the random seed once, at the top of an analysis script**, with
  `set.seed()`. Never set a seed inside a package function: it changes the
  caller's random stream.
- Record the environment of every published result with `sessionInfo()`.
- Read data with explicit column types, so a change in the input file fails
  loudly instead of silently changing the types.

## Security

- **Never run code built from strings**, such as `eval(parse(text = input))`.
  Anyone who controls the string controls the program.
- **Never load `.rds` or `.RData` files from untrusted sources.** Loading
  them can run arbitrary code. Exchange data as CSV, JSON or Parquet instead.
- Call external programs with `system2()` and a vector of arguments, and
  quote any value from outside the program with `shQuote()`.
- Pass values to SQL as parameters, never by pasting them into the query:

  ```r
  rows <- DBI::dbGetQuery(
    con,
    "SELECT * FROM surveys WHERE id = ?",
    params = list(survey_id)
  )
  ```

## Testing

- Write tests with [testthat](https://testthat.r-lib.org/), one test file per
  source file.
- Keep functions pure where you can: the same inputs always give the same
  output, with no I/O. Pure functions need no fixtures to test.

## Performance

- Profile before optimising, with `Rprof()` or profvis, and optimise the part
  the profiler points at.
- Vectorise first. Most slow R code is a loop that a vectorised function
  would replace.

## Sources

- [R Packages (2e)](https://r-pkgs.org/), by Hadley Wickham and Jennifer
  Bryan
- [Advanced R (2e)](https://adv-r.hadley.nz/), by Hadley Wickham
  (conditions, functions and environments)
- [The R Inferno](https://www.burns-stat.com/documents/books/the-r-inferno/),
  by Patrick Burns
- [renv documentation](https://rstudio.github.io/renv/)
