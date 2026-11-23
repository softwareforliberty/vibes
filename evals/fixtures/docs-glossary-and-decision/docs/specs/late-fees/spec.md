# Late fees

## Summary

Charge a late fee on invoices that are overdue, so clients who pay late
pay for the cost of chasing them.

## Requirements

- **R1:** A job runs every night at 02:00 and marks each invoice overdue
  once 30 days have passed since its issue date and it isn't fully paid.
- **R2:** When the job marks an invoice overdue, it adds a late fee of
  1.5% of the unpaid total, in whole cents rounded half up, to the
  invoice's `late_fee_cents`, and emails the client.
- **R3:** The fee is charged once per invoice.

## Open questions

None.
