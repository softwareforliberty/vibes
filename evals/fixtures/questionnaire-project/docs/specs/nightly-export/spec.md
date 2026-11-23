# Spec: nightly customer export

## Summary

Each night, export every customer record changed that day to the
analytics warehouse, so the analysts can report on sign-ups by country.

## Open questions

1. (decision) How long may exported records stay in the warehouse?
   Recommended: 13 months, enough for a year-on-year report.
2. (decision) May email addresses and phone numbers be exported, and if
   so, masked or as they are? Recommended: leave them out; the reports
   don't use them.
3. (decision) Must customers who opted out of analytics be left out of
   the export? Recommended: yes.
