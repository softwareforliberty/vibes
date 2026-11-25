# Changelog

Every release of the vibes plugin, newest first. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html): while the major
version is 0, a minor release may change how the workflow, the gate or the
guides behave, and says so under **Changed**.

## [Unreleased]

### Added

- **Contributing guidelines and a security policy.** `CONTRIBUTING.md`
  says how to report a bug, suggest an idea and send a change, and
  `SECURITY.md` how to report a vulnerability privately, through GitHub's
  private vulnerability reporting, which is now on.

## [0.7.0] - 2026-11-25

### Added

- **`bin/check-all`, and the slow tests once per build, not per batch.**
  `bin/check-all` runs `scripts/check --all` unless the same files already
  passed, remembered in the repository's shared git folder, so a worker's
  worktree and the main checkout share them. Builders no longer run the
  slow tests at the end of each batch: the main agent runs them once the
  batches are built and joined, before each rebuild review round, and at
  the finish, where an unchanged tree costs nothing. Joining a parallel
  batch runs the fast checks only.

- **The gate doesn't check the same commit twice.** After a pass it
  remembers the commit's parent, staged tree and mode, in the git folder,
  and a retry of exactly that commit, as after git refused its message,
  goes through without running `scripts/check` again. Git runs the gate
  before it reads the message, so a long subject used to cost a whole
  second gate run.

- **`scripts/test-one`, to run only the tests you name.** The commit-gate
  skill writes it beside `scripts/check-file` (its new Step 4): it takes
  test files, test functions or a source file of the code under test,
  builds only what they need, as the gate does, and lists what it can run
  when given nothing. The TDD skill and the builder run each red and
  green step with it, and a builder that finds a gated project without
  one writes it first. The vibe, debug and optimise workflows set it up
  with the rest of the gate.
- **The test-one hook.** In a project with `scripts/test-one`, it refuses
  `scripts/check` with no mode from `vibes:builder`, which runs its tests
  with `scripts/test-one` instead. `--all` and `--static` stay open, the
  gate still runs on every commit, and no other agent is held.

- **The designer keeps the project's glossary and decision records.**
  - **The glossary:** the spec uses its terms and none of the words it
    says to avoid, and a clash between the task's words and the glossary
    becomes an open question. Each new term the task brings into the
    project is added, and `GLOSSARY.md` is created when the first one
    needs it.
  - **Decision records:** the design keeps to the existing records, and
    asks before replacing one. Each new decision that is hard to reverse,
    surprising without its reason and a real choice gets a short record
    in `docs/adr/`, or wherever the project keeps them.
  - **Reviews:** the spec reviewer checks the glossary, the architecture
    reviewer checks the new records, and the project docs reviewer treats
    breaking a record as a BLOCKER and using a word the glossary says to
    avoid as MAJOR.
  - **The final report** lists the terms and records the task added.
- **Facts are researched, not asked.** Open questions are marked a fact
  or a decision. The new researcher answers each fact from primary
  sources, the dependency's own code at the pinned version first, in a
  dated note citing a source for every claim, committed with the spec
  that relies on it. It works in `/vibes:vibe`, `/vibes:optimise` and
  `/vibes:debug`.
- **`/vibes:survey` looks across the codebase for modules worth
  deepening.** The new surveyor starts where `bin/hotspots` shows recent
  commits keep landing, and writes ranked candidates, each with the code
  that shows the friction, the deletion test and before and after
  diagrams, which `bin/report-page` shows as a page. For the candidate
  you pick, three new interface designers each design it under a
  different constraint, and the surveyor compares them and recommends
  one, as a task for `/vibes:vibe`. It changes nothing.
- **Batches that don't need each other are built at once.** The rebuild
  plan marks what each batch waits for and which files it changes, and
  the new `bin/plan-graph` says which are ready and catches two that would
  change the same file. Each builds in its own worktree and branch, and
  joins the rebuild branch in a line as it finishes. How many at once is
  measured by the new `/vibes:capacity` and `bin/capacity`, from runs of
  the project's gate alone and two at once, and cached per machine in
  `.vibes/capacity.json`; it's measured again when the machine, the gate
  or the project's size changes.
- **`/vibes:grill`** stress-tests a plan before it's built: it maps every
  decision the plan leaves open and every fact it rests on, and asks you
  the decisions in rounds until nothing is left, ending with a decisions
  document `/vibes:vibe` can start from.
- **`/vibes:wizard`** writes a wizard for steps only you can do, such as
  creating an API key in a dashboard or setting a CI secret: a bash script
  you run in your own terminal that opens each page, says what to click,
  and saves what you paste in `.env` or as a GitHub secret or variable,
  with secrets in hidden prompts that never reach the agent. Each step
  comes from the provider's documentation, with its date. The new wizard
  writer writes the stages onto a tested library, and a run writes a
  wizard at its end when the new `bin/setup-needs` finds settings the
  branch needs that nobody has provided. `bin/wizard-check` checks a
  wizard without running it.
- **`/vibes:prototype`** answers one design question you can't judge in
  words with a throwaway prototype on a branch that's never merged: a
  single HTML file to click through a state model's scenarios, or three
  structurally different variants of a screen on the real page. The
  confirmed scenarios become examples in the spec, and a run offers a
  prototype for such a decision. The new prototyper builds them, and
  `bin/prototype-check` checks a logic prototype loads nothing from
  outside and keeps its logic apart from the page.
- **A guide for the instructions agents read:** `CLAUDE.md`, `AGENTS.md`,
  rules, skills and subagents. It covers their layout, and how to word
  them so an agent takes the same path every run: pointers that decide
  what gets read, steps before reference, a checkable end to every step,
  the behaviour wanted rather than a ban, one word for one idea, each rule
  in one place, and cutting what changes nothing. Agents read it before
  writing one of these files, and the retrospective words its
  suggestions by it.
- **`/vibes:questionnaire`** turns a decision only someone else can make
  into a questionnaire for them, asking you only who it's for and what
  you need back. A run offers one for such a decision and waits for the
  answers.
- **Work from GitHub issues.** `/vibes:vibe`, `/vibes:debug` and
  `/vibes:optimise` take an issue, such as `#123`. The new issue reader is
  the only agent that reads an issue's text, which anyone could have
  written: it writes a brief, lists anything that tries to direct an
  agent, and the run starts from the brief once you confirm it.
  `/vibes:pr` closes the issue in the pull request's body.
- **`/vibes:triage`** proposes a label and a reply for each open issue,
  checking the code and the decision records and reproducing bugs, and
  posts nothing until you approve the batch.
- **`/vibes:pickup`** works on the next issue you approved as ready for an
  agent, unattended, on a local branch. It takes only issues unchanged
  since you approved them, which the new `bin/issue-digest` checks, and
  posts, pushes and opens nothing.
- **`/vibes:pr` writes the pull request for a branch,** only when you ask.
  The new pull request writer gives the smallest view that makes the
  change clear, the evidence before and after quoted from the run's
  records, such as a reproduction going from `RED` to `GREEN` or each new
  test's failing line, and the merge risk: a one-way or two-way door, and
  what calls the changed code. Every claim is listed with its source, and
  what nothing shows is marked unverified. It pushes and opens a draft or
  ready pull request only when you say so, and never forces a push.
- **`architecture/deep-modules.md`:** depth, seams, leverage and locality,
  the deletion test, and designing it twice.
- **`/vibes:retro` looks back on a session** and suggests changes to the
  project that would make the next one go better, such as a check, a
  coding standard or a pointer to a file, each citing the calls behind
  it. It changes nothing. A change that would loosen a check is listed
  apart and applied only when named on its own, and the review rounds,
  the gate and the tests are never counted as waste.
- **`/vibes:debug` finds and fixes a bug whose cause isn't known.** The
  new diagnoser builds a command that fails on the exact symptom, which
  `bin/repro` must judge `RED` before anyone guesses at the cause, shrinks
  it, ranks hypotheses with predictions that could prove them wrong, and
  tests them one change at a time on a spike branch until a quick change
  makes the command pass. The fix is rebuilt test-first from a short bug
  spec, reviewed, and checked against the original reproduction, and its
  commit states the cause. Unattended runs are optional.
- **`bin/repro`** runs a reproduction several times and prints `RED`,
  `GREEN`, `FLAKY` or `CAN'T TELL`, with the median time, and `SLOW` when
  it's too slow for a debugging loop.
- **The gate refuses a commit that keeps a debug run's logs:** a line
  tagged `vibes-debug-<slug>`.
- **`bin/session-digest`** prints a compact digest of a session's
  transcript and its subagents': every tool call on one line with a
  reference, and the failures, hook blocks, retries, repeated calls and
  largest results.
- **vibes runs in Copilot CLI, Codex and Gemini CLI,** with as much of its
  enforcement as each allows, as the README's "Other agents" says.
  - **Copilot CLI** installs the plugin as it is.
  - **Codex** installs its skills and hooks, and `bin/host-files codex`
    writes its agents. Each skill only you start has an
    `agents/openai.yaml`, so Codex never starts it itself.
  - **Gemini CLI** gets an extension from `bin/host-files gemini`.
  - **The hooks** read each host's input, including a Codex patch that
    changes several files. Where a hook can't ask you, a commit that
    loosens the gate is refused. An agent listed without Bash may run
    only commands that read, on a host that can't take the shell away.
  - **Skills and agents** say what `${CLAUDE_PLUGIN_ROOT}` stands for
    where it isn't filled in, and skills pass the folder to each agent.

- **`/vibes:tracker` and `bin/tracker`: any issue tracker.** The project
  names its tracker's commands in `.vibes-tracker`, and vibes runs only
  those: issue intake, `/vibes:triage`, `/vibes:pickup` and `/vibes:pr`
  no longer call `gh` themselves. `/vibes:tracker` drafts the file for
  GitHub or GitLab, or writes one for another tracker from its CLI's
  documentation.
  - **You approve the commands** in your own terminal, with `tracker
    approve`, and any change needs approving again. The approval is kept
    in `~/.config/vibes/tracker-approvals/`, outside the repository, where
    an agent in Claude Code's sandbox can't write, and `tracker check`
    says whether the session is so guarded. The file is read from the
    default branch, never the checkout.
  - **No shell:** each command is one program and its arguments, each
    value is checked before it fills a placeholder, only `{body-file}`
    names a file, and the commands get only the tokens the file names.
  - **Posting needs your confirmation:** public operations run only from
    a batch, which you confirm, and which no subagent may run.
  - **Guarded like the gate:** a hook stops agents approving or touching
    the approval, and subagents writing the file; the commit gate asks
    before a commit that changes it; and `/vibes:review-pr` marks a
    change to it HIGH.

- **`/vibes:runbook`: changes that can't be undone,** such as a
  production migration, a DNS cutover or rotating a key. It writes a
  script you run yourself, on the wizard library, where each step checks
  what it needs first and verifies its change after; each one-way step
  says what it changes for good and how to recover, and runs only once
  you type its name; and each step is logged, so a second run starts
  where the first stopped and never repeats a finished step. `--plan`
  shows the steps and changes nothing. `/vibes:pr` offers one for a
  one-way door someone must deploy.

- **`/vibes:review-pr` on GitLab, Forgejo, Codeberg and Gitea,** through
  each forge's own CLI: `glab` for GitLab and `tea` for Forgejo and
  Gitea, beside `gh` for GitHub. The forge is told by the pull request's
  address or the `origin` remote, or named with `--forge`. Each forge's
  record of the pull request goes into one shape, `meta/pr.json`, so the
  same checks run on each, and a check the forge's data can't settle,
  such as GitLab's commits having no accounts, says so rather than pass.
  `--fetch <remote> <ref>` reviews a pull request on any other forge
  without the record.

- **Boundary rules stay proved.** The breach that proves each boundary
  rule bites is kept in `scripts/breaches/<rule>.patch`. `bin/rules-bite`
  applies each to a throwaway copy and checks `scripts/check` still
  catches it, and the commit gate runs it on every commit that changes
  the checks or a breach, refusing one that would let a rule stop
  biting. A run checks every rule again before it finishes, and a
  component the design gains after the first batch gets its rules and
  their breaches in the batch that creates it.

- **A commit whose files change during its gate is refused.** The gate
  compares what's staged, the tracked files and the untracked ones before
  and after its checks, so an edit made while a slow gate runs, such as
  after the agent's shell time limit moves the commit to the background,
  can't be committed unchecked. The builder and the main agent change
  nothing while a commit runs.

- **No agent waits forever.** The agents that run long commands run them
  in the shell's background mode, which reports however a command ends,
  and never detach a process themselves or wait in a loop for a file. The
  main agent keeps watch on each long-running agent with a timer, asks
  one that has made no progress what it's waiting on, and stops it and
  tells the user if it stays stuck.

### Changed

- **Open questions are asked in rounds.** The designer marks what each
  question waits on, and each round asks only the decisions whose
  prerequisites are answered, while the facts are researched in the
  background rather than before anything is asked. Answers that make
  questions moot remove them, and answers that raise new ones add them to
  the next round. An unattended run decides each round in turn.
- **Committing `CLAUDE.md`, `AGENTS.md`, a skill or a subagent needs the
  new `tools/Agent-instructions` guide** on `scripts/check`'s
  `# Guides:` line. It adds no checks.
- **Each component has a front door.** The design names each component's
  entry points, and the gate enforces them: code outside a component, and
  its own tests, use only those, while what's behind them can be
  organised freely. Each language guide's Architecture section says how,
  with the language's visibility rules or the build where they can, and
  its architecture test tool otherwise, each checked against the real
  tool. The architecture reviewer checks the design names them and the
  code keeps to them.
- **Every rule the gate gets is proved to bite.** Setting up the gate
  breaks each check once on purpose and sees it fail, and the first build
  batch does the same for each boundary rule, so a rule that matches
  nothing can't pass unnoticed.
- **Every decision you're asked comes with a recommended answer,** worded
  so "yes" accepts it, so you can accept them all at once. Unattended runs
  take the recommendation, unless it does more than you asked.
- **The spec reviewer checks outside facts are sourced,** and the project
  docs reviewer treats a research note as a record of its date, not a
  rule.
- **The commit gate asks before it's loosened.** In Claude Code, a commit
  that deletes `scripts/check` or `scripts/check-file`, makes either not
  executable, removes or changes a line of either so that a word is lost,
  or lets a failure pass, such as with `|| true`, now needs your
  confirmation, and is refused where nobody can give it. Builders report
  a check they think must change instead.

### Fixed

- **A long subject in a `git commit -F -` heredoc is caught before git
  runs.** The Claude hook split the whole command into shell words,
  heredoc included, so a lone apostrophe in the message, as in "isn't",
  read as an unclosed quote, and the hook let the commit through
  unchecked. Git then ran the whole gate before its own subject check
  refused the commit. A command that can't be split as a whole is now
  split with each heredoc's body cut out.
- **Evals whose agent runs git now work on macOS.** The eval's sandbox
  won't stat a real git binary, though it will run one, so the shell's
  search for `git` skipped Homebrew's, and Apple's `/usr/bin/git` stand-in
  couldn't find the developer tools' git. `lib/eval-path/git` runs the next
  git on the path by its full path, or the developer tools' own git in
  place of Apple's stand-in, so neither Homebrew nor any setup is needed.
  `evals/run` runs the evals with it first on the path, and on a Mac with
  no git the sandbox can run, stops and says to run
  `xcode-select --install` or `brew install git`.
- **`bin/capacity` no longer undercounts memory under pressure.** macOS
  compresses an idle process's pages when memory runs short, so sampling
  resident memory could see 9 MB of a command holding 80 MB, and allow too
  many builders. A measurement now counts at least the kernel's own peak
  for the command.

- **Three layer checks that couldn't fail now do.** On Julia 1.13,
  `Pkg.precompile()` printed a forbidden dependency but exited 0, so the
  Julia guide passes `strict=true`. On sbt 2, a cached `sbt test` skipped
  the architecture suite, so the Scala guide runs `sbt testFull`. The Go
  guide's go-arch-lint example refused a component's own packages and
  tests until each component lists itself.

## [0.6.1] - 2026-11-20

### Fixed

- **A commit behind `time`, `env`, `nice` or another wrapper skipped the
  gate.** The Claude Code hook looked for `git commit` only at the start of
  a command, so `time git commit …` ran no checks; it now finds it anywhere
  in the command, including in a subshell.
- **The git hooks broke silently when vibes updated.** They were links into
  one plugin version's folder, and git skips a hook whose link no longer
  resolves, so removing an old version turned the gate off. The new
  `bin/install-git-hooks` writes a small stub for each hook that runs the
  newest vibes installed, and refuses the commit when there's none.
  `/vibes:vibe` and `/vibes:optimise` run it at the start of each run,
  which replaces the old links and adds a missing `commit-msg` hook, and
  the Claude Code hook blocks a commit while a vibes hook's link is broken,
  saying how to reinstall.

## [0.6.0] - 2026-11-20

### Added

- **The project docs reviewer** checks the spec, design and code against
  the project's own documents, such as its README, architecture notes,
  decision records and earlier specs, in every review of `/vibes:vibe` and
  `/vibes:optimise`. It decides from their headings which apply, and stops
  at once when none do; a project with no documents never runs it. The
  designer corrects the spec and design to follow a document, and asks you
  when the task seems meant to change what the document says.
- **`bin/project-docs`** lists a project's own documents, skipping release
  notes, licences, templates, vendored code and test data.
- **The commit message suggester** writes the message for each commit the
  workflows' main agent makes itself, with a subject it has counted to 50
  characters or fewer.
- **A `commit-msg` git hook,** `hooks/git_commit_msg`, which holds every
  commit to the same limit.
- **`/vibes:review` reviews the checked-out branch,** uncommitted changes
  included, with the same scan, guides and reviewers as
  `/vibes:review-pr`, as your own work: the spec reviewer joins when the
  branch has a spec, and you can have the findings fixed test-first.
  `pr-prepare --branch` and `pr-scan report --branch` prepare and report
  it, without touching the working tree, index or branches.
- **`/vibes:review-pr`'s panel** gains the project docs reviewer when the
  project has documents.
- **Evals** for the project docs reviewer and the commit message
  suggester.
- **Each file is formatted and linted as it's written.** A new
  `PostToolUse` hook runs the project's `scripts/check-file` on every file
  an agent writes: it fixes the formatting and shows the agent any lint
  problems at once, rather than when the commit gate fails. It skips
  `spike/*` branches, the spiker and files git ignores, and does nothing
  in projects without `scripts/check-file`. The commit-gate skill writes
  it, and the vibe and optimise workflows add it to a gate that lacks it.
  It also checks each file a shell command writes, such as through a
  heredoc or `sed`, by comparing the changed files before and after the
  command; a command that runs git is left alone. Builders were making
  almost every edit through the shell.
- **`scripts/check --static` and `--all`.** The gate runs `--static`, the
  checks without the tests, for a commit of documents only, such as a
  spec. `--all` adds the slow tests, such as boot and smoke tests, which no
  longer run on every commit: builders run them once at the end of each
  batch, and the workflows before they finish. A `scripts/check` that
  ignores its arguments runs everything, as before.
- **A notification when a run needs you.** `/vibes:vibe` and
  `/vibes:optimise` send a push notification, where the session can, before
  they stop to ask you something, and ask everything they have at once.

### Changed

- **Commit subjects are 50 characters at most,** not 50 where you can and
  72 at most. The Claude Code gate hook reads the subject from
  `git commit`'s `-m`, heredoc or `-F` message and blocks a longer one
  before running the checks, on every branch.
- **The builder runs the type checks before each commit,** so the gate's
  full run seldom fails on a small mistake and runs again. Tests and
  coverage stay with the gate. It writes files with Write and Edit rather
  than the shell.
- **`scripts/check` fails fast:** the commit-gate skill now has it run the
  static checks first and stop before the tests if any fail, so a lint
  error no longer costs a full test run. The vibe and optimise workflows
  bring an older gate up to date.
- **The audit runs alongside the rebuild review,** on the rebuild's head
  in a worktree of its own, instead of after it, and runs again at the
  finish only when the dependencies changed.
- **The main agent no longer reruns `scripts/check` after each batch:** the
  gate ran it on every commit, and the builder ran the slow tests.

### Fixed

- **Reviewers write their findings file before they reply.** Some put
  their findings in their reply instead, or held back because Claude Code
  tells subagents not to write report files, so the main agent had to ask
  again. Each reviewer's output section now starts by saying the file is
  the output its brief asks for, and that a review left in the reply is
  lost.

## [0.5.1] - 2026-11-14

### Changed

- **`/vibes:vibe`, `/vibes:optimise` and `/vibes:review-pr` check their
  agents are loaded before they start,** and stop if they aren't, rather
  than stand in for them with general agents, which have none of their
  tool limits and slip past the hooks that keep reviewers read-only. A
  plugin enabled only for the main checkout can load its skills but not
  its agents in a git worktree session; the README says how to avoid it.

## [0.5.0] - 2026-11-13

### Added

- **`/vibes:optimise` makes a program faster where a profile shows the
  time goes.** It profiles a baseline, plans and specs the optimisation,
  tries each idea as a spike measured against the best version so far
  until the ideas stop paying, has the winner reviewed, then rebuilds it
  test-first and measures it again. `/vibes:vibe` never uses it.
- **`bin/bench`** runs a benchmark harness against two trees in
  interleaved pairs, and decides whether the change is better beyond the
  noise an A/A run measured, with guard rails such as peak memory.
- **The profiler and optimiser agents.** The profiler measures and never
  changes the code, which a hook enforces; the optimiser builds and never
  measures.
- **`performance/`:** the method for measuring and profiling, and the
  profilers and benchmark tools for each guide.
- **Evals** for the profiler, the optimiser and the whole command, on a
  small Python tool with a quadratic hot spot.

## [0.4.0] - 2026-11-13

### Added

- **`/vibes:review-pr` reviews a pull request from outside the project,**
  above all for malicious changes like the XZ Utils backdoor. It never runs
  the pull request's code, and never posts to GitHub: it writes a report and
  a draft comment for you.
- **`bin/pr-prepare` and `bin/pr-scan`** fetch a pull request and scan it,
  reading it only from git objects. The scan checks every file and every
  commit for hidden payloads, obfuscation, build-time code, weakened
  checks, pin and key changes, CI and agent-config risks, and text aimed at
  AI reviewers, and its HIGH findings can't be cleared by a reviewer.
- **The supply-chain reviewer,** used only by `/vibes:review-pr`, with its
  standards in `security/malicious-changes.md`.
- **A `.vibes-review` file** lists a project's protected paths, test data,
  allowed binaries and hosts, and is read from the base branch only.
- **Evals** for the supply-chain reviewer, on twelve versions of a pull
  request to a small C library, and for the whole command.

## [0.3.0] - 2026-11-09

### Fixed

- **The reviewer evals' clean change names the requirements its tests
  cover.** Its tests had no `# Covers:` markers, which the
  test-driven-development skill requires, so the test reviewer rightly
  flagged the clean change in every run.
- **pip-audit no longer fails on the project itself.** The Python guide's
  command skips editable packages, so the project, installed with
  `pip install -e .` and never published, isn't looked up on PyPI.

### Changed

- **The designer fixes the review findings in the spec and design,** in a
  new `revise` mode, so the main agent no longer edits them itself.
- **The main agent no longer reads the findings.** Each reviewer writes its
  own findings file and replies in one line, and the fixer, the designer
  or the builder, decides on each finding and records the response. The
  builder and the spiker write their own reports, and the designer writes
  the rebuild plan. A hook lets a reviewer write only its own findings
  file, and the reviewers write it even when they approve with no
  findings.
- **The spec and design stay in proportion to the task:** they specify
  what users would notice, follow the platform's conventions instead of
  restating them, and the reviewers don't hold them up over details that
  don't matter.
- **A fix to a MINOR finding isn't reviewed again,** and the rebuild's last
  round brings back only the reviewers whose area a BLOCKER or MAJOR fix
  changed.
- **The commit gate is set up while the spec is written,** at medium
  effort, with the spec drafted where git ignores it until the gate is
  committed.
- **A small new program whose design is clear is a medium task,** with no
  spike.
- **The builder shows every new test failing before writing its code,**
  with each red run's failure line in its report, since builders in
  trials 3 and 8 wrote some tests and code together.
- **The rebuild plan has fewer entries and batches:** about half as many
  entries as the spec has ids, and two or three batches of eight to twelve
  entries for one tool or feature, since each new builder reads the
  skills, guides, spec and design again.

## [0.2.0] - 2026-11-08

### Fixed

- **The commit gate missed some of the agent's commits.** A commit made
  with `git -C <dir> commit`, a bare `git commit`, or a commit after `cd`
  into another repository skipped the gate. The hook now runs on every
  Bash command, finds the repository each commit is in and checks it
  there, and blocks a commit whose repository it can't work out when the
  session's own repository is gated.

### Changed

- **The gate's tools are installed only from their own projects'
  sources,** never from a package of the same name in another registry.
- **The spike is reviewed once, and its code is never fixed.** Findings that
  change behaviour or structure correct the spec and design, which are
  approved again before the rebuild. An uncertain design change is tried in
  the spike once more, and every other finding becomes a lesson for the
  rebuild.
- **The builder and the spiker run on Sonnet.**
- **The rebuild plan has a section per batch,** with entries that each
  drive one piece of code, and each builder reads only its own section and
  the parts of the spec and design its entries need.
- **A test that passes straight away is checked by reading the code,** not
  by breaking it on purpose.
- **The main agent keeps its records short:** a line per step in
  `state.md`, and a line per reviewer and finding in each round.

## [0.1.0] - 2026-11-07

The first versioned release.

### Added

- **The vibe workflow** (`/vibes:vibe`): a complete spec, then a design,
  spike, review rounds, a test-first rebuild and a final review, scaled to
  the task's size, with unattended runs and resuming an interrupted run.
- **Agents:** the designer, the spiker, the builder, and ten reviewers for
  the spec, architecture, cleanliness, style, idioms, resource leaks,
  performance, bugs, security and tests.
- **Skills** for test-driven development, atomic commits and setting up the
  commit gate.
- **The commit gate,** for Claude Code and for git: every commit passes the
  project's `scripts/check`, the gate checks every guide the commit's files
  need, and requirement markers in tests are checked against the specs.
- **Guides** for 40 programming languages, web formats, data formats and
  database dialects, build systems, and tools (Docker, GitHub Actions,
  OpenTofu and Nix), each with a coding style, idioms, and checking tools,
  including mutation testing, with drop-in configs.
- **Architecture guides** for web, desktop and mobile applications,
  command-line tools, libraries, OS components and embedded systems, and
  the programming principles every change is held to.
- **Hooks** that make an agent read a file's guide before writing it, and
  keep the spec reviewer from changing files or git state.
- **Evals** for each reviewer, and for choosing the review panel.
- **A worked example** of a large, unattended run, in
  [`docs/example/`](docs/example/README.md).

[Unreleased]: https://github.com/softwareforliberty/vibes/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/softwareforliberty/vibes/compare/v0.6.1...v0.7.0
[0.6.1]: https://github.com/softwareforliberty/vibes/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/softwareforliberty/vibes/compare/v0.5.1...v0.6.0
[0.5.1]: https://github.com/softwareforliberty/vibes/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/softwareforliberty/vibes/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/softwareforliberty/vibes/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/softwareforliberty/vibes/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/softwareforliberty/vibes/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/softwareforliberty/vibes/releases/tag/v0.1.0
