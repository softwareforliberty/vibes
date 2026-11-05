# HTML Coding Style

A general-purpose coding style for HTML documents and templates. It builds on
the [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
and the [WHATWG HTML Living Standard](https://html.spec.whatwg.org/) (see
[Sources](#sources)).

This guide covers how markup looks. For how to structure it (semantics,
accessibility, forms, security and performance), see [idioms.md](idioms.md).
For the styles and scripts that work with it, see the
[CSS](../CSS/coding-style.md) and [JavaScript](../JavaScript/coding-style.md)
guides.

## Tools

All tools are free/open source.

| Tool | Licence | Used for |
| --- | --- | --- |
| [Prettier](https://prettier.io/) | MIT | Formatting (shared with CSS and JavaScript) |
| [html-validate](https://html-validate.org/) | MIT | Offline validation, accessibility and best-practice checks |
| [Nu HTML Checker](https://validator.github.io/validator/) (`vnu`) | MIT | Validation against the HTML standard |

### Configuration

Markup must pass all three checks with **no errors**:

```sh
npx prettier --check "**/*.html"
npx html-validate "**/*.html"
java -jar vnu.jar --skip-non-html .
```

`.prettierrc.json`, shared by HTML, CSS and JavaScript:

```json
{
  "printWidth": 80,
  "tabWidth": 2,
  "useTabs": false,
  "semi": true,
  "singleQuote": true,
  "trailingComma": "all",
  "endOfLine": "lf"
}
```

`.htmlvalidate.json`:

```json
{
  "extends": ["html-validate:recommended"],
  "rules": {
    "void-style": ["error", { "style": "selfclose" }]
  }
}
```

- Prettier owns layout. Don't hand-format markup it will rewrite.
- Prettier writes void elements with a closing slash (`<br />`), and
  html-validate is set to expect that, so the formatter and the validator
  agree. In HTML the slash is optional and has no effect.
- `vnu` checks against the current standard. html-validate adds rules the
  standard doesn't cover, such as accessibility checks and banned inline
  styles. Run both.

## Layout

### Indentation

- Indent with **2 spaces**. Never use tabs.
- Put each block, list or table element on its own line, and indent its
  children one level.
- Keep inline elements (`<a>`, `<em>`, `<code>`) inside the running text.

### Line length

- **80 columns**. Prettier wraps elements that don't fit by putting one
  attribute per line.
- Don't break a user-visible sentence across lines just to fit. Let the
  formatter decide.

### Files

- Use UTF-8 with LF line endings, and end every file with a newline.
- Name files in lowercase kebab-case: `order-history.html`.

## Document structure

Every page starts with the same skeleton:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Order history</title>
    <link rel="stylesheet" href="/css/main.css" />
    <script type="module" src="/js/main.js"></script>
  </head>
  <body>
    <main>
      <h1>Order history</h1>
    </main>
  </body>
</html>
```

- Start with `<!doctype html>`, which puts browsers in standards mode.
- Set `lang` on `<html>`. Screen readers use it to pick a voice, and browsers
  use it for hyphenation and translation.
- Make `<meta charset="utf-8" />` the first thing in `<head>`. The browser
  must know the encoding before it reads any text.
- Give every page a unique, descriptive `<title>`.
- Write `<html>`, `<head>` and `<body>` out, even though HTML lets you leave
  them out. The structure is then obvious to readers and tools.

## Elements and attributes

- Write element and attribute names in lowercase.
- Quote every attribute value with double quotes: `class="card"`.
- Write boolean attributes bare: `disabled`, not `disabled="disabled"`.
- Close every non-void element, including ones HTML lets you leave open
  (`</p>`, `</li>`). Leaving them open invites nesting mistakes.
- Write void elements (`<br />`, `<img />`, `<input />`, `<meta />`,
  `<link />`) with a closing slash, as Prettier does.
- Leave out the `type` attribute on stylesheets and classic scripts. `text/css`
  and JavaScript are the defaults. Do write `type="module"` on module
  scripts, which changes how they load.

## Naming

- Write `id` and `class` values in lowercase kebab-case.
- Name classes with **BEM** (block, element, modifier), as in the
  [CSS guide](../CSS/coding-style.md#naming):
  `order-list`, `order-list__item`, `order-list__item--paid`.
- Use classes for styling only, and `data-` attributes for JavaScript hooks:
  `data-order-list`. Restyling then can't break a script, and the reverse.
- Name `data-` attributes in lowercase kebab-case.
- Use `id` only for in-page links and to connect elements, as with
  `<label for>` and `aria-describedby`. Don't use ids to style.

## No inline styles or scripts

- Never use the `style` attribute or a `<style>` element. Put all styles in
  stylesheets.
- Never write `on*` event attributes (`onclick`) or inline `<script>` code.
  Load scripts from files.
- Inline code breaks a strict Content Security Policy and mixes concerns that
  belong in the [CSS](../CSS/coding-style.md) and
  [JavaScript](../JavaScript/coding-style.md).

## Text and entities

- Type characters directly in UTF-8 (`—`, `é`, `€`). Use character
  references only for characters with special meaning in HTML (`&lt;`,
  `&gt;`, `&amp;`) and for invisible ones (`&nbsp;`), so they stay visible in
  the source.

## Comments

- Use `<!-- -->` comments only to explain something non-obvious about the
  structure. Comments are sent to every visitor.
- Don't leave commented-out markup. Version control keeps the history.

## Third-party code

Vendored third-party files keep their upstream style and are not
reformatted. List them in `.prettierignore`.

## Sources

- [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- [WHATWG HTML Living Standard](https://html.spec.whatwg.org/)
- [MDN HTML reference](https://developer.mozilla.org/en-US/docs/Web/HTML)
- [html-validate rules](https://html-validate.org/rules/)
- [Prettier options](https://prettier.io/docs/en/options.html)
