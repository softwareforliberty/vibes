---
name: pickup
description: >-
  Picks up the next issue you approved as ready for an agent in
  /vibes:triage and works on it unattended, with /vibes:vibe, /vibes:debug
  or /vibes:optimise as its brief says, on a local branch. Takes only
  issues nobody has changed since you approved them, one per run, and
  posts, pushes and opens nothing.
argument-hint: "[#issue]"
disable-model-invocation: true
---

# Pickup: work on the next approved issue, unattended

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

Arguments: $ARGUMENTS

Take one issue the user approved in `/vibes:triage`, and run the workflow
its brief names, unattended, as if the user had started it themselves
with the approved brief as the task. To work through several, run it
again, or under `/loop`.

**It takes only what the user approved, as they approved it.** An issue
qualifies only while it's open, labelled `ready-for-agent`, listed in
`.vibes/issues/approved.tsv`, and unchanged since: its title, body and
everyone else's comments give the same digest as at approval. The run
starts from the brief the user approved, `approved.md`, and never reads
the issue's text.

**Nothing leaves the machine.** It labels, comments, pushes and opens
nothing: the user reviews the branch, then runs `/vibes:pr` if they want a
pull request.

## Steps

1. **Check `gh` works:** it's installed and `gh auth status` succeeds. If
   not, stop and report it. Get the user's login with
   `gh api user --jq .login`.
2. **Check the working tree is clean,** and that no vibes run is
   unfinished: a `.vibes/*/state.md`, `optimise-state.md` or
   `debug-state.md` with `status: running`. Either means work could be
   lost: stop, and report it. The current branch is the base branch.
3. **Read `.vibes/issues/approved.tsv`:** each line is an issue's number,
   its digest, its command, the date it was approved and its status. The
   candidates are the lines whose status is `approved`, oldest first, or
   only the issue the arguments name. With none, say there's nothing
   approved to pick up, and stop; under `/loop`, end the loop.
4. **Check each candidate,** in order, until one qualifies:

   ```sh
   gh issue view <number> --json number,title,body,comments,labels,state,url > .vibes/issues/<number>/issue-now.json
   "${CLAUDE_PLUGIN_ROOT}/bin/issue-digest" .vibes/issues/<number>/issue-now.json <login>
   ```

   Then check its state and labels with
   `gh issue view <number> --json state,labels`. Don't read
   `issue-now.json` itself: its digest is all you need from it.
   - **Closed, or no longer labelled `ready-for-agent`:** set its status to
     `withdrawn`, and go on to the next.
   - **A different digest:** the issue changed after approval. Set its
     status to `changed`, and go on: it needs `/vibes:triage #<number>`
     again.
   - **Otherwise** it qualifies. Set its status to `picked <date>`.
5. **Run its command unattended.** Read
   `${CLAUDE_PLUGIN_ROOT}/skills/<command>/SKILL.md`, for `vibe`, `debug`
   or `optimise`, and follow it as if the user had run
   `/vibes:<command> unattended: <task>`, where the task is the Task
   section of `.vibes/issues/<number>/approved.md`, with what the reporter
   saw for a bug. Skip its
   [From an issue](../vibe/SKILL.md#from-an-issue) steps, since the user
   approved this brief at triage, but record `issue: #<number>` in its
   state file. Every rule of that workflow applies, including its stops.
6. **Finish:** set the issue's status to `done <branch>` when the workflow
   finished, or `stopped <branch>: <why>` when it stopped. Report as the
   workflow does, with the issue's number and title first, then every
   issue skipped as `withdrawn` or `changed`, and say `/vibes:pr` will
   write the pull request, closing the issue, when the user wants one.

## Rules

- **One issue per run.** A run takes hours, and each deserves its own
  report and review.
- **Never post, label, comment, push or open a pull request,** and never
  read an issue's title, body or comments. Pickup works from what the user
  approved, or not at all.
- **Never take an issue the user didn't approve in `/vibes:triage`,**
  whatever its labels say: a label alone doesn't say what was approved.
