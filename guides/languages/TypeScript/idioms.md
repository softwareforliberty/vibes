# TypeScript Idioms and Principles

How to write TypeScript well, in the browser or on Node.js, with no
framework. [coding-style.md](coding-style.md) covers how code looks. This
guide covers how it's designed: using the type system to keep code correct,
safe and maintainable. Every example follows the style guide.

TypeScript compiles to JavaScript, so the
[JavaScript idioms](../JavaScript/idioms.md) apply to all run-time behaviour:
modules, immutability, errors, async code, the DOM, security and Node.js.
This guide covers what the types add.

## Principles

- **Types are the design.** Write the types first. A function whose types are
  right is hard to call wrongly.
- **Make invalid states unrepresentable.** Model data so that combinations
  that can't happen can't be written either.
- **Trust the types inside, check the data at the edges.** Everything that
  comes from outside the program is `unknown` until it's validated. Inside,
  the compiler's guarantees hold.
- **Never lie to the compiler.** `any`, `!` and `as` all tell it to stop
  checking. Each one is a place where a bug can hide.
- **Types are erased at run time.** They describe JavaScript values; they
  don't create, convert or check anything when the program runs.

## Modelling data

- **Use discriminated unions for values with several shapes.** Give each
  variant a literal `kind` field, and only the fields that variant has:

  ```ts
  type Payment =
    | { kind: 'card'; last4: string }
    | { kind: 'invoice'; dueDate: string }
    | { kind: 'free' };
  ```

  A `Payment` can't be a card without `last4`, and code reading `dueDate`
  must first check that it's an invoice.

- **Replace boolean flags with a status union.** Two booleans
  (`isLoading`, `hasError`) allow four combinations, one of them impossible.
  A `status: 'loading' | 'failed' | 'ready'` field allows exactly three.
- **Use string literal unions instead of enums**, and get the list of values
  from a constant when code needs to loop over them:

  ```ts
  export const ORDER_STATUSES = ['pending', 'paid', 'shipped'] as const;

  export type OrderStatus = (typeof ORDER_STATUSES)[number];
  ```

- **Brand values that share a primitive type but mustn't be mixed**, such as
  IDs of different entities or amounts in different units:

  ```ts
  type OrderId = string & { readonly brand: 'OrderId' };
  type Cents = number & { readonly brand: 'Cents' };
  ```

  Create branded values only in one function that validates them, so the
  brand means something.

- **Make data immutable in the type.** Use `readonly` properties,
  `readonly T[]` and `ReadonlyMap`, so the compiler rejects mutation instead
  of relying on convention.
- Derive related types instead of repeating them: `Pick<Order, 'id'>`,
  `Omit<Order, 'items'>`, `Partial<Settings>`. A derived type can't drift
  from its source.

## Exhaustive handling

- **Handle every variant of a union.** Switch on the discriminant, and end
  with a check that only compiles when every case is handled:

  ```ts
  function describe(payment: Payment): string {
    switch (payment.kind) {
      case 'card':
        return `Card ending ${payment.last4}`;
      case 'invoice':
        return `Invoice due ${payment.dueDate}`;
      case 'free':
        return 'No charge';
      default:
        return assertNever(payment);
    }
  }

  export function assertNever(value: never): never {
    throw new Error(`Unexpected value: ${JSON.stringify(value)}`);
  }
  ```

  Adding a fourth payment kind then fails to compile until `describe()`
  handles it.

## Outside data

- **Type everything from outside as `unknown`**: `JSON.parse()` results,
  `fetch()` bodies, messages, storage and environment variables. `unknown`
  forces a check before use; `any` would let a wrong shape flow through the
  whole program.
- **Narrow with type guards that really check.** A guard's body must test
  every field the type promises:

  ```ts
  function isLineItem(value: unknown): value is LineItem {
    return (
      typeof value === 'object' &&
      value !== null &&
      'sku' in value &&
      typeof value.sku === 'string' &&
      'quantity' in value &&
      Number.isInteger(value.quantity)
    );
  }
  ```

- Use an assertion function (`asserts value is Order`) when invalid data
  should throw rather than branch.
- **Validate once, at the edge**, and pass the typed value inward. Code
  inside the program then never re-checks.
- A schema library that validates and infers the type in one place is a good
  fit for large or nested data. Keep it at the edges too.

## Errors

- **Treat caught errors as `unknown`.** Anything can be thrown, so check
  before using it:

  ```ts
  try {
    await saveOrder(order);
  } catch (err) {
    if (err instanceof NotFoundError) {
      return null;
    }
    throw err;
  }
  ```

- For failures callers are expected to handle, consider returning a result
  union instead of throwing, so the type forces the caller to deal with
  them:

  ```ts
  type Result<T, E> = { ok: true; value: T } | { ok: false; error: E };
  ```

- Keep throwing for bugs and for failures nobody nearby can handle, as the
  [JavaScript idioms](../JavaScript/idioms.md#errors) describe.

## Functions and generics

- **Accept the widest type you can use, return the narrowest you can
  promise.** Take `readonly T[]` or `Iterable<T>` as input, so callers can pass
  any list. Return a precise type, so callers get the most information.
- **Use a generic only when it links types.** A type parameter that appears
  once (`function log<T>(value: T): void`) does nothing that `unknown`
  wouldn't. Generics earn their place when they connect an input to an
  output:

  ```ts
  export function first<T>(items: readonly T[]): T | undefined {
    return items[0];
  }
  ```

- Constrain type parameters to what the function needs:
  `<T extends { id: string }>`.
- Prefer union parameters to overloads. Overloads are hard to read and their
  implementation signature isn't checked against them.
- Don't use optional parameters to mean several different call shapes. Use
  an options object, as in JavaScript.

## Module boundaries

- **Export types alongside the functions that use them**, so callers can
  name them.
- Keep internal types unexported, like internal functions.
- Don't let library types leak through your API. Wrap a third-party type in
  your own when it's part of a public signature, so swapping the library
  doesn't break callers.
- Libraries publish declaration files (`"declaration": true`), so users get
  the types without the source.

## Testable design

- Pass dependencies in through typed interfaces (a clock, a storage, an HTTP
  client), so tests can supply fakes that the compiler checks.
- Test the edges where data is validated: a guard that's wrong breaks every
  guarantee behind it.
- Use `@ts-expect-error` in tests to prove that invalid calls don't compile.

## Sources

- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [TypeScript Handbook: Narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [JavaScript idioms](../JavaScript/idioms.md)
