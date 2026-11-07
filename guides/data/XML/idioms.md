# XML Idioms and Principles

How to design and use XML well. [coding-style.md](coding-style.md) covers how
XML looks. This guide covers how to design XML formats, and how to read and
write XML safely. Every example follows the style guide.

## Principles

- **Every format has a schema.** A schema is the format's contract: it says
  which elements and attributes exist, how they nest and what values they
  hold. Validate every document against it.
- **Parse XML as untrusted input.** A default parser setting can read local
  files, fetch URLs or expand a few bytes into gigabytes. Turn those features
  off before reading anything you didn't write.
- **Never build XML by joining strings.** Use a library that escapes every
  value, so data can't break the document or change its structure.
- **Prefer a simpler format for new data interchange.** Choose XML when a
  standard or a consumer requires it, or when the data is a document with
  mixed text and markup.

## Elements and attributes

Use **elements** for content and **attributes** for facts about it:

| Use an element when the value... | Use an attribute when the value... |
| --- | --- |
| Can repeat, or is a list | Appears at most once |
| Has structure, or might gain structure later | Is a single atomic value, such as an ID, a number or a flag |
| Is text a person reads, or mixed content | Describes the element, such as its units, language or version |
| Has an order that matters | Has no order that matters, since attribute order is ignored |

```xml
<price currency="EUR">19.99</price>
```

- An attribute can't hold structure, and can't later grow it without breaking
  every reader. When in doubt, use an element.
- Use the predefined `xml:lang` attribute for language, and `xml:space` only
  where whitespace must be kept exactly.

## Namespaces

- **Give every format you define its own namespace**, named with a URI you
  control and versioned: `https://example.com/ns/orders/1`. Other formats can
  then be mixed in without name clashes.
- **A namespace is a name, not a location.** Nothing needs to be published
  at the URI, and no program should fetch it.
- **Process names by namespace URI, never by prefix.** The prefix is an
  abbreviation each document chooses; two documents can use different
  prefixes for the same namespace.
- In XPath, a name with no prefix never matches an element in a default
  namespace. Bind a prefix to the namespace in your XPath context and use it:
  `/o:order/o:line`.
- Change the namespace URI only for a change that breaks readers. Adding an
  optional element or attribute isn't one.

## Schemas and validation

- **Write a schema** in XML Schema (XSD) or RELAX NG for every format you
  define. RELAX NG is shorter and easier to read; use XSD when a consumer or
  tool needs it.
- **Validate on read**, in CI and in the program, against a schema the
  program supplies. Don't load the schema a document names in
  `xsi:schemaLocation`: the document chooses that location, so it can point
  anywhere.
- Keep schemas in version control next to the code that reads the format,
  and ship them with it, so validation never needs the network.
- Make new elements and attributes optional, so documents written for the
  older schema stay valid.

## Encoding and characters

- **Always write UTF-8, and say so in the XML declaration.** A parser uses
  the declaration to decode the file, and UTF-8 can represent every
  character.
- Never change a file's encoding without changing its declaration, or the
  parser decodes it wrongly.
- XML 1.0 can't hold most control characters (such as `U+0000` to `U+0008`),
  even as character references. Encode binary data, and text that might
  contain them, as Base64.

## Reading XML safely

Turn off every parser feature that the format doesn't need. For a format with
no DTD, that means:

- **Reject any document with a `DOCTYPE`.** Almost every XML attack needs a
  DTD, and a data format doesn't. Rejecting DOCTYPE declarations outright is
  the simplest, safest setting.
- **Never expand external entities.** An external entity (XXE) makes the
  parser read a local file or fetch a URL and put the result in the document.
- **Limit entity expansion.** Nested entities ("billion laughs") expand a few
  bytes into gigabytes and exhaust memory.
- **Never let the parser use the network.** Don't fetch DTDs, schemas or
  XInclude targets while parsing.
- **Limit document size and nesting depth**, so a huge or deeply nested
  document can't exhaust memory or the stack.

Each language turns these off differently. Use the safe setting that the
language's documentation names, or a hardened parser library such as Python's
`defusedxml`. With libxml2, don't enable entity substitution
(`XML_PARSE_NOENT`) or DTD loading (`XML_PARSE_DTDLOAD`), and do pass
`XML_PARSE_NONET`.

### Queries and transforms

- **Never build XPath expressions from input.** Pass values as XPath
  variables instead, just as SQL passes values as parameters. Input joined
  into an expression can change what it selects.
- **Never run an XSLT stylesheet you didn't write.** XSLT processors can read
  files, write files and, through extensions, run code.

## Writing XML

- **Write XML with a serializer**, never with string joins or a text
  template. A serializer escapes `<`, `&` and quotes in every value.
- Write the XML declaration with `encoding="UTF-8"`, and write the bytes as
  UTF-8 to match.
- Sort or otherwise fix the order of elements whose order doesn't matter, so
  the same data always produces the same document and diffs stay small.

## Sources

- [Extensible Markup Language (XML) 1.0](https://www.w3.org/TR/xml/)
- [Namespaces in XML 1.0](https://www.w3.org/TR/xml-names/)
- [OWASP XML External Entity Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
- [RELAX NG specification](https://relaxng.org/spec-20011203.html)
