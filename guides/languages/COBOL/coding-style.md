# COBOL Coding Style

A general-purpose coding style for COBOL projects built with
[GnuCOBOL](https://gnucobol.sourceforge.io/). COBOL has no single canonical
style guide, so this one builds on the COBOL 2014 standard's reference format
and on structured-programming practice common to long-lived COBOL code bases
(see [Sources](#sources)).

This guide covers how code looks. For how to design and structure it (program
structure, data design, decimal arithmetic, file handling and other idioms),
see [idioms.md](idioms.md).

The tools that check COBOL code are listed in [tools.md](tools.md).

## Language baseline

Code targets **COBOL 2014 as implemented by GnuCOBOL 3.2 or later**, compiled
with `-std=cobol2014`. Sticking to the standard keeps programs portable to
other compilers, and every feature this guide relies on, such as `GOBACK`,
`*>` comments and explicit scope terminators, is in it.

## Files

- Name programs and source files in uppercase, with `.cob` for programs and
  `.cpy` for copybooks: `CUSTRPT.cob`, `CUSTREC.cpy`.
- Keep program names to 8 characters if the code may also run on systems
  that limit program names to 8.
- Put one program in each file, with the same name as its `PROGRAM-ID`.
- Use ASCII and LF line endings, and end every file with a newline.

## Reference format

Write source in fixed reference format, which every COBOL compiler accepts:

| Columns | Area | Contents |
| --- | --- | --- |
| 1–6 | Sequence area | Left blank |
| 7 | Indicator area | `*` for a comment line, `-` for a continuation line, otherwise blank |
| 8–11 | Area A | Division, section and paragraph headers, `FD` entries, and `01` and `77` levels |
| 12–72 | Area B | Statements, and all other data entries |
| 73–80 | Identification area | Never used |

- **Never write past column 72.** The compiler ignores anything in columns
  73–80, so a statement that runs past column 72 is silently cut short.
- Leave the sequence area blank. Version control tracks changes, so line
  numbers there only go stale.

## Layout

### Indentation

- Start statements in column 12, the start of Area B.
- Indent each nested statement 4 more columns than the statement that
  contains it.
- Indent clauses that continue a statement, such as `UNTIL`, `AT END` and
  `WHEN`, 4 columns under the statement they belong to.

### One thing per line

- One statement per line.
- End every statement with its explicit scope terminator (`END-IF`,
  `END-PERFORM`, `END-READ`, `END-EVALUATE`), never with a period.
- Put a single period at the end of each paragraph, on its last statement. A
  stray period inside a paragraph silently ends every open `IF` at that point.

```cobol
       2000-PROCESS-CUSTOMER.
           READ CUSTOMER-FILE
               AT END
                   SET WS-END-OF-CUSTOMERS TO TRUE
               NOT AT END
                   PERFORM 2100-ADD-TO-TOTALS
           END-READ.
```

### Blank lines

Leave one blank line between paragraphs, and between sections of the data
division.

## Case

Write reserved words and names in uppercase. COBOL is case-insensitive, and
uppercase matches the copybooks and existing code most projects have to work
with.

## Naming

- Name everything with uppercase words separated by hyphens:
  `CUSTOMER-BALANCE`.
- Prefix data names with where they're defined: `WS-` for working storage,
  `LS-` for the linkage section, and a short file prefix for record fields
  (`CUST-NAME` in the customer record).
- Name paragraphs with a 4-digit number and a verb phrase:
  `2000-PROCESS-CUSTOMER`. The numbers put paragraphs in the order they
  run, and related paragraphs share a leading digit.
- Name level-88 condition names as a true statement: `WS-END-OF-CUSTOMERS`,
  `CUST-IS-ACTIVE`.

## Data division

- Put `01` and `77` levels in Area A, and indent each subordinate level 4
  columns more than its parent.
- Number levels in steps of 5 (`01`, `05`, `10`), which leaves room to insert
  a level later without renumbering.
- Line up `PIC` clauses at column 40 and `VALUE` clauses at column 50. When a
  `PIC` clause runs past column 50, put `VALUE` on the next line at column 50.
- Write `PIC`, not `PICTURE`, and spell repeated symbols with a count:
  `PIC 9(7)`, not `PIC 9999999`.

```cobol
       WORKING-STORAGE SECTION.
       01  WS-CUSTOMER-STATUS          PIC XX.
           88  WS-CUSTOMER-OK                    VALUE "00".
       01  WS-FLAGS.
           05  WS-END-FLAG             PIC X     VALUE "N".
               88  WS-END-OF-CUSTOMERS           VALUE "Y".
       01  WS-TOTALS.
           05  WS-RECORD-COUNT         PIC 9(7)  VALUE ZERO.
           05  WS-BALANCE-TOTAL        PIC S9(11)V99 PACKED-DECIMAL
                                                 VALUE ZERO.
```

## Literals

- Quote alphanumeric literals with double quotes: `"00"`.
- Use figurative constants (`ZERO`, `SPACES`) instead of literals like `0`
  and `" "`, so the intent is clear.

## Comments

- Write whole-line comments with `*` in column 7.
- Write end-of-line notes with `*>`, after the statement they explain.
- Explain **why** the code does something, not **what** it does.
- Start each program with a comment block giving its purpose, its inputs and
  outputs, and its return codes.

## Third-party code

Vendored third-party sources keep their upstream style and are not
reformatted, so updates from upstream stay easy to merge.

## Sources

- [GnuCOBOL Programmer's Guide](https://gnucobol.sourceforge.io/guides.html)
- [GnuCOBOL FAQ](https://gnucobol.sourceforge.io/faq/index.html)
- ISO/IEC 1989:2014, the COBOL 2014 standard (reference format and scope
  terminators)
