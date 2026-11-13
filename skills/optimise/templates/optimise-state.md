# Optimise: <slug>

<!--
The optimise run's state, so an interrupted run can carry on. One line for
each finished step, naming the commits or the file that holds the details.
-->

status: running
unattended: <yes or no>
max attempts: <n>

## Task

<the task as the user gave it, and their answers>

## Setup

- base branch: <branch>
- baseline: <commit>
- rebuild branch: optimise/<slug>
- spec directory: <path>/optimise-<slug>/
- guides: <guides>
- noise floor: <±x.x% from profile/aa/main>
- guard rails: <bench guards, such as rss_kib=10>
- tools allowed to install: <none, or each tool and its command>

## Candidates

| Attempt | Candidate | Branch | Commit | Verdict | Accepted |
| --- | --- | --- | --- | --- | --- |

best: <branch and commit>

## Unattended decisions

None.

## Progress

phase: <0 to 8>
- <each finished step>
