# Debug: <slug>

<!--
The debug run's state, so an interrupted run can carry on. One line for
each finished step, naming the commits or the file that holds the details.
-->

status: running
unattended: <yes or no>
issue: <#number, or none>

## Symptom

<the symptom as the user gave it, and their answers>

## Setup

- base branch: <branch>
- base commit: <commit>
- spike branch: spike/debug-<slug>
- fix branch: debug/<slug>
- spec directory: <path>/debug-<slug>/
- debug tag: vibes-debug-<slug>
- guides: <guides>

## Diagnosis

- repro.sh: <bin/repro line>
- minimal.sh: <bin/repro line>
- hypothesis rounds: <n>
- cause: <the confirmed hypothesis, or none yet>
- proved by: <the spike commit, and both GREEN lines>
- seam: <the test file and what it calls, or none, and why>

## Unattended decisions

None.

## Progress

phase: <0 to 8>
- <each finished step>
