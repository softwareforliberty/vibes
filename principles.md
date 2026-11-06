# Programming Principles

The design principles every change is held to, in any language. The
[cleanliness reviewer](agents/cleanliness-reviewer.md) checks each change
against them, and anyone writing code in the vibe workflow should follow
them.

Each language's `idioms.md` in [lang/](lang/) has its own principles. Where
it disagrees with this guide, the language's guide wins. Where the codebase
has an established pattern, follow it unless it breaks a principle badly
enough to be worth a finding.

## How to apply them

- **A principle is a reason, not a rule.** Report a breach only when it has a
  concrete cost in this change: code that's harder to read, change, test or
  trust. "This isn't SOLID" is never a finding on its own.
- **Name the principle** at the start of each finding, then show the cost
  and the fix, for example: `DRY: the VAT rate is hard-coded in both
  invoice.py:12 and quote.py:30, so a rate change must find both. Fix: ...`.
- **Weigh the size of the change.** A 30-line script doesn't need the
  structure of a service. Judge the design the task needs, not the most
  general one possible.
- **Principles pull against each other.** When they do, see
  [Tensions](#tensions), and choose the simpler design.

## Severity

- **MAJOR:** the breach already costs something, or soon will: knowledge
  duplicated in places that have drifted apart, a function or class with
  several unrelated jobs, shared state mutated from many places, invalid
  input accepted and carried far from its source, an implementation that
  breaks its interface's contract, or a component holding authority it
  doesn't use.
- **MINOR:** the design works but would read or change more easily
  another way, and the fix is cheap.
- A breach is a BLOCKER only when it makes the code wrong or unsafe, and
  then the bug or security reviewer usually owns it too.

## SOLID

Five principles for code that's easy to change. They come from
object-oriented design, but each applies to modules and functions in any
language with them. See [Other languages](#other-languages) for how they
map.

### Single responsibility

A module, class or function has one reason to change: it serves one actor
or concern.

Look for:

- A function that parses, decides, formats and writes, so a change to the
  output format means editing the business rules.
- A class whose methods split into groups that share no fields.
- A name that needs "and", or a vague one such as `Manager`, `Helper`,
  `Utils` or `process`, hiding several jobs.
- A boolean parameter that switches between two behaviours.

Fix: split along the reasons to change, so each part can be read and tested
alone.

### Open/closed

Code is open to extension and closed to modification: adding a new variant
means adding code, not editing working code in many places.

Look for:

- The same `if`/`switch` on a type or kind repeated across the codebase, so
  every new kind means finding and editing each one.
- A new feature that works by threading flags through existing functions.

Fix: put the variation behind an interface, a table of handlers or a
polymorphic type, so a new variant lives in one place.

Don't flag a `match` over a closed set of cases in a language that checks
it's exhaustive, such as Rust, Haskell, OCaml or Swift. There the compiler
finds every place a new case must be handled, which is the idiomatic design.
And don't add an extension point for variants nobody has asked for (see
[YAGNI](#yagni-you-arent-gonna-need-it)).

### Liskov substitution

Any implementation of an interface, or subclass of a type, can stand in
wherever the interface or base type is expected, without callers noticing.

Look for:

- Methods that throw "not supported" or do nothing because the type can't
  honour the interface.
- An implementation that demands more of its inputs, or promises less about
  its outputs, than the contract it implements.
- Callers that check the concrete type before using an abstraction.

Fix: narrow the interface so every implementation can honour it, or stop
pretending the type is a kind of the other one and use composition.

### Interface segregation

No client depends on methods it doesn't use. Interfaces are small and shaped
by what their callers need.

Look for:

- A large interface that implementers half fill with stubs.
- A function that takes a whole object, such as the full config or a request
  context, when it uses one or two values from it.

Fix: split the interface by client, or pass only what the function uses.

### Dependency inversion

High-level policy doesn't depend on low-level details. Both depend on an
abstraction, owned by the policy side.

Look for:

- Business logic that opens files, reads the clock or environment, calls the
  network or queries the database directly, so it can't be tested or reused
  without them.
- Dependencies fetched from globals or singletons instead of passed in.

Fix: pass the dependency in, as a parameter, a constructor argument or a
function, and keep the I/O at the edges.

Don't add an interface that has only one implementation and no test that
needs another. Passing a concrete dependency in is often enough.

## The other principles

### DRY: Don't Repeat Yourself

Keep each piece of knowledge in one place, so a change to it is made once.

Look for:

- The same rule, formula, constant, validation or mapping written in two or
  more places.
- Copied blocks that differ only in a value that could be a parameter.

DRY is about knowledge, not text. Two pieces of code that look alike but
would change for different reasons aren't duplication, and merging them
couples things that should stay apart. Wait for the third copy before
extracting a shared abstraction, unless the copies are one rule that must
never drift.

### KISS: Keep It Simple

Prefer the simplest design that meets the need.

Look for:

- Indirection, generics, patterns or configuration the task doesn't need.
- Clever code where a plain loop or a standard library call would do.
- A general framework built to solve one case.

Fix: write the obvious version. The simpler design is easier to read,
review and change, and can grow when there's a real need.

### YAGNI: You Aren't Gonna Need It

Don't build features or abstractions until they're needed.

Look for:

- Parameters, options, hooks or extension points with no caller.
- Code for cases the task doesn't mention "in case we need it later".
- Layers or interfaces with a single use and no test that needs them.

Fix: delete it. It can be added, with a test, when a real need arrives.

### Separation of concerns

Keep distinct responsibilities in distinct modules or layers.

Look for:

- Domain logic mixed with presentation, transport, storage or framework
  code.
- Input parsing, validation, computation and output tangled in one place.
- Error handling, logging or retries woven through the business logic
  instead of at a boundary.

Fix: give each concern its own module or layer, with a narrow interface
between them. This is the single responsibility principle at the scale of
the system.

### Principle of least astonishment

Code behaves the way its users would naturally expect from its name, its
signature and the conventions around it.

Look for:

- A getter, query or predicate with side effects, such as `is_valid()` that
  also saves.
- A function that changes its arguments when nothing says it does.
- Behaviour inconsistent with similar code nearby: a different parameter
  order, error style, unit or return convention.
- Surprising defaults, such as a delete that's recursive unless told
  otherwise.

Fix: rename the code to say what it does, or change it to do what its name
says, and match the conventions around it.

### Law of Demeter

Code talks to its close collaborators, rather than reaching through chains
of objects: `order.customer.address.city` couples the code to the shape of
three other types.

Look for:

- Chains that walk through several objects to reach data or call a method.
- Code that pulls data out of an object to make a decision the object could
  make itself.

Fix: ask the nearest collaborator for what you need ("tell, don't ask"), or
pass the needed value in directly.

Fluent interfaces, builders and pipelines over plain data, such as a chain of
`map` and `filter`, aren't breaches: each call returns the same kind of thing
rather than reaching into another object.

### Composition over inheritance

Assemble behaviour from smaller parts when that's clearer than building deep
class hierarchies.

Look for:

- Inheritance used to reuse code rather than to model a genuine "is a"
  relationship.
- Hierarchies more than two levels deep, or subclasses that override methods
  to switch inherited behaviour off.
- A combination of features handled by a subclass for each combination.

Fix: give the class the parts it needs as fields or parameters, and delegate
to them.

### Favour immutability

Avoid changing shared state when values can be created and passed along
instead.

Look for:

- Mutable global or module-level state.
- Objects changed after they've been handed to other code, or returned
  collections that callers can change from outside.
- Functions that update their inputs in place when returning a new value
  would be as clear.

Fix: make values immutable by default, build new values instead of changing
old ones, and keep any mutation local to the code that owns the state.
Mutating a local value in a hot loop is fine when it's measurably faster and
doesn't escape.

### Fail fast

Detect invalid input or impossible states early, close to where they occur.

Look for:

- Invalid input accepted at a boundary and only failing deep inside the
  system, far from the cause.
- Errors swallowed, or replaced by a default such as `null`, an empty list
  or `-1`, that lets a broken state carry on.
- Impossible cases handled by silently doing nothing instead of an assertion
  or a clear error.

Fix: validate at the boundary, then trust the validated value inside, ideally
through a type that can only hold valid values. Failing fast means the
operation fails clearly. It doesn't mean crashing a whole server over one
bad request.

### Single source of truth

Store authoritative information in one place and derive other views from it.

Look for:

- The same fact stored twice, such as a count kept alongside the list it
  counts, or a status that can disagree with the fields it summarises.
- Configuration, schemas or constants defined in more than one place.
- Caches or copies with no clear owner or way to stay current.

Fix: keep one authoritative copy and compute the rest from it. Where a copy
is needed for speed, give it one owner and one path that updates it. Where
DRY is about logic, this principle is about data and state.

### Boy Scout Rule

Leave code a little cleaner than you found it.

Look for:

- A change that works around a confusing name, a stale comment or dead code
  in the lines it touches, instead of fixing it.
- New code that copies a poor pattern from nearby code.

Keep it small and local: tidy only the code the change touches, and put the
tidy-up in a commit of its own, as the
[atomic commits](skills/atomic-commits/SKILL.md) skill describes. A missed
tidy-up is MINOR, and a large refactor of untouched code is out of scope.

### POLA: Principle of Least Authority

Give a component only the access and permissions it needs.

Look for:

- Functions handed broad capabilities they don't use: a whole database
  connection to read one table, the full filesystem to read one file, or an
  admin client to make one call.
- Services, containers and processes running with more privilege than the
  task needs, or credentials with wider scopes than they use.
- Files, directories or sockets created with permissions wider than needed.
- Public visibility on modules, types and functions that only their own
  package uses.

Fix: pass the narrowest capability that works, and default to the least
access and visibility. The security reviewer owns any exploitable result of
the excess authority.

## Tensions

- **DRY and KISS:** a shared abstraction for code that only looks alike is
  worse than the duplication. Prefer the copies until the third one, or
  until they're one rule.
- **Open/closed and dependency inversion against YAGNI:** add the extension
  point or the interface when the second implementation or a test needs it,
  not before.
- **Immutability and performance:** immutable by default, with local
  mutation where measurements show it matters. The performance reviewer
  judges the measurements.
- **Fail fast and resilience:** fail fast inside the system, and at its
  boundaries turn the failure into a clear error for the one request or
  record, not the whole process.

## Other languages

- **Functional languages:** single responsibility and separation of concerns
  apply to modules and functions. Interfaces are type classes, protocols,
  behaviours, signatures or plain function parameters. Immutability is
  usually the default already, and composition is the only option.
- **Procedural languages such as C and assembly:** interfaces are headers,
  function pointers and structs of operations. The Law of Demeter applies to
  chains of struct members.
- **Data, query, markup and config languages,** such as SQL, CSS, HTML,
  YAML and Make: SOLID mostly doesn't apply. DRY, KISS, YAGNI, separation of
  concerns, least astonishment, single source of truth and least authority
  still do, for example in duplicated queries, style rules or settings, and
  database grants.
