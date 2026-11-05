# GraphQL Idioms and Principles

How to design GraphQL APIs well. [coding-style.md](coding-style.md) covers
how schemas and operations look. This guide covers how they're designed: the
idioms and principles that keep a GraphQL API correct, safe and able to
evolve. Every example follows the style guide.

## Principles

- **Design for the client, not the database.** The schema describes what
  clients need in the language of the domain. It isn't a mirror of tables or
  internal services.
- **Evolve, don't version.** Add fields and types freely; deprecate before
  removing; never change the meaning of an existing field.
- **Be precise about absence.** Nullability is part of the contract. Mark
  what can be missing, and only that.
- **Every query is bounded.** A client can ask for anything the schema
  allows, so the server limits depth, cost and page size.
- **Authorise data, not the schema.** Access checks belong in the business
  logic every resolver calls, so no path through the graph skips them.

## Schema design

- **Model the domain with object types and relationships**, not foreign
  keys. Expose `order.customer`, not `order.customerId`.
- **Give every fetchable object a globally unique, opaque `id: ID!`**, and
  implement a `Node` interface so clients can refetch any object by ID:

  ```graphql
  """
  An object with a globally unique ID.
  """
  interface Node {
    id: ID!
  }
  ```

  Clients must treat IDs as opaque strings, so the server can change how
  they're built.

- **Use enums for closed sets of values** (`OrderStatus`), and strings for
  open-ended text.
- Use interfaces for types that share fields and behaviour, and unions for
  results that can be one of several unrelated types.
- Don't expose internal details such as table names, database IDs or
  service names in type or field names.
- Prefer specific fields to generic ones. A `JSON` scalar or a
  `metadata: String` field turns off every guarantee the type system gives.

## Scalars

- Use the built-in scalars where they fit, and define a custom scalar for
  any value with a format, such as dates and URLs. Link each one to its
  specification with `@specifiedBy`:

  ```graphql
  """
  A date and time, as an RFC 3339 string with a time zone offset.
  """
  scalar DateTime @specifiedBy(url: "https://www.rfc-editor.org/rfc/rfc3339")
  ```

- Represent money with an amount in the smallest unit plus a currency code,
  never as a floating-point number.

## Nullability

- **Make a field non-null when it always has a value** and can't fail
  independently: an object's `id`, or a scalar stored on the object.
- **Make a field nullable when it can be missing, or when fetching it can
  fail on its own**, such as a field resolved from another service. A null
  in a non-null field nulls out its parent, so an error in one field could
  otherwise wipe out a whole response.
- Make list fields `[Item!]!`: the list is always there (it may be empty),
  and it never contains nulls.
- Make arguments non-null when they're required, and give optional
  arguments a default value where one makes sense.
- Changing a field from non-null to nullable is a breaking change for
  clients, and the reverse is a breaking change for inputs. Decide carefully
  the first time.

## Pagination

- **Paginate every list that can grow without bound**, using cursor-based
  connections:

  ```graphql
  type LineItemConnection {
    edges: [LineItemEdge!]!
    pageInfo: PageInfo!
  }

  type LineItemEdge {
    cursor: String!
    node: LineItem!
  }
  ```

- Cursors are opaque to the client, like IDs. Offsets break when items are
  added or removed between pages; cursors don't.
- **Cap the page size on the server.** Reject a `first` larger than the
  maximum, rather than silently returning fewer items.
- Small lists with a known upper bound, such as a product's colours, can be
  plain lists.

## Mutations

- **Give each mutation one required input argument** of its own input type,
  and return its own payload type:

  ```graphql
  type Mutation {
    """
    Cancels an order that hasn't shipped yet.
    """
    cancelOrder(input: CancelOrderInput!): CancelOrderPayload!
  }
  ```

  New optional input fields and new payload fields can then be added
  without breaking clients.

- **Return the changed object in the payload**, so clients can update their
  cache without a second request.
- Name mutations after a business action (`cancelOrder`, `markOrderPaid`),
  not a generic update (`updateOrder(status: CANCELLED)`). Each action can
  then have its own validation, permissions and errors.
- Make mutations idempotent where possible, or accept a client-generated key
  so a retried request doesn't act twice.

## Errors

- **Return expected failures as data in the payload**, typed so clients can
  handle them: validation failures, conflicts, "not allowed":

  ```graphql
  type CancelOrderPayload {
    order: Order
    errors: [UserError!]!
  }

  type UserError {
    message: String!
    path: [String!]
  }
  ```

- Use the top-level `errors` array only for unexpected failures and for
  requests that are invalid as a whole.
- **Never put internal details in an error**: stack traces, SQL, file paths
  or service names. Log them on the server, and return a generic message
  with a reference the client can quote.

## Evolution

- **Add, don't change.** New fields, types, enum values and optional
  arguments don't break existing clients.
- **Deprecate before removing.** Mark the field with `@deprecated` and a
  reason, watch usage until it drops to zero, then remove it.
- Treat adding an enum value as potentially breaking for clients that
  handle every value exhaustively, and tell clients to keep a fallback.
- Check every schema change for breaking changes in CI before it's merged.

## Security

- **Limit query depth and cost.** Reject queries nested deeper than the
  schema needs, and give fields a cost so a query that would touch millions
  of objects fails before it runs.
- **Limit aliases and batched operations.** Aliases let one request call the
  same field many times, which bypasses per-request rate limits.
- **Use trusted documents (persisted queries) for first-party clients.** The
  server then runs only operations it has seen at build time, which stops
  arbitrary queries entirely.
- **Check authorisation in the business logic**, for every object a resolver
  returns. A field that's only reachable through an authorised path today
  may be reachable through another path tomorrow.
- Introspection isn't a security boundary. Disabling it hides the schema
  from casual browsing, but doesn't protect anything the schema exposes.
- Validate every input value (lengths, ranges, formats) on the server, even
  when its type already constrains it.

## Performance

- **Batch data loading** so a list of N objects doesn't make N separate
  requests for their related data (the "N+1" problem). Load related objects
  for the whole list in one request per level.
- Resolve expensive fields only when they're selected, rather than
  precomputing everything an object could expose.

## Sources

- [GraphQL best practices](https://graphql.org/learn/best-practices/)
- [GraphQL: Pagination](https://graphql.org/learn/pagination/)
- [GraphQL: Global Object Identification](https://graphql.org/learn/global-object-identification/)
- [GraphQL Cursor Connections Specification](https://relay.dev/graphql/connections.htm)
- [OWASP GraphQL Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/GraphQL_Cheat_Sheet.html)
