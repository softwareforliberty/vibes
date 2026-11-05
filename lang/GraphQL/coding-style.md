# GraphQL Coding Style

A general-purpose coding style for GraphQL schemas (SDL) and operations,
independent of the server or client library. It builds on the
[GraphQL specification](https://spec.graphql.org/), the
[GraphQL best practices](https://graphql.org/learn/best-practices/) and the
conventions checked by [GraphQL-ESLint](https://the-guild.dev/graphql/eslint)
(see [Sources](#sources)).

This guide covers how schemas and operations look. For how to design them
(nullability, pagination, mutations, errors, evolution and security), see
[idioms.md](idioms.md).

The tools that check GraphQL code are listed in [tools.md](tools.md).

## Language baseline

The baseline is the **October 2021 edition** of the GraphQL specification.
It adds repeatable directives, interfaces that implement other interfaces,
and the `@specifiedBy` directive for custom scalars, which
[idioms.md](idioms.md#scalars) relies on.

## Layout

- **Prettier owns layout.** It formats `.graphql` files with the same
  settings as JavaScript (2-space indentation, 80 columns).
- Put each field, argument definition and enum value on its own line once a
  definition doesn't fit on one line.
- Separate top-level definitions with one blank line.
- Don't use commas between fields or enum values. GraphQL ignores them, and
  Prettier removes them.

```graphql
"""
A customer's order.
"""
type Order implements Node {
  id: ID!
  "When the order was placed."
  createdAt: DateTime!
  items(first: Int! = 20, after: String): LineItemConnection!
  status: OrderStatus!
}
```

## Files

- Use the `.graphql` extension, UTF-8 and LF line endings, and end every file
  with a newline.
- Split a large schema into one file per domain area (`orders.graphql`,
  `customers.graphql`), rather than one file per type.
- Put each client operation in its own file, named after the operation in
  kebab-case: `cancel-order.graphql` holds `mutation CancelOrder`.
- Keep operations and fragments out of schema files, and schema definitions
  out of operation files.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Types, interfaces, unions, enums, inputs, scalars | `PascalCase` | `Order`, `PaymentMethod` |
| Fields, arguments, variables | `camelCase` | `createdAt`, `orderId`, `$first` |
| Enum values | `UPPER_SNAKE_CASE` | `IN_TRANSIT` |
| Directives | `camelCase` | `@auth`, `@cacheControl` |
| Operations, fragments | `PascalCase` | `CancelOrder`, `OrderSummaryFields` |

- Treat acronyms as words: `HttpUrl`, `customerId`. This matches the
  JavaScript and TypeScript naming.
- Name input types after the mutation they serve, ending in `Input`:
  `CancelOrderInput`. Name its result type ending in `Payload`:
  `CancelOrderPayload`.
- Name mutation fields verb-first: `createOrder`, `cancelOrder`,
  `addLineItem`. Name query fields as nouns: `order`, `orders`.
- Name booleans as questions or states: `isPaid`, `hasShipped`.
- Don't put the type name in its fields: `Order.status`, not
  `Order.orderStatus`.
- Name fragments after the type and what they're for, ending in `Fields`:
  `OrderSummaryFields`.

## Descriptions and comments

- **Describe every type, field, argument and enum value** with a description
  string. Descriptions are part of the schema, so clients see them through
  introspection and in their tools.
- Use a block string (`"""`) for a multi-line description and a plain string
  (`"`) for a one-line description, placed directly above the definition.
- Use `#` comments only for notes to schema maintainers. They're dropped from
  the schema, so clients never see them.
- Every deprecation gives a reason that says what to use instead:
  `@deprecated(reason: "Use placedAt instead.")`.

## Schema definitions

- Put the `id: ID!` field first in every type that has one, then the other
  fields in a logical order: identity, core data, then connections to other
  types.
- Mark a field non-null (`!`) only when it always has a value; see
  [idioms.md](idioms.md#nullability).
- Give every argument with a sensible default a default value in the
  schema: `first: Int! = 20`.
- Write list fields with non-null items: `[String!]!`.

## Operations

- **Name every operation.** Anonymous operations can't be identified in logs,
  metrics or persisted-query lists.
- **Pass every value through a variable.** Never interpolate values into an
  operation string; variables keep operations static, cacheable and safe
  from injection:

  ```graphql
  mutation CancelOrder($input: CancelOrderInput!) {
    cancelOrder(input: $input) {
      order {
        id
        status
      }
      errors {
        message
        path
      }
    }
  }
  ```

- Select only the fields the client uses.
- Use fragments to share a selection that several operations need, not to
  shorten a single operation.
- Always select `id` on types that have one, so client caches can match
  objects.

## Third-party code

Vendored third-party schemas keep their upstream style and are not
reformatted. List them in `.prettierignore` and in ESLint's `ignores`.

## Sources

- [GraphQL specification](https://spec.graphql.org/)
- [GraphQL best practices](https://graphql.org/learn/best-practices/)
- [GraphQL-ESLint rules](https://the-guild.dev/graphql/eslint/rules)
- [Prettier options](https://prettier.io/docs/en/options.html)
