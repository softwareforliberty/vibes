# Diagnosis: <slug>

<!--
What the diagnoser found, for the main agent, the bug spec and the
builder. Reproduce mode fills in the first three sections; probe mode the
rest. Write "None yet." under a section that's still to come.
-->

## Symptom

<!-- The user's exact symptom: the wrong output or the error they saw. -->

## Reproduction

<!--
How repro.sh drives the code and checks the symptom, and its bin/repro
line. If there's none: every way tried and why it failed, and what would
make it possible.
-->

## Minimal scenario

<!-- What minimal.sh keeps, and what cutting each part showed. -->

## Cause

<!-- The confirmed hypothesis, by its id, and the evidence for it. -->

## Proving change

<!--
The smallest change that removed the cause, in a few lines, with its
commit on the spike branch, and the GREEN lines for minimal.sh and
repro.sh.
-->

## Seam

<!--
Where a regression test can drive the bug the way it really happens: the
test file, and the function or command it calls. Or "None", and why no
test can reach it, which is a finding about the code's structure.
-->
