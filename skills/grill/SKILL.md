---
name: grill
description: >-
  Stress-tests a plan or an idea before any work starts: maps every
  decision it leaves open and every fact it rests on, looks up the facts,
  and asks you the decisions in rounds, each holding only the questions
  whose prerequisites you've answered, until nothing is left. Ends with a
  decisions document /vibes:vibe can start from. Changes nothing else.
argument-hint: "<the plan or idea, or the path of a document describing it>"
disable-model-invocation: true
---

# Grill: settle a plan before it's built

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

Plan: $ARGUMENTS

Find every decision the plan leaves open and every fact it rests on, and
settle them with the user, nothing silently assumed. Ask in **rounds**, as
the vibe skill's [Open questions](../vibe/SKILL.md#open-questions) says:
each round asks every decision whose prerequisites are answered, the
facts are researched rather than asked, and each answer can make some
questions moot and raise new ones. The result is a decisions document the
user, or `/vibes:vibe`, can start from.

**It changes nothing in the project:** you write only the decisions
document and, with the user's yes, decision records and glossary terms.

## The agents

`vibes:researcher`.

**Check it's loaded before anything else:** it must be among the agent
types you can spawn. If it's missing, stop and tell the user, as the vibe
skill's [agents section](../vibe/SKILL.md#the-agents) says, which gives
the cause and the fix, and why no other agent may stand in for one.

## Steps

1. **Read the plan,** and what it touches: the code, the glossary and the
   decision records, as the vibe skill's
   [Phase 0](../vibe/SKILL.md#phase-0-set-up) finds them. Pick a short
   slug, and make the directory from the repository root:

   ```sh
   mkdir -p .vibes/grill-<slug>
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

2. **Map the tree** into `.vibes/grill-<slug>/decisions.md`, from
   `${CLAUDE_PLUGIN_ROOT}/skills/grill/templates/decisions.md`: the plan
   in a paragraph, and in Open questions every decision it leaves open
   and every fact it rests on, each marked and with what it waits on, as
   the spec template's
   [Open questions](../vibe/templates/spec.md) comment says. Settle
   yourself what the project's own code or records already answer, and
   put it under Facts or Decided, citing them. A decision record that
   rules a question out answers it. Done when every choice the plan's
   outcome depends on is either settled or in Open questions.
3. **Ask in rounds,** as the vibe skill's
   [Open questions](../vibe/SKILL.md#open-questions) says, with
   `decisions.md` in place of the spec and you in the designer's place:
   after each round, move each answer under Decided or Facts, each
   question it made moot under Not needed, and add each new question an
   answer raises, with what it waits on. Done when Open questions says
   "None.".
4. **Check you've reached the same understanding:** show the decided
   plan in a few lines, and ask whether it's what they mean, recommending
   yes. Their corrections start another round. Fill in the date and the
   number of rounds.
5. **Offer to keep what lasts,** in one ask:
   - each decision that's hard to reverse, surprising without its reason
     and a real choice, as a decision record, written from
     `${CLAUDE_PLUGIN_ROOT}/skills/vibe/templates/adr.md` and numbered
     after the project's last;
   - each new term the plan brings, in the glossary.

   Commit what they accept, on its own, as the vibe skill's
   [agents section](../vibe/SKILL.md#the-agents) says for your own
   commits.
6. **Hand it over:** the path of `decisions.md`, and the command to build
   it, `/vibes:vibe <the plan>, from the decisions in <path>`, whose
   designer takes each decision as the user's answer.
