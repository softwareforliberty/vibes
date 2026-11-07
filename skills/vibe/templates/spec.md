# Spec: <task>

<!--
The spec says what the task does, never how. Keep every heading, replace
each comment with the section's content, and write "None." under a heading
that doesn't apply. Every statement must be specific enough to check:
"rejects a quantity below 1 with the error `quantity must be at least 1`",
never "validates the quantity". Say each thing once, in as few words as
that precision allows: every agent in the run reads the spec.
-->

## Summary

<!-- The task in a short paragraph, and who or what uses the result. -->

## Scope

<!-- What's in scope, and what's explicitly out of it. -->

**In scope:**

- <what's included>

**Out of scope:**

- <what's left out>

## Definitions

<!--
Every term a reader might misread, and every outcome several requirements
share, such as what a usage error prints and its exit status, so the
requirements can name it instead of repeating it.
-->

- **Term:** what it means here.

## Requirements

<!--
Every behaviour, one per entry, grouped by feature under ### headings.

- Each has a stable id: R1, R2 and so on. Never renumber them. A removed
  requirement keeps its id, written as "- **R3:** Removed: <the reason>."
- Tests name the ids they cover in a comment, "Covers: <spec directory
  name> R1, R2", and scripts/check-requirements checks them.
- Each says what happens for which input, in which state, precisely
  enough to write a test from. Add an acceptance check, such as an example
  input and its result, only when the requirement's own words don't
  already say how to check it, and never restate the requirement in it.
- Errors and edge cases are requirements too: empty, missing, duplicate,
  too large, invalid, concurrent, interrupted and unauthorised input,
  wherever they can happen.
-->

### Feature

- **R1:** When <input, in this state>, <what happens>. Acceptance:
  <an example that shows it's met, where one helps>.

## Interfaces

<!--
The exact shape of everything the outside world sees, such as command-line
arguments and exit codes, endpoints, request and response bodies, file
formats, messages, and screens and their controls.
-->

## Quality requirements

<!--
Limits on performance, resource use, security, compatibility, platforms,
accessibility and localisation, each with an id (Q1, Q2 and so on) and a
measurable target. Leave out the ones that don't apply.
-->

- **Q1:** <quality> <measurable target>.

## Constraints

<!-- The languages, dependencies, existing code and conventions to fit. -->

## Assumptions

<!--
Each decision made where the task was silent, in a line or two: the
decision, why, and any options not chosen. Keep these to details: anything
that changes what the user gets is an open question.
-->

## Open questions

<!--
Each question only the user can answer, with the options. The spec isn't
complete until this section says "None.".
-->

## Change log

<!--
Empty until the spec is approved. Then one row for every change: the date,
the ids it touches, what changed and why.
-->

| Date | Ids | Change | Why |
| --- | --- | --- | --- |
