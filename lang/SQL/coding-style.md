# SQL Coding Style

A general-purpose coding style for portable SQL. It builds on Simon
Holywell's [SQL Style Guide](https://www.sqlstyle.guide/), uses ISO SQL where
the standard covers a feature, and matches the rules that
[SQLFluff](https://sqlfluff.com/) can check (see [Sources](#sources)).

This guide covers how SQL looks. For how to design schemas and write sound
queries (keys, constraints, NULL handling, transactions, indexing and
migrations), see [idioms.md](idioms.md).

The tools that check SQL code are listed in [tools.md](tools.md).

## Layout

### Indentation and line length

- Indent with **4 spaces**, never tabs. Spaces look the same in every editor,
  database client and log.
- Keep lines to **80 columns**, so queries can be read side by side and in
  narrow terminals.
- **Never break a string literal** across lines, so it stays greppable.

### Clauses

- Start each clause on a new line, with its keyword at the start of the line:
  `SELECT`, `FROM`, `JOIN`, `WHERE`, `GROUP BY`, `HAVING`, `ORDER BY`. The
  keywords form a column down the left edge, so the shape of the query is
  visible at a glance.
- A clause with **one short item** keeps it on the keyword's line.
- A clause with **several items** puts the keyword on its own line, and each
  item on its own line, indented one level:

  ```sql
  SELECT
      c.customer_id,
      c.name,
      COUNT(*) AS order_count
  FROM customers AS c
  INNER JOIN orders AS o
      ON c.customer_id = o.customer_id
  WHERE
      o.shipping_status = 'shipped'
      AND o.placed_at >= DATE '2026-01-01'
  GROUP BY
      c.customer_id,
      c.name
  ORDER BY order_count DESC;
  ```

- `AND` and `OR` start the line of the condition they join. The logic of a
  long condition then reads down the left edge.
- Put `ON` on the line after its `JOIN`, indented one level. Extra join
  conditions follow on their own lines, lined up with `ON`.
- In an `ON` condition, name the column from the table that appears earlier
  in the query first: `ON c.customer_id = o.customer_id`.
- `DISTINCT` stays on the `SELECT` line: `SELECT DISTINCT`.
- Put set operators (`UNION ALL`, `INTERSECT`, `EXCEPT`) on their own line,
  with a blank line before and after.

### Commas, spacing and parentheses

- Commas go at the **end** of the line, never the start.
- Put one space after each comma, and one space on each side of comparison,
  arithmetic and assignment operators.
- No space between a function name and its parenthesis: `COUNT(*)`, not
  `COUNT (*)`.
- No spaces just inside parentheses: `(a + b)`, not `( a + b )`.
- When the contents of parentheses span lines, the closing parenthesis goes
  on its own line, lined up with the line that opened it.

### Statements and whitespace

- End **every** statement with a semicolon, even the last one in a file.
  Scripts can then be concatenated and run without surprises.
- Separate statements with one blank line.
- No trailing whitespace, no blank lines at the start of a file, and end
  every file with exactly one newline.

## Case

| Element | Case | Example |
| --- | --- | --- |
| Keywords | `UPPERCASE` | `SELECT`, `INNER JOIN`, `NOT NULL` |
| Built-in function names | `UPPERCASE` | `COUNT(*)`, `COALESCE(a, b)` |
| Your own function names | `lowercase`, with at least one underscore | `order_count(c.customer_id)` |
| Data types | `UPPERCASE` | `INTEGER`, `VARCHAR(100)`, `TIMESTAMP` |
| Literals `NULL`, `TRUE`, `FALSE` | `UPPERCASE` | `WHERE deleted_at IS NULL` |
| Identifiers (tables, columns, aliases, constraints) | `lowercase` | `order_items`, `placed_at` |

Uppercase keywords and lowercase identifiers separate the language from the
data model, so each is easy to pick out. Your own functions are part of the
data model, so they're lowercase like any other identifier.

## Naming

- Use lowercase `snake_case` for every identifier. Lowercase names never need
  quoting, and behave the same on every database and operating system.
- Use only letters, digits and underscores, and start names with a letter.
- **Never use a reserved word as an identifier**, and **never quote
  identifiers**. A name that needs quoting is a name to change.
- Keep identifiers to **30 characters or fewer**. That fits the limit of every
  major database engine.
- Don't add type prefixes or suffixes (`tbl_orders`, `vw_sales`,
  `name_str`). The schema already records what an object is.

### Tables and columns

- Name tables with a **plural noun**, or a collective noun where one exists:
  `customers`, `order_items`, `staff`. A table holds a set of rows.
- Name columns with a **singular noun**: `name`, `email`, `price`.
- Never give a column the same name as its table.
- Name a junction table after the two tables it links: `customers_products`.

### Keys and column suffixes

Use the same suffix for the same meaning everywhere, so a column's role is
clear from its name:

| Suffix or prefix | Meaning | Example |
| --- | --- | --- |
| `<entity>_id` | Primary key, and every foreign key that points to it | `customer_id` |
| `_at` | Point in time (`TIMESTAMP WITH TIME ZONE`) | `created_at`, `shipped_at` |
| `_date` | Calendar date (`DATE`) | `birth_date` |
| `is_` / `has_` | Boolean | `is_active`, `has_discount` |
| `_count` | Number of things | `item_count` |
| `_total` | Sum of values | `invoice_total` |

- The primary key of `customers` is `customer_id`, and every foreign key to it
  is also `customer_id`. The same name on both sides of a join leaves no doubt
  about what's being joined.
- When a table holds two foreign keys to the same table, add a role prefix:
  `billing_address_id`, `shipping_address_id`.

### Constraints and indexes

Name every constraint and index explicitly. Generated names differ between
engines and make errors and migrations hard to read.

| Object | Pattern | Example |
| --- | --- | --- |
| Primary key | `pk_<table>` | `pk_orders` |
| Foreign key | `fk_<table>_<column>` | `fk_orders_customer_id` |
| Unique | `uq_<table>_<columns>` | `uq_customers_email` |
| Check | `ck_<table>_<rule>` | `ck_orders_total_positive` |
| Index | `ix_<table>_<columns>` | `ix_orders_placed_at` |

## Aliases

- Always write `AS` before an alias, for both tables and columns. An alias
  without `AS` looks like a typo.
- Alias every table when a query uses more than one. Derive the alias from
  the table name, using the first letter of each word: `customers AS c`,
  `order_items AS oi`.
- When a query uses more than one table, **qualify every column** with its
  table alias, so it's clear where each column comes from.
- Give every calculated column an alias: `COUNT(*) AS order_count`.
- Don't create aliases you never use.

## Queries

- **List columns explicitly.** Don't use `SELECT *` outside ad hoc queries. A
  query that names its columns doesn't break or change meaning when the table
  gains a column.
- In a `SELECT` list, put plain columns before calculated expressions.
- Write join types in full: `INNER JOIN`, `LEFT JOIN`, `CROSS JOIN`. Never
  write a bare `JOIN`.
- Don't use `RIGHT JOIN`. Swap the tables and use `LEFT JOIN`, so every join
  reads in the same direction.
- Put join conditions in `ON`, never in `WHERE`. Comma joins
  (`FROM a, b WHERE ...`) mix join logic with filters.
- Use **common table expressions** (`WITH`) instead of subqueries in `FROM`
  and `JOIN`. Named steps read top to bottom:

  ```sql
  WITH recent_orders AS (
      SELECT
          customer_id,
          order_total
      FROM orders
      WHERE placed_at >= DATE '2026-01-01'
  )

  SELECT
      customer_id,
      SUM(order_total) AS spend_total
  FROM recent_orders
  GROUP BY customer_id
  ORDER BY spend_total DESC;
  ```

- Leave a blank line after each CTE's closing parenthesis.
- In `GROUP BY` and `ORDER BY`, name columns or aliases, never positions
  (`ORDER BY 2`). A position silently changes meaning when the `SELECT` list
  changes.
- Give **every** `ORDER BY` column an explicit `ASC` or `DESC`.
- Always write `UNION ALL` or `UNION DISTINCT`, never a bare `UNION`, so the
  choice to remove duplicates is visible.
- Use `COUNT(*)` to count rows, not `COUNT(1)`.
- Limit rows with `FETCH FIRST n ROWS ONLY`, the standard form, and always
  with an `ORDER BY`. Without one, which rows you get is undefined.

## Expressions

- Use `<>` for "not equal", not `!=`. `<>` is the standard form.
- Test for NULL with `IS NULL` and `IS NOT NULL`. `= NULL` is never true.
- Use `COALESCE()`, not engine-specific variants such as `IFNULL()` or
  `NVL()`.
- Cast with `CAST(value AS type)`, not engine-specific shorthand.
- Quote string literals with **single quotes**. Double quotes are for
  identifiers in standard SQL.
- Write date and time literals with their type: `DATE '2026-01-01'`,
  `TIMESTAMP '2026-01-01 09:30:00'`.
- Use `CASE` instead of engine-specific conditional functions. Don't write
  `ELSE NULL`; it's the default.
- Use `BETWEEN` only for closed ranges of whole values. For time ranges, use
  `>=` and `<` (see [idioms](idioms.md#queries)).

## Comments

- A comment that sits on its own line or lines uses `/* ... */`. A short note
  at the end of a line of code uses `--`, followed by a space.
- Write multi-line comments with a column of asterisks, and put the
  delimiters on their own lines:

  ```sql
  /*
   * Orders placed before the 2024 migration have no region, so they're
   * reported under the default region.
   */
  ```

- Comments explain **why**, not what. The query already says what it does.
- Every migration and stored routine starts with a block comment saying what
  it's for.

## DDL

- Put each column of a `CREATE TABLE` on its own line, indented one level.
- Declare constraints by name after the columns, so they're easy to find.
  A constraint too long for one line continues on the next line at the same
  indent:

  ```sql
  CREATE TABLE orders (
      order_id BIGINT GENERATED ALWAYS AS IDENTITY,
      customer_id BIGINT NOT NULL,
      shipping_status VARCHAR(20) NOT NULL,
      order_total DECIMAL(12, 2) NOT NULL,
      placed_at TIMESTAMP WITH TIME ZONE NOT NULL,
      CONSTRAINT pk_orders PRIMARY KEY (order_id),
      CONSTRAINT fk_orders_customer_id FOREIGN KEY (customer_id)
      REFERENCES customers (customer_id),
      CONSTRAINT ck_orders_total_positive CHECK (order_total >= 0)
  );
  ```

- Write `NOT NULL` on every column that must have a value. Leave it off only
  where NULL has a meaning.

## Sources

- [SQL Style Guide](https://www.sqlstyle.guide/) by Simon Holywell
- ISO/IEC 9075, the SQL standard
- [SQLFluff rules reference](https://docs.sqlfluff.com/en/stable/reference/rules.html)
