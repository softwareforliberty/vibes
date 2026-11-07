# A worked example: dupfind

This page follows one real run of `/vibes:vibe`, from the task to the
middle of the rebuild, so you can see what each phase does and what it
leaves behind. Every excerpt below is copied from the run's files or its
git history, trimmed with `...` where it's long, and with long lines
wrapped.

The task was a new command-line tool, given as a large, unattended run:

> /vibes:vibe unattended: large: Build dupfind, a Python command-line tool
> that finds duplicate files under one or more directories by content. It
> groups files whose contents are identical, prints each group, and can
> write the groups as JSON for scripts. It must handle large files and
> large trees without reading whole files into memory, skip what it can't
> read with a warning, and never follow symlinks out of the given
> directories unless asked.

The prompt went on with rules confining installs to a project virtualenv.

Nobody answered a question during the run. The main agent made every
choice an attended run would have asked about, and recorded each one.
The run stopped once at the spike review's round limit, which is what
vibes did then, and was resumed with an updated vibes. We then stopped it
on purpose after the fourth of nine rebuild batches: the rest of the
rebuild repeats the same pattern, and the rebuild review wasn't run.

The run left three branches and a state directory:

- `main`: the project's first commit and the commit gate.
- `vibe/dupfind`: the spec, the design, then the rebuild.
- `spike/dupfind`: the spike, after five review rounds. It's never merged.
- `.vibes/dupfind/`: the run's own files, kept out of git.

## Phase 0: the commit gate

The main agent named the task `dupfind`, took the size the user gave
(large), and found the guides it needs: Python, BASH and TOML. The
project had no `scripts/check`, so it set one up from those guides'
`tools.md` files and committed it on `main`, before any branch:

```text
fcc85ee Add the commit gate
454d99d Start the project
```

The `# Guides:` line in `scripts/check` names the guides the gate checks.
The commit gate blocks any commit with a file whose guide isn't listed:

```bash
# Guides: languages/BASH languages/Python data/TOML
```

The task's environment rules allowed installs only into the project's
`.venv`, so six tools that pip can't install, such as gitleaks and
OSV-Scanner, were left out of the gate. The git pre-commit hook couldn't
be installed either, so only the plugin's Claude Code hook gated commits.
`.vibes/dupfind/state.md` records both for the final report.

## Phase 1: the spec

The main agent created `vibe/dupfind` and spawned the designer in `spec`
mode. Its spec, in `docs/specs/dupfind/spec.md`, had 50 requirements (R1
to R50) and 11 quality requirements (Q1 to Q11), each with an acceptance
check. A requirement reads like this:

```markdown
- **R12:** Without `--follow-symlinks`, dupfind follows no symlink inside a
  directory argument, whether it points to a file or a directory, inside or
  outside the directory arguments, or nowhere. Such a symlink isn't
  reported and produces no warning. Acceptance: in `d`, a symlink to a
  file with the same contents as `d/a`, a symlink to a directory holding
  duplicates, and a broken symlink together give no group and no warning,
  and the exit status is 0.
```

In an attended run, the spec's open questions go to you. Here the main
agent decided each one itself, taking the option that does the least you
didn't ask for, and wrote it into the spec's assumptions with the options
it didn't choose. The first approved spec had 20 such decisions:

```markdown
- **Unattended decision:** without `--follow-symlinks`, no symlink found
  while scanning is followed, not even one that points inside the
  directory arguments (R12). With it, every symlink is followed,
  including those pointing outside (R14). Not chosen: following symlinks
  whose targets resolve inside a directory argument by default, and
  skipping only those that leave. "Never follow symlinks out of the given
  directories unless asked" holds either way. Following none is simpler,
  and can be relaxed later.
```

The spec reviewer took three rounds to approve it. Round 1 had 15
findings: one blocker, eight major and six minor. The blocker, from
`.vibes/dupfind/review/spec-1/findings-spec-reviewer.md`:

```text
- [BLOCKER] spec.md:155-165: R17 (first path in path order) contradicts R16
  (each directory scanned once); with --follow-symlinks loops there's no
  first path. Fix: R17 chooses among visited paths; define which path a
  directory is scanned under, independent of OS listing order.
```

The main agent accepted every finding, edited the spec, and recorded what
it did with each in the round's `responses.md`. Round 2 found one more
blocker, a conflict between escaping output and writing file names
unchanged, and round 3 approved. The spec went in as one commit,
`21bdf5f Add the dupfind spec`, 725 lines long.

## Phase 2: the design

The designer wrote `design.md` to the spec: the kind of software, the
approach, each component's job, interface and dependencies, the flows,
errors, testing, and the boundary rules the gate will enforce. It took the
layers of the command-line tools architecture guide (entry point,
settings, command, core, output), and wrote each boundary rule so a tool
can check it. Two of the 13:

```markdown
1. **Layers of the tool:** `type = "layers"` with
   `layers = ["dupfind.__main__", "dupfind.cli", "dupfind.command",
   "dupfind.output | dupfind.osfs | dupfind.settings", "dupfind.core"]`.
   - A layer never imports a layer above it.
...
7. No module calls `print` or `input`.
```

Writing the design showed that the spec didn't say what happens when
standard error can't be written. That went back into the spec first, as
R51, and the spec reviewer checked the change in two more spec rounds
(`spec-4` and `spec-5`). The architecture reviewer's first round had four
major findings, such as skip counts kept in the output layer rather than
the core. It approved in round 2, with two minor findings that were fixed
and confirmed in round 3.

The design and the R51 change went in together as
`cf208a6 Add the dupfind design`.

## Phase 3: the spike

The main agent created `spike/dupfind` from `vibe/dupfind` and spawned
the spiker, which built the whole tool quickly to the spec and design. Its
report, in `.vibes/dupfind/spike-report.md`, starts:

```text
Commits on spike/dupfind: ba9a118 Build the dupfind spike, dc3aecd Check the
import-linter contracts in the gate, ab41964 Document dupfind in the README.
scripts/check passes: 333 tests, 4 skipped on macOS, coverage 97%.
```

It also measured the quality requirements against real files, such as
"Q2: 100k files / 25k groups ~17 s warm, 67 MiB". It found one thing the
spec couldn't meet as written: macOS's filesystem refuses file names that
aren't valid UTF-8, which three requirements' tests needed. The spiker
changed Q11 and recorded the change as another unattended decision.

The session running the workflow ended while the spiker was still
working. `/vibes:vibe` with no task picked the run up from `state.md`, and
a resumed spiker finished the spike. A session ended early once more,
during the spike review's first fixes, and was resumed the same way.

## Phase 4: reviewing the spike

The spike was reviewed in rounds by a panel of reviewers, each in its own
subagent, in parallel. Each round's `panel.md` says who runs and why.
Round 1 ran nine. By round 3, only the spec reviewer was still asking for
changes, but the others ran again to confirm the fixes, as vibes did then.
From `.vibes/dupfind/review/spike-3/panel.md`:

```markdown
Runs this round:
- spec, bug: requested changes in round 2 (P4/B4, P5). The spec reviewer
  also gives the final verdict on the spike.
- security, resource-leak, architecture, cleanliness, idioms, style:
  approved round 2, but the round 2 fixes touched their areas (S6, L4/L5,
  A3, C6, I3, T3/T4/T6 and the cli request rewrite), so each confirms.

Left out: performance. It approved round 2, and the changes since then
(argument matching in cli, a rename in _walk, a guarded redirect, docs and
test docstrings) do no I/O or work on the scan's hot path.
```

Round 1 had one blocker and six major findings, from the bug, security,
resource-leak and spec reviewers. The security reviewer found that the
scan could be led out of the tree by swapping a directory for a symlink
while the scan ran:

```text
- [MAJOR] src/dupfind/core/_walk.py:79 (with src/dupfind/osfs.py:47 and
  src/dupfind/core/_walk.py:54): `_enter` records the identity from `lstat`,
  then lists the directory by name with `os.listdir(path)`, and each child is
  then `lstat`ed by a name that runs through every parent. If `d/sub` is
  replaced with a symlink to `/root` or `/` between the `lstat` and the
  listing, or between the listing and a child's `lstat`, the walk follows it
  out of the tree without `--follow-symlinks`. ... Fix: in `osfs`, open
  each directory with `O_RDONLY|O_DIRECTORY|O_NOFOLLOW` (relative to the
  parent's descriptor). ...
```

The fix changes behaviour, so it went into the spec as a new
requirement, R52, and into the design as a new filesystem port, in the
same commit as the code:

```markdown
- **R52:** A directory is checked in the same way when it's opened to be
  listed, and a file's directory is checked again when the file is opened
  to be read. ...
  So replacing a directory with a symlink after it was found never leads
  the scan, or the opening of a file, outside the directory arguments
  without `--follow-symlinks`. Acceptance: ...
```

The round's `responses.md` ties each finding to the commit that fixed it,
such as "S1, S2, S3: fixed in 7110d05 (new R52; descriptor-relative
FileSystem port)". Not every finding was accepted. A minor one asking to
escape control bytes in text output was deferred to the final report,
because the spec chose raw bytes on purpose.

The bug reviewer's blocker in round 1, which the resource-leak reviewer
found too, was about the exit status after a failed write:

```text
- [BLOCKER] src/dupfind/cli.py:244: When stdout fails to write (R40), the
  failed bytes stay in the buffer. ... At exit the interpreter flushes
  `sys.stdout` again, the write fails again, and CPython prints "Exception
  ignored on flushing sys.stdout" with an `OSError` on stderr, then exits
  with status 120.
```

Later rounds found smaller problems, almost all of them the spec
reviewer's, about streams, interrupts and how older Python versions parse
arguments. In round 5, the last allowed, every reviewer that ran approved
except the spec reviewer, which found that R40 and R43 disagreed about one
case:

```text
- [MAJOR] docs/specs/dupfind/spec.md:437-438: R40 says that after
  `dupfind: error: cannot write output: REASON`, "Nothing more is written
  to either stream". B5 (cli.py:344-351) now writes `dupfind: interrupted`
  after that line when SIGINT lands during the final redirect ...
```

The bug reviewer approved with one minor finding, B6: a second Ctrl-C at
the same point wrote `dupfind: interrupted` twice. At the end of round 5
the spike's 379 tests passed, with 4 skipped on macOS.

## The round limit, and the resume

At the time, a review that reached its round limit stopped and asked the
user, even in an unattended run. So the run stopped here, with P12 and B6
outstanding. From `.vibes/dupfind/review/spike-5/responses.md`:

```text
- P12 [MAJOR] R40's "Nothing more is written" conflicts with B5, which
  writes `dupfind: interrupted` after `cannot write output` when SIGINT
  lands during the final redirect: would accept ... Not fixed:
  round 5 is the spike phase's limit, so the run stops here for the user.
```

We changed vibes so that an unattended run goes on to the rebuild at the
spike review's limit, since the rebuild writes the code again and is
reviewed again, and resumed the run. The main agent recorded the choice in
`state.md`:

```text
- Unattended decision (spike round limit): went on to the rebuild with
  P12 (spec MAJOR) and B6 (bug MINOR) outstanding. P12 is fixed in the
  spec through spec round spec-6 on vibe/dupfind; B6 goes into the
  rebuild plan's lessons. Not chosen: a sixth spike round; stopping for
  the user.
```

The spec reviewer approved P12's fix in round `spec-6`, with three minor
findings. One asked how often `dupfind: interrupted` may be written, so
the spec now says "at most once per run", which is B6's fix. Round
`spec-7` approved the result. Since a spec change is committed with the
code that implements it, the approved spec and design were kept in
`.vibes/dupfind/target/` for the rebuild to bring over, change by change.

## Phase 5: setting the spike aside

The main agent wrote `.vibes/dupfind/rebuild-plan.md`. It has a test list
of 135 entries, T1 to T135, ordered from simplest to hardest and split
into nine batches:

```markdown
| Batch | Entries | Headings |
| --- | --- | --- |
| 1 | T1 to T5 | 1.1 skeleton, packaging and boundaries |
| 2 | T6 to T23 | 1.2 core model, errors and paths; 1.3 walk |
| 3 | T24 to T44 | 1.4 reading and grouping; 1.5 ordering and the scan result |
| 4 | T45 to T52 | 1.6 the real filesystem |
...
```

Each entry names the requirements it covers, and a coverage table at the
end checks every R and Q id has at least one entry:

```markdown
- [x] T25: Files of size 0 form one group without being opened. (R21)
...
- [x] T36: `_read.open_found_directory` checks the opened directory: `d/sub`
  swapped for a symlink to an outside directory after `d` is listed and
  before `d/sub` is gives one skip for `d/sub`, nothing outside listed,
  opened or reported, no group. (R52)
```

The plan's lessons say what the spike's review rounds found, so the
rebuild gets it right first time: 26 of them, from the buffered bytes
behind the exit status 120 to B6, which T117 is to fix test-first.

A third section maps each change the spike phase made to the spec and
design to the entry whose commit brings it over, such as
`spec.md, R22, R52: ... → T36`.

## Phase 6: the rebuild, so far

Before the first batch, a builder brought the gate up to date with the
commit-gate skill in its new form, as a commit of its own:

```text
651fe34 Check requirement markers and add mutation testing to the audit
```

Now `scripts/check` fails on any test that names a requirement the spec
doesn't have, and `scripts/audit` fails on any requirement no test covers,
and runs mutation testing with mutmut on the changed modules, failing
under an 80% score. Bash mutation testing was left out, since the project
has no Bash tests to kill the mutants.

Then the main agent gave each batch to a fresh builder, one at a time.
Each builder wrote a failing test, the code to pass it, and committed both
through the gate, one entry at a time. The first batch added the design's
boundary rules to the gate, as import-linter contracts and AST tests, so
every later commit is held to them. A slice of `git log --oneline` from
batch 3:

```text
8cc1107 Skip the full digest when the prefix was the whole file
debc6a2 Read files a chunk of at most 1 MiB at a time
076da1a Split each size bucket by a prefix digest, then in full
0048177 Pin that each set of identical contents is one group
50809e4 Group empty files without opening them
ea22c34 Never open a file whose size no other file shares
```

Each test names what it covers in a `# Covers:` marker, which the gate
checks against the spec. T25's test, from `tests/core/test_scan.py`:

```python
# Covers: dupfind R21
def test_empty_files_form_a_group_without_being_opened() -> None:
    fs = FakeFileSystem()
    fs.file("d/a")
    fs.file("d/b")
    result, _ = _scan(fs)
    assert result.groups == (Group(0, ("d/a", "d/b")),)
    assert fs.opened == []
```

A commit whose subject starts with "Pin" adds a test that passed when it
was written, because an earlier entry's code already gave the behaviour.
The builder broke the code on purpose to see each such test fail before
committing it. `.vibes/dupfind/build-4.md` lists the breaks, such as
leaving out `O_NOCTTY`, which showed that macOS does make a terminal the
controlling one without it.

Each builder's report goes to `build-<batch>.md`, and notes for later
batches go into the plan, so the next fresh builder knows the state of the
code without reading the last one's work.

Four batches built 52 of the 135 entries in 54 commits. That covers the
whole core and the real filesystem layer: the walk, reading and grouping,
and every R52 race. We stopped the run there, before batch 5 made a
commit. The rest of the rebuild, the rebuild review and the final audit
weren't run.

## The numbers

| | Spec | Design | Spike | Rebuild so far |
| --- | --- | --- | --- | --- |
| Review rounds | 7 (3, then 2 for R51, then 2 for P12) | 3 | 5 | not run |
| Reviewer runs | 7 | 3 | 41 (9, 9, 8, 8, 7) | not run |
| Lines | 725 approved, 745 with R51, 863 after the spike | 791 approved, 1,005 after the spike | 1,463 of code in 21 files, 2,866 of tests | 827 of code, 2,026 of tests |
| Tests | | | 379 passed, 4 skipped | 159, under 94 `# Covers:` markers |
| Commits | 1 | 1, with R51 | 32 | 1 gate update, 54 for 52 entries |

The spec ended the spike phase with 52 requirements and 11 quality
requirements, and 25 unattended decisions. The rebuild's line counts
include modules that are still only a docstring, since the first batch
adds every module the design names.

Wall-clock times, from the commits:

| Step | Finished |
| --- | --- |
| Session started | 15:48 |
| Gate committed | 15:59 |
| Spec committed | 16:19 |
| Design committed | 16:39 |
| Spike committed | 17:13 |
| Last spike fix (round 4's) | 19:48 |
| Gate updated, after the resume | 20:16 |
| Batches 1 to 4 (5, 18, 21 and 8 entries) | 20:30, 20:52, 21:16, 21:29 |

The spike review took the longest: about two and a half hours, including
the restart during its first fixes.

## What the trial changed in vibes

- **Approvals are confirmed once.** A reviewer that approved ran again
  every round because the fixes touched its area. That's 41 reviewer runs
  in the spike review, where from round 3 the spec reviewer alone was
  asking for changes. Now an approving reviewer doesn't run again while
  others are still asking for changes, and runs once more in a last round
  only if its area changed.
- **Line-level reviewers wait for the rebuild.** The style, idioms and
  cleanliness reviewers' findings were fixed in spike code that the rebuild
  throws away. They're now left out of the spike review, and review the
  rebuild.
- **An unattended run carries on past the spike review's limit.** It fixes
  outstanding spec findings through a spec round on the rebuild branch,
  and puts the rest into the rebuild plan's lessons, as this run did after
  the resume.
- **Specs and designs say each thing once.** The spec reached 863 lines
  and the design 1,005, and almost every agent read both: 12% of all
  subagent context. The templates now ask to define shared outcomes once
  and keep notes short, and most reviewers now read only the sections in
  their area.
- **The gate prints one line for a passing check.** Command output was 11%
  of subagent context, much of it passing test runs read on every commit.
  A check's output is now printed only when it fails.

## Looking at a run of your own

Everything the workflow keeps for itself is in `.vibes/<task>/` in your
project, which a `.vibes/.gitignore` keeps out of git. Read it in this
order:

1. **`state.md`:** the task, the size, the branches, the guides, and a
   log of every phase, round and batch, with any unattended decisions.
   Read it first; it's also what a resume reads.
2. **The spec and design** in the spec directory, such as
   `docs/specs/<task>/`. Unattended decisions are in the spec's
   assumptions, and every later change has a change log row.
3. **`review/<phase>-<round>/`:** for each round,
   `findings-<reviewer>.md` (each verdict and finding) and `responses.md`
   (what was done with each finding, and in which commit). Spike and
   rebuild rounds also have `panel.md`, which says who ran and why. The
   last round of a phase shows where it ended.
4. **`spike-report.md`** and **`rebuild-plan.md`:** what the spike found,
   and the test list, lessons and spec changes the rebuild works from.
5. **`build-<batch>.md`:** each builder's report.

Then read the branches:

```sh
git log --oneline <base>..vibe/<task>
git log --oneline vibe/<task>..spike/<task>
git diff vibe/<task> spike/<task> -- docs/specs/<task>/
```

The first shows the rebuild, one commit per test list entry or so; the
second, the spike and its fixes; the third, what the spike phase changed
in the spec and design.
