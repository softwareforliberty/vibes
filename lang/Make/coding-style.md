# Make Coding Style

A general-purpose coding style for makefiles written for
[GNU Make](https://www.gnu.org/software/make/) 4.3 or later. It builds on the
GNU Make manual, the GNU Coding Standards and well-known practice from
long-lived FOSS projects (see [Sources](#sources)).

This guide covers how makefiles look. For how to structure a build
(dependencies, build directories, non-recursive make and other idioms), see
[idioms.md](idioms.md).

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [GNU Make](https://www.gnu.org/software/make/) 4.3 or later | GPLv3 | Building, and linting through its own warnings |

No well-maintained FOSS linter for makefiles exists, so none is listed.

### Make warnings

GNU Make's warning for undefined variables is the lint gate. It catches typos
in variable names, which Make otherwise expands silently to nothing. A
makefile must produce **no warnings** when dry-run with the check enabled:

```sh
make --warn-undefined-variables --dry-run all
```

- Newer GNU Make releases also spell this check `--warn=undefined-var`, and
  keep `--warn-undefined-variables` as an alias.
- The check only reports warnings, so CI fails the build when the output
  contains `warning:`.
- Define every variable the makefile reads, even as empty (`LDLIBS ?=`), so
  the check stays quiet for variables that are meant to be empty.
- macOS ships GNU Make 3.81, which is too old. Install a current GNU Make from
  a package manager.

## Files

- Name the main makefile `Makefile`, with a capital `M`, so it sorts near the
  top of a directory listing next to `README`.
- Name included fragments with a `.mk` extension: `src/module.mk`.
- Start every makefile with a comment saying what it builds and which GNU
  Make version it needs.

## Layout

### Order

Lay out a makefile in this order, so readers always know where to look:

1. The header comment.
2. Special targets and shell settings (`.DELETE_ON_ERROR`, `.SUFFIXES`,
   `SHELL`, `.SHELLFLAGS`).
3. Settings the user may override (`CC`, `CFLAGS`, `BUILD_DIR`, `prefix`).
4. Internal variables (source lists, derived flags).
5. The default target, `all`.
6. The other rules.
7. Generated dependency files (`-include $(deps)`), last.

### Indentation

- **Recipe lines start with exactly one tab.** Make requires it. Never change
  the recipe prefix with `.RECIPEPREFIX`, which surprises every reader and
  editor.
- **Never start any other line with a tab.** Make may read a tab-indented
  line as part of a recipe. Indent everything else with **4 spaces**.
- Indent the lines inside an `ifeq`/`ifdef` block by 4 spaces. Recipe lines
  inside a conditional still start with one tab.

### Line length and continuation

- **80 columns** is the preferred limit. You may go up to **100** only when
  that clearly reads better and hides nothing.
- **Never break user-visible strings** (messages, `$(error)` text) across
  lines, so they stay greppable.
- When a list doesn't fit on one line, put one item per line, each followed by
  ` \`, and indent the items by 4 spaces:

  ```make
  srcs := \
      src/buf.c \
      src/pipe.c \
      src/sync.c
  ```

  One item per line keeps diffs to one line per added or removed file.
- Continue a long recipe command with ` \`, and indent the continuation one
  more tab:

  ```make
  $(lib): $(objs)
  	$(quiet)rm -f $@
  	$(quiet)$(AR) rcs $@ \
  		$^
  ```

### Whitespace

- No trailing whitespace. Trailing spaces after a variable's value become
  part of the value.
- Don't use more than one blank line in a row. Put one blank line between
  rules.
- Use LF line endings, and end every file with a newline.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Settings the user may override, and the variables implicit rules use | `UPPER_SNAKE_CASE` | `CC`, `CFLAGS`, `LDLIBS`, `BUILD_DIR`, `V` |
| Installation directories | GNU's lowercase names | `prefix`, `bindir`, `libdir`, `includedir` |
| Internal variables | `snake_case` | `srcs`, `objs`, `all_cflags` |
| Functions defined with `define` | `snake_case` | `compile_rule` |
| Targets | lowercase, words separated by hyphens | `all`, `check`, `install`, `install-docs` |

- The case of a variable tells the reader who sets it: uppercase means "you
  may set this on the command line", lowercase means "the makefile owns this".
  The GNU Make manual recommends this split.
- Installation directories follow the GNU Coding Standards names, which
  packagers and distribution tools expect.
- Use the standard target names: `all`, `install`, `uninstall`, `clean`,
  `distclean` and `check`. Users and packaging tools run them without
  reading the makefile.

## Variables

- Put one space on each side of an assignment operator: `objs := ...`. Values
  in a block of related assignments may be lined up with spaces.
- Assign with **`:=` by default**. It expands the value once, at the point of
  assignment, like a variable in any other language. Use `=` only when the
  value must be expanded later, and add a comment saying why.
- Use `?=` only for settings the user may override.
- Use `+=` to add to a list.
- Reference variables as `$(name)`, never `${name}`, so every reference looks
  the same.
- Write single-character automatic variables without parentheses: `$@`, `$<`,
  `$^`, `$(@D)`.

## Function calls and conditionals

- **No spaces after the commas** in function calls and conditionals:
  `$(patsubst %.c,%.o,$(srcs))`, `ifeq ($(V),1)`. Make keeps spaces as part
  of the arguments, so `$(subst a, b,$(x))` replaces `a` with ` b`.
- Put one space between a function's name and its first argument:
  `$(filter %.c,$(files))`.
- Write conditionals as `ifeq (...)` / `else` / `endif`, with each directive
  at the start of its line:

  ```make
  ifeq ($(V),1)
      quiet :=
  else
      quiet := @
  endif
  ```

## Rules

- Put a `.PHONY` declaration directly above each phony target:

  ```make
  .PHONY: clean
  clean:
  	rm -rf $(BUILD_DIR)
  ```

- One rule per target. Write the target, a colon and a space, then its
  prerequisites. A long prerequisite list continues with ` \`, like any other
  list.
- **Use automatic variables in recipes** (`$@`, `$<`, `$^`) instead of
  repeating file names. The recipe then can't drift out of sync with the
  rule's target and prerequisites.
- Write one command per recipe line. Make runs each line in a separate shell,
  so a `cd` on one line has no effect on the next.

## Echoing commands

- **Don't hide commands unconditionally.** Prefix them with `$(quiet)`, which
  is `@` normally and empty when the user builds with `make V=1`. Silent
  commands make a failing build hard to debug.
- Use a bare `@` only for commands whose output is the whole point, such as
  `@echo` in a `help` target.

## Comments

- Use `#` comments, with a space after the `#`.
- **Don't put comments inside recipes.** A `#` line inside a recipe is passed
  to the shell and echoed in the build output. Put the comment above the
  rule instead.
- Comments explain **why** the build does something. A comment above a rule
  that only repeats the rule's target adds nothing.
- Explain every non-obvious setting, especially `=` assignments, order-only
  prerequisites and anything that works around a tool's bug.

## Third-party code

Vendored third-party makefiles keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

This guide builds on:

- [GNU Make manual](https://www.gnu.org/software/make/manual/)
- [GNU Coding Standards: Makefile Conventions](https://www.gnu.org/prep/standards/html_node/Makefile-Conventions.html)
- [Paul Smith's Rules of Makefiles](https://make.mad-scientist.net/papers/rules-of-makefiles/)
