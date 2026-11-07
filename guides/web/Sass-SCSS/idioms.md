# Sass (SCSS) Idioms and Principles

How to write Sass well. [coding-style.md](coding-style.md) covers how
stylesheets look. This guide covers how they're structured: the idioms and
principles that keep Sass predictable and maintainable. Every example
follows the style guide.

Sass compiles to CSS, so the [CSS idioms](../CSS/idioms.md) apply to
everything it produces: the cascade and layers, BEM components, custom
properties, layout, responsive design, logical properties, accessibility
and performance. This guide covers what Sass adds.

## Principles

- **Sass is a build tool for CSS.** Use it to organise source and to compute
  values at build time, not to generate large amounts of CSS.
- **Read the output.** Every Sass feature becomes plain CSS. If the compiled
  CSS is bigger, more specific or harder to follow than hand-written CSS
  would be, the Sass is wrong.
- **Prefer CSS features to Sass features** when both work. Custom
  properties, `calc()`, `clamp()` and cascade layers run in the browser and
  respond to the page; Sass values are fixed when the stylesheet compiles.
- **Every module has a clear API.** Members other files use are public;
  everything else is private.

## Modules

- **Organise partials by role**, each directory with an `_index.scss` that
  forwards its public members:
  - `tokens/`: design-token variables and maps
  - `mixins/` and `functions/`: reusable helpers
  - `base/`: element styles, in the `base` cascade layer
  - `components/`: one BEM block per partial, in the `components` layer
- **One entry point per CSS file** (`main.scss`) loads everything with
  `@use`, in cascade-layer order.
- **Configure a library once, with `@use ... with`**, instead of overriding
  its variables after loading it:

  ```scss
  @use 'tokens' with (
    $space-base: 0.25rem
  );
  ```

  Give configurable variables a `!default` value in the library, and make
  everything else private.

- **Re-export with `@forward`**, and use `show` or `hide` to keep a
  directory's API small:

  ```scss
  // tokens/_index.scss
  @forward 'colors';
  @forward 'spacing' show $space-s, $space-m, $space-l;
  ```

## Variables and custom properties

- **Use Sass variables for build-time values**: breakpoints, which media
  queries can't read from custom properties, and inputs to Sass functions.
- **Use custom properties for everything the browser should see**: colours,
  spacing and other design tokens that themes or components change at run
  time, as the [CSS idioms](../CSS/idioms.md#custom-properties) describe.
- When a token is needed in both places, define it once in Sass and emit it
  as a custom property, so the two can't drift:

  ```scss
  $colors: (
    'primary': #1a73e8,
    'danger': #c62828,
  );

  :root {
    @each $name, $value in $colors {
      --color-#{$name}: #{$value};
    }
  }
  ```

- Never change a variable's value partway through a file. Sass variables are
  read at the point they're used, so reassigning one makes the output depend
  on source order.

## Mixins, functions and placeholders

- **Use a function to compute a value**, and a **mixin to output
  declarations**. A function never outputs CSS, and a mixin never returns a
  value.
- **Keep mixins small.** A mixin's whole body is copied into every rule that
  includes it, so a large mixin bloats the output.
- **Don't use `@extend`.** It moves the extending selector into every place
  the extended one appears, across files and media queries, which produces
  selectors and specificity nobody wrote. Use a mixin, or a shared class in
  the markup.
- Give mixins and functions explicit parameters with defaults, and pass
  named arguments when a call has more than one:
  `@include truncate($lines: 2)`.
- Use `@content` for mixins that wrap rules, such as a breakpoint mixin, so
  every breakpoint is written the same way:

  ```scss
  @use 'sass:map';
  @use 'tokens';

  @mixin from($breakpoint) {
    @media (width >= map.get(tokens.$breakpoints, $breakpoint)) {
      @content;
    }
  }
  ```

- Validate arguments with `@error` and a message that names the mixin or
  function, so a wrong call fails the build instead of producing bad CSS.

## Control flow

- Use `@each` and `@for` to generate a small, known set of rules from a map,
  such as one utility class per spacing token.
- Don't generate large utility sets "just in case". Every generated rule is
  shipped to every page whether it's used or not.
- Keep `@if` logic inside functions and mixins, not in component rules.

## Maths and units

- Do unit arithmetic with matching units, and convert explicitly. Sass
  refuses to add `px` to `rem`, which catches unit mistakes at build time.
- Use `math.div()` for division, and the `sass:math` module for rounding and
  other maths.
- Leave arithmetic the browser should do (anything involving percentages of
  the viewport or container, or custom properties) to CSS `calc()`.

## Output

- **Compile with source maps** in development, so browser tools point to the
  `.scss` source.
- Compile with `--style=compressed` for production.
- Treat every deprecation warning as an error. Deprecated features are
  removed in a later major release, and fixing them early is cheapest.

## Sources

- [Sass documentation](https://sass-lang.com/documentation/)
- [Sass: @use](https://sass-lang.com/documentation/at-rules/use/)
- [Sass: @forward](https://sass-lang.com/documentation/at-rules/forward/)
- [Sass: @extend](https://sass-lang.com/documentation/at-rules/extend/)
- [CSS idioms](../CSS/idioms.md)
