# Perl Idioms and Principles

How to write Perl well. [coding-style.md](coding-style.md) covers how code
looks. This guide covers how it's designed: the idioms and principles that
keep Perl code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Clarity beats cleverness.** Perl lets you say almost anything in one
  line. Write the version the next reader understands without `perldoc`.
- **Fail loudly.** Check every call that can fail, and die with a message
  that says what went wrong and with which input.
- **Keep scope small.** Every variable is `my`, and lives in the narrowest
  block that works.
- **Never trust input.** Data from users, files, the environment or the
  network is checked before it reaches a command, a file path or a query.
- **Use CPAN, carefully.** A well-maintained module beats a hand-rolled
  parser, but every dependency is code you must keep up to date.

## Modules and packages

- **One package per file**, at the path matching its name, with an explicit
  export list. Export nothing by default: use `@EXPORT_OK` so callers name
  what they import:

  ```perl
  package My::App::Text;
  use v5.36;

  use Exporter 'import';
  our @EXPORT_OK = qw(slugify);
  ```

- **Importing a module must have no side effects.** Don't open files or
  connect at load time; do that work in a subroutine the caller runs.
- **Write objects as blessed hash references** with an explicit
  constructor, or use a well-maintained object system such as
  [Moo](https://metacpan.org/pod/Moo) when the project already depends on
  one. Don't mix the two styles in one project.

## Errors

- **Die on failure, with context.** `die` with a message naming the
  operation and its input. End the message without a newline so Perl adds
  the file and line, or with one when the location would only confuse a
  user:

  ```perl
  open(my $fh, '<', $path) or die "Cannot open '$path': $!";
  ```

- **Catch errors with `try`/`catch`** from the
  [Try::Tiny](https://metacpan.org/pod/Try::Tiny) module, or with
  `eval { ...; 1 } or do { ... }`. Never test `$@` after a bare `eval`: a
  destructor can clear it, so the failure looks like success.
- **Throw exception objects when callers need to tell errors apart.** A
  class per error kind can be checked with `isa`; a string can only be
  matched with a regex.
- **Use `autodie`** in scripts that do a lot of file and process work. It
  makes `open`, `close`, `unlink` and the rest die on failure, so no check
  is forgotten.
- **Catch errors only where something can be done about them**: retry,
  fall back, or report to the user. Lower levels let them propagate.

## Files and I/O

- **Use lexical filehandles and the three-argument `open`.** A lexical
  handle closes itself when it goes out of scope, and the three-argument
  form never treats part of the file name as a mode:

  ```perl
  open(my $fh, '<:encoding(UTF-8)', $path)
      or die "Cannot open '$path': $!";
  ```

- **Never use bareword filehandles** (`open(FH, ...)`). They're package
  globals shared by every caller.
- **State the encoding on every handle** with an `:encoding(...)` layer, and
  `use utf8;` in source files that contain non-ASCII text. Perl otherwise
  treats text as bytes.
- **Check `close` on files you write.** A full disk is often reported only
  when the buffer is flushed.

## References and data structures

- **Build nested data with references:** `my %users = (ada => { age => 36 })`.
  Use the arrow to reach into them: `$users{ada}{age}`.
- **Use postfix dereference** for whole structures: `$users->@*`,
  `$config->%*`. It reads left to right, unlike the `@{$users}` form.
- **Copy deliberately.** Assigning a reference shares the data. Use
  [Storable](https://metacpan.org/pod/Storable)'s `dclone` for a deep copy.
- **Pass and return references for large or structured data.** Passing an
  array flattens it into the argument list and loses its boundaries.
- **Check `ref` or use `Scalar::Util`'s `reftype`/`blessed`** before
  dereferencing data that might not be the type you expect.

## Lists and context

- **Know the context.** The same expression returns different things in
  list and scalar context: `my $count = @items` gives the count, but
  `my ($first) = @items` gives the first element.
- **Return a list or `return;` on failure, never `return undef;`** from a
  subroutine called in list context. `undef` in list context is a
  one-element list, which is true.
- **Use `map` and `grep` for transformations**, and a `foreach` loop for
  anything with side effects.

## Security

- **Run with taint mode (`-T`) for programs that handle untrusted input**,
  such as CGI scripts and setuid tools. Perl then refuses to pass tainted
  data to the shell, the file system or `eval` until it's been checked
  against a regex.
- **Never use string `eval`.** It compiles and runs whatever the string
  contains. Use block `eval` (or `try`) to catch errors, and dispatch tables
  instead of building code.
- **Never pass a single string to `system` or `exec`** when any part comes
  from input. Pass a list, so no shell is involved:

  ```perl
  system('git', 'log', '--', $path) == 0
      or die "git log failed: $?";
  ```

- **Use placeholders for every SQL query** through DBI. Never interpolate
  values into SQL.
- **Validate file paths** before opening them, and reject `..` and absolute
  paths in user-supplied names.

## Dependencies

- **List every dependency in a `cpanfile`** with a minimum version, and pin
  exact versions for applications in a lockfile (`cpanfile.snapshot`).
  Builds then install the same code everywhere.
- **Prefer core and widely used modules.** Check a module's maintenance and
  open issues before adding it.

## Testable design

- **Write tests with [Test2](https://metacpan.org/pod/Test2::V0)** or
  Test::More in `t/`, and run them with `prove -lr t`.
- **Pass dependencies in.** A subroutine that takes its clock, file handle
  or user agent as an argument can be tested with a stub.
- **Keep I/O at the edges.** Pure subroutines that transform data are easy
  to test; the code that reads and writes stays thin.

## Performance

- **Measure before optimising**, with
  [Devel::NYTProf](https://metacpan.org/pod/Devel::NYTProf).
- **Precompile regexes used in loops** with `qr//`, and avoid capturing
  groups you don't use.
- **Use a hash for lookups**, not `grep` over an array.
- **Stream large input** with `while (my $line = <$fh>)`. Reading `<$fh>` in
  list context reads the whole file into memory.
- **Memory-map a large file that's read at random positions or many times**
  with `File::Map`'s `map_file`. Don't map a file you read once from start to
  end, where buffered reads are as fast and simpler, or one that another
  process may shrink while it's mapped, which can crash the program.

## Sources

- [perlstyle](https://perldoc.perl.org/perlstyle)
- [perlsec](https://perldoc.perl.org/perlsec) (taint mode)
- [perlfunc: open](https://perldoc.perl.org/functions/open)
- [perlref](https://perldoc.perl.org/perlref)
- [Perl::Critic](https://metacpan.org/pod/Perl::Critic) policies
