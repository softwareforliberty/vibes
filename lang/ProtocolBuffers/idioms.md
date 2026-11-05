# Protocol Buffers Idioms and Principles

How to design Protocol Buffers schemas well. [coding-style.md](coding-style.md)
covers how `.proto` files look. This guide covers how to design messages and
services that stay compatible as they change. Every example follows the style
guide.

## Principles

- **A field number is forever.** The wire format identifies fields by number,
  not name. Old and new programs must agree on what every number means, for
  as long as any data or client using it exists.
- **Every change must work in both directions.** New code must read old
  data, and old code must read new data. Old readers skip fields they don't
  know, so adding is safe; changing or reusing is not.
- **Design for the API, not for storage.** Messages describe what crosses a
  boundary. Keep internal storage formats out of them.
- **Check compatibility automatically.** Compare every change with the
  released schema in CI, because a breaking change looks harmless in review.

## Field numbers

- **Never reuse a field number**, and never change the type or meaning of an
  existing field. Old data and old clients would read the new field's values
  as the old one's, silently.
- **When you delete a field, reserve its number and its name**, so nobody can
  reuse them by accident:

  ```proto
  message Order {
    reserved 6, 9;
    reserved "discount_code", "notes";

    string order_id = 1;
  }
  ```

- Reserving the name also protects the JSON form, which identifies fields by
  name rather than number.
- Give numbers **1 to 15** to the most frequently set fields. They encode in
  one byte; numbers 16 to 2047 take two.
- Never use the numbers **19000 to 19999**. Protocol Buffers reserves them for
  its own use.

## Enums

- **Make the first value the zero value, named `<ENUM>_UNSPECIFIED`**, and
  never give it a meaning. An unset field reads as zero, so zero must mean
  "not set", not a real state.
- Reserve deleted enum values and names, just like deleted fields.
- **Expect values you don't know.** A newer writer can send a value an older
  reader doesn't have, so handle unknown values instead of assuming the list
  is complete.
- Prefer an enum to a `bool` for a state that might gain more options later.
  A `bool` can never grow a third value.

## Presence

- In proto3, a plain scalar field can't tell "set to zero" from "not set".
  **Mark a scalar field `optional` when that difference matters**, and check
  whether it's set before reading it:

  ```proto
  message UpdateLimitRequest {
    string account_id = 1;
    optional int32 daily_limit = 2;
  }
  ```

- Message fields always record whether they're set, so they don't need
  `optional`.
- Use `optional` rather than the wrapper types (`google.protobuf.Int32Value`
  and the others) in new schemas. It says the same thing more simply.

## Types

- Use the **well-known types** for common values: `google.protobuf.Timestamp`
  for points in time and `google.protobuf.Duration` for lengths of time.
- Never use `float` or `double` for money. Use an integer in the smallest
  unit, with the currency in a separate field.
- Use `string` for text and identifiers, and `bytes` for binary data. A
  `string` must be valid UTF-8.
- Use `int64` or `uint64` only for values that need them. JSON writes them as
  strings, because JavaScript numbers lose precision above 2^53.
- Use a `map` for a lookup by key, and a `repeated` message for an ordered
  list of records.
- Use a `oneof` when exactly one of several fields can be set. Add new fields
  to an existing `oneof` only with care: an old reader that doesn't know the
  new field sees none of the fields set.

## Messages and services

- **Give every RPC its own request and response messages**, even if they
  start out empty or identical to another's. Each can then gain fields
  without affecting the other methods.
- Don't put a domain message directly in an RPC's signature. Wrap it:
  `GetOrderResponse` holds an `Order`.
- Keep messages focused. A message with hundreds of fields is slow to build,
  and every user pays for every field.
- Put one top-level message, enum or service in each file, along with the
  small types only it uses. Small files keep dependencies narrow and generated
  code small.
- For lists that can grow, add paging from the start (`page_size` and
  `page_token` in the request, `next_page_token` in the response). Adding it
  later breaks every client that expects the full list.
- For partial updates, take a `google.protobuf.FieldMask` naming the fields
  to change, so an unset field isn't mistaken for "clear this value".

## Packages and versions

- **End every package with a major version**: `example.orders.v1`. Keep it
  stable for as long as changes stay compatible.
- Make a breaking change only in a **new package version** (`v2`), served
  alongside the old one while clients move over.
- Don't put a language-specific option in a shared schema unless every
  consumer agrees on it. Each language's generator can set its own package or
  namespace.

## Compatibility

These changes are safe for both old and new readers:

- Adding a field, enum value, message, method or service.
- Removing a field, as long as its number and name are reserved.
- Renaming a message or enum, as long as nothing uses its full name (as
  `google.protobuf.Any` and JSON type URLs do).

These changes break old or new readers, so they need a new package version:

- Changing a field's number, type or `repeated`/singular label.
- Renaming a field, which breaks the JSON form.
- Reusing a field number or enum value.
- Moving existing fields into or out of a `oneof`.
- Changing a package, service or method name, which changes the RPC's path.

## Sources

- [Protocol Buffers language guide (proto3)](https://protobuf.dev/programming-guides/proto3/)
- [Proto best practices](https://protobuf.dev/best-practices/dos-donts/)
- [API best practices](https://protobuf.dev/best-practices/api/)
- [Buf breaking change rules](https://buf.build/docs/breaking/rules/)
