# Make Idioms and Principles

How to write GNU makefiles well. [coding-style.md](coding-style.md) covers
how makefiles look. This guide covers how a build is structured: an accurate
dependency graph, build directories, flags, and the idioms that keep builds
correct, fast and parallel-safe. Every example follows the style guide.

## Principles

- **The dependency graph must be complete.** Make rebuilds a file only when
  it knows what the file depends on. A missing dependency means a stale build
  that looks fine until it ships.
- **Every rule creates exactly its target.** A rule's recipe writes the file
  named by `$@`, and nothing else. Make can't track files a rule creates
  behind its back.
- **One Make, one graph.** Build the whole project from a single `make`
  invocation that sees every dependency, rather than running Make again in
  each directory.
- **Builds work in parallel.** A makefile that only works with `-j1` has a
  missing dependency. Build with `-j` everywhere, including CI.
- **The source tree stays clean.** Every generated file goes into a build
  directory, which `make clean` deletes in one step.

## The standard header

Start every makefile with these settings:

```make
# Builds libbuf and its tests. Requires GNU Make 4.3 or later.

.DELETE_ON_ERROR:
.SUFFIXES:
SHELL := /bin/sh
.SHELLFLAGS := -eu -c
```

- `.DELETE_ON_ERROR` deletes a target whose recipe fails. Otherwise a
  half-written file has a fresh timestamp, and the next `make` treats it as up
  to date.
- `.SUFFIXES:` with nothing after it turns off Make's old suffix rules, so
  only the rules the makefile defines can build anything.
- `SHELL := /bin/sh` runs recipes with the POSIX shell. Recipes follow the
  [SH coding style](../SH/coding-style.md), not Bash, so they work on every
  system.
- `.SHELLFLAGS := -eu -c` makes the shell stop at the first failing command in
  a multi-command line, and treat unset shell variables as errors.

## Variables and flags

- **Keep the flags the build needs separate from the user's flags.** Users
  expect to set `CFLAGS` freely, for example to change optimisation, without
  breaking the build. Put the flags that must always be there in internal
  variables, and append the user's flags after them:

  ```make
  CPPFLAGS ?=
  CFLAGS   ?= -O2 -g

  all_cppflags := -Iinclude $(CPPFLAGS)
  all_cflags   := -std=c99 -Wall -Wextra -Wvla $(CFLAGS)
  ```

- Don't set `CC`, `AR` or the other variables Make predefines with `?=`. They
  already have defaults (`cc`, `ar`), so `?=` never takes effect. Users set
  them on the command line: `make CC=clang`.
- **Don't add `-Werror` by default.** A newer compiler adds warnings, and a
  hard-coded `-Werror` breaks the build for every user who has it. Add it
  behind a switch that CI turns on:

  ```make
  WERROR ?= 0

  ifeq ($(WERROR),1)
      all_cflags += -Werror
  endif
  ```

- Never call `$(shell ...)` in a variable assigned with `=`. It reruns the
  command every time the variable is expanded, which can be thousands of
  times. Assign it with `:=`, so it runs once.

## Pattern rules and automatic dependencies

Compile every source file with one pattern rule, and have the compiler write
the list of headers each object depends on:

```make
srcs := src/buf.c src/pipe.c
objs := $(srcs:%.c=$(BUILD_DIR)/%.o)
deps := $(objs:.o=.d)

$(BUILD_DIR)/%.o: %.c
	$(quiet)mkdir -p $(@D)
	$(quiet)$(CC) $(all_cppflags) $(all_cflags) -MMD -MP -c -o $@ $<

-include $(deps)
```

- `-MMD` writes a `.d` file next to each object, listing the headers it
  included. Including those files tells Make to rebuild an object when any of
  its headers changes, with no hand-written header lists to go stale.
- `-MP` adds an empty rule for each header, so deleting or renaming a header
  doesn't stop the build with "no rule to make target".
- `-include` (with the leading `-`) skips `.d` files that don't exist yet,
  as on the first build.
- Put the `-include` at the end of the makefile, so the rules it adds can't
  become the default target.

## Build directories

- **Write every generated file under `$(BUILD_DIR)`**, which defaults to
  `build`. Mirror the source tree's layout under it, so two source files with
  the same name in different directories can't collide.
- Create directories in the recipe that needs them, with `mkdir -p $(@D)`.
  `$(@D)` is the directory part of the target, and `mkdir -p` is safe when
  several parallel jobs create the same directory.
- `make clean` deletes `$(BUILD_DIR)` and nothing else.

## Order-only prerequisites

A prerequisite after a `|` must exist before the target is built, but doesn't
make the target out of date when it changes. Use one for a generated header
that every object needs before its first compile:

```make
gen_dir := $(BUILD_DIR)/gen

$(objs): | $(gen_dir)/version.h

$(gen_dir)/version.h: VERSION
	$(quiet)mkdir -p $(@D)
	$(quiet)printf '#define BUF_VERSION "%s"\n' "$$(cat $<)" > $@
```

After the first build, the `.d` files list `version.h` for every object that
really includes it, so only those objects rebuild when it changes.

## Targets with several outputs

When one command creates several files, declare them as a **grouped target**
with `&:`, so Make knows a single run creates all of them:

```make
$(gen_dir)/parser.c $(gen_dir)/parser.h &: src/parser.y
	$(quiet)mkdir -p $(@D)
	$(quiet)bison -o $(gen_dir)/parser.c --header=$(gen_dir)/parser.h $<
```

Without `&:`, Make treats the line as one rule per file, and a parallel build
may run the command twice at the same time. In a grouped target's recipe, `$@`
names only the output that triggered the run, so name each output
explicitly.

## Non-recursive make

Running Make again in each subdirectory (`$(MAKE) -C src`) splits the
dependency graph into pieces that can't see each other. A change in one
directory then fails to rebuild what depends on it in another. Instead,
**include a fragment from each directory into one makefile**:

```make
# Makefile
srcs :=
tests :=

include src/module.mk
include tests/module.mk
```

```make
# src/module.mk
srcs += \
    src/buf.c \
    src/pipe.c
```

- Write every path in a fragment relative to the top-level directory, where
  Make runs.
- A fragment only adds to lists and defines rules. It never sets shared
  settings, which belong to the top-level makefile.
- If a recipe must run Make again (for example, to build a vendored project
  that has its own makefile), call it as `$(MAKE)`, never `make`, so it
  inherits the command-line flags and shares the parallel job slots.

## Phony targets

- Declare every target that doesn't name a file as `.PHONY`. Otherwise a file
  that happens to have the target's name (a directory called `check`, say)
  stops the target from ever running.
- Never make a real file depend on a phony target. A phony target always
  counts as out of date, so the file would rebuild on every run.

## Installing

Follow the GNU conventions, so packagers can install into a staging
directory without editing the makefile:

```make
DESTDIR    ?=
prefix     ?= /usr/local
libdir     ?= $(prefix)/lib
includedir ?= $(prefix)/include

.PHONY: install
install: $(lib)
	$(quiet)mkdir -p $(DESTDIR)$(libdir) $(DESTDIR)$(includedir)
	$(quiet)cp $(lib) $(DESTDIR)$(libdir)/
	$(quiet)cp include/buf.h $(DESTDIR)$(includedir)/
```

- `prefix` and the directories built from it are where the files will live
  when the program runs. `DESTDIR` is a staging root prepended at install
  time only. Never bake `DESTDIR` into the program.
- Never install from the `all` target, and never need root to run `make`.

## Testing

- Run the tests with `make check`, the GNU standard target name. `check`
  depends on everything it tests, so it always tests a current build.
- Build the tests in CI with `-j` and `WERROR=1`, and run them from a clean
  `$(BUILD_DIR)`, so missing dependencies and warnings can't hide behind an
  old build.

## Portability

- Target **GNU Make only**, and say so in the header comment. BSD and other
  Makes differ in syntax, and supporting all of them limits a makefile to a
  small common subset.
- Keep recipes to the POSIX shell and POSIX utilities (`cp`, `mkdir -p`,
  `rm -f`). Tools like `sed -i` and `readlink -f` behave differently on macOS
  and the BSDs.
- Use features newer than GNU Make 4.3 only after raising the minimum version
  in the header comment.

## Sources

- [GNU Make manual](https://www.gnu.org/software/make/manual/)
- [GNU Coding Standards: Makefile Conventions](https://www.gnu.org/prep/standards/html_node/Makefile-Conventions.html)
- [Paul Smith's Rules of Makefiles](https://make.mad-scientist.net/papers/rules-of-makefiles/)
- [Recursive Make Considered Harmful](https://aegis.sourceforge.net/auug97.pdf),
  Peter Miller
