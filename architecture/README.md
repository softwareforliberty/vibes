# Software Architecture

How to structure software so each part has one job, and a change stays in
one place. This page holds the rules for every kind of software, and says
which guide to read for the kind you're building.

The [spiker](../agents/spiker.md) designs to these guides, and the
[architecture reviewer](../agents/architecture-reviewer.md) holds each change
to them. They apply the [programming principles](../principles.md) at the
scale of a whole program: separation of concerns, single responsibility and
dependency inversion above all.

## Pick the guide

| Building | Read |
| --- | --- |
| Web applications, HTTP APIs and the services behind them | [Web applications](web-applications.md) |
| Desktop and other GUI applications | [Desktop applications](desktop-applications.md) |
| OS components: kernels, drivers, firmware, system services and system libraries | [OS components](os-components.md) |
| Anything else, such as a library, a command-line tool or a script | This page alone |

A task that spans kinds uses the guide for each part.

Where guides disagree, the more specific one wins:

1. the existing codebase's architecture, unless the change has a stated
   reason to depart from it;
2. the established pattern of the framework, toolkit or kernel the code
   builds on;
3. the language's `idioms.md` in [guides/](../guides/);
4. the guide for the kind of software;
5. this page.

## Scale the structure to the task

Add structure only where it removes a real cost.

- **A script or small tool:** a few functions, with the input and output at
  the edges and the logic in pure functions between them.
- **A small program:** a core and its edges, as described below.
- **A larger program:** the full structure from its guide.

At every size, keep the core free of I/O and of the outside world's types.
That boundary is the hardest to add later.

## A core and its edges

Every guide shares one shape: a **core** that holds the logic and knows
nothing about the outside world, and **edges** that connect it to that
world: users, files, the network, databases, hardware, the operating system,
the GUI toolkit or the web framework.

- **Dependencies point inward.** The core defines the small interfaces it
  needs, such as a store, a clock or a device, and the edges implement them.
  The core never includes, imports or links an edge.
- **The core can be tested with no I/O.** Its inputs and outputs are plain
  values, and anything else it needs is passed in.
- **The edges are thin.** Each one translates between the outside world and
  the core, and holds no rules of its own.
- **One place builds and wires the parts,** at startup: `main`, or the
  framework's equivalent. Dependencies are passed in from there, never
  fetched from global singletons.

## Layers and boundaries

- **Each layer has one job,** and depends only on the layers inside it.
  There are no dependency cycles between layers or modules.
- **Each boundary has its own types.** The outside world's types, such as
  database rows, widgets, wire formats and hardware registers, are converted
  at the boundary and never travel into the core. The conversion lives on the
  boundary, in one place.
- **Interfaces are small,** shaped by what their callers need, and owned by
  the side that uses them.
- **The public surface is as small as it can be.** Everything else is hidden
  with the language's visibility rules, so it can change without breaking
  anyone.

## State and ownership

- **Every piece of state has one owner,** the only code that changes it.
  Everything else reads it, or asks the owner to change it.
- **Every resource has one owner** that releases it: memory, files, sockets,
  locks, handles and threads. Each is created and released in a matching pair,
  and the owner's lifetime covers every use.
- **Shared state says what protects it:** confinement to one thread, a lock,
  or message passing between owners. Prefer confinement and messages to
  locks.

## Errors

- **Each layer reports errors one consistent way,** in the language's
  idiom. Inner layers report them, and the edges decide how to present them.
- **Validate at the boundary,** then trust validated values inside, ideally
  through types that can't hold invalid ones.
- **Errors carry the context needed to act on them,** added as they pass up
  through the layers.

## Configuration

Configuration lives in one place. It's read into typed values with
defaults, and validated at startup, so a bad setting fails at once. Code
receives the values it needs, never the whole configuration.

## Layout and naming

- **Name each module and type by its role,** consistently, so its layer is
  obvious and rules can be checked by name.
- **Group by layer in a small program, and by feature then layer in a larger
  one,** unless the language's `idioms.md` says otherwise.
- **Platform-specific code lives in its own files,** one set per platform,
  chosen by the build, behind one shared interface. Avoid conditional
  compilation in the middle of functions.
- **Tests mirror the source layout.** When a file moves, its test moves with
  it.

## Enforce it

- **Make the build enforce the layers** where the language allows: each layer
  its own module, package, crate or library target, depending only on what it
  may use, so a forbidden dependency fails to build.
- **Write the remaining rules as architecture tests** and run them in
  `scripts/check`, so a change that breaks a boundary fails the gate. Each
  guide suggests rules and tools.
- **When existing code breaks a rule,** keep the rule and disable it for that
  one case, with a comment naming the violation and how to fix it. Never
  weaken a rule to make the code pass.

## Test each layer at its boundary

- **The core:** fast unit tests with no I/O.
- **The edges:** against the real thing where it's practical, such as a real
  database, file system, toolkit or emulator, and otherwise against a
  faithful fake.
- **The whole program:** a few end-to-end tests of the most important
  journeys.
- **Replace only your own interfaces,** never third-party code. To control a
  library in a test, put it behind an interface you own.
