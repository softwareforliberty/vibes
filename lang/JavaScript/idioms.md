# JavaScript Idioms and Principles

How to write plain JavaScript well, in the browser or on Node.js, with no
framework. [coding-style.md](coding-style.md) covers how code looks. This
guide covers how it's designed: the idioms and principles that keep
JavaScript code correct, safe and maintainable. Every example follows the
style guide.

## Principles

- **Clarity beats cleverness.** Prefer the obvious version unless profiling
  proves it too slow.
- **No hidden state.** Pass data in through parameters and get it back
  through return values. Shared mutable state and globals make code hard to
  follow and hard to test.
- **Fail loudly.** Throw real `Error` objects, and never swallow an error
  without handling it.
- **Every promise is awaited or handled.** A rejection nobody handles is a
  silently lost error.
- **Treat outside data as hostile.** Anything from the network, the URL,
  storage or the user is untrusted until it's validated, and is never
  executed or inserted as markup.

## Modules

- **One module, one job.** A module exports a small, named API and keeps
  everything else private by not exporting it.
- **No globals.** Don't assign to `window`, `globalThis` or undeclared
  variables. Modules already have their own scope, so share values by
  exporting and importing them.
- **Keep modules free of side effects at import time.** Importing a module
  should only define things. Start work (event listeners, timers, network
  requests) from an explicit function the entry point calls, so modules can
  be imported in tests without running anything.
- **One entry point** per page or program (`main.js`) wires the modules
  together and starts the application.

## Data and immutability

- **`const` stops reassignment, not mutation.** A `const` object can still be
  changed. Treat data as immutable by convention: build new values instead of
  changing existing ones:

  ```js
  const updated = { ...order, status: 'shipped' };
  const paid = orders.filter((order) => order.paid);
  ```

- Spread (`...`) makes **shallow** copies. Use `structuredClone()` when you
  need a deep copy.
- Freeze module-level constant tables with `Object.freeze()`, so a caller
  can't change shared data by accident.
- Sort a copy, not the original: `[...items].sort(compare)`. `sort()` and
  `reverse()` change the array in place.
- Use `Map` and `Set` for collections keyed by data. Plain objects are for
  records with known property names.
- Represent "no value" with `null`, and check for it with `=== null` or
  `??`. Leave `undefined` for "never set", such as missing properties and
  parameters.

## Errors

- **Throw only `Error` objects** (or subclasses), never strings or plain
  objects. Only `Error` carries a stack trace.
- **Use the right built-in type**: `TypeError` for a wrong type, `RangeError`
  for a value out of range. Define a subclass when callers need to tell your
  errors apart:

  ```js
  export class NotFoundError extends Error {
    constructor(message, options) {
      super(message, options);
      this.name = 'NotFoundError';
    }
  }
  ```

- **Keep the cause when you wrap an error**, so the original stack trace
  isn't lost:

  ```js
  try {
    return JSON.parse(text);
  } catch (err) {
    throw new SyntaxError(`Bad config file: ${path}`, { cause: err });
  }
  ```

- **Catch only where you can do something**: retry, fall back, or report to
  the user. Otherwise let the error propagate.
- **Never use an empty `catch`.** If ignoring an error really is right, say
  why in a comment.
- **Report each error once.** A function either logs an error or rethrows it,
  not both.
- Validate arguments at the edge of your public API and throw early, instead
  of failing deep inside with a confusing message.

## Async code

- **Use `async`/`await`**, not `.then()` chains or callbacks. The code reads
  top to bottom, and `try`/`catch` handles failures.
- **Never leave a promise floating.** Every promise is awaited, returned, or
  given a `.catch()`. In Node.js an unhandled rejection ends the process. In
  the browser it's lost.
- **Run independent work in parallel** with `Promise.all()`, rather than
  awaiting each step in a loop:

  ```js
  const [user, orders] = await Promise.all([
    loadUser(userId),
    loadOrders(userId),
  ]);
  ```

- Use `Promise.allSettled()` when every result matters, even if some fail.
- **Make long work cancellable** with an `AbortSignal`, and use one for
  timeouts on network requests:

  ```js
  const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  ```

- `fetch()` only rejects on network failure. Always check `response.ok`
  before using the body.
- Don't mix callbacks and promises in one API. Wrap old callback APIs once
  (Node.js has `util.promisify`) and use promises everywhere else.

## Iteration

- Use `for...of` to loop over arrays, strings, `Map` and `Set`. It reads
  values directly, and `break` and `await` work inside it.
- Use `map`, `filter` and `reduce` when you're building a new value from a
  collection. Use `for...of` when the loop has side effects.
- Never use `for...in` on arrays. It visits inherited properties and gives
  string indexes.
- To loop over an object's own properties, use `Object.entries()`,
  `Object.keys()` or `Object.values()`. To check for one, use
  `Object.hasOwn()`.

## The DOM

- **Put text in with `textContent`**, never `innerHTML`. `innerHTML` parses
  its input as markup, so untrusted data in it becomes a script injection
  hole:

  ```js
  const item = document.createElement('li');
  item.className = 'order-list__item';
  item.textContent = order.title;
  list.append(item);
  ```

- Build elements with `document.createElement()`, or clone a `<template>`
  from the page. Never assemble markup by concatenating strings.
- **Find elements by `data-` attributes, never by styling class**:
  `document.querySelector('[data-order-list]')`. Classes belong to the CSS,
  so a restyle shouldn't break the script.
- **Attach events with `addEventListener()`**, never with `on*` attributes in
  the HTML. Inline handlers can't run under a strict Content Security Policy.
- **Use event delegation for lists.** One listener on the container,
  checking `event.target.closest()`, handles items added later and costs less
  than a listener per item.
- **Show state through attributes the CSS can style**, preferring real
  attributes over classes: `hidden`, `aria-expanded`, `aria-current`,
  `disabled`. Use a BEM modifier class (see the
  [CSS idioms](../CSS/idioms.md)) only when no attribute fits.
- Look an element up once and keep the reference, instead of querying the
  DOM again on every event.
- Load scripts with `<script type="module">`, which runs after the page is
  parsed, so there's no need to wait for `DOMContentLoaded`.

## Security

- **Never execute strings as code.** No `eval()`, `new Function()`, or string
  arguments to `setTimeout()` and `setInterval()`.
- **Guard against prototype pollution.** When you copy, merge or index by
  keys that come from outside, never write the keys `__proto__`,
  `constructor` or `prototype`. Use a `Map`, or an object made with
  `Object.create(null)`, for dictionaries keyed by untrusted data.
- **Validate parsed data.** `JSON.parse()` returns whatever shape the input
  had. Check the fields you use before trusting them.
- **Build URLs with `URL` and `URLSearchParams`**, which encode each part,
  instead of concatenating strings.
- **Only follow URLs with a safe scheme.** Before putting an outside URL in
  `href` or `src`, check that its protocol is `https:` (or `http:`), never
  `javascript:`.
- **On Node.js, never build shell commands from data.** Use
  `child_process.execFile()` or `spawn()` with an argument array, not
  `exec()`. Pass values to databases through parameters, never by string
  concatenation.
- Never put secrets in browser code. Anything sent to the browser is public.
- Keep dependencies few, pinned in a lockfile, and audited
  (`npm audit`).

## Node.js

- Import built-ins with the `node:` prefix (`node:path`, `node:fs/promises`),
  so they can't be confused with packages of the same name.
- Use the promise-based APIs (`node:fs/promises`). The synchronous ones
  (`readFileSync`) block every other request, and belong only in start-up
  code and scripts.
- Read configuration from the environment once, at start-up, validate it,
  and pass it down. Don't read `process.env` throughout the code.
- Exit with a non-zero status on failure, so scripts and supervisors can
  tell something went wrong.

## Testable design

- Write pure functions where you can: same input, same output, no side
  effects. They need no setup to test.
- Pass dependencies in (a `fetch` function, a clock, a storage object)
  instead of reaching for globals, so tests can supply fakes.
- Keep DOM code thin. Put the logic in plain functions that take and return
  data, and test those.

## Performance

- **Measure before you optimise**, with the browser's performance tools or
  Node.js's profiler.
- Batch DOM changes. Reading layout (`offsetHeight`,
  `getBoundingClientRect()`) straight after writing styles forces the browser
  to recalculate layout each time.
- Debounce or throttle handlers for frequent events such as `input`,
  `scroll` and `resize`.
- Load code only when needed, using dynamic `import()` for rarely used
  features.

## Sources

- [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide)
- [Google JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)
- [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- [OWASP DOM-based XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/DOM_based_XSS_Prevention_Cheat_Sheet.html)
- [OWASP Prototype Pollution Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Prototype_Pollution_Prevention_Cheat_Sheet.html)
- [Node.js documentation](https://nodejs.org/docs/latest/api/)
