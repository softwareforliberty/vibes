# Perl Coding Style

A general-purpose coding style for Perl 5 projects. It builds on
[perlstyle](https://perldoc.perl.org/perlstyle) and the *Perl Best Practices*
guidelines as implemented by
[Perl::Critic](https://metacpan.org/pod/Perl::Critic), with the layout fixed
by [perltidy](https://metacpan.org/pod/Perl::Tidy) (see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it
(errors, files, references, security and other idioms), see
[idioms.md](idioms.md).

The tools that check Perl code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **Perl 5.36**. Every file starts with:

```perl
use v5.36;
```

That one line turns on `strict`, `warnings` and subroutine signatures, and
turns off indirect method syntax. It replaces the separate `use strict;` and
`use warnings;` lines older code needs.

## Layout

### Indentation

- Indent with **4 spaces**. Never use tabs.
- Indent continuation lines by 4 more spaces than the line they continue.
- When a call or data structure doesn't fit on one line, put one item per
  line and end with a trailing comma. Adding an item then changes only one
  line in a diff:

  ```perl
  my %user = (
      name  => $name,
      email => $email,
      roles => ['admin'],
  );
  ```

### Line length

- Lines are at most **78 characters**. perltidy enforces it.
- **Never break user-visible strings** (messages, log lines) across lines,
  so they stay greppable.

### Files

- Use UTF-8, LF line endings, and end every file with a newline.
- No trailing whitespace.
- Scripts use the `.pl` extension, modules `.pm` and tests `.t`. A module's
  path matches its package name: `My::App::UserStore` lives in
  `lib/My/App/UserStore.pm`.
- Scripts start with `#!/usr/bin/env perl`.
- Every module ends with `1;` before any `__END__` marker. `require`
  fails when a module's last statement returns a false value.

### One thing per line

- One statement per line.
- Put the body of a block on its own lines. Postfix conditions
  (`return if $done;`) are fine for a single simple statement.

## Braces

- The opening brace goes on the same line as its keyword or `sub`:

  ```perl
  sub find_user ($self, $id) {
      return $self->{users}{$id};
  }
  ```

- `else` and `elsif` go on a new line after the closing brace (the
  "uncuddled" form), so each branch keyword starts its own line:

  ```perl
  if ($user) {
      greet($user);
  }
  else {
      register();
  }
  ```

## Whitespace

- One space around binary operators, including `=`, `=>` and `.`:
  `$total = $price * $count`.
- No space between a function name and its opening parenthesis:
  `find_user($id)`.
- One space between a keyword and its parenthesis: `if ($x)`,
  `foreach my $item (@items)`.
- One space after a comma, none before it.
- Line up `=>` in a block of key-value pairs. perltidy does this for you.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Variables and subroutines | `snake_case` | `$retry_count`, `load_config` |
| Packages | `CamelCase` segments joined by `::` | `My::App::UserStore` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRIES` |
| Private subroutines and methods | Leading underscore | `_parse_header` |

- Name arrays and hashes in the plural (`@users`), and scalars in the
  singular (`$user`).
- Name boolean variables and predicate subroutines as questions:
  `$is_ready`, `has_access()`.
- Use inclusive terms. Say primary/secondary, controller/device or
  leader/follower instead of master/slave, and allowlist/denylist instead of
  whitelist/blacklist. The only exceptions are names fixed by an external
  API or protocol.

## Variables

- Declare every variable with `my`, where it's first needed, in the
  narrowest scope that works. `use v5.36` makes undeclared variables an
  error.
- Don't use package variables (`our`) except for the few that Perl's own
  machinery reads, such as `@ISA` and `$VERSION`.
- Use only the common punctuation variables (`$_`, `@_`, `$@`, `$!`,
  `$0`). When you must change another one, such as `$/`, do it with `local`
  in the smallest block that works, and comment why.

## Subroutines

- Use **signatures** for parameters. They state the arguments in one place
  and check how many were passed:

  ```perl
  sub fetch_user ($id, %options) {
      my $timeout = $options{timeout} // 5;
      ...
  }
  ```

- Don't use prototypes. They change how arguments are parsed at the call
  site and surprise readers.
- Always end a subroutine with an explicit `return`. Otherwise the value of
  the last statement leaks out to the caller.
- Call subroutines with parentheses, and never with a leading `&`. The `&`
  form bypasses signatures and passes on the caller's `@_`.

## Strings

- Use **single quotes** for strings that don't interpolate, and double
  quotes only when they do. The quote then tells the reader whether to look
  for variables.
- Use `qw()` for lists of words: `my @fields = qw(name email role);`.
- Use a here-doc with the `<<~` form for multi-line text, so it can be
  indented with the code.

## Regular expressions

- Use the `/x` flag for any pattern longer than a few characters, and lay
  it out over several lines with comments.
- Use `{}` as the delimiter when the pattern contains `/`:
  `m{^/users/(\d+)$}`.
- Name captures that the code uses: `(?<id>\d+)`, then `$+{id}`.

## Comments and documentation

- Comments start with `# ` (hash and one space).
- Comments explain **why**, not **what**. The code already says what it
  does.
- Document every module with POD after the `__END__` marker: `NAME`,
  `SYNOPSIS`, `DESCRIPTION`, and a section per public subroutine.
- Don't leave commented-out code. Version control keeps the history.

## Third-party code

Vendored third-party sources keep their upstream style and are excluded from
formatting and linting, so updates from upstream stay easy to merge.

## Sources

This guide starts from perlstyle and borrows from:

- [perlstyle](https://perldoc.perl.org/perlstyle)
- [Perl::Critic](https://metacpan.org/pod/Perl::Critic), which implements
  the *Perl Best Practices* guidelines
- [perltidy](https://metacpan.org/pod/Perl::Tidy)
- [perlsub: Signatures](https://perldoc.perl.org/perlsub#Signatures)
- [perlpod](https://perldoc.perl.org/perlpod)
