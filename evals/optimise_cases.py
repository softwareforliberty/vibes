"""The optimise evals: fixtures and cases for /vibes:optimise and its agents.

Every case works on contacts, a small Python tool whose dedupe command scans
a list of the addresses seen so far once per row, so it takes time that
grows with the square of the rows. The profiler cases check it finds that
hot spot, and that its measurements give the right verdict for a faster
candidate, one that changes nothing and one that's faster but wrong. The
optimiser case checks its plan goes after the hot spot, not cold code. The
end-to-end case runs the whole command, unattended.

generate.py calls build() after clearing the generated files.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from pr_cases import GENERATED, write_case

EVALS = Path(__file__).resolve().parent
PROJECT = EVALS / "source" / "optimise"
RUN = EVALS / "source" / "optimise-run"
FIXTURES = EVALS / "fixtures"
SLUG = "dedupe"
RUN_DIR = f".vibes/optimise-{SLUG}"
BRANCH = f"spike/optimise-{SLUG}-1"
TASK = "the dedupe command is slow on large exports"

# The tools the profiler's commands need, so no case runs with unrestricted
# Bash.
PROFILER_TOOLS = ('"Bash(git *)", "Bash(python3 *)", "Bash(*/bin/bench *)", '
                  '"Bash(*/bench/run *)", "Bash(*/bench/prepare *)", '
                  '"Bash(command -v *)", "Bash(which *)", "Bash(mkdir *)", '
                  '"Bash(chmod *)", "Bash(ls *)", "Bash(cat *)", '
                  '"Bash(head *)", "Bash(tail *)", "Bash(wc *)", '
                  '"Bash(sort *)", "Bash(cd *)", "Bash(time *)", '
                  '"Bash(/usr/bin/time *)", "Bash(uname *)", '
                  '"Bash(sw_vers*)", "Bash(pmset *)", "Bash(sysctl *)", '
                  '"Bash(diff *)", "Bash(shasum *)", "Bash(sample *)"')


@dataclass(frozen=True)
class Candidate:
    """A candidate optimisation: dedupe.py as it rewrites it, and what the
    profiler's report must say about it."""

    name: str
    dedupe: str
    expected: str


IMPROVED = '''"""Removes duplicate contacts, keeping the first row for each address."""


def normalise(email: str) -> str:
    """The form of an address that duplicates share."""
    return email.strip().lower()


def dedupe(rows: list) -> list:
    """The rows with a new address, in their original order."""
    kept = []
    seen = set()
    for row in rows:
        key = normalise(row["email"])
        if key not in seen:
            seen.add(key)
            kept.append(row)
    return kept
'''

NO_CHANGE = (PROJECT / "contacts" / "dedupe.py").read_text(
    encoding="utf-8").replace("kept", "result")

BROKEN = IMPROVED.replace('key = normalise(row["email"])',
                          'key = row["email"]')

CANDIDATES = (
    Candidate("improved", IMPROVED,
              "the main size's verdict line says IMPROVED, and the tests "
              "passed"),
    Candidate("no-change", NO_CHANGE,
              "the main size's verdict line says NO CHANGE or INCONCLUSIVE, "
              "never IMPROVED or REGRESSED"),
    Candidate("broken", BROKEN,
              "the verdict is BROKEN, because the tests failed or the output "
              "differs, and no timing is claimed for it"),
)

PREPARE_REPO = """
export GIT_CONFIG_GLOBAL=/dev/null GIT_CONFIG_NOSYSTEM=1
fixtures="$(dirname -- "$0")/../fixtures"
commit() {{
  git add -A
  git -c user.name=evals -c user.email=evals@example.invalid \\
    commit -q -m "$1"
}}
git init -q -b main .
cp -R "${{fixtures}}/optimise-project/." .
commit "contacts"
"""

COPY_RUN = """
mkdir -p .vibes
printf '*\\n' > .vibes/.gitignore
cp -R "${{fixtures}}/optimise-run/." {run}/
python3 {run}/bench/make_data.py
"""

SCAFFOLD_BASELINE = """#!/usr/bin/env bash
{generated}
#
# A git repository holding contacts on its main branch.

set -euo pipefail
""" + PREPARE_REPO

SCAFFOLD_PLAN = """#!/usr/bin/env bash
{generated}
#
# contacts on main, with the run directory as the baseline left it.

set -euo pipefail
""" + PREPARE_REPO + "mkdir -p {run}" + COPY_RUN

SCAFFOLD_MEASURE = """#!/usr/bin/env bash
{generated}
#
# contacts on main, the candidate on {branch}, and the run directory as the
# baseline left it, with its A/A measurement taken here.

set -euo pipefail
""" + PREPARE_REPO + """
git switch -q -c {branch}
cp "${{fixtures}}/optimise-candidate-{candidate}/dedupe.py" contacts/dedupe.py
commit "Candidate"
git switch -q main
mkdir -p {run}""" + COPY_RUN + """
git worktree add -q --detach {run}/wt/best main
"$(dirname -- "$0")/../../bin/bench" run --out {run}/profile/aa/main \\
  --a {run}/wt/best --b {run}/wt/best --pairs 10 --max-pairs 10 \\
  -- "$(pwd)/{run}/bench/run" '{{tree}}' main >/dev/null
"""

SCAFFOLD_E2E = """#!/usr/bin/env bash
{generated}
#
# A git repository holding contacts on its main branch, with its gate.

set -euo pipefail
""" + PREPARE_REPO

AGENT_PROMPT = """---
max_turns: {turns}
timeout_seconds: {timeout}
runs: {runs}
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, {tools}]
---

Run the `vibes:{agent}` agent, giving it exactly this brief, with `<cwd>`
replaced by the absolute path of your working directory:

```text
{brief}
```

Don't do its work yourself. When it's done, run `git status --porcelain` and
`git branch --show-current` in your working directory, then read this file:

```text
<cwd>/{report}
```

Reply with the agent's reply, then `TREE CLEAN` if `git status --porcelain`
printed nothing or `TREE CHANGED` if it printed anything, then the branch,
then the file's contents, all complete and unchanged, and nothing else.
"""

BASELINE_BRIEF = f"""Mode: baseline
Task: {TASK}
Run directory: <cwd>/{RUN_DIR}
Guides: languages/Python
Commit: main
Answers: the exports have tens of thousands of rows; the tool runs on the
  maintainer's laptop. Install nothing."""

MEASURE_BRIEF = f"""Mode: measure
Task: {TASK}
Run directory: <cwd>/{RUN_DIR}
Guides: languages/Python
Side a: main
Side b: {BRANCH}
Measurement directory: <cwd>/{RUN_DIR}/profile/candidate-1
Noise directory: <cwd>/{RUN_DIR}/profile/aa/main
Test command: scripts/check
Guard rails: rss_kib=10
Install nothing."""

PLAN_BRIEF = f"""Mode: plan
Task: {TASK}
Run directory: <cwd>/{RUN_DIR}
Spec directory: <cwd>/docs/specs/optimise-{SLUG}
Guides: languages/Python
Latest profile: <cwd>/{RUN_DIR}/profile/baseline.md"""

E2E_PROMPT = f"""---
max_turns: 400
timeout_seconds: 10800
runs: 1
allowed_tools: [Read, Glob, Grep, Agent, Write, Edit, {PROFILER_TOOLS}, "Bash(scripts/check*)", "Bash(*/bin/guides-for*)", "Bash(printf *)", "Bash(cp *)", "Bash(git worktree *)"]
---

/vibes:optimise unattended: max 3 {TASK}
"""

TREE_CLEAN = ("---\ntype: regex\npattern: 'TREE CLEAN'\n---\n")


def dispatched(agent: str) -> str:
    return (f"---\ntype: regex\npattern: 'subagent_type\\W+vibes:{agent}'\n"
            "target: trace\n---\n")


def llm(criterion: str) -> str:
    return f"---\ntype: llm\n---\n\nPASS if {criterion}.\nFAIL otherwise.\n"


def build_fixtures() -> None:
    shutil.copytree(PROJECT, FIXTURES / "optimise-project")
    shutil.copytree(RUN, FIXTURES / "optimise-run")
    for candidate in CANDIDATES:
        target = FIXTURES / f"optimise-candidate-{candidate.name}"
        target.mkdir(parents=True)
        (target / "dedupe.py").write_text(candidate.dedupe, encoding="utf-8")


def agent_case(name: str, tags: str, agent: str, brief: str, report: str,
               scaffold: str, graders: Dict[str, str],
               tools: str = PROFILER_TOOLS, runs: int = 3) -> None:
    write_case(name, tags,
               AGENT_PROMPT.format(turns=60, timeout=2400, runs=runs,
                                   tools=tools, agent=agent, brief=brief,
                                   report=report),
               scaffold, {"dispatched": dispatched(agent), **graders})


def build() -> None:
    """Write every optimise fixture and case."""
    build_fixtures()
    agent_case(
        "profiler-finds-hot-spot", "recall, profiler, optimise", "profiler",
        BASELINE_BRIEF, f"{RUN_DIR}/profile/baseline.md",
        SCAFFOLD_BASELINE.format(generated=GENERATED),
        {"tree-clean": TREE_CLEAN,
         "profiled": "---\ntype: regex\npattern: 'cProfile|pyinstrument|"
                     "py-spy|samply|xctrace|\\bsample\\b'\ntarget: trace\n---\n",
         "finds-it": llm("the profile's hot-spot table ranks _is_seen in "
                         "contacts/dedupe.py first, with most of the time, "
                         "and the reply or the profile gives a noise floor "
                         "from an A/A run")},
        runs=1)
    for candidate in CANDIDATES:
        agent_case(
            f"profiler-measures-{candidate.name}",
            "recall, profiler, optimise", "profiler", MEASURE_BRIEF,
            f"{RUN_DIR}/profile/candidate-1/report.md",
            SCAFFOLD_MEASURE.format(generated=GENERATED, run=RUN_DIR,
                                    branch=BRANCH, candidate=candidate.name),
            {"tree-clean": TREE_CLEAN, "verdict": llm(candidate.expected)},
            runs=1)
    agent_case(
        "optimiser-plans-by-profile", "precision, optimiser, optimise",
        "optimiser", PLAN_BRIEF, f"{RUN_DIR}/optimise-plan.md",
        SCAFFOLD_PLAN.format(generated=GENERATED, run=RUN_DIR),
        {"tree-clean": TREE_CLEAN,
         "targets-hot-spot": llm(
             "the top-ranked candidate replaces the scan of the list of "
             "seen addresses in _is_seen with a set or dict lookup, and no "
             "candidate targets header() in contacts/summary.py or any "
             "code the profile gives under 2% of the time")},
        tools='"Bash(git *)"')
    write_case(
        "optimise-speeds-up-dedupe", "optimise-e2e", E2E_PROMPT,
        SCAFFOLD_E2E.format(generated=GENERATED),
        {"profiled": dispatched("profiler"),
         "optimised": dispatched("optimiser"),
         "rebuilt": dispatched("builder"),
         "decided": "---\ntype: regex\npattern: 'bin/bench\\W+verdict'\n"
                    "target: trace\n---\n",
         "no-push": "---\ntype: regex\npattern: 'git push'\ntarget: trace\n"
                    "match: not_contains\n---\n",
         "reports-gain": llm(
             "the final report shows dedupe measured faster than the "
             "baseline after the rebuild, lists each attempt with its "
             "verdict, and names the optimise/dedupe branch and its "
             "commits")})
