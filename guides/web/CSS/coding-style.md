# CSS Coding Style

A general-purpose coding style for plain CSS, with no preprocessor or
framework. It builds on the
[Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html),
[MDN](https://developer.mozilla.org/en-US/docs/Web/CSS) and the conventions
of [stylelint-config-standard](https://github.com/stylelint/stylelint-config-standard)
(see [Sources](#sources)).

This guide covers how stylesheets look. For how to structure them (the
cascade, naming, layout, responsive design and accessibility), see
[idioms.md](idioms.md). For the markup and scripts that work with them, see
the [HTML](../HTML/coding-style.md) and
[JavaScript](../../languages/JavaScript/coding-style.md) guides.

The tools that check CSS code are listed in [tools.md](tools.md).

## Language baseline

Write for browsers that support every feature in **Baseline Widely available**:
features that have worked in all the major browsers (Chrome, Edge, Firefox and
Safari, on desktop and mobile) for at least 30 months. That level also covers
the JavaScript guide's
[ES2022 baseline](../../languages/JavaScript/coding-style.md#language-baseline). Check a
newer feature's Baseline status on MDN before using it, and give it a fallback
until it's widely available.

## Layout

### Indentation and line length

- Indent with **2 spaces**. Never use tabs.
- **80 columns**. Prettier wraps long values.

### Rules and declarations

- Put each selector in a list on its own line.
- Put a space before the opening brace, one declaration per line, and the
  closing brace on its own line.
- Put a space after the colon, and end **every** declaration with a
  semicolon, including the last. Adding a declaration then never breaks the
  one before it.
- Separate rules with one blank line.

```css
h1,
h2 {
  font-weight: 600;
  line-height: 1.2;
}

.order-list {
  display: grid;
  gap: 1rem;
  list-style: none;
  margin: 0;
  padding: 0;
}
```

### Declaration order

- List declarations in **alphabetical order** by property name. There's
  nothing to debate, and a property is easy to find in a long rule.
- Custom properties come first, in their own group, then a blank line, then
  the other declarations.

### Files

- Use UTF-8 with LF line endings, and end every file with a newline.
- Name files in lowercase kebab-case: `order-list.css`.
- Split styles into one file per component, and combine them in the build
  rather than with `@import`, which makes the browser download them one after
  another.

## Values

- Write `0` without a unit: `margin: 0`, not `margin: 0px`.
- Write a leading zero on decimals: `0.5rem`, not `.5rem`.
- Write hex colours in lowercase, in the short form where one exists:
  `#fff`, `#2e7d32`.
- Write colours with transparency in the modern space-separated notation:
  `rgb(0 0 0 / 50%)`.
- Quote strings and URLs with single quotes: `url('/img/logo.svg')`,
  `content: ''`.
- Quote font names only when they need it (spaces or digits):
  `font-family: 'Source Sans 3', Inter, sans-serif;`.
- Write keywords in lowercase: `display: block`, `color: currentcolor`.
- Use a shorthand property (`margin`, `padding`, `font`) when you set all of
  its parts. Use the longhand when you mean to change just one part, so you
  don't reset the others by accident.
- Don't write vendor prefixes by hand. Prefix in the build if you must
  support old browsers.

## Selectors

- **Style components with classes.** Use bare element selectors (`h1`, `a`,
  `img`) only for the base styles every page shares.
- Never select by `id`, which can't be reused and has very high specificity.
- **Don't style `data-` attributes.** They're JavaScript hooks, as set out in
  the [HTML guide](../HTML/coding-style.md#naming). Do style real state
  attributes such as `[hidden]`, `[aria-expanded='true']` and `:disabled`.
- Don't qualify a class with an element (`ul.order-list`). It adds
  specificity and stops the class working on other elements.
- Keep selectors short. A BEM class rarely needs a descendant selector.
- Don't nest rules. Nesting raises specificity and hides the full selector
  from anyone searching for it.
- Use `::` for pseudo-elements (`::before`) and `:` for pseudo-classes
  (`:hover`).

## Naming

- Name classes with **BEM** in lowercase kebab-case:
  - **Block**: a standalone component, such as `order-list`.
  - **Element**: a part of a block, joined with `__`, such as
    `order-list__item`.
  - **Modifier**: a variant or state, joined with `--`, such as
    `order-list__item--paid`.
- An element never belongs to another element: write `order-list__price`, not
  `order-list__item__price`.
- Name custom properties and `@keyframes` in kebab-case, starting with what
  they're for: `--color-text`, `--space-m`, `fade-in`.

## Media queries

- Write media queries in **range syntax**, with breakpoints in `em`:
  `@media (width >= 40em)`. It reads like a comparison, and `em` breakpoints
  follow the user's font size.
- Put a media query next to the base rule it changes, rather than collecting
  every breakpoint at the end of the file:

  ```css
  .order-list {
    display: grid;
    gap: 1rem;
  }

  @media (width >= 40em) {
    .order-list {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  ```

## Comments

- Use `/* */`, the only comment syntax CSS has.
- Start each file, or each group of related rules, with a short comment
  saying what it styles.
- Explain values that aren't obvious, such as a magic number or a browser
  workaround:
  `/* Matches the header height, so anchors aren't hidden under it. */`.
- Don't leave commented-out rules. Version control keeps the history.

## Third-party code

Vendored third-party stylesheets keep their upstream style and are not
reformatted. List them in `.prettierignore` and `.stylelintignore`.

## Sources

- [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- [MDN CSS reference](https://developer.mozilla.org/en-US/docs/Web/CSS)
- [stylelint-config-standard](https://github.com/stylelint/stylelint-config-standard)
- [Stylelint rules](https://stylelint.io/user-guide/rules/)
- [BEM methodology](https://en.bem.info/methodology/)
- [Prettier options](https://prettier.io/docs/en/options.html)
