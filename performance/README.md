# Measuring and profiling performance

How `/vibes:optimise` finds where a program spends its time, and how it
decides whether a change made it faster. The profiler and the optimiser
follow it; [tools.md](tools.md) lists the tools for each guide, and
`bin/bench` does the comparisons. The vibe workflow never loads this
directory.

## The rules

1. **Measure before changing anything.** Every optimisation starts from a
   profile of a real workload, and ends with a measurement against the
   version before it. A change nobody measured isn't an optimisation.
2. **Optimise where the time goes.** A function that takes 5% of the time
   can save at most 5%, however fast it gets (Amdahl's law). Rank ideas by
   the share of time they can remove, not by how clever they are.
3. **Correctness first.** A faster program that gives a different answer is
   broken. Every candidate passes the project's tests and prints the same
   output as the version before it, before it's timed.
4. **The one who optimises never measures.** The optimiser builds a change;
   the profiler measures it; `bench verdict` decides. Nobody judges timings
   by eye.
5. **The harness stays fixed.** It lives outside the trees it measures, and
   takes the tree as an argument, so a change can't change how it's
   measured.

## The workload

The workload is what the program is measured doing. Choose it before
anything else, because every profile and every verdict depends on it.

- **Representative.** Use what the program really does: its README's
  examples, its existing benchmarks, the inputs its users have, the problem
  the user described. A focus on one area, such as "the import is slow",
  makes a workload that exercises that area.
- **Two sizes.** Measure a small input and one at least ten times larger. A
  change in complexity, such as quadratic to linear, shows as a gain that
  grows with size; a constant-factor change doesn't.
- **A holdout.** Keep one input the optimiser never sees. A change that
  speeds up the workload but not the holdout is tuned to the benchmark,
  not the program.
- **Deterministic output.** The harness prints the same output on every run
  of the same code: sort what's unordered, and leave out times, addresses
  and random values. `bench` compares it between sides.
- **Long enough.** Each sample lasts at least 100 ms, so timer resolution
  and start-up don't dominate. `bench run` repeats a short harness inside a
  sample to reach that.

### Kinds of workload

| Kind | The harness | Finding the hot spots |
| --- | --- | --- |
| Process | Runs the program, or a script calling the library, on the input | A sampling profiler on the run |
| Service | Starts the service, drives it with a load generator, stops it; prints `metric p50_ms`, `metric p99_ms` and `metric rps` | A sampling profiler attached to the service, under load |
| Build | Prepares the tree untimed (clean, or a one-file change for an incremental build), then times the build | The build's own timing: `.ninja_log`, `make --trace`, `-ftime-trace`, `cargo build --timings`, BuildKit timings |
| Boot | Boots the image headless in QEMU with a serial console; prints `metric boot_ms` and each stage's time from the serial log | Stage timestamps; `systemd-analyze` inside the guest |
| Query | Runs the query against a database loaded with realistic data | The query plan: `EXPLAIN ANALYZE` or its dialect's form |

A harness prints `metric <name> <value>` lines for anything it measures
itself, such as a boot time read from a log. `bench` records each one
beside the times it takes, and `bench verdict --measure metric.<name>`
decides on it. Mark a measure where higher is better, such as requests a
second, with `--higher-is-better`.

When a profiler can't see inside the workload, such as a kernel booting in
an emulator, say so. Adding stage timestamps is then the first change, made
like any other: in the spec first, with the user's approval.

## Measuring

`bench run` runs the harness against two trees, side a (the version before)
and side b (the change), in interleaved pairs whose order is random but
seeded. Drift, such as a laptop warming up, falls on both sides alike.

1. **An A/A run first.** Measure the baseline against itself. The half-width
   of its interval is the noise floor: how much two runs of the same code
   differ on this machine today.
2. **Compare each candidate with its parent,** the best version so far, in
   the same session. Never compare with numbers stored from another
   session, another machine or another load.
3. **The verdict:** `bench verdict` takes the median of the pairs' ratios and
   its 95% bootstrap interval. The minimum effect is twice the noise floor,
   and never under 2%.

   | Verdict | When |
   | --- | --- |
   | `BROKEN` | The project's tests failed, the harness failed, or the output differs. Decided before any timing |
   | `IMPROVED` | The whole interval is below no change, and the gain is at least the minimum effect |
   | `REGRESSED` | The whole interval is above no change, and the loss is at least the minimum effect |
   | `INCONCLUSIVE` | The interval is wider than the minimum effect, even after `bench run` added pairs up to its maximum |
   | `NO CHANGE` | Anything else |

4. **Guard rails.** A measure that mustn't grow, such as peak memory, is a
   guard: `--guard rss_kib=10` fails when it grows by more than 10%, beyond
   the noise. A failed guard is a trade-off for the user to decide.

### Keeping the noise down

On a laptop, noise comes from power management, other work and heat.

- Run on mains power, with Low Power Mode off (`pmset -g` on macOS) or the
  `performance` CPU governor on Linux. `bench` warns about both, and about
  a high load average.
- Run nothing else: no other agent, build or test run while measuring. Let
  Spotlight and Time Machine finish.
- On Apple Silicon, performance and efficiency cores run at very different
  speeds, and macOS can't pin a process to one. Interleaving and more pairs
  are the defence; an `INCONCLUSIVE` verdict says when they weren't enough.
- Build both sides the same way, in release mode with debug symbols, and
  with frame pointers where the language allows, so profiles have stacks.
- A JIT, a cache or a lazy import makes the first run slower: `bench run`
  warms up first, and a harness for a JIT runtime warms up inside too.

## Reading a profile

- **Self time** is spent in a function itself; **inclusive time** includes
  what it calls. A hot spot has high self time, or high inclusive time with
  a callee that shouldn't be there.
- **Look for the shape, not the leaf.** A library function at the top of
  the profile, such as `memcpy` or a hash lookup, is usually called too
  often by your code: find the caller.
- **Time off the CPU** (waiting on I/O, locks or the network) doesn't show
  in a CPU profile. When the wall time is much more than the CPU time, use
  an off-CPU, I/O or lock profile.
- **Memory** shows as time in the allocator and the garbage collector, and
  as peak RSS. A memory profile says which code allocates it.
- **Every profile records how it was taken:** the workload, the commands,
  the tool and its version, and the environment. A profile nobody can
  repeat can't be checked.

## Where the gains usually are

From the largest typical payoff to the smallest:

1. **Algorithms and data structures:** quadratic work made linear, a scan
   made a lookup, work done once instead of per item.
2. **I/O:** batched queries instead of one per item (N+1), buffered reads
   and writes, fewer round trips, streaming instead of loading everything.
3. **Allocation and copying:** reused buffers, preallocated capacity, views
   instead of copies, fewer temporary objects.
4. **Caching:** a result that's computed again with the same inputs. Every
   cache needs a size limit and a rule for when it's stale, in the spec.
5. **Parallelism:** independent work spread across cores, after the serial
   work is as small as it gets.
6. **Micro-optimisation:** the inner loop's instructions. Only on a hot spot
   the profile proves, and only when everything above is done.

Clarity counts too: a change that saves 2% and makes the code much harder to
read is rarely worth it. The reviewers weigh that, with the measured gain in
front of them.

## Tools

Use what's installed, or built into the language, first. Sample before you
instrument: a sampling profiler barely slows the program, so its picture is
closer to the truth. Never use `sudo`. In an attended run, ask the user
before installing a tool, saying what it would show that the installed
ones don't. In an unattended run, use only what's installed, and report
what a missing tool would have shown.

[tools.md](tools.md) lists the profilers and benchmark harnesses for each
guide, and the system-level tools for native code, builds, boot and
services.
