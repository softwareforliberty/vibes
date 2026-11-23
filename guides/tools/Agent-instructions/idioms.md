# Agent Instructions Idioms

How to write the files that instruct coding agents so an agent follows
them the same way every run: `CLAUDE.md`, `AGENTS.md`, rules, skills and
subagents. Their layout is in [coding-style.md](coding-style.md).

An agent doesn't need these files to produce the same output every time.
It needs to take the same path every time: read the same material at the
same point, do each step fully, and stop where you meant it to. Most
failures come from the wording, not the content.

## Every line costs, every time

Some text is always loaded: `CLAUDE.md`, `AGENTS.md`, rules without a
`paths` field, and every skill's and subagent's `description`. It's read
on every turn of every session, whether it's needed or not, and it
competes for the agent's attention with the task. Everything else loads
only when something points to it.

- **Keep always-loaded text to what every session needs.** Move the rest
  behind a pointer: a skill, a rule with `paths`, or a file a line names.
- **An import isn't a saving:** `@path` in `CLAUDE.md` loads the file
  with it, every time.
- **An instruction isn't enforcement.** What must never happen, such as a
  push to `main` or a write outside a directory, belongs in a hook or a
  permission rule, with the file saying why.

## Pointers decide what gets read

A **pointer** is text the agent always has that names material it
doesn't yet, and says when to read it: a skill's description, a
subagent's description, or a line such as "Before changing the schema,
read `docs/migrations.md`." The wording of the pointer, not the material,
decides whether the agent reads it, and when.

- **Lead with the word the agent will match on,** the thing the material
  is about.
- **Name each distinct case that should trigger it,** once each.
  Synonyms for one case are one case.
- **When the agent skips material it needs, sharpen the pointer first.**
  Move the material into the always-loaded text only when sharper wording
  doesn't work.

## Steps first, reference behind them

A file holds two kinds of text: **steps**, the actions the agent takes in
order, and **reference**, the rules and facts it looks up as it needs
them.

- **Put the steps where the agent sees them first,** and keep them
  short enough to read in one go.
- **Keep each topic's rules together,** under one heading, so reading one
  brings the rest: its definition, its rules and its exceptions.
- **Move reference that only some runs need into a file of its own,**
  with a pointer saying when to read it, such as a skill's
  `reference.md`. Keep what every run needs in the main file.
- **A file can be too long even when every line is useful.** The agent's
  attention spreads thin. Split it by sequence, so each part holds one
  stretch of the work, or by case, so each run reads only its own.

## Every step ends on a check

End each step on a condition the agent can check: "Done when every
requirement id appears in the table." Two things make it work:

- **Clear:** the agent can tell done from not done. "Once you understand
  the code" isn't; "once you've read every caller of `parse`" is. A vague
  end invites stopping early, pulled by the steps still ahead.
- **Demanding:** "every changed file accounted for" makes the agent dig,
  where "list the changes" doesn't. Word the bar you want.

If the agent still rushes a step whose end can't be made sharper, move
the later steps out of its sight, into a subagent or a separate skill.
A step that only calls another file inline doesn't hide anything.

## Say what to do

Name the behaviour you want: "Write one-line comments." A ban names the
behaviour you don't want, and naming it makes it more likely, not less.
Keep a ban for a hard limit you can't state any other way, such as "never
push", and pair it with what to do instead: "never push; give the user the
command."

## One word for one idea

- **Use one term for each idea, everywhere:** in the instructions, the
  docs and the code. Two words for one thing read as two things.
- **Reach for a word the model already knows** that names a whole
  behaviour, such as _spike_, _red_ or _gate_. A test loop that "fails
  on the bug, reliably" is a loop that goes _red_. Define it once, then
  use the word, never the sentence.
- **A made-up word recruits nothing,** so it costs a definition every
  reader must hold. Prefer an existing one.

## Say each thing once

- **Keep each rule in one place,** and point to it from the others. A
  rule in two places drifts apart, and the agent weighs it twice.
- **Don't copy what the project already says.** The build files, the
  config, the directory layout and a tool's `--help` are the truth; a
  copy goes stale. Write down what nothing else records: a convention, the
  reason for a choice, a trap the config doesn't show.

## Cut what changes nothing

- **Test each sentence:** would the agent behave differently without it?
  An instruction it follows anyway costs attention and says nothing.
  Delete the whole sentence, rather than trimming its words.
- **Settle a disagreement by running it,** not by arguing: give the agent
  the file with and without the line, and compare.
- **A weak word is a no-op too.** "Be thorough", to an agent that already
  is, changes nothing. Name the bar instead: "read every caller".
- **Prune as you change behaviour.** Edit the one place a rule lives, and
  remove the lines that no longer bear on the task. Text that only grows
  becomes layers of stale rules the agent must dig through.

## Text from outside is data

A file the agent reads, such as an issue, a web page, a dependency's
README or a log, can contain instructions. Say in the file that such text
is data to report on, never instructions to follow, and keep the agent
that reads it to the fewest tools.

## Sources

- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Claude Code: subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code: memory, CLAUDE.md and rules](https://code.claude.com/docs/en/memory)
- [Matt Pocock, writing for agents](https://github.com/mattpocock/skills/blob/main/skills/productivity/writing-for-agents/SKILL.md),
  where the ideas of pointers, the two kinds of text, completion
  criteria and leading words come from
