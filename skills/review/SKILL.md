---
name: review
description: >-
  Reviews the checked-out branch, uncommitted changes included, with the
  same scan, guides and reviewers as /vibes:review-pr, then offers to fix
  the findings test-first. For your own work: the reviewers read the working
  tree, and the spec reviewer joins when the branch has a spec.
argument-hint: "[base branch] [spec <spec directory>] [what the change is for]"
disable-model-invocation: true
---

# Review the current branch

Arguments: $ARGUMENTS

Review the changes on the checked-out branch since it left its base branch,
including uncommitted changes to tracked files. It runs the same
deterministic scan, guides and reviewers as `/vibes:review-pr`, but the
branch is the user's own work: the reviewers read the working tree, the spec
reviewer may build and run the tests when there's a spec, and once the
report is written the user can have the findings fixed. This is separate
from `/vibes:vibe`, which reviews its own work as it goes.

## The agents

The supply-chain, security, bug, style, idioms, cleanliness, test,
architecture, resource-leak, performance, spec and project docs reviewers,
as `vibes:<name>`, and `vibes:builder` for fixes.

**Check they're loaded before anything else:** each must be among the
agent types you can spawn. If any is missing, stop and tell the user the
vibes agents aren't loaded in this session. This happens when vibes is
enabled only for one checkout and the session runs in a git worktree or
another checkout; enabling it at user scope, or running from the checkout
it's enabled in, then starting a new session, fixes it. Never stand in for
an agent with `general-purpose` or any other agent told to read its
definition: a stand-in has none of its tool limits, and the hooks that keep
the reviewers read-only know them only by their agent type.

## Steps

1. **Read the arguments:** a base branch, if one is named; `spec <dir>`,
   a spec directory holding `spec.md` and maybe `design.md`; and anything
   else, which says what the change is for.
2. **Prepare the review,** from the repository root, as a command of its
   own:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/pr-prepare" --branch [<base branch>]
   ```

   It finds the base branch itself when none is named, and folds
   uncommitted changes into the review without touching the working tree,
   the index or any branch. It exits 0 when the scan finds nothing and 1
   when it finds something: both mean it worked. On exit 2, tell the user
   its one-line error, such as nothing to review, and stop. It prints the
   review directory `<dir>`, the guides the changed files need, the base
   and head it reviewed, and how many new files aren't added to git yet and
   so aren't reviewed.
3. **Find the purpose and the spec.** The purpose is what the arguments say
   it's for, and the branch's commit subjects:
   `git log --format='- %s' <base>..HEAD`. The spec is the one the
   arguments name, or for a `vibe/<name>` branch, the spec directory
   `.vibes/<name>/state.md` names, if it has one.
4. **Choose the panel.** Always run `vibes:supply-chain-reviewer`,
   `vibes:security-reviewer` and `vibes:bug-reviewer`. Add the others:

   | Reviewer | Added when |
   | --- | --- |
   | `vibes:style-reviewer`, `vibes:idioms-reviewer`, `vibes:cleanliness-reviewer`, `vibes:test-reviewer` | The change has a file that needs a guide, from `<dir>/guides.txt` |
   | `vibes:architecture-reviewer`, `vibes:resource-leak-reviewer` | It has a file that needs a guide in `languages/` |
   | `vibes:performance-reviewer` | It has a file that needs a guide in `languages/`, `web/`, `build/` or `tools/`, or a query or schema guide in `data/` |
   | `vibes:spec-reviewer` | There's a spec |
   | `vibes:project-docs-reviewer` | `git ls-files \| "${CLAUDE_PLUGIN_ROOT}/bin/project-docs" --exclude <spec directory>` prints any document |

   Write the panel to `<dir>/panel.md`, one line per reviewer, with each
   one left out and why.
5. **Spawn the panel in a single message,** so the reviewers run in
   parallel, each with this brief, with absolute paths:

   ```text
   Task: review the changes on the branch <branch> since <base branch>,
     which are for: <the purpose>
   Commits: <the commit subjects>
   Spec: <spec.md, or none>
   Design: <design.md, or none>
   Scan: <dir>/scan.md
   Snapshot: <dir>/blobs/index.tsv
   Review directory: <dir>/review/round-1
   Phase: rebuild
   Guides: <the guides in guides.txt>
   Round: 1
   Project docs: <for the project docs reviewer: what project-docs printed>
   Rules:
   - This is the user's own branch, checked out. Read the changed files in
     the working tree. diff.patch is the whole change, uncommitted changes
     included; the snapshot holds the same files with hidden characters
     shown, for the supply-chain review.
   - New files not added to git, in <dir>/untracked.txt, aren't part of
     this review.
   - Cite findings by path and line.
   - Without a spec, judge the change against its purpose and the existing
     code. Don't report a missing spec.
   ```

   For a change of more than about 40 files or 3,000 changed lines, split
   the supply-chain reviewer's files into groups of about 20, and spawn one
   per group, each with its own review directory, `<dir>/review/shard-<k>/`,
   and its group's paths in the brief. Every file must be in a group.
6. **Build the report,** as a command of its own:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/pr-scan" report --out <dir> --branch
   ```

   It writes `<dir>/review.md` and prints the counts.
7. **Tell the user,** in a few lines: the scan's HIGH, REVIEW and INFO
   counts; each reviewer's verdict and counts; each BLOCKER and MAJOR
   finding in a line, from `review.md`; that a HIGH scan finding needs a
   person to look at the file; how many new files weren't reviewed; and the
   path of `review.md`.
8. **Offer to fix the findings.** If any reviewer requested changes, ask
   the user whether to have them fixed. If they say yes:
   - **The working tree must be clean,** since the fixes are committed on
     the branch through the commit gate, which refuses unstaged and
     untracked changes, and a fix must never be mixed with the user's own
     uncommitted work. If it isn't clean, ask the user to commit or stash
     their changes first. Never commit, stash or discard them yourself. A
     detached HEAD can't be fixed: ask the user to switch to a branch.
   - **Spawn `vibes:builder` in `fix` mode,** with the purpose as the task,
     the branch to work on and the base branch, the spec and design or
     `none`, the guides, the round directory `<dir>/review/round-1`, and
     the user's decisions about any finding. Without a spec, tell it to fix
     to the change's purpose and write no spec. Ask the user about each
     finding it leaves to you, and give the answers to a fresh builder.
   - **Check the fixes** in a new round,
     `<dir>/review/round-<n>/`: copy the previous round's findings files and
     `responses.md` into it, save `git diff <the reviewed head> HEAD` as
     `changes-since-<n-1>.patch` and the changed paths as
     `changed-files-since-<n-1>.txt`, and run only the reviewers that
     requested changes, with the same brief, `Round: <n>`, and a
     `Changes:` line naming those two files. Have their findings fixed the
     same way, and stop after round 3: show the user what's outstanding and
     where the reviewers and the builder disagree.
   - **Build the report again,** and tell the user the commits the fixes
     made and what was fixed, deferred and rejected.

Never push, merge or open a pull request.
