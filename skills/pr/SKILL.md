---
name: pr
description: >-
  Writes the body of a pull request for the current branch: the smallest
  view that makes the change clear, the evidence before and after, and the
  merge risk, taken from the records a vibes run kept, or from the branch
  itself. Shows it, and opens or updates the pull request only when you
  say so.
argument-hint: "[base branch] [#issue]"
disable-model-invocation: true
---

# PR: write the pull request for this branch

Arguments: $ARGUMENTS

Write the body of a pull request for the checked-out branch, for a
reviewer who hasn't seen the work: what changed, the proof it works, and
the risk of merging it. A read-only agent writes it from the records: the
run's, when a vibes run built the branch, and the branch's commits, diff
and a fresh run of its checks. Every claim comes from a record, and what
no record shows is said to be unverified.

**Nothing leaves the machine until the user says so.** Pushing the branch
and opening the pull request are theirs to choose, after they've read the
body.

## The agents

`vibes:pr-writer`.

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

1. **Find the branches.** The branch is the checked-out one,
   `git branch --show-current`. The base is, in order: the argument; the
   base branch in the run's state file (step 2); the remote's default,
   from `git rev-parse --abbrev-ref origin/HEAD` without its `origin/`;
   or `main` or `master`, whichever exists. Stop if the branch is the
   base, detached, or has no commits the base lacks
   (`git log --oneline <base>..HEAD` is empty). If the working tree has
   uncommitted changes, tell the user they won't be in the pull request,
   and carry on.
2. **Find the run,** if a vibes run built the branch: `vibe/<name>` is
   `.vibes/<name>/` with `state.md`, `optimise/<slug>` is
   `.vibes/optimise-<slug>/` with `optimise-state.md`, and `debug/<slug>`
   is `.vibes/debug-<slug>/` with `debug-state.md`. Any other branch, or a
   run directory that's gone, has no run. A run whose state isn't
   `status: done` hasn't finished: tell the user, and ask whether to write
   the body anyway. The issue the pull request closes is the one the
   arguments name, such as `#123`, or else the run's `issue:` line, if
   either.
3. **Make the pull request's directory** from the repository root,
   `.vibes/pr-<slug>`, the branch name with each `/` made `-`, such as
   `.vibes/pr-vibe-sales-csv`. If it exists from an earlier run, empty
   it. Keep it out of git:

   ```sh
   mkdir -p .vibes/pr-<slug>
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

4. **Gather the branch,** each as a command of its own:

   ```sh
   git log --reverse --format='%h %s%n%n%b' <base>..HEAD > .vibes/pr-<slug>/commits.txt
   git diff --stat <base>...HEAD > .vibes/pr-<slug>/diff-stat.txt
   git diff <base>...HEAD > .vibes/pr-<slug>/diff.patch
   "${CLAUDE_PLUGIN_ROOT}/bin/hotspots" > .vibes/pr-<slug>/hotspots.txt
   ```

   If `hotspots` exits 2, there's no history to rank: delete the file.
5. **Run the checks at the branch's head,** if the project has
   `scripts/check`, in a worktree, so uncommitted changes don't count. It
   runs the slow tests, so it can take a while: run it in the background,
   and carry on when it's done.

   ```sh
   git worktree add --detach .vibes/pr-<slug>/wt HEAD
   cd .vibes/pr-<slug>/wt && scripts/check --all > ../check.txt 2>&1; echo "exit $? at $(git rev-parse --short HEAD)" >> ../check.txt
   ```

   Then remove the worktree with
   `git worktree remove --force .vibes/pr-<slug>/wt`.
6. **Find the repository's template,** if it has one:
   `.github/pull_request_template.md`, `.github/PULL_REQUEST_TEMPLATE.md`,
   `docs/pull_request_template.md` or `pull_request_template.md`, in any
   case.
7. **Spawn `vibes:pr-writer`,** with the branch, the base, the pull
   request's directory, the run directory and its kind, or that there's
   none, the issue it closes or that there's none, the template's path or
   that there's none, and the paths of
   `pr.md` and `sources.md` in the directory, all as absolute paths.
8. **Show the body.** Print `pr.md` in full. Then say, in a line each:
   the merge risk; anything the body says isn't verified; and that
   `sources.md` lists where each claim came from. If `check.txt` shows a
   failure, say so first: a pull request whose checks fail is rarely ready
   to open.
9. **Ask what to do,** in one question, recommending one answer:
   - **Open it as a draft pull request.** Recommended, so the user can look
     it over where it'll live before asking for reviews.
   - **Open it ready for review.**
   - **Change the body first:** take their changes, edit `pr.md` yourself,
     show it again and ask again.
   - **Leave it:** stop, and give the path of `pr.md`.

   Say plainly that opening it pushes the branch to the remote. When a
   pull request for the branch already exists
   (`gh pr view <branch> --json url` succeeds), offer to replace its body
   instead of opening one.

## Opening the pull request

Only with the user's answer from step 9, which covers the push and the
pull request for this branch, this once:

1. **Check the tools:** `gh` is installed and `gh auth status` succeeds,
   and the repository has a remote. If either fails, stop and give the
   user the commands to run themselves, from step 3 below.
2. **Split the title from the body:** the title is `pr.md`'s first line
   without its `# `, and the body is the rest:

   ```sh
   tail -n +3 .vibes/pr-<slug>/pr.md > .vibes/pr-<slug>/body.md
   ```

3. **Push the branch and open it:**

   ```sh
   git push -u origin <branch>
   gh pr create --base <base> --head <branch> --title "<title>" --body-file .vibes/pr-<slug>/body.md --draft
   ```

   Leave out `--draft` for a pull request ready for review. To replace an
   existing pull request's body, run
   `gh pr edit <branch> --title "<title>" --body-file .vibes/pr-<slug>/body.md`
   after the push instead.
4. **Never force a push.** If the push is refused, because the remote
   branch has commits this one lacks, stop and tell the user: settling it
   is theirs.
5. **Give the user the pull request's address.**

Keep the pull request's directory: it records what the body was built
from.
