# Sass (SCSS) Coding Style

A general-purpose coding style for Sass in the SCSS syntax, compiled with
[Dart Sass](https://sass-lang.com/dart-sass/). It builds on the
[Sass documentation](https://sass-lang.com/documentation/), the conventions
of [stylelint-config-standard-scss](https://github.com/stylelint-scss/stylelint-config-standard-scss),
and the [CSS coding style](../CSS/coding-style.md) (see [Sources](#sources)).

SCSS is a superset of CSS, so every rule in the CSS coding style applies to
the CSS that a stylesheet contains and produces: layout, declaration order,
values, selectors, BEM naming, media queries and the ban on nesting. This
guide adds the rules for Sass features. For how to structure stylesheets
(modules, variables, mixins and functions), see [idioms.md](idioms.md).

The tools that check Sass code are listed in [tools.md](tools.md).

## Language baseline

The baseline is **Dart Sass 1.80** with the SCSS syntax. Dart Sass 1.80
deprecates `@import` and the global built-in functions in favour of the
module system, so every deprecation it reports can be treated as an error.
Don't use the indented `.sass` syntax, LibSass or Ruby Sass; the last two are
no longer maintained.

## Layout

- Follow the [CSS layout rules](../CSS/coding-style.md#layout): 2-space
  indentation, 80 columns, one declaration per line, and a semicolon after
  every declaration. Prettier formats SCSS with the same settings.
- Put a blank line between a rule's groups, in this order:
  1. Custom properties
  2. `@include` calls without a content block
  3. Declarations, in alphabetical order
  4. Nested at-rules, such as `@media` or an `@include` with a content block

```scss
@use 'mixins';
@use 'tokens';

.order-list {
  --order-list-gap: #{tokens.$space-m};

  @include mixins.reset-list;

  display: grid;
  gap: var(--order-list-gap);

  @media (width >= tokens.$breakpoint-m) {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

## Files

- Use the `.scss` extension, UTF-8 and LF line endings, and end every file
  with a newline.
- Name every file that's only loaded by other files as a **partial**, with a
  leading underscore and in kebab-case: `_order-list.scss`. Sass then never
  compiles it on its own.
- Give each directory of partials an `_index.scss` that `@forward`s them, so
  the directory can be loaded with one `@use`.
- Keep one BEM block per partial, named after the block, as in CSS.
- Only entry-point files, which produce a CSS file each, have no underscore:
  `main.scss`.

## Modules

- **Load every file with `@use` or `@forward`, never `@import`.** `@import`
  is deprecated, makes every name global, and loads a file again each time
  it's imported.
- Put all `@use` rules at the top of the file, built-in modules first, then
  your own, each group sorted alphabetically:

  ```scss
  @use 'sass:map';
  @use 'sass:math';
  @use 'tokens';
  @use 'typography';
  ```

- Call built-in functions through their module: `math.div($a, $b)`,
  `map.get($map, key)`. Their global versions (`map-get()`) are deprecated.
- Keep the default namespace, which is the file name. Use `as` only to
  resolve a clash, never `as *`, which makes every member global again.

## Naming

| Kind | Convention | Example |
| --- | --- | --- |
| Variables | `$kebab-case` | `$space-m`, `$breakpoint-l` |
| Mixins, functions | `kebab-case` | `reset-list`, `rem()` |
| Placeholder selectors | `%kebab-case` | `%visually-hidden` |
| Private members | leading `-` | `$-base-size`, `-scale()` |
| Partials | `_kebab-case.scss` | `_order-list.scss` |

- Name classes with BEM, as the [CSS naming rules](../CSS/coding-style.md#naming)
  describe.
- Prefix members that are only used inside their own file with `-`. Sass
  hides them from other modules.
- Name variables after their purpose, not their value: `$color-danger`, not
  `$red`.

## Nesting

- **Don't nest selectors**, as in CSS. Write every rule at the top level with
  its full BEM class.
- **Don't build class names with `&`** (`&__item`, `&--paid`). The full
  class name then never appears in the source, so searching for it finds
  nothing.
- Nesting is allowed only for at-rules inside a rule: `@media`,
  `@supports`, `@container` and `@include` with a content block. They keep a
  rule's variations next to it without raising specificity.

## Values and expressions

- Write Sass values with the same notation the
  [CSS value rules](../CSS/coding-style.md#values) require: no unit on `0`,
  a leading zero on decimals, lowercase hex colours.
- Divide with `math.div()`, never `/`, which Sass now reads as a CSS
  separator.
- Interpolate (`#{...}`) only where Sass requires it, such as a variable in
  a custom property value or a selector. Don't wrap a plain value in
  interpolation.
- Quote strings with single quotes, as in CSS.

## Comments

- Use `//` comments for notes to developers. Sass removes them, so they
  never reach the browser.
- Use `/* */` only for comments that must appear in the compiled CSS, such
  as a licence notice.
- Document every public mixin, function and variable with `///` comments:

  ```scss
  /// Converts a pixel value to `rem`, based on a 16px root font size.
  /// @param {Number} $px - A size in pixels, without a unit.
  /// @return {Number} The size in `rem`.
  @function rem($px) {
    @return math.div($px, 16) * 1rem;
  }
  ```

- Don't leave commented-out rules. Version control keeps the history.

## Third-party code

Vendored third-party stylesheets keep their upstream style and are not
reformatted. List them in `.prettierignore` and `.stylelintignore`, and load
them through `@use` like any other module.

## Sources

- [Sass documentation](https://sass-lang.com/documentation/)
- [Sass: The module system](https://sass-lang.com/documentation/at-rules/use/)
- [Sass: @import deprecation](https://sass-lang.com/d/import)
- [stylelint-config-standard-scss](https://github.com/stylelint-scss/stylelint-config-standard-scss)
- [CSS coding style](../CSS/coding-style.md)
