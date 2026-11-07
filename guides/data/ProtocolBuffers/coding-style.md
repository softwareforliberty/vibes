# Protocol Buffers Coding Style

A general-purpose style for Protocol Buffers schema files (`.proto`). It
builds on the [Protocol Buffers style guide](https://protobuf.dev/programming-guides/style/)
and the layout that `buf format` produces (see [Sources](#sources)).

This guide covers how `.proto` files look. For how to design messages that
stay compatible as they change (field numbers, reserved fields, enums,
presence and versioning), see [idioms.md](idioms.md).

The tools that check Protocol Buffers code are listed in [tools.md](tools.md).

## Language baseline

Write **proto3** (`syntax = "proto3";`). Protobuf Editions
(`edition = "2023";`) replace the `syntax` line with per-feature settings;
when a project moves to editions, every rule in this guide still applies.

## Files

- Name files in **`lower_snake_case`**, ending in `.proto`:
  `order_service.proto`.
- Put each file in a directory that matches its package:
  `example/orders/v1/order.proto` holds `package example.orders.v1;`.
- Encode files in **UTF-8**. No trailing whitespace; use LF line endings, and
  end every file with a newline.

### File structure

Lay out every file in this order, with one blank line between sections:

1. A comment describing the file.
2. The `syntax` line.
3. The `package` line.
4. Imports, sorted alphabetically.
5. File options.
6. Everything else: services, then messages, then enums.

```proto
// Orders placed by customers.
syntax = "proto3";

package example.orders.v1;

import "google/protobuf/timestamp.proto";

// An order placed by a customer.
message Order {
  // Server-assigned identifier, unique across all orders.
  string order_id = 1;
  string customer_id = 2;
  OrderStatus status = 3;
  repeated OrderLine lines = 4;
  google.protobuf.Timestamp placed_at = 5;
}

// One product and quantity within an order.
message OrderLine {
  string sku = 1;
  int32 quantity = 2;
}

// Where an order is in its life cycle.
enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PLACED = 1;
  ORDER_STATUS_SHIPPED = 2;
}
```

## Layout

- Indent with **2 spaces**.
- Keep lines to **80 columns**.
- Put the opening brace on the same line as the declaration, and the closing
  brace on its own line.
- Put one field, enum value or method on each line.
- Separate top-level definitions with one blank line.
- Quote strings, such as import paths and option values, with **double
  quotes**.

## Names

| Element | Case | Example |
| --- | --- | --- |
| Packages | `lower.dot.separated`, ending in a version | `example.orders.v1` |
| Messages, enums and services | `PascalCase` | `OrderLine`, `OrderStatus`, `OrderService` |
| RPC methods | `PascalCase`, starting with a verb | `GetOrder`, `ListOrders` |
| Fields, including `oneof` names | `lower_snake_case` | `customer_id`, `placed_at` |
| Enum values | `UPPER_SNAKE_CASE`, prefixed with the enum's name | `ORDER_STATUS_SHIPPED` |

- Treat an abbreviation as one word: `GetDnsRequest`, `http_url`, not
  `GetDNSRequest`. Generated code then gets consistent names in every
  language.
- Name a `repeated` field with a **plural**: `repeated OrderLine lines`.
- Prefix every enum value with the enum's name in `UPPER_SNAKE_CASE`. Enum
  values share their enclosing scope, so two enums can't otherwise both have
  a value called `UNKNOWN`.
- End a service's name with `Service`, and name each method's messages after
  the method: `GetOrder` takes a `GetOrderRequest` and returns a
  `GetOrderResponse`.
- Never use a name that is a keyword in a language you generate code for,
  such as `class` or `type`. Generators rename it, and the names then differ
  between languages.

## Comments

- Use `//` comments.
- Put a comment directly above every message, enum, service and method, and
  above any field whose meaning isn't obvious from its name. Code generators
  copy these comments into the generated code's documentation.
- Comments describe **what** a definition means and its rules (units,
  ranges, when it's set), not how it's encoded.

## Sources

This guide starts from the Protocol Buffers style guide and borrows from:

- [Protocol Buffers style guide](https://protobuf.dev/programming-guides/style/)
- [Proto best practices](https://protobuf.dev/best-practices/dos-donts/)
- [Buf lint rules](https://buf.build/docs/lint/rules/)
