# HTML Idioms and Principles

How to write HTML well. [coding-style.md](coding-style.md) covers how markup
looks. This guide covers how it's structured: the idioms and principles that
keep pages meaningful, accessible, secure and fast. Every example follows the
style guide.

## Principles

- **Markup describes meaning, not appearance.** Choose each element for what
  its content *is*. The CSS decides how it looks.
- **Use the native element first.** A real `<button>`, `<a>` or `<input>`
  brings keyboard support, focus handling and screen-reader behaviour for
  free. Rebuilding them from `<div>`s means rebuilding all of that by hand.
- **Content works before enhancements.** The page's core content and links
  should work with HTML alone, with CSS and JavaScript layered on top.
- **Keep structure, style and behaviour apart.** HTML for structure, CSS for
  presentation, JavaScript for behaviour, each in its own files.

## Semantic structure

- **Mark up the page's regions with landmarks**: `<header>`, `<nav>`,
  `<main>`, `<aside>` and `<footer>`. Screen-reader users jump between them.
  Use exactly one `<main>` per page.
- **Use headings as an outline.** One `<h1>` per page, then `<h2>`–`<h6>` in
  order, without skipping levels. Choose the level for its place in the
  outline, never for its size; the CSS sets the size.
- Use `<article>` for self-contained content (a post, a product card) and
  `<section>` for a themed part of a page that has its own heading.
- Use lists for lists: `<ul>` when order doesn't matter, `<ol>` when it does,
  `<dl>` for term and description pairs.
- **Use `<a>` to go somewhere and `<button>` to do something.** A link
  changes the URL. A button runs an action or submits a form.
- **Use tables only for tabular data**, never for layout. Give each table a
  `<caption>`, and give header cells `<th>` with `scope="col"` or
  `scope="row"`:

  ```html
  <table>
    <caption>
      Recent orders
    </caption>
    <thead>
      <tr>
        <th scope="col">Order</th>
        <th scope="col">Total</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>#1042</td>
        <td>£18.50</td>
      </tr>
    </tbody>
  </table>
  ```

- Use `<time datetime="2026-11-05">` for dates, so machines can read them.

## Accessibility

- **Give every image an `alt` attribute.** Describe what the image conveys.
  Use an empty `alt=""` for purely decorative images, so screen readers skip
  them.
- **Every form control needs a visible `<label>`**, connected with `for` and
  `id`. A placeholder is not a label; it disappears as soon as someone types.
- **Follow the first rule of ARIA: don't use ARIA when a native element does
  the job.** Add ARIA only to describe state or relationships HTML can't
  express, such as `aria-expanded` on a disclosure button or
  `aria-describedby` linking a field to its hint.
- **Everything must work from the keyboard.** Native controls do this. Never
  use a positive `tabindex`, which breaks the natural focus order.
- **Link text must make sense on its own.** "Download the 2026 report" works
  in a list of links. "Click here" doesn't.
- Announce content that changes without a page load (search results, form
  errors) with an `aria-live` region.
- Use `hidden` to hide content from everyone, including screen readers. Use
  the CSS's visually-hidden class only for text meant just for screen
  readers.

## Forms

- **Pick the right `type`** for each `<input>` (`email`, `tel`, `number`,
  `date`, `password`). Phones show the right keyboard, and the browser
  validates the format.
- **Add `autocomplete` values** (`name`, `email`, `street-address`,
  `current-password`, `new-password`), so browsers and password managers can
  fill fields correctly.
- Mark required fields with `required`, and say so in the label text too.
- Group related controls, such as radio buttons, in a `<fieldset>` with a
  `<legend>`.
- Connect hints and error messages to their field with `aria-describedby`:

  ```html
  <label for="email">Email address</label>
  <input
    id="email"
    name="email"
    type="email"
    autocomplete="email"
    required
    aria-describedby="email-hint"
  />
  <p id="email-hint">We'll send your receipt here.</p>
  ```

- **Use `method="post"` for any form that changes data.** `GET` puts the
  values in the URL, where they're logged and cached.
- Browser validation helps users, but it's not security. Always validate
  again on the server.

## Progressive enhancement

- Build the HTML so its core task works on its own: real links that go
  somewhere, and forms that submit to a server.
- Let JavaScript enhance what's already there, finding its elements through
  `data-` attributes (see the [JavaScript idioms](../../languages/JavaScript/idioms.md)).
- Load scripts as modules (`<script type="module">`). They download in
  parallel and run after the page is parsed, so they never block rendering.

## Security

- **Keep markup compatible with a strict Content Security Policy**: no inline
  `<script>` code, no `on*` attributes, no `style` attributes and no
  `javascript:` URLs.
- **Escape all data inserted into HTML**, in the server's template engine.
  Never mark untrusted data as safe to output raw.
- **Add `rel="noopener noreferrer"` to links with `target="_blank"`** that
  point to other sites. The new page then can't reach back into yours through
  `window.opener`, and doesn't learn which page linked to it.
- **Load third-party scripts and stylesheets with an `integrity` hash** (and
  `crossorigin="anonymous"`), so a compromised CDN can't swap in different
  code.
- Embed untrusted content in an `<iframe>` with the `sandbox` attribute,
  allowing only the abilities it needs.
- Never put secrets, internal URLs or debugging notes in the markup or its
  comments. Every visitor can read the source.

## Performance

- **Give every `<img>` its `width` and `height`.** The browser reserves the
  space, so the page doesn't jump when the image arrives.
- Add `loading="lazy"` to images and iframes below the fold. Leave it off the
  main image near the top, which should load straight away.
- Serve sized images with `srcset` and `sizes`, so small screens don't
  download large files:

  ```html
  <img
    src="/img/shoe-800.jpg"
    srcset="/img/shoe-400.jpg 400w, /img/shoe-800.jpg 800w"
    sizes="(width <= 40em) 100vw, 50vw"
    width="800"
    height="600"
    alt="Red running shoe, side view"
  />
  ```

- Link stylesheets in `<head>` and load scripts as modules, as in the
  [document skeleton](coding-style.md#document-structure).
- Use `<link rel="preload">` sparingly, only for resources the profiler shows
  are discovered too late.

## Internationalisation

- Set `lang` on `<html>`, and on any element whose text is in a different
  language.
- Set `dir="rtl"` for right-to-left languages, and use logical CSS properties
  (see the [CSS idioms](../CSS/idioms.md)) so the layout mirrors with it.
- Keep text in the markup or templates, never baked into images.

## Sources

- [WHATWG HTML Living Standard](https://html.spec.whatwg.org/)
- [MDN HTML guides](https://developer.mozilla.org/en-US/docs/Web/HTML)
- [W3C: Using ARIA](https://www.w3.org/TR/using-aria/)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- [OWASP Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
