---
name: runbook
description: >-
  Writes a runbook for a change that can't simply be undone, such as a
  production migration, a DNS cutover or rotating a signing key: a bash
  script you run in your own terminal that checks things are ready before
  each change, shows what each one-way step changes and how to recover,
  waits for you to type its name, checks each change worked, and starts
  again where it stopped. /vibes:pr offers one for a change it judges a
  one-way door.
argument-hint: "<the change, such as: move the sales database to the new server>"
disable-model-invocation: true
---

# Runbook: walk the user through a change that can't be undone

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

Change: $ARGUMENTS

Some changes can't simply be undone: a migration that drops a column, a
DNS cutover, a release that publishes something for good, rotating a key
that revokes the old one. Write a **runbook**, a bash script that walks
the user through the change one step at a time, on vibes' tested runbook
library, which builds on the wizard library:

- **Checks before each change:** each step first checks what it needs,
  such as that a fresh backup exists or the new server answers, and stops
  before changing anything when one fails.
- **A fence round each one-way step:** it says what the step changes for
  good and how to recover, and runs it only once the user types the
  step's name.
- **Verification after each change:** each step checks it worked, such as
  that the row counts match, before the next one starts.
- **A log, and resuming:** each step is logged, and a second run starts
  from the step that stopped, never repeating one that finished.

You find where things stand, where they must end and every step between,
from the repository and each provider's own documentation;
`vibes:wizard-writer` writes the steps onto the library. **Nobody runs the
runbook but the user,** and a wrong step can lose data, so every command
comes from the documentation or the project, never a guess.

## The agents

`vibes:wizard-writer` and `vibes:researcher`.

**Check they're loaded before anything else:** each must be among the
agent types you can spawn. If any is missing, stop and tell the user, as
the vibe skill's [agents section](../vibe/SKILL.md#the-agents) says, which
gives the cause and the fix, and why no other agent may stand in for one.

## Steps

1. **Make the run directory,** `.vibes/runbook-<slug>` from the
   repository root, keeping it out of git:

   ```sh
   mkdir -p .vibes/runbook-<slug>
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

2. **Find where things stand and where they must end,** from the
   repository before asking anything: the change itself, such as a
   branch's migrations, from `git diff <base>...HEAD`; the deploy and
   release scripts; the CI and deploy workflows; the infrastructure's
   config, such as Terraform, OpenTofu, Kubernetes or Compose files; the
   README's deploy or release section; and any earlier runbook in
   `scripts/`. Done when you can say what is true before the change, what
   must be true after it, and what has to be done to get there.
3. **Split it into steps,** each one thing that changes the world, in
   order, and for each step:
   - **its kind:** `check` for a step that only checks and runs every
     time, such as that everything is ready; `one-way` for one that can't
     be undone by doing the opposite; `step` for any other;
   - **its checks:** what must hold before it changes anything, each with
     a command that only reads;
   - **what it does:** each command it runs, or what the user does by
     hand, such as in a dashboard;
   - **its verification:** what must hold once it's done, each with a
     command that only reads;
   - **for a one-way step,** what it changes for good, and how to recover:
     the undo when there is one, or else what to do instead, such as
     restoring the backup an earlier step took. A one-way step with no
     way to recover needs an earlier step that makes one, such as a
     backup: add it.

   Start with a `check` step for everything the whole change needs, such
   as being signed in to the right account and having a recent backup.
   Done when every one-way step has its checks, verification and
   recovery.
4. **Confirm the steps** with the user: show them in order, the one-way
   steps marked with what each changes and how to recover, and ask
   whether to add, drop or reorder any, recommending yes to the list as
   it is. Ask about anything only they know, such as the maintenance
   window or which backup to trust. An unattended run skips this, and the
   report lists the steps.
5. **Find each step in the provider's own documentation:** a
   `vibes:researcher` for each outside service or tool, all in one
   message, each asking for the exact commands or pages for its steps and
   their checks, at the version the project uses, with the note's path,
   `.vibes/<run>/research/<topic>.md`. Commands from the project's own
   scripts need no research. A step the sources don't settle is marked
   for the user to check, never guessed.
6. **Write the plan** to `.vibes/<run>/runbook-plan.md`: the title, then
   each step in order, as step 3 lists, with its research note.
7. **Spawn `vibes:wizard-writer` in `runbook` mode,** with the plan, the
   research notes, the template,
   `${CLAUDE_PLUGIN_ROOT}/skills/runbook/templates/runbook.sh`, the
   runbook's path, `.vibes/<run>/runbook.sh`, and the check command,
   `${CLAUDE_PLUGIN_ROOT}/bin/wizard-check`. On `RUNBOOK PROBLEMS:`, give
   the problems to a fresh one.
8. **Check it yourself:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/wizard-check" .vibes/<run>/runbook.sh`
   exits 0, with `SYNTAX OK`, `LIBRARY INTACT` and `STEPS OK`. Then read
   `runbook.sh` below its `# ── STEPS` line, and check each step against
   the plan: every one-way step is a `runbook::one_way` with its recovery,
   every check and verification is there, and every command matches the
   plan or a note. Never run it, not even with `--plan`.
9. **Hand it over:** the runbook's path, its steps, with each one-way
   step and its recovery, anything to check by hand, and the commands:

   ```sh
   bash .vibes/<run>/runbook.sh --plan
   bash .vibes/<run>/runbook.sh
   ```

   The first shows the steps and changes nothing. Tell the user to run the
   second from the repository root **in their own terminal,** not through
   this conversation, and that if it stops, they fix what it says and run
   it again: it starts from that step.
10. **Offer to keep it** when the change will happen again, such as a
    yearly key rotation or each release: with the user's yes, copy it to
    `scripts/runbook-<thing>`, make it executable, link it from the
    README, and commit it as the vibe skill's
    [agents section](../vibe/SKILL.md#the-agents) says for your own
    commits. The gate then holds it to the BASH guide like any other
    script.
