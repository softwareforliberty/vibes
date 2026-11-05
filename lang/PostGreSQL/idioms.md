# PostgreSQL Idioms and Principles

How to design schemas and write SQL well in PostgreSQL 15 and later.
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
- **Grant the least privilege that works.** An application account can read
  and write data. It doesn't own or change the schema.

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
- Use a **surrogate key** (a `BIGINT GENERATED ALWAYS AS IDENTITY` column) as
  the primary key for entity tables. Natural values such as emails and product
  codes change, and every foreign key would have to change with them. Don't
  use `SERIAL`: identity columns are standard SQL, and their sequence belongs
  to the column.
- Put a **`UNIQUE` constraint on the natural key** as well, so duplicates
  can't creep in behind the surrogate key.
- A junction table's primary key is the pair of foreign keys it links.
- Never reuse a deleted key value.

### Constraints

- Declare a **`FOREIGN KEY`** for every reference to another table, so orphan
  rows can't exist.
- Choose each foreign key's `ON DELETE` behaviour deliberately: `RESTRICT`
  (the default to reach for), `CASCADE` (for rows that can't exist without
  their parent), or `SET NULL` (for optional links).
- Add **`CHECK` constraints** for rules about a single row: ranges, allowed
  values, and relationships between columns.
- Represent a fixed set of values with a `CHECK` constraint, or with a lookup
  table when the values carry extra data or change at run time.
- **Don't use `CREATE TYPE ... AS ENUM`.** You can add values to an enum type,
  but you can't remove or rename them without rebuilding every column that
  uses it.

### Data types

- Choose the **narrowest type that holds every valid value**. The type is the
  first constraint on a column.
- Store **money and other exact quantities as `NUMERIC`**, never as `FLOAT`
  or `REAL`. Floating-point values can't represent most decimal fractions
  exactly. Don't use the `MONEY` type either: its behaviour depends on the
  server's locale setting.
- Store **points in time as `TIMESTAMPTZ`**, in UTC. Convert to local time
  only for display. `TIMESTAMP` without a time zone throws away which moment
  a value means.
- Store dates as `DATE` and booleans as `BOOLEAN`, never as strings or
  numbers.
- **Use `TEXT` for strings**, with a `CHECK` constraint on its length when a
  real rule limits it. In PostgreSQL, `VARCHAR(n)` is no faster than `TEXT`,
  and changing a `CHECK` is easier than changing a type.
- Store UUIDs as `UUID`, not as text.
- Use `JSONB`, not `JSON`, and only for data that really has no fixed
  structure. Data you filter or join on belongs in columns, where it can be
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
- Compare values that may be NULL with `IS DISTINCT FROM` or
  `IS NOT DISTINCT FROM`, which treat two NULLs as equal.
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
      o.placed_at >= TIMESTAMPTZ '2026-01-01 00:00:00+00'
      AND o.placed_at < TIMESTAMPTZ '2026-02-01 00:00:00+00'
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
- Prefer `UNION ALL`. Use `UNION DISTINCT` only when you need duplicates
  removed, because removing them costs a sort or hash.
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

- Use `MERGE` when one statement must insert, update and delete depending on
  the source rows.

## Transactions

- **Group writes that must succeed or fail together** into one transaction.
- **Keep transactions short.** Never wait for user input, network calls or
  other slow work while a transaction is open. Open transactions hold locks
  and block other sessions.
- **Choose the isolation level deliberately.** Know your engine's default and
  what it allows, and raise it when a transaction relies on data not changing.
  PostgreSQL defaults to `READ COMMITTED`, where each statement sees the data
  committed before it started, not before the transaction started.
- **Retry on serialisation failures and deadlocks.** They're a normal outcome
  under concurrency, not a bug. Retry the whole transaction, not just the
  failed statement. In PostgreSQL, they're SQLSTATE `40001` and `40P01`.
- **Access tables and rows in the same order** in every transaction, which
  makes deadlocks rarer.
- For read-modify-write logic, either lock the rows you read with
  `SELECT ... FOR UPDATE`, or use **optimistic concurrency**. With optimistic
  concurrency, add a version column and make each update check it:

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

- For work queues, claim rows with `SELECT ... FOR UPDATE SKIP LOCKED`, so
  workers don't wait on rows another worker already holds.

## Indexing

- **Index for the queries you actually run.** Start from the `WHERE`, `JOIN`
  and `ORDER BY` clauses of real queries.
- **Index every foreign key column.** Joins use it, and so does every delete
  of a parent row. PostgreSQL doesn't create these indexes for you.
- In a multi-column index, **put columns tested for equality first**, then
  the column used for a range or sort. An index helps only with a prefix of
  its columns.
- **Don't over-index.** Every index slows every write, and uses space and
  memory.
- **Check plans before and after a change.** Use `EXPLAIN` to confirm a
  query uses the index you expect, and `EXPLAIN (ANALYZE, BUFFERS)` to see
  what it actually did.
- Use a **partial index** (`WHERE ...`) when queries only ever look at a
  subset of rows, such as unprocessed jobs.
- Use an **expression index** when a query must filter on an expression. The
  query has to use exactly the same expression.
- Use `INCLUDE` to add columns that a query reads but doesn't filter on, so
  the index alone can answer it.

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
- Give each application its own database account, with only the privileges
  it needs.
- Never store passwords. Store a slow, salted hash made by the application,
  using a dedicated password-hashing algorithm.
- Keep credentials out of SQL files and version control.
- Give every `SECURITY DEFINER` function a fixed `search_path`
  (`SET search_path = pg_catalog, pg_temp`), and schema-qualify the objects it
  uses. Otherwise a caller can put their own objects first in the path and
  run code with the function owner's privileges.
- Use **row-level security** when different users must see different rows of
  the same table. The database then enforces it, whatever query is run.

## Migrations

- **Make every schema change a migration**: a version-controlled script that
  runs in order. Never change a shared database by hand.
- **Run each migration in a transaction.** PostgreSQL DDL is transactional,
  so a failed migration leaves no half-applied changes. The exception is
  `CREATE INDEX CONCURRENTLY`, which can't run inside a transaction, so put it
  in a migration of its own.
- **Set `lock_timeout` at the start of every migration** (for example,
  `SET lock_timeout = '5s'`). A migration waiting for a lock blocks every
  query that queues behind it. It's better for the migration to fail and be
  retried.
- **Create indexes on live tables with `CREATE INDEX CONCURRENTLY`**, which
  doesn't block writes.
- **Add constraints to large tables in two steps.** Add them with
  `NOT VALID`, which only checks new rows, then run
  `VALIDATE CONSTRAINT`, which checks existing rows without blocking writes.
- **Never edit a migration once it has run** anywhere that matters. Write a
  new one.
- **Keep changes backward-compatible** with the code that's still running
  (expand, then contract). Add the new structure, deploy code that uses it,
  backfill, and remove the old structure in a later migration.
- **Add a required column in steps.** Add it as nullable, backfill it, then
  add `NOT NULL`.
- **Backfill large tables in batches**, so no single statement locks the table
  or holds a huge transaction open.
- Rename in steps too. Add the new name, copy the data, move the code over,
  then drop the old name.
- Test migrations against a copy of production-sized data, because a change
  that's instant on a small table can lock a large one for minutes.

## Sources

- [SQL Style Guide](https://www.sqlstyle.guide/) by Simon Holywell
- ISO/IEC 9075, the SQL standard
- [PostgreSQL documentation](https://www.postgresql.org/docs/current/)
- [Use The Index, Luke](https://use-the-index-luke.com/) by Markus Winand
