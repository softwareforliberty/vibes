# COBOL Idioms and Principles

How to write COBOL well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep COBOL code correct, auditable and maintainable. Every example follows
the style guide.

## Principles

- **Structure the control flow.** Every paragraph has one entry and one exit,
  and the program reads top-down. Unstructured jumps make a program
  impossible to follow.
- **Define data once.** A record layout lives in one copybook that every
  program shares, so the layouts can't drift apart.
- **Money is decimal.** Use fixed-point decimal types for every amount, with
  explicit rounding. Binary floating point can't represent most decimal
  fractions exactly.
- **Check every result.** Every file operation and every arithmetic
  statement that can overflow is checked where it happens.
- **Validate input before using it.** A non-numeric value in a numeric field
  can stop the program, or silently corrupt a total.

## Program structure

- Give each program a main paragraph that reads like a summary: it
  `PERFORM`s the other paragraphs in order, then ends with `GOBACK`:

  ```cobol
         0000-MAIN.
             PERFORM 1000-OPEN-FILES
             PERFORM 2000-PROCESS-CUSTOMER
                 UNTIL WS-END-OF-CUSTOMERS
             PERFORM 9000-CLOSE-FILES
             GOBACK.
  ```

- **Use `PERFORM`, never `GO TO`.** A `PERFORM`ed paragraph always returns,
  and `GO TO` doesn't, so control flow can no longer be read top-down.
- Never use `ALTER`, which changes where a `GO TO` jumps at run time, or
  `PERFORM ... THRU`, which runs every paragraph between two names, including
  any added later.
- Use `CONTINUE` for an empty branch, never `NEXT SENTENCE`. `NEXT SENTENCE`
  jumps past the next period, which may be far below.
- End programs with `GOBACK`, not `STOP RUN`. `GOBACK` returns to the caller
  when the program is called, and ends the run when it's the main program.
- Use `EVALUATE` instead of nested `IF`s when there are more than two cases:

  ```cobol
             EVALUATE TRUE
                 WHEN CUST-IS-ACTIVE
                     PERFORM 2200-BILL-CUSTOMER
                 WHEN CUST-IS-SUSPENDED
                     PERFORM 2300-SEND-REMINDER
                 WHEN OTHER
                     PERFORM 8000-REPORT-BAD-STATUS
             END-EVALUATE
  ```

## Data design

- **Keep every shared record layout in a copybook**, and `COPY` it wherever
  it's used.
- **Use level-88 condition names instead of comparing to literals.**
  `IF CUST-IS-ACTIVE` says what's being tested, and the literal is defined in
  one place.
- Set condition names with `SET ... TO TRUE`, rather than moving the literal
  into the field.
- Give signed numeric fields an `S` in their picture. Without it, a negative
  result silently loses its sign.
- Use `REDEFINES` sparingly, and only when the record has a field that says
  which layout applies. Reading through the wrong layout gives garbage.
- Initialise working storage with `VALUE` clauses or `INITIALIZE`. Don't rely
  on fields being zero or spaces at startup.

## Decimal arithmetic

- **Store money as packed decimal** (`COMP-3`) or display numeric fields,
  with the decimal places in the picture: `PIC S9(11)V99 COMP-3`. Never use
  the floating-point types `COMP-1` and `COMP-2` for money.
- Add `ROUNDED` to every calculation whose result has fewer decimal places
  than its inputs. Without it, the result is truncated.
- Add `ON SIZE ERROR` to every calculation whose result could overflow the
  receiving field. Without it, the high-order digits are silently lost:

  ```cobol
             COMPUTE WS-BALANCE-TOTAL ROUNDED =
                 WS-BALANCE-TOTAL + CUST-BALANCE
                 ON SIZE ERROR
                     PERFORM 8100-REPORT-OVERFLOW
             END-COMPUTE
  ```

## Validating input

- Test every numeric field read from outside the program with `IS NUMERIC`
  before any arithmetic uses it.
- Check ranges and codes against level-88 condition names, so every valid
  value is listed in one place.

## Files

- **Give every file a `FILE STATUS`**, and check it after every `OPEN`,
  `READ`, `WRITE`, `REWRITE` and `CLOSE`. Define condition names for the
  status codes you expect:

  ```cobol
             SELECT CUSTOMER-FILE ASSIGN TO "customers.dat"
                 ORGANIZATION IS LINE SEQUENTIAL
                 FILE STATUS IS WS-CUSTOMER-STATUS.
  ```

- Close every file the program opened, on every path, including errors.
- Treat any status you didn't expect as an error, and report the file name
  and the status code.

## Errors and return codes

- Report a program's result to its caller in `RETURN-CODE`: 0 for success,
  and a documented nonzero code for each kind of failure.
- Handle errors in the program that can do something about them. Lower-level
  programs set a return code and `GOBACK`.

## Strings

- Use `STRING` and `UNSTRING` with `ON OVERFLOW`, so a result too long for
  its receiving field is caught instead of silently cut short.
- Check the bounds of every reference modification (`WS-NAME(start:length)`).
  An out-of-range reference reads or overwrites neighbouring fields.

## Calling other programs

- Pass arguments `BY CONTENT` unless the called program must change them.
  `BY REFERENCE` lets it change the caller's data.
- Declare the receiving fields in the called program's `LINKAGE SECTION` with
  the same copybook the caller uses.
- When calling C from GnuCOBOL, pass C's scalar arguments `BY VALUE`, and
  follow the C function's conventions: `0` for success, or a negative errno
  code, as in the [C idioms](../C/idioms.md#error-handling).

## Security

- Embedded SQL must use host variables for every value, never SQL text built
  from input. That's the only defence against SQL injection.
- Never build a command line for `CALL "SYSTEM"` from input.
- Keep credentials out of source and copybooks. Read them from the
  environment at run time.

## Testing

- Test each program through its interface: its files, its linkage section and
  its return code.
- Run tests on a build with GnuCOBOL's runtime checks (see
  [tools.md](tools.md#compiler-warnings)), which stop on out-of-range
  subscripts and invalid numeric data instead of continuing with bad values.

## Sources

- [GnuCOBOL Programmer's Guide](https://gnucobol.sourceforge.io/guides.html)
- [GnuCOBOL FAQ](https://gnucobol.sourceforge.io/faq/index.html)
- ISO/IEC 1989:2014, the COBOL 2014 standard
