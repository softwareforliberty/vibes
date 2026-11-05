---
name: atomic-commits
description: >-
  Splits work into small, self-contained git commits with clear messages, each
  of which builds and passes the tests. Use whenever creating commits, staging
  changes, or cleaning up local history before pushing.
---

# Atomic Commits

An atomic commit holds **one logical change, complete and nothing else**. It
builds, passes the tests, and can be reviewed, reverted or cherry-picked on its
own. Atomic history makes review easier, makes `git bisect` find the exact
change that broke something, and makes reverting a bad change safe.

## When to use this skill

- Every time you commit.
- Before pushing, when tidying commits that only exist locally.

## What makes a commit atomic

- **One logical change.** You can describe it in one sentence without "and".
  "Add order export" is one change; "Add order export and fix login typo" is
  two commits.
- **Complete.** It includes everything the change needs: the code, its tests,
  docs, config and migrations. Nothing is left half-done for a later commit.
- **Green.** The project builds and the tests pass at that commit, not just at
  the end of the branch. A broken commit breaks `git bisect` for everyone.
- **Nothing extra.** No unrelated formatting, debug output, commented-out code
  or stray files.

## Splitting work into commits

Keep these apart, each in its own commit:

- **Refactoring and behaviour changes.** First restructure with behaviour
  unchanged, then change behaviour. Reviewers can check the refactor for "no
  change" and the behaviour change in isolation.
- **Formatting and logic.** Run formatters in a commit of their own, so the
  logic change isn't buried in whitespace.
- **Moves and renames, and edits.** Move or rename a file in one commit with
  `git mv`, then edit it in the next, so git can follow its history.
- **Dependency changes.** Add or upgrade a dependency, with its lockfile, in
  its own commit.
- **Generated files** go in the same commit as the change that generated them,
  never on their own and never mixed with unrelated changes.

When following [test-driven development](../test-driven-development/SKILL.md),
commit at each green step. A behaviour commit holds the test together with the
code that makes it pass, and a refactor gets its own commit.

## Workflow

1. **Review what changed.**

   ```sh
   git status
   git diff
   ```

   Group the changes into logical commits before staging anything.

2. **Stage one change at a time.** Stage by file, or by hunk when a file holds
   more than one change. Never stage blindly with `git add -A` or
   `git commit -a`.

   ```sh
   git add path/to/file
   git add -p path/to/file
   ```

3. **Review what's staged.** This is exactly what the commit will contain.

   ```sh
   git diff --staged
   ```

4. **Hide everything you're not committing,** so the working tree holds
   exactly the staged change:

   ```sh
   git stash push --keep-index --include-untracked
   ```

   Skip this when there's nothing unstaged or untracked.

5. **Check that the staged change is green on its own.** Run the project's
   tests and linters. If the project has a commit gate (see the
   [commit gate](../commit-gate/SKILL.md) skill), it runs them for you when
   you commit, and it refuses to commit while anything is unstaged or
   untracked.

6. **Commit with a clear message** (see below), then bring the rest back:

   ```sh
   git stash pop
   ```

   If the checks or a formatter changed files, the pop can conflict. Resolve
   the conflict, and stage any formatter changes deliberately in a later
   commit.

7. **Repeat** until the working tree is clean or holds only unfinished work.

## Commit messages

```text
Add CSV export for orders

Finance needs order data in their spreadsheet tool. Export uses the same
filters as the order list, so users get exactly what they see on screen.

Closes #142
```

- **Subject line:** what the commit does, in the imperative mood, as if
  finishing "This commit will…": "Add CSV export", not "Added" or "Adds".
  Capitalise it, keep it to 50 characters where you can and 72 at most, and
  don't end it with a full stop.
- **Blank line** between the subject and the body.
- **Body:** explain **why** the change was made and anything a reviewer
  wouldn't see from the diff: context, trade-offs, side effects. The diff
  already shows what changed. Wrap at 72 characters. Leave the body out when
  the subject says it all.
- **Trailers** go at the end: issue references (`Closes #142`) and
  `Co-authored-by:` lines.
- If the project uses a convention such as Conventional Commits
  (`feat: add CSV export`), follow it instead.

## Fixing commits before you push

Rewrite only commits that haven't been pushed. Once others have them, add new
commits instead.

- **Change the last commit:** stage the fix, then amend it.

  ```sh
  git commit --amend --no-edit
  ```

- **Fix an older commit:** commit the fix as a fixup, then squash it into its
  target with a rebase. Setting `GIT_SEQUENCE_EDITOR` to `:` accepts the
  rebase plan without opening an editor.

  ```sh
  git commit --fixup=<commit>
  GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash <commit>~1
  ```

- **Split the last commit:** undo it but keep its changes, then commit them
  again in parts.

  ```sh
  git reset HEAD~1
  git add -p
  ```

## Never commit

- **Secrets:** keys, passwords, tokens and `.env` files. Scan with gitleaks
  (see any language's `tools.md` in [`lang/`](../../lang/)). If a secret is
  committed, rotate it: removing it from history doesn't make it safe again.
- **Build output and dependencies:** compiled files, `node_modules/` and
  similar. Ignore them in `.gitignore`.
- **Editor and OS files:** `.DS_Store`, swap files and IDE workspace state.
  Ignore them in your global gitignore.
- **Failing builds or tests,** unless the project has an explicit
  work-in-progress convention.

## Checklist

Before each commit:

- [ ] The staged diff holds one logical change, and nothing unrelated.
- [ ] The project builds and the tests and linters pass with only the staged
      changes.
- [ ] Tests, docs and config for the change are included.
- [ ] The message has an imperative subject of 72 characters or fewer, and the
      body explains why.
- [ ] No secrets, build output or editor files are staged.
