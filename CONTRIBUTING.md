# Contributing to vibes

Thanks for helping. This file says how to report a problem, suggest an
idea and send a change. The [README](README.md) says what vibes does and
how to install it.

## Ground rules

- **Licence.** vibes is [0BSD](LICENSE). By sending a change, you agree to
  release it under the same licence. There's no contributor licence
  agreement and no sign-off to add.
- **Security problems go to [SECURITY.md](SECURITY.md),** never to a
  public issue.
- **Ask before a big change.** For anything larger than a small fix, such
  as a new skill, agent or guide, or a change to how the workflow or the
  commit gate behaves, open an issue first, so we can agree on the approach
  before you spend time on it.

## Report a bug

Open an [issue](https://github.com/softwareforliberty/vibes/issues) with:

- the vibes version (`claude plugin list` shows it), and the agent and its
  version: Claude Code, Copilot CLI, Codex or Gemini CLI;
- your operating system;
- what you ran, such as `/vibes:vibe` or a `bin/` tool, what you expected,
  and what happened, with any error text in full;
- where it helps, the relevant part of the session or the run's folder,
  `.vibes/<task>/`. Read it first, and remove anything private.

## Suggest an idea

Start a [discussion](https://github.com/softwareforliberty/vibes/discussions)
for an open-ended idea, or open an issue for a concrete change.

## Set up

You need Bash, git, `realpath`, Python 3.9 or later and Claude Code. Clone
the repository, then try your checkout without installing it:

```sh
claude --plugin-dir /path/to/vibes
```

## Where things live

| Path | Holds |
| --- | --- |
| `skills/` | The skills, such as `/vibes:vibe` |
| `agents/` | The agents: the designer, the builder, the reviewers and the rest |
| `hooks/` | The hooks: the commit gate, the guide check and the others |
| `bin/`, `lib/` | The command-line tools the skills run, and their Python code |
| `guides/` | The style, idiom and tool guides, and `map.tsv`, which says which guide each file needs |
| `architecture/`, `principles.md` | The architecture guides and programming principles every change is held to |
| `security/` | What the pull request review looks for |
| `tests/` | The tests, one folder for each tool or hook |
| `evals/` | The evals, which check that the agents and skills behave |

## Make a change

- **Test first.** A change to `bin/`, `lib/` or `hooks/` comes with a test
  in `tests/` that fails without it.
- **Follow the guide for each file you touch.** [`guides/map.tsv`](guides/map.tsv)
  says which one. Every change also follows the
  [programming principles](principles.md) and the
  [architecture guides](architecture/README.md).
- **A new or changed guide** follows the
  [rules for every guide](guides/README.md#rules-for-every-guide), and gets
  a line in `map.tsv`, or it's never picked up.
- **A change to what an agent or skill does** comes with a new or updated
  eval. Edit the generators and run `python3 evals/generate.py`; never edit
  a generated fixture or case by hand. [evals/README.md](evals/README.md)
  says how.
- **Write plainly:** short sentences, plain words and British spelling, as
  the rest of the repository does. Update the README when something a user
  sees changes.
- **Add a changelog entry** under `[Unreleased]` in
  [CHANGELOG.md](CHANGELOG.md), in **Added**, **Changed** or **Fixed**. A
  change to how the workflow, the gate or the guides behave goes under
  **Changed**.

## Run the tests

Each folder under `tests/` runs on its own:

```sh
python3 -I -m unittest discover -s tests/hooks -t tests/hooks
```

To run them all:

```sh
for dir in tests/*/; do
  python3 -I -m unittest discover -s "${dir}" -t "${dir}"
done
```

The evals run real agent sessions, so they take time and use your Claude
usage. Run the cases your change affects with `evals/run`, as
[evals/README.md](evals/README.md) shows.

## Commits

- **Keep each commit small and whole.** It does one thing, and the tests
  pass after it.
- **Write the subject in the imperative,** such as "Add a guide for Zig",
  in 50 characters or fewer, with no full stop. When the subject can't say
  why, a body after a blank line does, wrapped at 72 characters.

## Pull requests

- **Branch from `master`,** keep each pull request to one topic, and
  rebase it on `master` before asking for review.
- **Say what it changes and why,** how you tested it (the tests and any
  evals you ran), and which issue it closes, if any.
- **Expect a careful review.** Every pull request from outside is reviewed
  with vibes' own `/vibes:review-pr`, which looks for the risks in
  [security/malicious-changes.md](security/malicious-changes.md). Explain
  anything that would look unusual there, such as a binary file, a network
  call, generated code or a change to a hook or the gate.
- **The maintainer merges** by rebase, and makes each release and its
  version.
