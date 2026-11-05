# TypeScript Coding Style

A general-purpose coding style for plain, modern TypeScript: ES modules
running in the browser or on Node.js, with no framework. It builds on the
[Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
and the [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/),
and it extends the [JavaScript coding style](../JavaScript/coding-style.md)
(see [Sources](#sources)).

TypeScript is JavaScript with types, so every rule in the JavaScript coding
style applies to TypeScript code too: layout, semicolons, braces, imports,
strings, naming, declarations, functions, classes and expressions. This guide
adds the rules for types. For how to design and structure code (modelling
data with types, handling outside data and errors), see
[idioms.md](idioms.md).

The tools that check TypeScript code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **TypeScript 5.8** with the `strict` compiler options shown in
[tools.md](tools.md#configuration), compiling to **ES2022**. TypeScript 5.8
adds `erasableSyntaxOnly`, which limits code to syntax that can be removed
without changing behaviour. Node.js 22.18 and later can then run `.ts` files
directly by stripping the types, with no build step.

## Files

- Use UTF-8 with LF line endings, and end every file with a newline.
- One module per file. Name files in lowercase kebab-case, ending in `.ts`:
  `order-summary.ts`. Kebab-case matches the JavaScript, HTML and CSS naming.
- Name test files after the module they test: `order-summary.test.ts`.

## Imports and exports

- Follow the [JavaScript import rules](../JavaScript/coding-style.md#imports-and-exports):
  ES modules only, named exports only, no wildcard re-exports, and imports
  grouped at the top of the file.
- Write the `.ts` extension in every relative import:
  `import { total } from './cart.ts';`. Node.js needs the real file name to
  run the source directly, and the compiler rewrites it to `.js` when it
  emits.
- Import types with `import type`, so the import is erased completely and
  never loads a module at run time:

  ```ts
  import type { Order } from './order.ts';
  import { orderTotal } from './order-total.ts';
  ```

## Naming

The [JavaScript naming rules](../JavaScript/coding-style.md#naming) apply,
plus these:

| Kind | Convention | Example |
| --- | --- | --- |
| Types, interfaces | `PascalCase` | `Order`, `PaymentResult` |
| Type parameters | `T`, or `T` plus a name | `T`, `TItem`, `TKey` |
| String literal union members | `kebab-case` or `lowercase` | `'pending'`, `'in-transit'` |

- Don't prefix interfaces with `I` (`IOrder`) or suffix types with `Type`.
  The name says what the thing is, not how it's declared.
- Use a single `T` only when a function or type has one type parameter and
  its meaning is obvious. Otherwise give each one a name: `TItem`, `TKey`.
- Treat acronyms as words, as in JavaScript: `HttpClient`, `UserId`.

## Types

### Declaring types

- Use an **`interface` for object shapes** and a **`type` alias** for
  everything else: unions, intersections, tuples, function types and mapped
  types. Interfaces give clearer error messages and can't accidentally
  become a union.
- Separate interface members with semicolons, one per line:

  ```ts
  interface Order {
    readonly id: string;
    items: readonly LineItem[];
    status: OrderStatus;
  }

  type OrderStatus = 'pending' | 'paid' | 'shipped';
  ```

- Write array types as `T[]` and `readonly T[]`. Use `Array<T>` only when the
  element type is itself complex, such as `Array<string | number>`.
- Mark properties that never change after creation as `readonly`.
- Make a property optional (`note?: string`) only when it can be missing.
  Don't use `| undefined` on a property to mean "optional".

### Annotations

- **Annotate the parameters and return type of every exported function and
  method.** The signature is the module's contract, and an explicit return
  type stops an implementation change from silently changing the API.
- **Let TypeScript infer local variables.** Don't annotate what's already
  obvious from the value: `const total = 0;`, not
  `const total: number = 0;`.
- Annotate a variable when it starts empty and is filled later, so its type
  is clear: `const ids: string[] = [];`.

### Forbidden constructs

- **Never use `any`.** It switches type checking off for everything it
  touches. Use `unknown` for values whose type isn't known yet, and narrow
  them before use.
- **Never use non-null assertions** (`value!`). Check for `null` instead, so
  the code handles the case the type allows.
- **Avoid type assertions** (`value as Order`). An assertion overrides the
  compiler instead of proving anything. Use `satisfies` to check a value
  against a type without changing its type, and use a type guard to narrow
  outside data (see [idioms.md](idioms.md#outside-data)).
- **Don't use `enum`, `namespace` or constructor parameter properties.**
  They generate run-time code, so they can't be erased by type stripping.
  Use a union of string literals instead of an enum, and ordinary modules
  instead of namespaces.
- Don't use `@ts-ignore`. If a suppression is truly needed, use
  `@ts-expect-error` with a comment saying why, so it fails once the error
  goes away.
- Don't use the wrapper types `String`, `Number`, `Boolean` or `Object`. Use
  `string`, `number`, `boolean` and `object`.

## Classes

The [JavaScript class rules](../JavaScript/coding-style.md#classes) apply,
plus these:

- Use `#private` members, not the `private` keyword. `private` is only
  checked by the compiler, while `#private` is enforced at run time.
- Mark methods that override a parent method with `override`.
- Declare fields with their types at the top of the class body, and assign
  them in the constructor. Don't use parameter properties
  (`constructor(private readonly db: Db)`), which can't be type-stripped.

## Comments

- Follow the [JavaScript comment rules](../JavaScript/coding-style.md#comments).
- Document every exported function, class, type and constant with a
  `/** ... */` comment. Don't repeat the types in `@param` or `@returns` tags:
  the signature already states them.

  ```ts
  /**
   * Returns the order total in cents, including tax.
   *
   * @param order The order to price.
   * @param taxRate Tax rate as a fraction, such as 0.2 for 20%.
   * @throws {RangeError} If `taxRate` is negative.
   */
  export function orderTotal(order: Order, taxRate: number): number {
  ```

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted. List them in `.prettierignore` and in ESLint's `ignores`, and
exclude them from `tsconfig.json`.

## Sources

- [Google TypeScript Style Guide](https://google.github.io/styleguide/tsguide.html)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/)
- [TypeScript compiler options](https://www.typescriptlang.org/tsconfig/)
- [Node.js: Running TypeScript natively](https://nodejs.org/en/learn/typescript/run-natively)
- [JavaScript coding style](../JavaScript/coding-style.md)
