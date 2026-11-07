# Fortran Idioms and Principles

How to write Fortran well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Fortran code correct, fast and maintainable. Every example follows the
style guide.

## Principles

- **Let the compiler check everything it can.** Modules, explicit
  interfaces, `implicit none` and `intent` turn whole classes of bugs into
  compile errors.
- **Every resource has one owner.** Prefer allocatable arrays, which the
  language frees automatically, over pointers, which it doesn't.
- **Fail early and report it.** Fortran has no exceptions, so every procedure
  that can fail returns a status, and every caller checks it.
- **Write to the standard.** Compiler extensions tie the code to one
  compiler.
- **Respect memory order.** Fortran arrays are column-major. Code that walks
  them in the right order is many times faster.

## Modules

- **Put every procedure in a module.** A module gives each procedure an
  explicit interface, so the compiler checks every call's arguments.
  External procedures get no such check.
- Make module contents `private` by default, and mark the public API
  explicitly:

  ```fortran
  module linalg
      use, intrinsic :: iso_fortran_env, only: dp => real64
      implicit none
      private

      public :: solve_system
  contains
      ...
  end module linalg
  ```

- Import names explicitly with `use ..., only:`, so every name has a visible
  source and nothing leaks in.
- Never use `common` blocks or `include` files to share data. Use module
  variables, and keep even those to a minimum.

## Arguments

- Give every dummy argument an `intent`: `in`, `out` or `inout`. The compiler
  then rejects writes to inputs.
- Take arrays as assumed shape (`real(dp), intent(in) :: x(:)`), so the size
  travels with the array and needs no extra argument.
- Remember that `intent(out)` deallocates allocatable arguments on entry and
  leaves other arguments undefined. Use `intent(inout)` if the procedure
  reads the old value.
- Mark optional arguments `optional` and test them with `present()` before
  use.
- **Never pass the same variable as two arguments if the procedure modifies
  either.** The standard forbids that aliasing, and the compiler optimises on
  the assumption it can't happen.

## Kinds and precision

- Define kind parameters once, in one module, from `iso_fortran_env`, and use
  them everywhere.
- Give every real literal its kind (`0.1_dp`). Mixing single-precision
  literals into double-precision code silently loses precision.
- Make conversions explicit with `real(n, dp)` and `int(x)`, so a reader sees
  each one.

## Memory

- **Use allocatable arrays instead of pointers.** Allocatables can't alias,
  can't dangle, and are freed automatically when they go out of scope.
- Check every allocation with `stat=`, and report the failure:

  ```fortran
  allocate(work(n), stat=stat, errmsg=errmsg)
  if (stat /= 0) return
  ```

- Use `move_alloc()` to transfer an allocation without copying it.
- Use pointers only for structures that really need them, such as linked
  lists, and give their targets the `target` attribute.
- Don't put large arrays on the stack as automatic arrays. A big automatic
  array can overflow the stack with no useful error. Make them allocatable.

## Procedures

- Mark procedures `pure` when they have no side effects, and `elemental` when
  they apply element by element. The compiler checks the promise, and it
  lets the procedure be used in more places.
- Prefer whole-array operations (`c = a + b`) to explicit loops when they're
  clearer. They say what's computed, not how.
- When you loop over a 2D array, put the first index in the innermost loop,
  because Fortran stores columns contiguously:

  ```fortran
  do j = 1, n_cols
      do i = 1, n_rows
          total = total + matrix(i, j)
      end do
  end do
  ```

## Error handling

- A procedure that can fail takes an `integer, intent(out) :: stat`, and
  optionally a `character(len=:), allocatable, intent(out) :: errmsg`. Set
  `stat` to 0 on success. This mirrors the intrinsics' own `stat=` and
  `iostat=` arguments.
- Check `iostat=` on every `open`, `read`, `write` and `close`.
- Never use `stop` or `error stop` in library code. Only a main program
  decides when the program ends.

## Derived types

- Group related data into derived types, and bind the procedures that work
  on them as type-bound procedures.
- Give types that own resources a `final` procedure to release them.
- Avoid unlimited polymorphic `class(*)` except for truly generic
  containers. Every use needs a `select type`, which defeats the compiler's
  checks.

## Interoperating with C

- Use `iso_c_binding` and `bind(c)` for every procedure called from C or
  calling into it. Without them, name mangling and argument passing are
  compiler-specific.
- Give each exported procedure the same name C uses, following the
  [C naming rules](../C/coding-style.md#naming): a module prefix and
  `snake_case`, as in `bind(c, name="linalg_solve")`.
- Use `c_int`, `c_double`, `c_ptr` and the other interoperable kinds for
  every argument, and `value` for arguments C passes by value.
- Return errors the way C expects: `0` for success, or a negative errno code,
  as in the [C idioms](../C/idioms.md#error-handling).
- Strings passed to C must end with `c_null_char`.

## Testing

- Test through the public API of each module, with
  [fpm](https://fpm.fortran-lang.org/)'s `fpm test` or a test program per
  module.
- Run tests with the compiler's runtime checks turned on (see
  [tools.md](tools.md#compiler-warnings)). Bounds and shape errors that pass
  silently in an optimised build fail immediately there.

## Performance

- Profile before optimising, and optimise the part the profiler points at.
- Watch for hidden array temporaries, which gfortran's
  `-Warray-temporaries` reports. Passing a non-contiguous section to an
  explicit-shape argument copies it on every call.
- **Read and write large data unformatted,** with `access='stream'` and
  `form='unformatted'`, a whole array per statement. Formatted I/O converts
  every value to and from text, which is far slower.

## Sources

- [fortran-lang.org: Fortran Best Practices](https://fortran-lang.org/learn/best_practices/)
- [GNU Fortran manual: Interoperability with C](https://gcc.gnu.org/onlinedocs/gfortran/Interoperability-with-C.html)
- [fpm documentation](https://fpm.fortran-lang.org/)
- ISO/IEC 1539-1:2018, the Fortran 2018 standard
