# Guides

Each guide says how to write one language, format or tool well: the
style that keeps it consistent, the decisions and traps that decide whether
it's correct and safe, and the free and open source tools that check it.
Agents read the guide for everything a change touches, and reviewers hold
the change to it.

| Directory | Holds | Examples |
| --- | --- | --- |
| `languages/` | Programming languages, shells and assembly dialects | C, Python, Rust, BASH |
| `web/` | Markup and style sheets for the web | HTML, CSS, Sass-SCSS |
| `data/` | Query languages, database dialects, data formats and schemas | SQL, PostgreSQL, YAML, Protocol Buffers |
| `build/` | Build systems and linker scripts | CMake, Make, Linker-GNU-ld |
| `tools/` | Tools whose files are code: containers, infrastructure, CI, packaging | Docker |

A framework guide, such as one for a web framework, would go in a
`frameworks/` directory, following the rules for tools below.

[`map.tsv`](map.tsv) says which guide each kind of file needs, by file
name, path or a script's interpreter. The workflow, the guide check hook
and the commit gate all find guides through it, so a guide with no
line in it is never picked up. Its header says how to write a line.

## What a guide holds

Every guide is a directory with the same files:

- **`coding-style.md`:** how the files look: layout, formatting, naming,
  comments, and how files are organised. Where a formatter exists, the guide
  follows it, and says which settings it uses.
- **`idioms.md`:** how to design well: the principles, the decisions, and the
  traps that make code or config wrong, unsafe or hard to change.
- **`tools.md`:** the tools that check it, how to configure and run them, and
  what `scripts/check` and `scripts/audit` run.
- **`.editorconfig`:** the editor settings that match the style.
- **Config files:** a drop-in template for every tool that reads one, named
  as the tool expects, which a project copies into its root.

## Rules for every guide

- **Say what to do and why, briefly.** Every rule names the problem it
  prevents, in a clause or a sentence: "use `isinstance`, which also
  matches subclasses", not just "use `isinstance`".
- **Don't reproduce the documentation.** A guide is not a tutorial or a
  reference. It covers the choices and traps that the official
  documentation leaves to the reader, and links to the documentation for
  everything else, in a Sources section at the end of each file.
- **Prefer rules a tool can check.** A rule that a linter, a test or the
  build enforces holds on every commit. When a rule can be checked, the
  guide says which tool checks it.
- **State the baseline:** the oldest version of the language or tool the
  guide supports, so every rule and example holds for it.
- **Stay consistent.** The three files and the config files never
  contradict each other, and every guide follows the
  [programming principles](../principles.md) and the
  [architecture guides](../architecture/README.md). A guide's own advice
  wins where it's more specific.
- **Every example is real.** Code and config examples follow the guide's
  own style, and each one is run: the formatter leaves it unchanged, the
  linter passes it, and it does what the text says.
- **Every tool is free and open source,** under a licence the Open Source
  Initiative approves, and maintained, with a release in the last two
  years. Pin the version the guide was checked with.
- **Write plainly.** Short sentences, wrapped at 79 columns, never splitting
  a link.

## tools.md

1. **A table of the tools,** with columns Tool (linked), Licence, Category
   (Formatting, Linting, Auditing, Code quality or Testing) and Used for.
2. **`## Config files`:** every file in the guide's directory, linked, with
   the tool that reads it, starting with `.editorconfig`. A config shown in
   tools.md is identical to its file.
3. **How to format, lint and check,** with the exact commands. Every command
   exits non-zero when it finds a problem, so `scripts/check` can run it.
4. **`## Auditing`,** with Security analysis, Dependency vulnerabilities and
   Secrets subsections, where they apply.
5. **`## Code quality`,** with Complexity, Duplication, Dead code, Coverage,
   Testing and Architecture subsections, where they apply.

## Tools and frameworks

A tool's files, such as a Dockerfile, an infrastructure module or a CI
workflow, are code: they have style, design and bugs, and the vibe workflow
applies to them as it does to a program. Their guides follow every rule
above, and these too:

- **Lead with the traps.** Most of `idioms.md` is the mistakes that look
  fine and work in a quick test but fail in production, and that the tool's
  own quick-start examples often make: unpinned versions, excess privilege,
  secrets in the wrong place, builds that can't be repeated, changes that
  destroy data. Each says what goes wrong and what to do instead.
- **Map the principles onto the tool.** Least authority, a single source
  of truth, immutability, fail fast and separation of concerns all have a
  concrete form in each tool, such as running as a non-root user,
  pinning versions in one lock file, or keeping build and runtime apart.
  `idioms.md` names them.
- **Say how to write the spec.** Give examples of measurable requirements a
  spec can state for the tool, such as an image's user, size and how it
  stops, so the spec reviewer can check them.
- **Say how to test first.** `tools.md` has a Testing section with the way
  to write a check that proves a requirement before the config that meets
  it, using a test tool, the tool's own test command, or a script that runs
  the result and checks it.
- **Keep spikes safe.** Where the tool changes real systems, such as
  infrastructure or deployments, the guide says how to try it out without
  touching them, and that a spike never touches production.

## Checking a guide

Before a guide is committed, every config and example in it is run against
the real tool, preferably in a container so nothing is installed on the
host. Each config loads with no warnings, compliant examples pass, an
example of each trap the tool can catch is caught, and formatters leave the
examples unchanged.

A new guide also gets its line in `map.tsv`. Check it with
`bin/guides-for` on the file names the guide covers, and on the config
files it ships, which must not be reported as having no guide.
