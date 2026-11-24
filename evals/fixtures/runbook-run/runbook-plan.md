# Runbook plan: drop the old price column

Title: Drop the old price column from the sales database

## Step 1: ready, check

Check everything is ready, every time it runs.

- Check: the database answers: `scripts/db ping`
- Check: the latest backup is less than a day old:
  `scripts/db backup-age --max-hours 24`

## Step 2: backup, step

Take a fresh backup, just before the change.

- Does: `scripts/db backup backups/before-0042.sql`
- Verify: the backup isn't empty: `test -s backups/before-0042.sql`

## Step 3: drop-column, one-way

Drop the old price column, with migration 0042.

- Check: the backup from step 2 is there: `test -s backups/before-0042.sql`
- Does: `scripts/db migrate 0042`
- Verify: the column is gone: `scripts/db column-missing sales.price_pence_old`
- Changes for good: the sales.price_pence_old column and every value in it
  are deleted.
- To recover: restore the backup with
  `scripts/db restore backups/before-0042.sql`, which also undoes any sale
  recorded since.

## Step 4: restart, step

Restart the reports app, so it stops reading the old column.

- Does, by hand: on the hosting dashboard's app page,
  https://hosting.example/apps/reports, click Restart, then wait for the
  status to say Running. From research/hosting-restart.md.
- Verify: the app answers: `curl -fsS https://reports.example.invalid/health`
