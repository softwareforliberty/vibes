---
name: retro
description: >-
  Looks back on a Claude Code session, this one by default, and suggests
  changes to the project's checks, coding standards, steering files and
  docs that would make the next session go better, each citing the moments
  in the session behind it. Suggests only, and changes nothing: anything
  that would remove or loosen a check is listed apart from the rest.
argument-hint: "[session id or transcript path] [what to focus on]"
disable-model-invocation: true
---

# Retro: look back on a session

Arguments: $ARGUMENTS

Look back on a session and suggest what in the project's **environment**
would have made it go better: a check that would have caught a mistake, a
coding standard a reviewer needed, a pointer to a file the agent hunted
for, or a fix for wasted calls. A read-only agent finds them in a digest
of the session's transcript and writes a report. You show it to the user.

The checks are the point of the environment, so a retro only ever
tightens it. **It changes nothing.** A change that would remove or loosen
a check is listed apart, for the user to weigh on its own.

## The agents

`vibes:retrospective`.

**Check it's loaded before anything else:** it must be among the agent
types you can spawn. If it's missing, stop and tell the user the vibes
agents aren't loaded in this session. This happens when vibes is enabled
only for one checkout and the session runs in a git worktree or another
checkout; enabling it at user scope, or running from the checkout it's
enabled in, then starting a new session, fixes it. Never stand in for it
with `general-purpose` or any other agent told to read its definition: a
stand-in has none of its tool limits, and the hook that keeps it read-only
knows it only by its agent type.

## Steps

1. **Read the arguments.** A first word that's a path to a `.jsonl` file,
   or a session id such as `1b2c3d4e-…`, names the session. Anything else
   is the focus, such as `the commit gate blocks`. Without a session, look
   back on this one: `${CLAUDE_SESSION_ID}`.
2. **Make the retro's directory** from the repository root, or the current
   directory outside a repository: `.vibes/retro-<date>-<n>`, such as
   `.vibes/retro-2026-11-23-1`, with the next free number. Keep it out of
   git without touching the project's own `.gitignore`:

   ```sh
   mkdir -p .vibes/retro-<date>-<n>
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

3. **Write the digest,** as a command of its own:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/session-digest" --project "$PWD" <session> \
     > .vibes/retro-<date>-<n>/digest.md
   ```

   It finds a session id's transcript in Claude Code's projects
   directory. On exit 2, tell the user its one-line error, such as no
   transcript for the session, and stop. Read only the digest's third
   line, `Transcript: <path>`, for the brief; the agent reads the rest.
4. **Spawn `vibes:retrospective`** with a brief giving:
   - the transcript's path;
   - the digest's path;
   - the digest command, `${CLAUDE_PLUGIN_ROOT}/bin/session-digest`, with
     its path expanded;
   - the focus, or that there's none;
   - the report path, `.vibes/retro-<date>-<n>/retro.md`, as an absolute
     path.

   It replies with one line: how many suggestions, and how many would
   loosen a check.
5. **Show the user the report.** Read `retro.md`, and give:
   - **Suggestions,** in the report's order: for each, its number, what
     to add, its severity, what happened with the references, and the
     change, in a line or two.
   - **Would loosen a check,** under its own heading, apart from the
     suggestions: for each, its `L` number, the change, and what it would
     stop catching. Leave the section out when it's empty.
   - The report's path, for the full text.

   Then say that nothing has been changed, and that they can name the
   suggestions to apply.

## Applying suggestions

Only when the user names them, after the report:

- **"All" or a list of numbers** means the suggestions only, never an
  `L` item. Apply an `L` item only when the user names it on its own, and
  say first what it would stop catching.
- Make each change its own commit, so any one can be reverted. A change
  big enough to need a spec, such as a new check with tests, goes through
  `/vibes:vibe` instead.
- The commit gate asks the user to confirm any commit that removes or
  weakens a line of `scripts/check` or `scripts/check-file`, deletes
  either, or makes either not executable, so loosening the gate always
  needs their word, whoever makes the change.
