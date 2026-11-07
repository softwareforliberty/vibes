# Reviewer evals

These evals check that each reviewer agent finds the problems in its area
and doesn't invent problems in clean code. Run them after changing an
agent's instructions, to see whether the change made it better or worse.

## What's here

Every case reviews the same change to a small Python library: a low-stock
report, with its spec and design. There are two cases per reviewer:

- **`<reviewer>-finds-<defect>`** reviews a version of the change with one
  defect seeded in that reviewer's area, such as SQL injection for the
  security reviewer. It passes when the reviewer dispatches, requests
  changes, and reports the defect, as an LLM judge decides.
- **`<reviewer>-approves-clean`** reviews the clean version of the change. It
  passes when the reviewer approves it with no BLOCKER or MAJOR findings.

| Path | What it holds |
| --- | --- |
| `source/base/` | The library before the change, with the spec and design |
| `source/change/` | The files the clean change adds or replaces |
| `generate.py` | The defect variants, and the code that writes the fixtures and cases |
| `fixtures/` | Each variant's project and review directory, generated |
| `<case>/` | Each case's prompt, graders and setup script, generated |

## Run them

You need Claude Code 2.1.269 or later. From the repository root:

```sh
claude plugin eval . --scaffold --ablation none
```

- `--scaffold` lets each case's setup script copy its fixture into the run's
  working directory. The scripts only copy files from `fixtures/`.
- `--ablation none` skips the run without the plugin, which can't dispatch
  the reviewers and would only add cost.
- `--case 'security-reviewer-*'` or `--tag recall` runs a subset, and
  `--runs 1` runs each case once instead of three times.
- `--max-cost-usd 30` sets a hard limit on the cost.

Results and an HTML report go to `evals/results/`, which git ignores.

## Change them

Edit `source/` for the library and the clean change, and `generate.py` for
the defects, the expected findings and the case template. Then regenerate:

```sh
python3 evals/generate.py
```

Never edit `fixtures/` or a case directory by hand: the generator replaces
them. Before committing, check every fixture's tests still pass, so no
defect is given away by a failing test, and run the affected cases.

The clean change must stay clean. When a reviewer flags it, decide whether
the finding is fair. If it is, fix the clean change, and the matching edits
in `generate.py`. If it isn't, the reviewer's instructions need work.
