---
name: capacity
description: >-
  Measures how many vibes builders this machine can run at once for this
  project: runs the project's gate once alone and twice at the same time,
  in worker worktrees, sampling memory and CPU, Docker's included, and
  caches the answer in .vibes/capacity.json for later runs. Run it again
  when the project has grown, or the machine or Docker's resources have
  changed; runs re-measure by themselves when the cache goes stale.
disable-model-invocation: true
---

# Capacity: how many builders this machine can run

**Outside Claude Code,** a path here may still begin with the
`CLAUDE_PLUGIN_ROOT` variable. It stands for vibes' own folder, the one
holding the `skills/` folder this file is in: use that folder in its place.
Start the brief of each vibes agent you spawn with `Vibes root:` and that
folder, and spawn each with a fresh context, not a copy of this
conversation. An agent named here as `vibes:<agent>` may be listed as
`<agent>` or `vibes-<agent>`.

Work out how many builders a vibes run can have building at once, here,
for this project, and cache it. A builder's cost is roughly one run of the
project's gate, `scripts/check`, which it runs on every commit, so measure
that: once alone, for the memory and CPU it needs, then twice at the same
time, to see whether two really finish sooner than one after the other.
A machine that's already saturated, by its disk, by Docker, or by the
build itself, shows it there, whatever its numbers say.

The cache, `.vibes/capacity.json`, holds only numbers about the machine
and the project. `"${CLAUDE_PLUGIN_ROOT}/bin/capacity" check` reads it,
and says to measure again when the machine, the project's gate or its
size has changed, or after 30 days.

## Steps

1. **Check there's a gate:** the project has an executable
   `scripts/check`. Without one there's nothing to measure: say a run
   builds one batch at a time until the gate is set up, and stop.
2. **Check the working tree is clean,** and tell the user what's coming:
   the gate runs four times, once to warm the worktrees, once alone and
   twice together, so it takes about four times as long as one
   `scripts/check`.
3. **Prepare the worker worktrees,** from the repository root, at the
   current commit, reusing them when they exist, so caches such as
   per-checkout build outputs stay warm for the runs that use them later:

   ```sh
   mkdir -p .vibes
   [ -f .vibes/.gitignore ] || printf '*\n' > .vibes/.gitignore
   ```

   Then for each of `.vibes/workers/1` and `.vibes/workers/2`: if it's a
   worktree already, check it has no uncommitted changes (stop and ask if
   it has), then `git -C <worktree> switch --detach <commit>`, where the
   commit is the main checkout's `git rev-parse HEAD`; otherwise
   `git worktree add --detach <worktree> HEAD`.
4. **Warm both worktrees,** each as a command of its own, so the
   measurements aren't of a cold first build:

   ```sh
   cd .vibes/workers/1 && scripts/check
   cd .vibes/workers/2 && scripts/check
   ```

   A failure is fine here: the gate's cost is what's measured, not its
   verdict.
5. **Measure one, then two at once,** from the repository root:

   ```sh
   "${CLAUDE_PLUGIN_ROOT}/bin/capacity" measure --cache .vibes/capacity.json --as single --tree .vibes/workers/1 -- scripts/check
   "${CLAUDE_PLUGIN_ROOT}/bin/capacity" measure --cache .vibes/capacity.json --as pair --tree .vibes/workers/1 --tree .vibes/workers/2 -- scripts/check
   ```

6. **Decide:**
   `"${CLAUDE_PLUGIN_ROOT}/bin/capacity" decide --cache .vibes/capacity.json`.
7. **Report:** the number of builders, each limit it gives with its
   reason, and the measurements: one gate run's wall time and peak memory,
   Docker's too, and how much faster two at once were than one after the
   other. When a cache existed before, say what changed. Leave the worker
   worktrees in place: runs reuse them.
