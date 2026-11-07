# XML Coding Style

A general-purpose style for XML documents. It builds on the
[XML 1.0 specification](https://www.w3.org/TR/xml/) and
[Namespaces in XML 1.0](https://www.w3.org/TR/xml-names/), and matches the
layout that `xmllint --format` produces (see [Sources](#sources)). It covers
XML itself, not the vocabulary of any one format.

This guide covers how XML looks. For how to design XML formats and read them
safely (elements versus attributes, namespaces, schemas, encoding and secure
parsing), see [idioms.md](idioms.md).

The tools that check XML code are listed in [tools.md](tools.md).

## Language baseline

Write **XML 1.0** with **Namespaces in XML 1.0**. XML 1.1 changes which
characters are allowed and how line endings are read, and few parsers
support it.

## Files

- Name XML files with the **`.xml`** extension, or the extension the format
  defines (`.xsd`, `.svg`).
- Encode files in **UTF-8**, without a byte order mark.
- Start every file with the XML declaration, naming the version and the
  encoding:

  ```xml
  <?xml version="1.0" encoding="UTF-8"?>
  ```

- No trailing whitespace. Use LF line endings, and end every file with a
  newline.

## Layout

- Indent with **2 spaces**, one level for each level of nesting.
- Put each element that holds other elements on its own line, with its child
  elements indented one level and its end tag lined up with its start tag.
- Keep **mixed content** (text with elements inside it) exactly as written.
  Adding line breaks or spaces inside it changes the text.
- Keep a start tag and its attributes on one line. Aim for **80 columns**; a
  line may run longer only when a single start tag doesn't fit.
- Write an element with no content as an empty-element tag, with no space
  before the `/>`: `<customer ref="c-7"/>`.
- Use at most one blank line in a row, to separate groups of related
  elements.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<order xmlns="https://example.com/ns/orders/1" id="42" currency="EUR">
  <customer ref="c-7"/>
  <!-- Lines are kept in the order they were added. -->
  <line sku="A-1" quantity="2">
    <note>Gift wrap, <em>please</em>.</note>
  </line>
  <line sku="B-2" quantity="1"/>
</order>
```

## Names

- When you define the format, name elements and attributes in
  **`lowerCamelCase`**: `<orderLine unitPrice="9.99"/>`. When a consumer or
  standard defines it, use its names exactly.
- Use only letters and digits, and start names with a letter. Never start a
  name with `xml`, in any case; those names are reserved.
- Use nouns for elements, since they hold things: `<customer>`, not
  `<getCustomer>`.
- Name a list element as the plural of its items: `<lines>` holds `<line>`
  elements.

## Attributes

- Quote attribute values with **double quotes**.
- Put namespace declarations first, then identifying attributes (such as
  `id`), then the rest.
- Never repeat an attribute on one element. XML forbids it.

## Text and characters

- Write characters directly in UTF-8: `café`, not `caf&#233;`.
- Escape `<` and `&` in text as `&lt;` and `&amp;`. In attribute values, also
  escape `"` as `&quot;`.
- Don't use entities other than the five that XML predefines (`&lt;`, `&gt;`,
  `&amp;`, `&quot;` and `&apos;`) and numeric character references. Other
  entities need a DTD (see [security](idioms.md#reading-xml-safely)).
- Avoid `CDATA` sections. Use them only to embed a block of code or markup
  that would otherwise need escaping on every line.

## Namespaces

- Declare every namespace on the **root element**, so a reader sees them all
  in one place.
- Use a default namespace (`xmlns="..."`) for the document's own vocabulary,
  and short, well-known prefixes for the others (`xsi`, `xs`, `xlink`).
- Use the same prefix for the same namespace everywhere in a project.

## Comments

- Write comments as `<!-- text -->`, with one space after `<!--` and before
  `-->`. A comment can't contain `--`.
- Put a comment on its own line, directly above the element it describes.
- Comments explain **why**, not what the element names already say.
- Never put data in comments. Programs that read the document ignore them.

## Generated and third-party files

Generated XML and vendored third-party files keep their own format and are
excluded from the formatter, so regenerating or updating them stays a clean
replacement.

## Sources

This guide starts from the XML specifications and borrows from:

- [Extensible Markup Language (XML) 1.0](https://www.w3.org/TR/xml/)
- [Namespaces in XML 1.0](https://www.w3.org/TR/xml-names/)
- [xmllint manual](https://gnome.pages.gitlab.gnome.org/libxml2/xmllint.html)
