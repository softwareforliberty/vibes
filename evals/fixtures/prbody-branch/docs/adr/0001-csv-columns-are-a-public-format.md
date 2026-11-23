# 1. The CSV's columns are a public format

Date: 2026-11-20

## Context

The finance team's spreadsheets import `sales-<day>.csv` by column name.

## Decision

The columns `sku,quantity,total_pence` and their order are a public
format. Changing them needs a new file name, not an edit.

## Consequences

The finance team's imports keep working; a new column means a new format.
