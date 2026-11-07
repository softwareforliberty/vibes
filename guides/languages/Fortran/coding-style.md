# Fortran Coding Style

A general-purpose coding style for modern Fortran projects. It builds on the
[Fortran best practices](https://fortran-lang.org/learn/best_practices/)
published by fortran-lang.org, and on the Fortran 2018 standard (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(modules, argument intent, memory, error handling, C interoperability and
other idioms), see [idioms.md](idioms.md).

The tools that check Fortran code are listed in [tools.md](tools.md).

## Language baseline

Code targets **Fortran 2018**, compiled with `-std=f2018`. Every feature this
guide relies on, such as `implicit none`, modules, allocatable arrays and
`iso_c_binding`, is standard, so the code builds with any conforming
compiler.

## Files

- Write free-form source with a `.f90` extension, whatever standard the code
  uses. `.f90` means "free form", not "Fortran 90", and every compiler
  recognises it.
- Put one module in each file, and name the file after the module:
  `linalg.f90` holds `module linalg`.
- Use lowercase `snake_case` file names, UTF-8 and LF line endings, and end
  every file with a newline.

## Layout

### Indentation

- Indent with **4 spaces**. Never use tabs, which the standard doesn't allow
  in source.
- Indent the body of every program unit, procedure and construct (`do`, `if`,
  `select case`, `block`, `associate`) one level.

### Line length

- Keep lines to **100 columns**. The standard allows 132, but shorter lines
  fit side-by-side diffs and review.
- Never break a user-visible string across lines, so it stays greppable.

### Continuation

End a continued line with `&`, and indent the continuation one level:

```fortran
call solve_system(matrix, rhs, solution, &
    tolerance=1.0e-10_dp, max_iterations=500)
```

### One thing per line

- One statement per line. Never join statements with `;`.
- Declare one variable per line, so each can have its own comment and
  attributes.

## Case

Write everything in lowercase: keywords, intrinsics and names. Fortran is
case-insensitive, so case can't carry meaning, and lowercase is easiest to
read.

## Naming

- Use `snake_case` for modules, procedures, variables and constants.
- Name procedures with verbs (`solve_system`) and data with nouns
  (`residual`).
- Name derived types with a `_type` suffix (`matrix_type`), so a type and a
  variable of that type can share a stem: `type(matrix_type) :: matrix`.
- Name kind parameters after what they mean, such as `dp` for double
  precision, and declare them once in a module that everything uses.

## Declarations

- Put `implicit none` in every module and program. Procedures inside a
  module inherit it.
- Use `::` in every declaration, with a space on each side.
- Give every dummy argument an `intent`.
- Use kind parameters from `iso_fortran_env` for every real and integer kind:
  `real(dp)`, never `real*8` or `double precision`.
- Give every real literal its kind: `0.1_dp`. A plain `0.1` is single
  precision, even when assigned to a double.

## Statements

- Close every construct with its full name: `end subroutine solve_system`,
  `end module linalg`, `end do`, `end if`.
- Use the symbolic comparison operators (`==`, `/=`, `<`, `<=`, `>`, `>=`)
  instead of `.eq.`, `.ne.` and the rest.
- Quote character strings with double quotes: `"tests: passed"`.
- Never use `goto`, arithmetic `if`, `common` blocks, `equivalence`,
  statement functions or fixed-form source. Each has a modern replacement
  that the compiler can check.
- Name long or nested loops, so `exit` and `cycle` say which loop they leave:
  `rows: do i = 1, n_rows`.

## Spacing

- Put spaces around assignment, relational and logical operators, and around
  binary arithmetic operators except `**`: `area = pi * radius**2 + margin`.
- Put no spaces around `=` in keyword arguments: `tolerance=1.0e-10_dp`.
- Put a space after every comma, and none just inside parentheses.

## Comments

- Start each comment with `! ` and write it as a sentence. Explain **why**,
  not **what**.
- Document every public procedure and type with a comment block directly
  above it, using [FORD](https://github.com/Fortran-FOSS-Programmers/ford)'s
  `!>` markers, so the documentation can be generated:

  ```fortran
  !> Solve the linear system matrix * x = rhs by LU decomposition.
  !> stat is 0 on success, or nonzero if the matrix is singular.
  subroutine solve_system(matrix, rhs, x, stat)
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [fortran-lang.org: Fortran Best Practices](https://fortran-lang.org/learn/best_practices/)
- [GNU Fortran manual](https://gcc.gnu.org/onlinedocs/gfortran/)
- [FORD documentation](https://forddocs.readthedocs.io/)
- ISO/IEC 1539-1:2018, the Fortran 2018 standard
