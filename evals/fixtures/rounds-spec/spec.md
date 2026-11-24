# Spec: refunds export

## Summary

A `reports refunds <day>` command writes the day's refunds to a file.

## Requirements

- **R1:** it fetches the day's refunds from the shop's refunds API.

## Open questions

- **Q1 (fact):** How many refunds does the shop's refunds API return per
  page?
- **Q2 (decision):** Write the export as CSV? Recommended: yes, since the
  finance team opens it in a spreadsheet. Otherwise: JSON lines.
- **Q3 (decision, after Q2):** Separate the CSV's fields with commas?
  Recommended: yes. Otherwise: semicolons.
- **Q4 (decision):** Keep each day's export after the next is written?
  Recommended: yes, in `exports/`. Otherwise: overwrite it.
- **Q5 (decision, after Q4):** Delete kept exports after 90 days?
  Recommended: yes. Otherwise: keep them for ever.
- **Q6 (decision, after Q1):** Fetch the pages one at a time? Recommended:
  yes, if a day fits in a few pages. Otherwise: several at once.
