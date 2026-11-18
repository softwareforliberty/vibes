# Late fees

## Summary

Charge a late fee on invoices that are overdue, so customers who pay late
pay for the cost of chasing them.

## Requirements

- **R1:** An invoice is overdue once 30 days have passed since its issue
  date and it isn't fully paid.
- **R2:** The late fee is 1.5% of the invoice's unpaid total, stored on the
  invoice as `late_fee`, a `float` number of dollars rounded to two
  decimal places.
- **R3:** The fee is charged once per invoice, the first time it's found
  overdue.

## Open questions

None.
