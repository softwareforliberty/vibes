# Deep modules

How to judge whether a module is worth having, and where its boundary
should sit. The ideas are John Ousterhout's, from _A Philosophy of Software
Design_, with Michael Feathers' seams. The
[surveyor](../agents/surveyor.md) looks for modules that fail these tests,
and the [interface designer](../agents/interface-designer.md) designs
replacements that pass them.

They complement [the architecture rules](README.md): those say which way
dependencies point and where the core and its edges meet; these say
whether each module's boundary pays for itself.

## The words

Use these words, exactly, when judging a module. Name the things the
modules hold with the project's glossary terms.

- **Module:** anything with an interface and code behind it: a function,
  a class, a file, a package or a service.
- **Interface:** everything a caller must know to use the module correctly:
  its names and types, but also its order of calls, its errors, its side
  effects and the states it can be in.
- **Depth:** how much the module does for its callers, against how much
  its interface asks them to know. A **deep** module hides a lot behind a
  small interface. A **shallow** one's interface is nearly as complex as
  the code behind it, so callers gain little by going through it. Depth is
  the leverage callers get, not a ratio of lines.
- **Seam:** a place where behaviour can change without editing the code
  around it, because the code reaches it only through an interface.
- **Adapter:** the code that fills a seam, such as a database store behind
  a repository interface.
- **Leverage:** what callers gain: how much work, and how many decisions,
  one call saves them.
- **Locality:** how much of what you need to understand, or change, for one
  concept sits in one place.

## The tests

- **The deletion test.** Imagine deleting the module and inlining it into
  its callers. If the complexity would spread out across them, the module
  concentrates it, and it's earning its place. If the callers would barely
  change, it was only moving complexity around, and it's shallow.
- **The interface is the test surface.** A module is tested through its
  interface. When a test has to reach behind it, or the code had to be
  split up only so a piece could be tested, the interface is in the wrong
  place. Once a module is deep, the architecture rules
  [give it a front door](README.md#enforce-it), so callers and tests can't
  reach past its interface and make it shallow again.
- **One adapter means a hypothetical seam; two mean a real one.** An
  interface with only one implementation, and no second one planned, adds
  a jump for every reader and buys nothing yet. Keep it only where the
  architecture rules ask for it, such as a store the core needs.

## Signs of a shallow design

- **Understanding one concept means jumping between many small modules,**
  each passing the work on to the next.
- **Pass-through methods and wrappers** that add a name but no decision.
- **Pure functions pulled out only to be testable,** while the bugs live in
  how their callers combine them: the logic lost its locality.
- **Callers that must call things in the right order,** or set up state
  first, which the module could do for them.
- **Modules that leak across their seams:** callers that know, and depend
  on, what's behind an interface.
- **Code that's hard to test through its current interface,** so it's
  untested or tested by reaching inside.

## Deepening

To deepen a module is to move complexity behind a smaller interface:
merge shallow modules that always change together, pull knowledge callers
share into the module, make the common case one call, and handle errors
and special cases inside rather than passing them out. Its tests then move
to the new interface, and tests of the internals it absorbed are removed.

## Design it twice

The first interface you think of is rarely the best. For a module worth
deepening, design several very different interfaces, each under a
different constraint, such as the smallest possible interface, the one the
commonest caller wants, or one that puts the seam somewhere else. Then
compare them on depth, locality, where the seam sits and what the change
would cost, and choose, or combine the best parts.
