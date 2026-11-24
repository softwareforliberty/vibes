# Build batches in parallel

How a `/vibes:vibe` run builds batches that don't need each other at the
same time, each by its own builder in its own worktree, once
[Phase 6](SKILL.md#phase-6-rebuild-test-first) finds a plan whose
`plan-graph` prints `WIDTH:` 2 or more. Everything else in Phase 6 holds:
each batch is built test-first through the gate, checked when it's done,
and reviewed with the rest in Phase 7.

The rebuild branch, `vibe/<name>`, stays checked out in the main checkout,
and collects the batches as they finish, one at a time, so it ends with
every commit in a line, as a run that built one batch at a time would.

## Before the first batch

1. **Check the graph:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/plan-graph" .vibes/<name>/rebuild-plan.md`.
   If it lists problems, give them to `vibes:designer` in `plan` mode to
   fix: making one batch wait for another, or moving a change both make
   into a batch both wait for. Done when it lists none.
2. **Find how many builders this machine can run:**

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/capacity" check --cache .vibes/capacity.json
   ```

   - `BUILDERS <n>`, perhaps with fewer `now`, because memory is in use:
     the limit is the smaller of that and the graph's width.
   - `MEASURE: <why>`: build one batch at a time until two are ready at
     once. Then, with nothing else building, measure as
     `${CLAUDE_PLUGIN_ROOT}/skills/capacity/SKILL.md` says from its step
     3, and check again. In an attended run, tell the user first that it
     takes about four runs of the gate, and why.

   With a limit of 1, build one batch at a time, as Phase 6 says, and
   stop reading here.
3. **Record it** in `state.md`: the limit, and for each batch, once it
   starts, its worktree and its branch.

## Building

1. **Find what's ready:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/plan-graph" .vibes/<name>/rebuild-plan.md --done <batches joined> --running <batches building>`
   prints `READY:`, in plan order.
2. **Start each ready batch, up to the limit.** For each, take a free
   worker worktree, `.vibes/workers/<k>` for `k` from 1 to the limit:
   create it with `git worktree add --detach .vibes/workers/<k>` when it
   doesn't exist, and check one that does has no uncommitted changes,
   stopping to ask if it has. Then put the batch's branch in it, from the
   rebuild branch's tip:

   ```sh
   git -C .vibes/workers/<k> switch -c vibe/<name>--<batch> vibe/<name>
   ```

   Spawn a fresh `vibes:builder` for each, all in one message, with the
   brief Phase 6 gives, its worktree and its branch, and the notes from
   every batch joined so far that bear on it, such as a decision or a
   problem a builder reported.
3. **When a builder finishes, check its batch** as Phase 6's step 3 says,
   in its worktree.
4. **Join it,** one batch at a time, in the order they finish:
   1. **Bring it up to date** with the rebuild branch:
      `git -C .vibes/workers/<k> rebase vibe/<name>`. On a conflict, run
      `git -C .vibes/workers/<k> rebase --abort`, and give a fresh builder
      in `fix` mode, in that worktree, the conflicting files and the task
      of bringing the branch up to date without losing either batch's
      work.
   2. **Check the result** if the rebase moved anything, because the
      rebuild branch had changed since the batch started: run
      `cd .vibes/workers/<k> && scripts/check --all`. If it fails, give
      the failure to a builder in `fix` mode in that worktree, and check
      again. The rebased commits each passed the gate where they were
      made; this check covers them where they now sit.
   3. **Move the rebuild branch on,** in the main checkout:

      ```sh
      git merge --ff-only vibe/<name>--<batch>
      git -C .vibes/workers/<k> switch --detach
      git branch -d vibe/<name>--<batch>
      ```

   4. **Record it** in `state.md`, and check the guides on the joined
      changes, as [Keep the guides current](SKILL.md#keep-the-guides-current)
      says.
5. **Start what's now ready,** from step 1. A batch waiting on a decision
   for the user holds back only itself and the batches after it; the rest
   carry on. Done when every batch is joined.

## When the machine can't keep up

A builder that reports its gate was killed for want of memory, such as
exit status 137, or a gate run far slower than the measured one, means
the limit is too high. Lower it for this run and later ones:

```sh
"${CLAUDE_PLUGIN_ROOT}/bin/capacity" lower --cache .vibes/capacity.json --to <one fewer> --reason "<what happened>"
```

Let the running builders finish, start no more than the new limit, and
give the stopped batch to a fresh builder once there's room.

## After the build

Leave the worker worktrees in place, detached: the next run reuses them,
with whatever they've built warm. A resumed run finds each batch's
worktree and branch in `state.md`; uncommitted changes in a worktree are
an unfinished step of that batch, to finish as
[resume.md](resume.md) says for the rebuild branch.
