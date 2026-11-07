# JavaScript Coding Style

A general-purpose coding style for plain, modern JavaScript: ES2022 modules
running in the browser or on Node.js, with no framework. It builds on the
[Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html),
the [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript) and
[MDN](https://developer.mozilla.org/en-US/docs/Web/JavaScript) (see
[Sources](#sources)).

This guide covers how code looks. For how to design and structure it (modules,
immutability, errors, async code, DOM and injection safety), see
[idioms.md](idioms.md). For the markup and styles that JavaScript works with,
see the [HTML](../../web/HTML/coding-style.md) and [CSS](../../web/CSS/coding-style.md)
guides.

The tools that check JavaScript code are listed in [tools.md](tools.md).

## Language baseline

The baseline language is **ES2022**: modules, class fields with `#private`
members, `Object.hasOwn()`, top-level `await` and `Error` causes.

## Layout

### Indentation

- Indent with **2 spaces**. Never use tabs.
- When a call, array, object or parameter list doesn't fit on one line, put
  one item per line and end with a trailing comma. Adding an item then changes
  only one line in a diff:

  ```js
  const order = createOrder({
    customerId,
    items,
    shipping: 'express',
  });
  ```

### Line length

- **80 columns**. The formatter wraps code. Rewrite comments and long strings
  yourself.
- Don't break a user-visible string across lines just to fit, so it stays
  greppable. Let that line run long.

### Semicolons and braces

- End every statement with a semicolon. Relying on automatic semicolon
  insertion lets a line that starts with `(`, `[` or `` ` `` join onto the
  one before it.
- Always use braces, even for a one-line body. The opening brace goes at the
  end of the line, and `else`, `catch` and `finally` go on the same line as
  the closing brace:

  ```js
  if (!user) {
    return null;
  }

  try {
    await save(user);
  } catch (err) {
    log.error('Save failed', err);
  }
  ```

### Blank lines

- Separate top-level functions and classes, and the methods inside a class,
  with one blank line.
- Use single blank lines inside a function to separate its logical steps.
  Never use more than one in a row.

### Files

- Use UTF-8 with LF line endings, and end every file with a newline.
- One module per file. Name files in lowercase kebab-case, ending in `.js`:
  `order-summary.js`. Kebab-case is safe on case-insensitive file systems and
  matches the HTML and CSS naming.

### One thing per line

- One statement per line.
- One variable per declaration: `const a = 1;` then `const b = 2;`, never
  `const a = 1, b = 2;`.

## Imports and exports

- Use ES modules (`import`/`export`) only. Don't use CommonJS `require()`.
- Put all imports at the top of the file, grouped in this order with a blank
  line between groups:
  1. Node.js built-ins, with the `node:` prefix (`node:fs/promises`)
  2. Packages
  3. Your own modules, by relative path
- Write the file extension in every relative import:
  `import { total } from './cart.js';`. Browsers and Node.js both require it.
- **Use named exports only.** Don't use `export default`. Named exports keep
  one name for each thing across the codebase, and tools can rename and find
  them.
- Don't use wildcard re-exports (`export * from`). List what the module
  exports so readers can see its public API in one place.

## Strings

- Use single quotes: `'text'`.
- Use template literals for interpolation and multi-line strings, never `+`
  concatenation: `` `Hello, ${name}` ``.
- Don't escape a quote where a different quote would avoid it. Prettier picks
  the quote style that needs the fewest escapes.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Variables, functions, methods, parameters | `camelCase` | `orderTotal`, `fetchOrders()` |
| Classes | `PascalCase` | `OrderQueue`, `HttpClient` |
| Module-level constants that never change | `UPPER_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_TIMEOUT_MS` |
| Private class members | `#camelCase` | `#pending`, `#flush()` |
| Files | `kebab-case.js` | `order-queue.js` |

- Treat acronyms as words: `HttpClient`, `userId`, `parseUrl()`. This keeps
  word boundaries clear when two acronyms meet.
- Name booleans as questions: `isOpen`, `hasItems`, `canRetry`.
- Name functions with a verb (`loadOrders()`, `formatPrice()`) and values
  with a noun.
- Include the unit in names that hold quantities: `timeoutMs`, `sizeBytes`.
- Don't use a leading or trailing underscore to mean "private". Use real
  `#private` members, or don't export the name.
- Use `UPPER_SNAKE_CASE` only for primitive values and deeply frozen data
  that's fixed when the module loads. A `const` that holds a mutable object
  is a normal `camelCase` variable.

## Declarations

- Use `const` by default. Use `let` only when the variable is reassigned.
  Never use `var`: it's function-scoped and hoisted, which causes surprising
  bugs.
- Declare each variable where it's first needed, in the narrowest scope that
  works.
- Use object and array shorthand: `{ name, total }`, not
  `{ name: name, total: total }`.
- Use destructuring to pull out several properties at once:
  `const { id, items } = order;`.

## Functions

- Write named top-level functions as function declarations:
  `function formatPrice(cents) { ... }`.
- Use arrow functions for callbacks and other short inline functions. They
  keep the surrounding `this`, so no `.bind()` is needed.
- Give parameters default values in the signature instead of patching them
  in the body: `function retry(fn, attempts = 3)`.
- Use rest parameters (`...args`), never the `arguments` object.
- When a function takes more than three parameters, or any optional ones,
  take a single options object instead. Callers then name every argument:
  `connect({ host, port, timeoutMs: 5000 })`.
- Don't reassign or mutate parameters. Make a local copy if you need to
  change a value.
- Keep functions short and focused on one thing.

## Classes

- Use `class` syntax. Never assign to `prototype` directly.
- Declare fields at the top of the class body, public fields first, then
  `#private` ones, then the constructor, then methods.
- Use `#private` fields and methods for anything outside the class's API.
- Don't extend built-in types other than `Error`.

## Expressions

- Always use `===` and `!==`. Loose equality (`==`) applies type conversions
  that are hard to predict.
- Use optional chaining (`?.`) and nullish coalescing (`??`) for values that
  may be `null` or `undefined`. Don't use `||` for defaults, because it also
  replaces `0`, `''` and `false`.
- Don't nest ternaries. Use `if`/`else` or a lookup table.
- Use parentheses to make mixed-operator precedence obvious:
  `(a && b) || c`.

## Comments

- Use `//` for comments, on their own line above the code they describe.
  Write them as full sentences that explain **why**, not **what**.
- Document every exported function, class and constant with a **JSDoc**
  `/** ... */` comment. It describes the contract: parameters, return value,
  thrown errors, and types where they aren't obvious:

  ```js
  /**
   * Returns the order total in cents, including tax.
   *
   * @param {Order} order The order to price.
   * @param {number} taxRate Tax rate as a fraction, such as 0.2 for 20%.
   * @returns {number} The total in cents.
   * @throws {RangeError} If `taxRate` is negative.
   */
  export function orderTotal(order, taxRate) {
  ```

- Don't leave commented-out code. Version control keeps the history.
- A `// TODO:` comment says what's missing and links to an issue.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted. List them in `.prettierignore` and in ESLint's `ignores`.

## Sources

- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [MDN JavaScript reference](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
- [ESLint rules](https://eslint.org/docs/latest/rules/)
- [Prettier options](https://prettier.io/docs/en/options.html)
