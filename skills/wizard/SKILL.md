---
name: wizard
description: >-
  Writes a wizard for steps only you can do, such as creating an API key in
  a provider's dashboard, setting a CI secret or registering a webhook: a
  bash script you run in your own terminal that opens each page, says what
  to click, and saves what you paste where it belongs, with secrets typed
  into hidden prompts that never reach the agent. A run that adds such
  settings writes one at its end.
argument-hint: "<the procedure, such as: set up Stripe for local development and CI>"
disable-model-invocation: true
---

# Wizard: walk the user through what only they can do

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

Procedure: $ARGUMENTS

Some steps need a person: signing in to a provider's dashboard, creating a
key, copying it back, setting a CI secret. Write a **wizard**, a bash
script that walks the user through them one stage at a time. It opens each
page, says what to click and copy, and saves each value where it belongs:
`.env`, created readable only by them, or a GitHub Actions secret or
variable. Secrets go into hidden prompts, straight to where they're saved,
so they never pass through this conversation.

You scope the procedure and find each step in the provider's own
documentation; `vibes:wizard-writer` writes the stages onto vibes' tested
wizard library. **Nobody runs the wizard but the user.**

## The agents

`vibes:wizard-writer` and `vibes:researcher`.

**Check they're loaded before anything else:** each must be among the
agent types you can spawn. If any is missing, stop and tell the user, as
the vibe skill's [agents section](../vibe/SKILL.md#the-agents) says, which
gives the cause and the fix, and why no other agent may stand in for one.

## Steps

1. **Find the run directory:** in a vibes run, its own; otherwise make
   `.vibes/wizard-<slug>` from the repository root, keeping it out of git:

   ```sh
   mkdir -p .vibes/wizard-<slug>
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

2. **Scope it from the repository,** before asking anything: the example
   env files, such as `.env.example`; the README's setup steps;
   `docker-compose*`; the framework's config; and every `secrets.<NAME>`
   and `vars.<NAME>` in `.github/workflows/`, each a value the wizard must
   produce. At the end of a run, start from what
   `"${CLAUDE_PLUGIN_ROOT}/bin/setup-needs" <base>` lists. For a change of
   state, such as moving to a new provider, find where things stand, where
   they must end, and each action between that can't be undone. When the
   procedure is mostly such changes, such as a migration or a cutover,
   recommend `/vibes:runbook` instead, which checks and fences each one.

   Write the stages in order. For each value, know where the user finds
   it, where it's saved (`.env`, a GitHub secret, a GitHub variable, or
   nowhere), and whether it's a secret. Done when every value has all
   three.
3. **Confirm the stages** with the user: show them in order, with the
   values each saves, and ask whether to add, drop or reorder any,
   recommending yes to the list as it is. An unattended run skips this,
   and the report lists the stages.
4. **Find each step in the provider's own documentation:** a
   `vibes:researcher` for each outside service, all in one message, each
   asking for the exact steps on the current pages to get the stage's
   values or do its action, with the note's path,
   `.vibes/<run>/research/<topic>.md`. A step the sources don't settle is
   marked for the user to check, never guessed.
5. **Write the plan** to `.vibes/<run>/wizard-plan.md`: the wizard's
   title, then each stage in order with its task, its page, its values
   with where each comes from and goes and whether it's a secret, any
   action that can't be undone, and its research note.
6. **Spawn `vibes:wizard-writer`,** with the plan, the research notes, the
   template, `${CLAUDE_PLUGIN_ROOT}/skills/wizard/templates/wizard.sh`,
   the wizard's path, `.vibes/<run>/wizard.sh`, and the check command,
   `${CLAUDE_PLUGIN_ROOT}/bin/wizard-check`. On `WIZARD PROBLEMS:`,
   give the problems to a fresh one.
7. **Check it yourself:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/wizard-check" .vibes/<run>/wizard.sh` exits
   0, with `SYNTAX OK` and `LIBRARY INTACT`.
8. **Hand it over:** the wizard's path, what it will ask for and where
   each value goes, any step to check by hand, and the command:

   ```sh
   bash .vibes/<run>/wizard.sh
   ```

   Tell the user to run it from the repository root **in their own
   terminal,** not through this conversation, so their secrets stay out
   of it, and that they can stop and run it again: it keeps what it saved.
9. **Offer to keep it** when the steps will be needed again, such as for
   each new developer: with the user's yes, copy it to
   `scripts/setup-<thing>`, make it executable, link it from the README's
   setup section, and commit it as the vibe skill's
   [agents section](../vibe/SKILL.md#the-agents) says for your own
   commits. The gate then holds it to the BASH guide like any other
   script.

## At the end of a run

The vibe, debug and optimise workflows run, before their final report:

```sh
"${CLAUDE_PLUGIN_ROOT}/bin/setup-needs" <base branch>
```

When it lists anything, follow the steps above to write
`.vibes/<run>/wizard.sh` for those settings, without asking first: a
wizard does nothing until the user runs it. The report then says what the
wizard asks for, and the command to run it.
