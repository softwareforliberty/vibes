# Web Application Architecture

How to structure a web application, an HTTP API or a service behind one.
Read the [rules for all software](README.md) first: a core of logic with thin
edges, dependencies pointing inward, and one owner for each piece of state.
This guide builds on them.

The layers here are the MVC pattern grown for real applications. The same
layers suit a worker that consumes a queue: only the entry points differ.

## Scale the structure to the task

Add structure only where it removes a real cost.

- **A small application:** controllers, services and repositories. Until
  they differ, a request model may serve as the command, and the domain model
  as the view.
- **A growing application:** everything in this guide.

At every size, keep persistence records inside the repositories. A database
row that reaches a controller or a response is the leak that's hardest to
undo.

## The layers

```text
request ─▶ controller ─────────────▶ assembler ─▶ response
             │    ▲
     command │    │ view
             ▼    │
            service ─▶ domain services, adapters
             │
             ▼
          repository ─▶ database
```

| Layer | Its job | Depends on | Never depends on |
| --- | --- | --- | --- |
| Controller | Turns input into a call to a service | Services, assemblers | Repositories, persistence, domain models |
| Service | One area's business logic | Repositories, domain services, adapters | Controllers, other services |
| Domain service | One piece of logic that services share | Repositories, adapters, other domain services | Services |
| Repository | Stores and loads one aggregate | The database and its library | Business logic |
| Assembler | Turns a view into a response | Views, response models | Services, repositories |
| Adapter | Talks to one outside system | Its own message types | Domain models, persistence |

An **aggregate** is a cluster of data that's loaded, changed and saved as one
unit, such as an order with its lines.

### Controllers

A controller is thin. Each handler:

1. binds and validates the request model;
2. takes the acting user from the authenticated principal, never from the
   request body;
3. builds a command from the request and what only it knows: the target's id
   from the path, the acting user and any precondition, such as `If-Match`;
4. calls one service method;
5. hands the view it gets back to an assembler;
6. sets the transport details: status, `Location`, cache headers and ETags.

A controller holds no business rules, no queries and no response building.

Every entry point is a controller: HTTP handlers, scheduled jobs, queue
consumers and command-line commands. They all call the same services, so the
behaviour doesn't depend on how it was triggered.

### Services

A service holds the business logic for one area, such as orders or
invoices. It's the layer most worth unit testing.

- **It owns the transaction.** Each public method is one use case and one
  transaction.
- **It takes a single command for a write,** so its signature can't drift
  from the request. Reads, and writes with no request body, take ids and
  simple values.
- **It returns views,** never domain models or persistence records.
- **It checks access to the target:** whether this caller may act on this
  record, as opposed to this kind of operation (see
  [Security](#security)).
- **Its dependencies are passed in,** including the clock and the id
  generator, so a test can construct it directly with no framework or
  database.

**A service never depends on another service.** Services sit at the top of
the domain layer. Wiring one into another breeds large hub classes, invites
dependency cycles, and nests one transaction inside another without anyone
seeing it. When two services need the same behaviour, it doesn't belong to
either: move it into a domain service that both use.

### Domain services

A domain service is a small, single-purpose component that owns one piece of
shared logic, such as hashing and checking passwords, registering a user, or
checking access to a record. It's named for what it does
(`PasswordHasher`, `UserRegistrar`, `ProjectAccess`), not `Helper` or
`Manager`.

It may depend on repositories, adapters, other domain services and the
clock, but never on a service. It runs inside its caller's transaction. It's
the one home for its logic, and the one place that logic is tested.

### Repositories

There's one repository per aggregate. It's a facade in domain terms: it takes
and returns domain models, and is keyed by typed ids.

- **It maps between the domain model and the persistence record.** That
  mapping is the only code that knows both.
- **It holds no business logic.** It stores, loads and maps.
- **The persistence library stays inside it:** ORM sessions, entity
  managers, query builders and any framework-generated repository
  interfaces. Services see only the facade.
- **It loads what a caller needs in one query.** When a service needs a few
  fields of a related aggregate, the repository loads them with the query and
  returns a small projection model, rather than an object graph to walk later.
  Lists that need related data load it for all rows in one batched query, not
  one query per row.

### Assemblers

An assembler turns a view into the response: the response model, plus any
links and available actions. Response models have one factory that builds
them from a view.

The controller passes in anything else the assembler needs, such as the
principal or a related record's state, so the assembler never calls a
service.

In a server-rendered MVC application, the template and its view model fill
this role. A template gets a view model built for it, never a domain model or
persistence record, and holds no logic beyond display.

### Adapters

Each outside system, such as email, payments, a message queue, file storage or
another service's API, sits behind an interface the application owns. The
adapter implements it, and tests and local development swap in a fake that
records what was sent.

- **Adapters take simple values or their own small message types,** never
  domain models or persistence records, so they don't depend on the model's
  shape.
- **Building a message is separate from sending it.** For email, one part
  renders the bodies from templates and another sends them, so each is tested
  on its own.

### Supporting code

- **Configuration** follows the [shared rules](README.md#configuration),
  with each concern's settings in a small typed object of its own, not one
  large one.
- **Errors:** one error type per failure mode, mapped to a transport status
  in one place at the edge. HTTP APIs return a consistent, machine-readable
  error body, such as [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)
  problem details, with field errors for failed validation.
- **Helpers are small and stateless.** A helper that knows business rules is
  a domain service.
- **Seed data for development** is idempotent, and never runs in production.

## A model for each boundary

Each layer has its own model, and each model crosses only its own boundary.

| Model | Holds | Made by | Used by |
| --- | --- | --- | --- |
| Request | The input as sent, with its validation rules | The framework | Controller |
| Command | A write's input: the request data, the target id, the acting user and any precondition | Controller | Service |
| Domain model | The aggregate and its rules | Service, repository | Service, domain services, repository |
| Persistence record | The stored shape | Repository | Repository only |
| View | A service's result | Service | Controller, assembler |
| Response | The representation sent back | Assembler | The transport |

A write flows:

```text
request → command → service → domain model → repository → record
```

A read flows:

```text
record → repository → domain model → service → view → assembler → response
```

- **Persistence records never leave the repository,** domain models never
  leave the service layer, and request and response models never enter it.
- **The mapping between two models lives on the boundary between them:**
  record and domain model in the repository, domain model to view on the
  service side, and view to response in the response model's factory. Keep
  the view model free of domain imports, so it stays a leaf.
- **Shared enums and value types,** such as ids, money and statuses, live in
  a neutral package every layer may import, never next to the persistence
  records. "Nothing outside the repositories imports persistence code" then
  stays a simple rule a test can check.
- **Don't merge models because they look alike.** A request, a domain model
  and a response change for different reasons, and copying a few fields
  between them is cheaper than coupling the API to the database.

## Domain models

- **Immutable values with value equality.** To change one, copy it with new
  values and save the copy through the repository.
- **One place stamps audit fields,** such as `updatedAt`, on every save, so
  every write path agrees.
- **Typed ids.** Each aggregate has its own id type (`OrderId`, `UserId`),
  using the language's zero-cost wrapper where it has one, so two ids can't
  be swapped by mistake.
- **Aggregates refer to each other by id,** never by holding each other, so
  what's loaded is always explicit and the boundaries stay clear.
- **Valid by construction.** Validate at the boundary, and use types that
  can't hold invalid values.

## Security

- **The acting user comes from the authenticated principal,** never from a
  field in the request.
- **Authorisation has two layers.** A permission check at the edge, before
  the controller runs, decides whether this caller may perform this kind of
  operation at all. Checks in the service decide whether they may perform it
  on this record. Write permissions as named permissions, with each role a
  set of them defined in code, rather than checking roles throughout.
- **A record the caller can't access looks the same as one that doesn't
  exist,** usually a 404, so its existence doesn't leak.
- **Security-relevant actions are recorded,** with the actor, the target and
  the time, by a domain service the services share.

## HTTP APIs

- **One endpoint per action.** A separate flow, such as changing an email
  address, a password or a role, gets its own endpoint, not optional fields
  in a general update.
- **Conditional updates.** Reads return an ETag derived from the record's
  `updatedAt`. Updates require `If-Match`, and fail with 428 when it's
  missing and 412 when it's stale, so one client can't silently overwrite
  another's change.
- **Retried creates are safe.** A create that clients may retry takes an
  idempotency key.
- **The server decides what's allowed.** Each response says which actions the
  caller may take on it, as links or flags, and clients show an action only
  when it's offered, rather than repeating the server's rules.
- **With hypermedia,** such as HAL or JSON:API, every resource is reachable
  by following links from the root, and an action appears only when it's
  allowed for this caller and this state. Assemblers build the links, never
  controllers. Tests check that each conditional link appears when it
  should and is absent when it shouldn't.

## Front ends

A single-page client has the same separation:

- **API module:** the only code that makes HTTP requests. It turns responses
  into plain values and error bodies into field errors. Tests replace this
  module, so no test touches the network.
- **Session module:** holds the session, and is the one place that handles
  an expired session, by clearing it and sending the user to log in.
- **Pages:** one per route. A page loads its data through the API module and
  composes components.
- **Components:** reusable pieces of interface that get data and callbacks
  through their props, so they render the same anywhere and test without a
  network.
- **Hooks or stores:** reusable stateful logic, such as a debounced
  availability check, each tested on its own.
- **Layouts:** the page frame that routes share.
- **Pure helpers:** formatting, dates, money and other plain functions, with
  their own unit tests.

## Layout and naming

- **Name each type by its role, with a consistent suffix:**
  `OrderController`, `OrderService`, `OrderRepository`, `CreateOrderCommand`,
  `OrderView`, `OrderResponse`. The layer is then obvious, and the rules can
  be checked by name.
- **Group by layer in a small application, and by feature then layer in a
  larger one,** unless the language's `idioms.md` says otherwise. Go, for
  example, groups by feature.

## Enforce it with tests

Write the boundary rules as architecture tests, as the
[shared rules](README.md#enforce-it) describe. Typical rules:

- persistence records and the persistence library are used only in
  repositories;
- services don't depend on other services;
- view models don't depend on domain models;
- adapters don't depend on domain models or persistence records;
- controllers don't query the database or build links.

Tools that check these include [ArchUnit](https://www.archunit.org/) for the
JVM, [import-linter](https://github.com/seddonym/import-linter) for Python,
[dependency-cruiser](https://github.com/sverweij/dependency-cruiser) for
JavaScript and TypeScript, and [Deptrac](https://github.com/deptrac/deptrac)
for PHP. Where a language has none, a check in `scripts/check` that searches
imports can enforce the simple rules.

## Test each layer at its boundary

| Layer | Test with | Replace |
| --- | --- | --- |
| Services and domain services | Unit tests, with no framework or database | Their own dependencies |
| Repositories | A real database, such as one in a container | Nothing |
| Controllers | The real HTTP stack and security | The services |
| The whole application | User journeys over HTTP | Only outside systems, with recording fakes |

- **Repository tests round-trip** a domain model through the repository, and
  check each custom query against real rows.
- **Controller tests check every rejected request,** such as invalid input,
  no login or a missing permission, and prove the service was never called.
- **Never wrap a test in a transaction that's rolled back at the end.** It
  hides code that forgets to open its own transaction, and bugs that only
  show once data is committed.
