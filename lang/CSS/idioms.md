# CSS Idioms and Principles

How to write CSS well. [coding-style.md](coding-style.md) covers how
stylesheets look. This guide covers how they're structured: the idioms and
principles that keep styles predictable, maintainable and accessible. Every
example follows the style guide.

## Principles

- **Keep specificity low and flat.** Most selectors should be a single
  class. When every rule has about the same weight, source order and cascade
  layers decide which wins, and nobody needs `!important`.
- **Components are independent.** A component's styles live in its own
  block, and look the same wherever it's placed.
- **Respect the user's settings**: font size, reduced motion, colour scheme
  and contrast. They exist for accessibility.
- **Let the browser do the work.** Flexbox, grid, intrinsic sizing and
  `clamp()` adapt to content and screens, so fixed sizes and magic numbers
  become rare.
- **Style, don't script.** Use CSS for presentation and state styling, and
  leave behaviour to JavaScript.

## The cascade

- **Declare cascade layers once, at the top of the main stylesheet**, from
  lowest to highest priority. A later layer always beats an earlier one,
  whatever the selectors' specificity:

  ```css
  @layer reset, base, components, utilities;

  @layer components {
    .order-list {
      display: grid;
    }
  }
  ```

- Use the layers for what their names say:
  - `reset` normalises browser defaults.
  - `base` styles bare elements (`body`, `a`, `h1`).
  - `components` holds the BEM blocks.
  - `utilities` holds single-purpose helpers such as `.visually-hidden`, which
    must win over components.
- **Never use `!important`.** Fix the specificity or the layer order instead.
  An `!important` can only be beaten by another one, and they pile up.
- Use `:where()` in the `base` and `reset` layers to keep their selectors at
  zero specificity, so any component class overrides them.

## Naming and components

- **One BEM block per component**, in its own file named after the block.
  The [style guide](coding-style.md#naming) sets the naming rules.
- **Use a modifier instead of a context selector.** Don't style
  `.sidebar .card` to change cards in the sidebar. Add `.card--compact` to
  the markup, so the card's styles stay in one place.
- **Don't let components set their own outer margins.** Spacing between
  components belongs to the layout that contains them, often as `gap`.
  A component with built-in margins breaks in every new context.
- **Style state through attributes where HTML has one**: `[hidden]`,
  `[aria-expanded='true']`, `[aria-current='page']`, `:disabled`,
  `:checked`. The visual state then can't drift from what assistive
  technology reports. Use a BEM modifier for states with no attribute.

## Custom properties

- **Keep design tokens in custom properties on `:root`**: colours, spacing,
  font sizes and radii. Changing a token then updates everything that uses
  it:

  ```css
  :root {
    --color-danger: #c62828;
    --color-focus: #1a73e8;
    --color-primary: #1a73e8;
    --color-text: #1a1a1a;
    --radius-s: 0.25rem;
    --space-m: 1rem;
    --space-s: 0.5rem;
  }
  ```

- **Give components their own custom properties for the values a modifier
  changes**, so the modifier sets one variable instead of repeating
  declarations:

  ```css
  .button {
    --button-bg: var(--color-primary);

    background-color: var(--button-bg);
    border: 0;
    border-radius: var(--radius-s);
    color: #fff;
    padding-block: var(--space-s);
    padding-inline: var(--space-m);
  }

  .button--danger {
    --button-bg: var(--color-danger);
  }
  ```

- Name a component's custom properties after its block (`--button-bg`), so
  they can't collide with tokens or other components.

## Layout

- **Use flexbox for one dimension** (a row of buttons, a toolbar) and **grid
  for two** (a page layout, a card gallery).
- **Space items with `gap`**, not margins on the items. `gap` only appears
  between items, so there's no stray margin at the edges to cancel.
- Don't use floats or absolute positioning for page layout. Keep `float` for
  wrapping text around an image, and `position: absolute` for overlays
  anchored to a parent.
- **Let content size itself.** Prefer `min()`, `max()`, `clamp()`, `fr` and
  `auto` to fixed widths and heights. Fixed heights clip text when it grows
  or the user zooms.
- Limit line length for reading with `ch`: `max-inline-size: 65ch`.

## Responsive design

- **Write mobile-first.** Base styles target small screens, and
  `@media (width >= ...)` queries add to them for larger ones. Small screens
  then download and apply the least CSS.
- **Choose breakpoints where the content breaks**, not at particular devices.
- **Use relative units.** `rem` for font sizes and spacing, so they follow
  the user's font size. `em` for media queries. `%`, `fr` and viewport units
  for layout. `px` only for hairline details such as borders.
- Scale headings smoothly with `clamp()`:
  `font-size: clamp(1.5rem, 1rem + 2vw, 2.5rem);`.
- Stop images overflowing their container:

  ```css
  img {
    block-size: auto;
    max-inline-size: 100%;
  }
  ```

## Logical properties

- **Use logical properties** for anything with a direction: `margin-inline`,
  `padding-block`, `inline-size`, `inset-inline-start`, `text-align: start`.
  They follow the writing direction, so a right-to-left page (`dir="rtl"`)
  mirrors without extra rules.
- Physical properties are still right for things that really are physical,
  such as a shadow that falls downwards.

## Accessibility

- **Never remove the focus outline without a replacement.** Keyboard users
  need to see where they are. Style `:focus-visible`, which shows for keyboard
  focus but not mouse clicks:

  ```css
  :focus-visible {
    outline: 3px solid var(--color-focus);
    outline-offset: 2px;
  }
  ```

- **Only animate for users who haven't asked for less motion.** Put
  transitions and animations inside a `no-preference` query, so the default
  is no motion:

  ```css
  @media (prefers-reduced-motion: no-preference) {
    .drawer {
      transition: transform 200ms ease-out;
    }
  }
  ```

- **Meet WCAG AA contrast**: at least 4.5:1 for normal text, and 3:1 for
  large text and for the edges of controls.
- **Never use colour alone to carry meaning.** Pair it with text, an icon or
  a pattern, so colour-blind users get the message too.
- **Hide text visually but keep it for screen readers** with a
  `.visually-hidden` utility:

  ```css
  .visually-hidden {
    block-size: 1px;
    clip-path: inset(50%);
    inline-size: 1px;
    overflow: hidden;
    position: absolute;
    white-space: nowrap;
  }
  ```

- Never use `display: none` or `visibility: hidden` for content screen
  readers should read. Both hide it from everyone.
- Size text in `rem`, never `px`, so it grows when the user raises their
  browser's font size.

## Performance

- **Animate only `transform` and `opacity`.** The browser can animate them
  without recalculating layout. Animating `width`, `top` or `margin` makes it
  redo layout on every frame.
- Don't use `@import` in production stylesheets. Each one is another request
  the browser only discovers after downloading the file that contains it.
- Load web fonts with `font-display: swap` in `@font-face`, so text shows in
  a fallback font instead of staying invisible while the font downloads.
- Delete unused rules. Every rule is downloaded, parsed and matched on every
  page.

## Sources

- [MDN: Cascade, specificity and inheritance](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Cascade_and_inheritance)
- [MDN: Cascade layers](https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics/Cascade_layers)
- [MDN: CSS logical properties and values](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_logical_properties_and_values)
- [BEM methodology](https://en.bem.info/methodology/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
