# SQLite Idioms and Principles

How to design schemas and write SQL well in SQLite 3.38 and later.
[coding-style.md](coding-style.md) covers how SQL looks. This guide covers
how it's designed: the idioms and principles that keep data correct, queries
fast and changes safe. Every example follows the style guide.

## Principles

- **The database guards the data.** Constraints, keys and types enforce the
  rules in one place, for every application and every ad hoc fix. Application
  checks are a convenience, not a guarantee.
- **Think in sets, not rows.** One statement that works on many rows beats a
  loop that sends one statement per row.
- **Store each fact once.** Duplicated facts drift apart. When you duplicate
  data on purpose, for speed, write down why and how it's kept in sync.
- **Be explicit.** Name columns, join types, sort orders and constraints.
  Defaults differ between engines and change between versions.
- **Grant the least privilege that works.** SQLite has no accounts, so
  access is whatever the database file's permissions allow. Open connections
  that only read in read-only mode, and let only the programs that write the
  database write to its file.

## Connection settings

SQLite applies most settings per connection, so every connection sets them
as soon as it opens:

```sql
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
PRAGMA trusted_schema = OFF;
```

- **Turn foreign keys on.** SQLite only enforces foreign keys on connections
  that ask for it, and the setting can't change inside a transaction.
- **Set a busy timeout**, so a connection waits for a lock instead of failing
  at once with `SQLITE_BUSY`.
- **Turn `trusted_schema` off**, so views, triggers and other schema objects
  can only call functions that are marked safe for them.
- **Use write-ahead logging** (`PRAGMA journal_mode = WAL`). Readers then
  don't block the writer, and the writer doesn't block readers. The setting is
  stored in the database file, so it only needs setting once.
- With WAL, use `PRAGMA synchronous = NORMAL`. The database stays consistent
  after a crash, and only the last few commits can be lost after a power
  failure, in exchange for much faster commits.

## Schema design

- **Normalise to third normal form by default.** Each table describes one kind
  of thing, and every column depends on that table's key. Denormalise only
  when measurement shows you need to.
- **Keep columns atomic.** One value per column: no comma-separated lists, no
  numbered columns (`phone1`, `phone2`). Repeated values belong in a child
  table.
- **Avoid entity–attribute–value tables** (one generic `attribute`/`value`
  pair per row). They throw away types, constraints and indexing.
- **Avoid polymorphic foreign keys**, where one column points at different
  tables depending on another column. The database can't enforce them. Use a
  separate foreign key column for each target table.
- Keep history explicitly, in its own table or with validity columns, rather
  than overwriting values you'll need later.

### Keys

- **Every table has a primary key.** Without one, rows can't be told apart,
  updated reliably or replicated.
- Use a **surrogate key** (an `INTEGER PRIMARY KEY AUTOINCREMENT` column) as
  the primary key for entity tables. Natural values such as emails and product
  codes change, and every foreign key would have to change with them.
- Put a **`UNIQUE` constraint on the natural key** as well, so duplicates
  can't creep in behind the surrogate key.
- A junction table's primary key is the pair of foreign keys it links.
- Never reuse a deleted key value. That's what `AUTOINCREMENT` is for:
  without it, SQLite can hand out the largest deleted key again.
- **Never rely on the hidden `rowid`.** An `INTEGER PRIMARY KEY` column
  becomes the table's `rowid`, so it's stable. In a table without one,
  `VACUUM` can change the `rowid` values.

### Constraints

- Declare a **`FOREIGN KEY`** for every reference to another table, so orphan
  rows can't exist. SQLite enforces them only on connections that
  [turn them on](#connection-settings).
- Choose each foreign key's `ON DELETE` behaviour deliberately: `RESTRICT`
  (the default to reach for), `CASCADE` (for rows that can't exist without
  their parent), or `SET NULL` (for optional links).
- Add **`CHECK` constraints** for rules about a single row: ranges, allowed
  values, and relationships between columns.
- Represent a fixed set of values with a `CHECK` constraint, or with a lookup
  table when the values carry extra data or change at run time.

### Data types

- **Make every table `STRICT`.** In an ordinary SQLite table, a column's
  type is only a hint (its "type affinity"), and SQLite stores `'abc'` in an
  `INTEGER` column without complaint. A `STRICT` table rejects any value that
  doesn't match its column's type.
- A `STRICT` table allows only `INTEGER`, `REAL`, `TEXT`, `BLOB` and `ANY`.
  Don't use `ANY`, which switches the type check off for its column.
- Choose the **narrowest type that holds every valid value**, and add `CHECK`
  constraints for the rules a type can't express. The type is the first
  constraint on a column.
- Store **money and other exact quantities as `INTEGER`**, in the smallest
  unit, never as `REAL`. Floating-point values can't represent most decimal
  fractions exactly. Name the unit in the column: `order_total_cents`.
- Store **points in time as `TEXT` in ISO 8601 format**, in UTC
  (`'2026-01-01 09:30:00'`). Convert to local time only for display. It's the
  format SQLite's date and time functions read and write, and it sorts in
  time order.
- Store dates as `TEXT` in `YYYY-MM-DD` format, and booleans as `INTEGER`
  with `CHECK (is_active IN (0, 1))`. SQLite has no date or boolean types:
  `TRUE` and `FALSE` are just `1` and `0`.
- **Use `TEXT` for strings**, with a `CHECK` constraint on its length when a
  real rule limits it: `CHECK (length(name) <= 100)`. SQLite ignores the
  length in `VARCHAR(100)`.
- Use JSON only for data that really has no fixed structure. Store it as
  `TEXT` with `CHECK (json_valid(settings))`, and read it with the `->>`
  operator. Data you filter or join on belongs in columns, where it can be
  typed, constrained and indexed.

## NULL

- **NULL means "unknown" or "not applicable".** It isn't zero, an empty string
  or false. Make every column `NOT NULL` unless NULL has a meaning for it.
- **Don't use magic values instead of NULL** (`''`, `0`, `-1`,
  `'1900-01-01'`). They look like real data, and every query has to know to
  exclude them.
- Comparisons with NULL are neither true nor false.
  `WHERE shipping_status <> 'shipped'` skips rows where `shipping_status` is
  NULL.
- Compare values that may be NULL with `IS` and `IS NOT`, which treat two
  NULLs as equal.
- **Never use `NOT IN` with a subquery that can return NULL.** One NULL makes
  the whole test unknown, and no rows match. Use `NOT EXISTS`:

  ```sql
  SELECT c.customer_id
  FROM customers AS c
  WHERE NOT EXISTS (
      SELECT 1
      FROM orders AS o
      WHERE o.customer_id = c.customer_id
  );
  ```

- Aggregate functions skip NULLs. `COUNT(column)` counts non-NULL values, while
  `COUNT(*)` counts rows. `AVG()` averages only the non-NULL values.
- Use `COALESCE()` to supply a default at the point of use, not to hide NULLs
  in stored data.

## Queries

- **Let the database do set work.** Filter, join, sort and aggregate in SQL,
  not in application loops.
- **Avoid N+1 queries**, where one query fetches a list and then another runs
  for each item. Fetch related rows with a join, or with one query that uses
  `IN` or `EXISTS`.
- **Keep filters index-friendly.** Don't wrap an indexed column in a function
  or calculation in `WHERE`. Rewrite the condition so the bare column is
  compared with a value:

  ```sql
  WHERE
      o.placed_at >= '2026-01-01 00:00:00'
      AND o.placed_at < '2026-02-01 00:00:00'
  ```

- **Use half-open ranges for time** (`>=` the start and `<` the end). They
  can't miss the last fraction of a second, or count a boundary twice.
- **Never rely on row order without `ORDER BY`.** Tables have no inherent
  order, and the same query can return rows differently from one run to the
  next.
- Make `ORDER BY` deterministic when it matters (for example, when paging) by
  ending it with a unique column.
- For deep pagination, use **keyset pagination** (`WHERE sort_key > last_seen`)
  instead of a large `OFFSET`. The database still reads every skipped row.
- **Don't use `DISTINCT` to hide duplicate rows** from a bad join. Fix the
  join.
- Use `EXISTS` to test whether matching rows exist. It can stop at the first
  match.
- Prefer `UNION ALL`. Use `UNION` only when you need duplicates removed,
  because removing them costs a sort or hash.
- Use `RETURNING` to get generated keys and changed values back from
  `INSERT`, `UPDATE` and `DELETE`, instead of querying again.

### Upserts

- Insert-or-update with `INSERT ... ON CONFLICT`, naming the conflict target
  and referring to the new values through `excluded`:

  ```sql
  INSERT INTO stock_levels (product_id, quantity)
  VALUES (42, 10)
  ON CONFLICT (product_id)
  DO UPDATE SET quantity = excluded.quantity;
  ```

- **Don't use `INSERT OR REPLACE`** (or `REPLACE`). It deletes the old row and
  inserts a new one, so every column the statement doesn't set loses its
  value.

## Transactions

- **Group writes that must succeed or fail together** into one transaction.
- **Keep transactions short.** Never wait for user input, network calls or
  other slow work while a transaction is open. Open transactions hold locks
  and block other sessions.
- **Choose the isolation level deliberately.** Know your engine's default and
  what it allows, and raise it when a transaction relies on data not changing.
  SQLite runs every transaction as serialisable, and lets only one connection
  write at a time.
- **Start every transaction that writes with `BEGIN IMMEDIATE`.** It takes
  the write lock at the start. A plain `BEGIN` waits until the first write, and
  if another connection has written in the meantime, the transaction fails
  with `SQLITE_BUSY` and has to start again.
- **Retry on serialisation failures and deadlocks.** They're a normal outcome
  under concurrency, not a bug. Retry the whole transaction, not just the
  failed statement. In SQLite, they're `SQLITE_BUSY` errors.
- **Access tables and rows in the same order** in every transaction, which
  makes deadlocks rarer.
- For read-modify-write logic, either do the read and the write inside one
  `BEGIN IMMEDIATE` transaction, which holds the write lock throughout, or use
  **optimistic concurrency**. SQLite has no `SELECT ... FOR UPDATE`. With
  optimistic concurrency, add a version column and make each update check it:

  ```sql
  UPDATE accounts
  SET
      balance = balance - 100,
      row_version = row_version + 1
  WHERE
      account_id = 42
      AND row_version = 7;
  ```

  If no row was updated, someone else changed the row first. Re-read it and
  try again.
- Keep read transactions short too. In WAL mode, an open read transaction
  stops the log from being checkpointed, so the WAL file keeps growing.

## Indexing

- **Index for the queries you actually run.** Start from the `WHERE`, `JOIN`
  and `ORDER BY` clauses of real queries.
- **Index every foreign key column.** Joins use it, and so does every delete
  of a parent row. SQLite doesn't create these indexes for you, and without
  one, every delete of a parent row scans the whole child table.
- In a multi-column index, **put columns tested for equality first**, then
  the column used for a range or sort. An index helps only with a prefix of
  its columns.
- **Don't over-index.** Every index slows every write, and uses space and
  memory.
- **Check plans before and after a change.** Use `EXPLAIN QUERY PLAN` to
  confirm a query uses the index you expect.
- Use a **partial index** (`WHERE ...`) when queries only ever look at a
  subset of rows, such as unprocessed jobs.
- Use an **expression index** when a query must filter on an expression. The
  query has to use exactly the same expression.
- Run `PRAGMA optimize` before closing each long-lived connection, so the
  query planner's statistics stay current.

## Security

- **Always pass values as parameters**, never by building SQL strings. String
  building is how SQL injection happens:

  ```sql
  /* Built by the application, with :email bound as a parameter. */
  SELECT customer_id
  FROM customers
  WHERE email = :email;
  ```

- Identifiers (table and column names) can't be parameters. If one must come
  from input, **check it against a fixed allowlist** of names.
- Open connections that only read in read-only mode (`mode=ro` in the
  connection URI), so a bug or an injected statement can't change data.
- **Treat a database file from outside as untrusted input.** It can contain
  triggers and views that run when you query it. Before using one, turn on
  SQLite's defensive mode (`SQLITE_DBCONFIG_DEFENSIVE`), keep
  `trusted_schema` off, and run `PRAGMA integrity_check`.
- Never store passwords. Store a slow, salted hash made by the application,
  using a dedicated password-hashing algorithm.
- Keep credentials out of SQL files and version control.

## Migrations

- **Make every schema change a migration**: a version-controlled script that
  runs in order. Never change a shared database by hand.
- **Never edit a migration once it has run** anywhere that matters. Write a
  new one.
- **Keep changes backward-compatible** with the code that's still running
  (expand, then contract). Add the new structure, deploy code that uses it,
  backfill, and remove the old structure in a later migration.
- **Add a required column with a default.** SQLite can only add a `NOT NULL`
  column that has a non-NULL default, and adding the constraint later means
  rebuilding the table.
- **Backfill large tables in batches**, so no single transaction holds the
  database's write lock for long.
- Rename in steps too. Add the new name, copy the data, move the code over,
  then drop the old name.
- **Run each migration in a transaction.** SQLite DDL is transactional, so a
  failed migration leaves no half-applied changes.
- **Track the schema version in `PRAGMA user_version`.** Each migration
  checks the number, makes its changes, and sets the next number, all in the
  same transaction.
- **Know what `ALTER TABLE` can do.** It can rename a table or column, add a
  column, and drop a column that no index, key or constraint uses. Any other
  change, such as changing a type or adding a constraint, needs a table
  rebuild: create the new table, copy the rows across, drop the old table,
  rename the new one, then run `PRAGMA foreign_key_check`. Turn foreign keys
  off before the rebuild's transaction and back on after it, because the
  setting can't change inside a transaction.
- Test migrations against a copy of production-sized data, because a change
  that's instant on a small table can lock a large one for minutes.

## Sources

- [SQL Style Guide](https://www.sqlstyle.guide/) by Simon Holywell
- ISO/IEC 9075, the SQL standard
- [Use The Index, Luke](https://use-the-index-luke.com/) by Markus Winand
- [SQLite documentation](https://sqlite.org/docs.html)
