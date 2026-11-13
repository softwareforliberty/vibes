# Reviewer evals

These evals check that each reviewer agent finds the problems in its area
and doesn't invent problems in clean code, and that the workflow picks the
right reviewers for a change. Run them after changing an agent's
instructions or the workflow's panel rules, to see whether the change made
it better or worse.

## What's here

Every case reviews the same change to a small Python library: a low-stock
report, with its spec and design. There are two cases per reviewer:

- **`<reviewer>-finds-<defect>`** reviews a version of the change with one
  defect seeded in that reviewer's area, such as SQL injection for the
  security reviewer. It passes when the reviewer dispatches, requests
  changes, and reports the defect, as an LLM judge decides.
- **`<reviewer>-approves-clean`** reviews the clean version of the change. It
  passes when the reviewer approves it with no BLOCKER or MAJOR findings.

The **`panel-<change>`** cases give the main agent the vibe skill and a list
of changed files, such as only config or only docs, and pass when it picks
exactly the reviewers the skill's panel rules call for.

The **`supply-chain-reviewer-*`** cases review a pull request to a small C
library, strbuf, with no spec: a clean version, a noisy but benign one, and
ten malicious ones, such as an XZ-style payload in test data, Trojan Source
characters or a prompt injection. Each fixture holds what `pr-prepare`
wrote for the pull request, so they test the reviewer, not the scan, whose
own tests are in `tests/pr_scan/`. **`review-pr-flags-xz-payload`** runs the
whole `/vibes:review-pr` command on a local pull request, and fails if it
builds, tests, checks out or posts anything.

| Path | What it holds |
| --- | --- |
| `source/base/` | The library before the change, with the spec and design |
| `source/change/` | The files the clean change adds or replaces |
| `source/pr-base/`, `source/pr-change/` | strbuf, and the clean pull request's files |
| `generate.py` | The defect variants, and the code that writes the fixtures and cases |
| `pr_cases.py` | The pull request variants and cases, which `generate.py` writes too |
| `fixtures/` | Each variant's project and review directory, generated |
| `<case>/` | Each case's prompt, graders and setup script, generated |

## Run them

You need Claude Code 2.1.269 or later. From the repository root:

```sh
claude plugin eval . --scaffold --ablation none --allow-tools Write "Bash(cat:*)"
```

- `--scaffold` lets each case's setup script copy its fixture into the run's
  working directory. The scripts only copy files from `fixtures/`.
- `--allow-tools` lets each reviewer write its findings file, which the
  case then reads. The spec reviewer, which Claude Code gives no Write
  tool because it has Bash, writes it with `cat`. The plugin's hook keeps
  every reviewer to its own findings file.
- `--ablation none` skips the run without the plugin, which can't dispatch
  the reviewers and would only add cost.
- `--case 'security-reviewer-*'`, `--tag recall` or `--tag panel` runs a
  subset, and `--runs 1` runs each case once instead of three times.
- `--max-cost-usd 30` sets a hard limit on the cost.

Results and an HTML report go to `evals/results/`, which git ignores.

## Change them

Edit `source/` for the library and the clean change, and `generate.py` for
the defects, the expected findings and the case template. Then regenerate:

```sh
python3 evals/generate.py
```

Never edit `fixtures/` or a case directory by hand: the generator replaces
them. The pull request fixtures hold the scanner's output, so regenerate
after changing it. Before committing, check every fixture's tests still pass, so no
defect is given away by a failing test, and run the affected cases.

The clean change must stay clean. When a reviewer flags it, decide whether
the finding is fair. If it is, fix the clean change, and the matching edits
in `generate.py`. If it isn't, the reviewer's instructions need work.
