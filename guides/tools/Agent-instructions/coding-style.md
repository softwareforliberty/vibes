# Agent Instructions Coding Style

How the files that instruct coding agents look: `CLAUDE.md` and
`AGENTS.md`, path rules in `.claude/rules/`, skills (`SKILL.md`), subagent
definitions, and the files they point to. They're Markdown, read by a
model on every run, so their layout serves the model first and a human
editor second.

This guide covers how the files look. For how to write them so an agent
follows them the same way every time, see [idioms.md](idioms.md). The
tools are in [tools.md](tools.md).

## Baseline

- **Claude Code,** with skills, subagents and `.claude/rules/`. `AGENTS.md`
  follows the [AGENTS.md](https://agents.md/) convention, which other
  coding agents read too.
- **CommonMark with GitHub's extensions:** tables, fenced code and task
  lists.

## Files

- **`CLAUDE.md` or `AGENTS.md` at the repository root** holds what every
  session in the project needs. Keep it under 200 lines: Claude Code loads
  it whole into every session, and a longer file is followed less closely.
- **`.claude/rules/<topic>.md`** holds what matters only for some files.
  Give it a `paths` field, so it loads only when Claude works on them.
- **A skill is a directory,** `skills/<name>/SKILL.md`, named for what it
  does, in kebab-case, such as `review-pr`. Its supporting files sit
  beside it: `templates/`, `reference.md`, or scripts.
- **A subagent is one file,** `agents/<name>.md`, named for its role, such
  as `security-reviewer`.
- **`CLAUDE.local.md`** is personal, and stays out of git.

## Frontmatter

Skills and subagents start with YAML frontmatter. Use only the fields the
file needs, in this order:

- **A skill:** `name`, `description`, `argument-hint` when it takes
  arguments, then `disable-model-invocation: true` for one only a person
  should start, such as a workflow that commits or posts.
- **A subagent:** `name`, `description`, `tools`, the fewest it needs, as a
  comma-separated list, then `model`.

Write a long `description` as a folded block, `>-`, wrapped like the body:

```yaml
---
name: pr-writer
description: >-
  Writes the body of a pull request for a branch: the smallest view that
  makes the change clear, the evidence before and after, and the merge
  risk. Used only by /vibes:pr.
tools: Read, Grep, Glob, Write
model: inherit
---
```

## Layout

- **One `#` heading,** the file's subject, then `##` sections in the
  order the agent uses them: what it's for, its inputs, its steps, its
  rules, and what it replies.
- **Number steps the agent takes in order,** and use bullets for rules
  and options that have no order.
- **Lead a bullet with its point in bold,** ending with a colon or a full
  stop, so the agent can scan for it: `- **Install nothing:** …`.
- **Put every path, command, field, label and literal reply in
  backticks,** so it's copied exactly.
- **Show a file the agent must write as a fenced template,** with
  `<placeholders>` in angle brackets, and a four-backtick fence around a
  template that holds a fence of its own.
- **Link to a supporting file by a relative path,** or by
  `${CLAUDE_PLUGIN_ROOT}` in a plugin, and say when to read it.
- **Wrap prose at 79 columns,** never splitting a link or a code span.

## Voice

- **Address the agent as "you",** in the present tense: "You review one
  change."
- **Write instructions in the imperative:** "Read the spec first."
- **Use short sentences and plain words,** and one term for each idea
  throughout, as [idioms.md](idioms.md#one-word-for-one-idea) says.

## Sources

- [Claude Code: skills](https://code.claude.com/docs/en/skills)
- [Claude Code: subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code: memory, CLAUDE.md and rules](https://code.claude.com/docs/en/memory)
- [AGENTS.md](https://agents.md/)
