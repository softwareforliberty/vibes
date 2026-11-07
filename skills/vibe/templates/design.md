# Design: <task>

<!--
The design says how the code will be structured, at the level of modules
and their boundaries, not lines of code. Keep every heading, replace each
comment with the section's content, and write "None." under a heading that
doesn't apply. Keep to structure and boundaries: the details are the
spike's to test.
-->

## Kind of software

<!-- Which architecture guide applies, and why. -->

## Approach

<!--
The design in a few sentences, the alternatives considered, and why this
one was chosen.
-->

## Components

<!--
Each module or layer: its one job, what it may depend on, and its
interface, as the main types and function signatures.
-->

### Component

- **Job:**
- **Depends on:**
- **Interface:**

## Boundary types

<!--
The data types that cross each boundary, and where each conversion
happens.
-->

## Flows

<!--
For each main operation, the path through the components, naming the
requirement ids it serves.
-->

## State and concurrency

<!--
Who owns each piece of state, and the threads, execution contexts or
locks involved, where there are any.
-->

## Errors

<!--
How each layer reports errors, and where they become what the user sees.
-->

## Dependencies

<!-- Each third-party dependency, and why it's needed. -->

## Testing

<!-- How each layer is tested, and how each requirement will be verified. -->

## Traceability

<!--
Every requirement and quality id in the spec, with the components that
satisfy it. Every id in the spec appears here.
-->

| Id | Components |
| --- | --- |
| R1 | <components> |

## Boundary rules

<!--
The dependency rules between components, such as "the core never imports
the adapters", written so the build or an architecture test from the
guide's tools.md can enforce them.
-->

- <component> never depends on <component>.

## Change log

<!--
Empty until the design is approved. Then one row for every change: the
date, the components it touches, what changed and why.
-->

| Date | Components | Change | Why |
| --- | --- | --- | --- |
