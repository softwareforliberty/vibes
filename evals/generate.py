"""Generate the reviewer eval fixtures and cases.

Every reviewer case reviews the same change to a small Python library: a
low-stock report. The clean version of the change follows the spec, the
design and the Python guides. Each defect variant seeds one kind of problem
into it, for the reviewer whose area it is.

The panel cases check that the main agent picks the review panel from what
a change contains, as the vibe skill's rules say.

Run it from anywhere after changing the fixtures or the cases below:

    python3 evals/generate.py

It rewrites evals/fixtures/ and every generated case directory, and needs
git on the PATH to produce each fixture's diff.
"""

# The edits quote lines of the fixtures exactly, so some are longer than the
# line limit.
# ruff: noqa: E501

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

EVALS = Path(__file__).resolve().parent
GUIDES_FOR = EVALS.parent / "bin" / "guides-for"
BASE = EVALS / "source" / "base"
CHANGE = EVALS / "source" / "change"
FIXTURES = EVALS / "fixtures"

TASK = "Add a low-stock report to the stock library, as docs/spec.md describes."
# The round directory, where the plugin's hook lets a reviewer write its
# findings file.
REVIEW = ".vibes/stock/review/round-1"


@dataclass(frozen=True)
class Edit:
    """Replace one exact piece of text in one file of the clean change."""

    path: str
    old: str
    new: str


@dataclass(frozen=True)
class Variant:
    """A version of the change, and the cases that review it."""

    name: str
    edits: tuple[Edit, ...]


@dataclass(frozen=True)
class Case:
    """One reviewer reviewing one variant."""

    reviewer: str
    variant: str
    phase: str
    finding: str | None
    tags: tuple[str, ...]

    @property
    def name(self) -> str:
        """Name the case after the reviewer and what it should conclude."""
        if self.finding is None:
            return f"{self.reviewer}-approves-clean"
        return f"{self.reviewer}-finds-{self.variant}"


READS_ONCE_TEST = """def test_reads_the_database_once(
    service: StockService,
    connection: sqlite3.Connection,
) -> None:
    statements: list[str] = []
    connection.set_trace_callback(statements.append)

    service.low_stock(5, page=1, page_size=3)

    assert len(statements) == 1


"""

CLOSE_TEST = """


def test_export_closes_the_file_when_writing_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    opened: list[TextIOWrapper] = []
    real_open = Path.open

    def recording_open(
        path: Path,
        mode: Literal["w"],
        *,
        newline: str,
        encoding: str,
    ) -> TextIOWrapper:
        file = real_open(path, mode, newline=newline, encoding=encoding)
        opened.append(file)
        return file

    def failing_items() -> Iterator[Item]:
        yield Item("C3", "Chain", 1)
        raise OSError("disk full")

    monkeypatch.setattr(Path, "open", recording_open)

    with pytest.raises(OSError, match="disk full"):
        export_low_stock_csv(failing_items(), tmp_path / "low.csv")
    assert opened[0].closed
"""

VARIANTS = (
    Variant("clean", ()),
    Variant(
        "threshold-boundary",
        (
            Edit(
                "src/stock/repository.py",
                '" WHERE quantity < ? AND instr(casefold(name), ?) > 0"',
                '" WHERE quantity <= ? AND instr(casefold(name), ?) > 0"',
            ),
            Edit(
                "tests/test_low_stock.py",
                """def test_excludes_items_at_the_threshold(service: StockService) -> None:
    assert [item.sku for item in service.low_stock(3)] == ["E5", "C3"]


""",
                "",
            ),
            Edit(
                "tests/test_low_stock.py",
                """def test_returns_nothing_when_no_item_is_low(service: StockService) -> None:
    assert service.low_stock(0) == []


""",
                "",
            ),
        ),
    ),
    Variant(
        "sql-injection",
        (
            Edit(
                "src/stock/repository.py",
                """        rows = self._connection.execute(
            "SELECT sku, name, quantity FROM item"
            " WHERE quantity < ? AND instr(casefold(name), ?) > 0"
            " ORDER BY quantity, sku LIMIT ? OFFSET ?",
            (threshold, needle, limit, offset),
        ).fetchall()""",
                """        rows = self._connection.execute(
            "SELECT sku, name, quantity FROM item"
            f" WHERE quantity < {threshold} AND instr(casefold(name), '{needle}') > 0"
            f" ORDER BY quantity, sku LIMIT {limit} OFFSET {offset}",
        ).fetchall()""",
            ),
        ),
    ),
    Variant(
        "unclosed-file",
        (
            Edit(
                "src/stock/report.py",
                """    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["sku", "name", "quantity"])
        for item in items:
            writer.writerow(
                [_neutralise(item.sku), _neutralise(item.name), item.quantity]
            )""",
                """    file = path.open("w", newline="", encoding="utf-8")
    writer = csv.writer(file)
    writer.writerow(["sku", "name", "quantity"])
    for item in items:
        writer.writerow([_neutralise(item.sku), _neutralise(item.name), item.quantity])
    file.close()""",
            ),
            Edit(
                "tests/test_low_stock.py",
                CLOSE_TEST,
                "\n",
            ),
            Edit(
                "tests/test_low_stock.py", "from collections.abc import Iterator\n", ""
            ),
            Edit("tests/test_low_stock.py", "from io import TextIOWrapper\n", ""),
            Edit("tests/test_low_stock.py", "from typing import Literal\n", ""),
        ),
    ),
    Variant(
        "query-per-item",
        (
            Edit(
                "tests/test_low_stock.py",
                READS_ONCE_TEST,
                "",
            ),
            Edit("tests/test_low_stock.py", "import sqlite3\n", ""),
            Edit(
                "src/stock/repository.py",
                '''        rows = self._connection.execute(
            "SELECT sku, name, quantity FROM item"''',
                '''        rows = self._connection.execute(
            "SELECT sku FROM item"''',
            ),
            Edit(
                "src/stock/repository.py",
                "        return [Item(*row) for row in rows]",
                "        return [self.get(sku) for (sku,) in rows]",
            ),
        ),
    ),
    Variant(
        "dead-code",
        (
            Edit(
                "src/stock/service.py",
                "        page_size: int = DEFAULT_PAGE_SIZE,",
                "        page_size: int = 50,",
            ),
            Edit(
                "src/stock/service.py",
                """
DEFAULT_PAGE_SIZE = 50
""",
                "",
            ),
            Edit(
                "src/stock/service.py",
                """class StockService:""",
                """def _clamp_page(page: int, last_page: int) -> int:
    return max(1, min(page, last_page))


class StockService:""",
            ),
            Edit(
                "src/stock/repository.py",
                "        return [Item(*row) for row in rows]",
                """        # items = [Item(row[0], row[1], row[2]) for row in rows]
        return [Item(*row) for row in rows]""",
            ),
        ),
    ),
    Variant(
        "style-breaches",
        (
            Edit(
                "src/stock/service.py",
                """        threshold: int,
        *,
        name_contains: str | None = None,""",
                """        threshold: int,
        name_contains: Optional[str] = None,""",
            ),
            Edit(
                "src/stock/service.py",
                "from dataclasses import replace\n",
                "from dataclasses import replace\nfrom typing import Optional\n",
            ),
            Edit(
                "src/stock/report.py",
                '''    """Write a low-stock report to a CSV file.

    Args:
        items: The items to write, in report order.
        path: The file to write. An existing file is replaced.

    Text that a spreadsheet would run as a formula is written with a
    leading apostrophe, so opening the report can't run anything.
    """
''',
                "",
            ),
        ),
    ),
    Variant(
        "index-loops",
        (
            Edit(
                "src/stock/report.py",
                """        for item in items:
            writer.writerow(
                [_neutralise(item.sku), _neutralise(item.name), item.quantity]
            )""",
                """        rows = list(items)
        for i in range(len(rows)):
            writer.writerow(
                [_neutralise(rows[i].sku), _neutralise(rows[i].name), rows[i].quantity]
            )""",
            ),
            Edit(
                "src/stock/repository.py",
                "        return [Item(*row) for row in rows]",
                """        items = []
        for i in range(len(rows)):
            items.append(Item(rows[i][0], rows[i][1], rows[i][2]))
        return items""",
            ),
        ),
    ),
    Variant(
        "layer-breach",
        (
            Edit(
                "src/stock/service.py",
                """        return self._repository.find_low_stock(
            threshold,
            name_contains=name_contains,
            limit=page_size,
            offset=(page - 1) * page_size,
        )""",
                """        needle = "" if name_contains is None else name_contains.casefold()
        rows = self._repository._connection.execute(
            "SELECT sku, name, quantity FROM item"
            " WHERE quantity < ? AND instr(casefold(name), ?) > 0"
            " ORDER BY quantity, sku LIMIT ? OFFSET ?",
            (threshold, needle, page_size, (page - 1) * page_size),
        ).fetchall()
        return [Item(*row) for row in rows]""",
            ),
        ),
    ),
    Variant(
        "weak-tests",
        (
            Edit(
                "tests/test_low_stock.py",
                """    items = service.low_stock(5)

    assert items == [
        Item("E5", "Bolt cutter", 0),
        Item("C3", "Chain", 1),
        Item("A1", "Anvil", 3),
        Item("B2", "Bolt", 3),
    ]""",
                """    items = service.low_stock(5)

    assert len(items) == 4""",
            ),
            Edit(
                "tests/test_low_stock.py",
                """def test_rejects_a_negative_threshold(service: StockService) -> None:
    with pytest.raises(ValueError, match="threshold must not be negative"):
        service.low_stock(-1)


@pytest.mark.parametrize(
    ("page", "page_size"),
    [(0, 10), (-1, 10), (1, 0), (1, -1)],
)
def test_rejects_pages_below_one(
    service: StockService,
    page: int,
    page_size: int,
) -> None:
    with pytest.raises(ValueError, match="must be at least 1"):
        service.low_stock(5, page=page, page_size=page_size)


""",
                "",
            ),
            Edit(
                "tests/test_low_stock.py",
                """    with path.open(newline="", encoding="utf-8") as file:
        assert list(csv.reader(file)) == [
            ["sku", "name", "quantity"],
            ["C3", "Chain", "1"],
            ["A1", "Anvil", "3"],
        ]""",
                "    assert path.exists()",
            ),
        ),
    ),
    Variant(
        "missing-requirement",
        (
            Edit(
                "src/stock/service.py",
                """        if threshold < 0:
            raise ValueError("threshold must not be negative")
""",
                "",
            ),
            Edit(
                "src/stock/service.py",
                """            ValueError: If threshold is negative, or page or page_size
                is below 1.""",
                "            ValueError: If page or page_size is below 1.",
            ),
            Edit(
                "tests/test_low_stock.py",
                """def test_rejects_a_negative_threshold(service: StockService) -> None:
    with pytest.raises(ValueError, match="threshold must not be negative"):
        service.low_stock(-1)


""",
                "",
            ),
        ),
    ),
)

FINDINGS = {
    "threshold-boundary": (
        "a finding reports that `find_low_stock` in src/stock/repository.py"
        " includes items whose quantity equals the threshold, because it"
        " compares with `<=` where the spec says below the threshold"
    ),
    "sql-injection": (
        "a finding reports SQL injection in `find_low_stock` in"
        " src/stock/repository.py, because `name_contains` (and the other"
        " values) are formatted into the SQL instead of passed as parameters"
    ),
    "unclosed-file": (
        "a finding reports that `export_low_stock_csv` in src/stock/report.py"
        " leaves the file open when writing raises, because it calls"
        " `close()` itself instead of using `with`"
    ),
    "query-per-item": (
        "a finding reports that `find_low_stock` in src/stock/repository.py"
        " runs one query per matching item (an N+1 query), because it loads"
        " each item with `self.get`"
    ),
    "dead-code": (
        "the findings report at least two of these three: the unused"
        " `_clamp_page` function in src/stock/service.py; the commented-out"
        " code in src/stock/repository.py; and the unnamed literal `50` as"
        " the default `page_size`"
    ),
    "style-breaches": (
        "the findings report at least two of these three: `name_contains` is"
        " no longer keyword-only; `typing.Optional` is used instead of"
        " `str | None`; and the public `export_low_stock_csv` has no"
        " docstring"
    ),
    "index-loops": (
        "the findings report at least one of these: the `range(len(...))`"
        " loop in src/stock/report.py, or the `range(len(...))` loop that"
        " builds a list with `append` in src/stock/repository.py, saying to"
        " loop over the items, or use a comprehension, instead"
    ),
    "layer-breach": (
        "a finding reports that `StockService.low_stock` in"
        " src/stock/service.py runs SQL itself, through the repository's"
        " private `_connection`, instead of going through the repository as"
        " the design says"
    ),
    "weak-tests": (
        "the findings report at least two of these three: the first test"
        " only checks the number of items, not their order; the tests no"
        " longer cover the negative threshold or the page checks (R4, R5);"
        " and the CSV test only checks that the file exists"
    ),
    "missing-requirement": (
        "the COVERAGE or FINDINGS show that R4 (a negative threshold raises"
        " `ValueError`) is not met"
    ),
}

# Defects found by a fixed line in the reviewer's output, checked with a
# regular expression rather than a judge. The spec reviewer's coverage
# lists every id with its status, and the judge misread long coverage
# lists.
PATTERNS = {
    "missing-requirement": r"R4:\s*not met",
}

REVIEWERS = (
    ("bug-reviewer", "threshold-boundary", "spike"),
    ("security-reviewer", "sql-injection", "spike"),
    ("resource-leak-reviewer", "unclosed-file", "spike"),
    ("performance-reviewer", "query-per-item", "spike"),
    ("cleanliness-reviewer", "dead-code", "spike"),
    ("style-reviewer", "style-breaches", "spike"),
    ("idioms-reviewer", "index-loops", "spike"),
    ("architecture-reviewer", "layer-breach", "spike"),
    ("test-reviewer", "weak-tests", "rebuild"),
    ("spec-reviewer", "missing-requirement", "spike"),
)

CASES = tuple(
    case
    for reviewer, variant, phase in REVIEWERS
    for case in (
        Case(reviewer, variant, phase, FINDINGS[variant], ("recall", reviewer)),
        Case(reviewer, "clean", phase, None, ("precision", reviewer)),
    )
)


@dataclass(frozen=True)
class PanelCase:
    """The panel for the first rebuild review of a medium task's change."""

    name: str
    files: tuple[str, ...]
    panel: tuple[str, ...]


ALL_REVIEWERS = tuple(sorted(reviewer for reviewer, _, _ in REVIEWERS))

PANEL_CASES = (
    PanelCase(
        "python",
        ("src/stock/report.py", "tests/test_report.py", "docs/specs/low-stock/spec.md"),
        ALL_REVIEWERS,
    ),
    PanelCase(
        "config",
        ("config/settings.yaml", "config/limits.toml"),
        tuple(
            r
            for r in ALL_REVIEWERS
            if r not in {"performance-reviewer", "resource-leak-reviewer"}
        ),
    ),
    PanelCase(
        "container",
        ("Dockerfile", ".github/workflows/ci.yaml"),
        tuple(r for r in ALL_REVIEWERS if r != "resource-leak-reviewer"),
    ),
    PanelCase(
        "migration",
        ("migrations/001_add_reorder_level.sql", "docs/specs/reorder/spec.md"),
        tuple(r for r in ALL_REVIEWERS if r != "resource-leak-reviewer"),
    ),
    PanelCase(
        "docs",
        ("README.md", "docs/usage.md"),
        ("security-reviewer", "spec-reviewer"),
    ),
)

GENERATED = "# Generated by evals/generate.py: edit that, not this file."

PROMPT = """---
max_turns: 12
timeout_seconds: 900
runs: 3
allowed_tools: [Read, Glob, Grep, Agent]
---

Run the `vibes:{reviewer}` agent on a change, giving it exactly this brief,
with `<cwd>` replaced by the absolute path of your working directory:

```text
Task: {task}
Spec: <cwd>/docs/spec.md
Design: <cwd>/docs/design.md
Review directory: <cwd>/{review}
Phase: {phase}
Guides: languages/Python
Round: 1
```

Don't review the change yourself. When the agent is done, read the file it
writes its review to:

```text
<cwd>/{review}/findings-{reviewer}.md
```

Reply with the agent's reply, then the file's contents, both complete and
unchanged, and nothing else.
"""

SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# Copy this case's fixture into the run's working directory.

set -euo pipefail

cp -R "$(dirname -- "$0")/../fixtures/{variant}/." .
"""


PANEL_PROMPT = """---
max_turns: 8
timeout_seconds: 300
runs: 3
allowed_tools: [Read, Glob, Grep]
---

`SKILL.md` in your working directory is the vibes workflow skill. You're its
main agent, about to start round 1 of the `rebuild` review of a medium task,
which has a design. `files.txt` lists the files the change touches, and
`guides.txt` is what `guides-for` printed for them. Following the skill's
rules for the review panel, decide which reviewers run. Don't run any.

Reply with one line: `PANEL:` and then the reviewers' names without the
`vibes:` prefix, in alphabetical order, separated by ", ".
"""

PANEL_SCAFFOLD = """#!/usr/bin/env bash
{generated}
#
# Copy the vibe skill and this case's change into the run's working
# directory.

set -euo pipefail

here="$(dirname -- "$0")"
cp "${{here}}/../../skills/vibe/SKILL.md" .
cp -R "${{here}}/../fixtures/panel-{name}/." .
"""


def build_clean(target: Path) -> None:
    """Lay out the project with the clean change applied."""
    shutil.copytree(BASE, target)
    shutil.copytree(CHANGE, target, dirs_exist_ok=True)


def apply(edits: tuple[Edit, ...], root: Path) -> None:
    """Apply each edit, checking its text appears exactly once."""
    for edit in edits:
        path = root / edit.path
        text = path.read_text(encoding="utf-8")
        count = text.count(edit.old)
        if count != 1:
            raise ValueError(f"{edit.path}: expected 1 match, found {count}")
        path.write_text(text.replace(edit.old, edit.new), encoding="utf-8")


def git(root: Path, *args: str) -> str:
    """Run git in root and return its output."""
    # Every argument comes from this script, never from outside input.
    return subprocess.run(  # noqa: S603
        ["git", "-c", "core.autocrlf=false", *args],  # noqa: S607
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def build_fixture(variant: Variant) -> None:
    """Write a variant's project and its review directory."""
    target = FIXTURES / variant.name
    with tempfile.TemporaryDirectory() as temporary:
        work = Path(temporary) / "work"
        shutil.copytree(BASE, work)
        git(work, "init", "--quiet")
        git(work, "add", ".")
        git(
            work,
            "-c",
            "user.name=evals",
            "-c",
            "user.email=evals@example.invalid",
            "commit",
            "--quiet",
            "--message=Base",
        )
        shutil.copytree(CHANGE, work, dirs_exist_ok=True)
        apply(variant.edits, work)
        git(work, "add", ".")
        diff = git(work, "diff", "--cached", "--no-color")
        files = git(work, "diff", "--cached", "--name-only")
        shutil.rmtree(work / ".git")
        shutil.copytree(work, target)
    review = target / REVIEW
    review.mkdir(parents=True)
    (review / "diff.patch").write_text(diff, encoding="utf-8")
    (review / "files.txt").write_text(files, encoding="utf-8")


def write_case(case: Case) -> None:
    """Write a case's definition, prompt, graders and scaffold script."""
    directory = EVALS / case.name
    graders = directory / "graders"
    graders.mkdir(parents=True)
    tags = ", ".join(case.tags)
    (directory / "case.yaml").write_text(
        f"{GENERATED}\n"
        'schema_version: "1.1"\n'
        f"name: {case.name}\n"
        f"tags: [{tags}]\n"
        "context:\n"
        "  scaffold_script: scaffold.sh\n",
        encoding="utf-8",
    )
    (directory / "prompt.md").write_text(
        PROMPT.format(
            reviewer=case.reviewer, task=TASK, phase=case.phase, review=REVIEW
        ),
        encoding="utf-8",
    )
    scaffold = directory / "scaffold.sh"
    scaffold.write_text(
        SCAFFOLD.format(generated=GENERATED, variant=case.variant),
        encoding="utf-8",
    )
    scaffold.chmod(0o755)
    (graders / "dispatched.md").write_text(
        "---\n"
        "type: regex\n"
        f"pattern: 'subagent_type\\W+vibes:{case.reviewer}'\n"
        "target: trace\n"
        "---\n",
        encoding="utf-8",
    )
    verdict = "APPROVED" if case.finding is None else "CHANGES REQUESTED"
    (graders / "verdict.md").write_text(
        f"---\ntype: regex\npattern: 'VERDICT:\\s*{verdict}'\n---\n",
        encoding="utf-8",
    )
    if case.finding is None:
        (graders / "no-major-findings.md").write_text(
            "---\n"
            "type: regex\n"
            "pattern: '\\[(BLOCKER|MAJOR)\\]'\n"
            "match: not_contains\n"
            "---\n",
            encoding="utf-8",
        )
    elif case.variant in PATTERNS:
        (graders / "finds-defect.md").write_text(
            f"---\ntype: regex\npattern: '{PATTERNS[case.variant]}'\nflags: i\n---\n",
            encoding="utf-8",
        )
    else:
        (graders / "finds-defect.md").write_text(
            f"---\ntype: llm\n---\n\nPASS if {case.finding}.\n"
            "FAIL if no finding reports it.\n",
            encoding="utf-8",
        )


def build_panel_fixture(case: PanelCase) -> None:
    """Write a panel case's file list, and what guides-for prints for it."""
    target = FIXTURES / f"panel-{case.name}"
    target.mkdir()
    with tempfile.TemporaryDirectory() as temporary:
        for path in case.files:
            (Path(temporary) / path).parent.mkdir(parents=True, exist_ok=True)
            (Path(temporary) / path).touch()
        # The paths come from this script, never from outside input.
        guides = subprocess.run(  # noqa: S603
            [GUIDES_FOR, *case.files],
            cwd=temporary,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    (target / "files.txt").write_text("\n".join(case.files) + "\n", encoding="utf-8")
    (target / "guides.txt").write_text(guides, encoding="utf-8")


def write_panel_case(case: PanelCase) -> None:
    """Write a panel case's definition, prompt, grader and scaffold script."""
    directory = EVALS / f"panel-{case.name}"
    graders = directory / "graders"
    graders.mkdir(parents=True)
    (directory / "case.yaml").write_text(
        f"{GENERATED}\n"
        'schema_version: "1.1"\n'
        f"name: panel-{case.name}\n"
        "tags: [panel]\n"
        "context:\n"
        "  scaffold_script: scaffold.sh\n",
        encoding="utf-8",
    )
    (directory / "prompt.md").write_text(PANEL_PROMPT, encoding="utf-8")
    scaffold = directory / "scaffold.sh"
    scaffold.write_text(
        PANEL_SCAFFOLD.format(generated=GENERATED, name=case.name),
        encoding="utf-8",
    )
    scaffold.chmod(0o755)
    # The whole list, ended by anything but another name, so a reviewer
    # added or left out fails.
    panel = ", ".join(case.panel)
    (graders / "panel.md").write_text(
        f"---\ntype: regex\npattern: 'PANEL:\\s*{panel}(?![\\w,-])'\n---\n",
        encoding="utf-8",
    )


def remove_generated() -> None:
    """Delete the fixtures and every case this script wrote before."""
    shutil.rmtree(FIXTURES, ignore_errors=True)
    for case_file in EVALS.glob("*/case.yaml"):
        if case_file.read_text(encoding="utf-8").startswith(GENERATED):
            shutil.rmtree(case_file.parent)


def main() -> None:
    """Regenerate the fixtures and the cases."""
    remove_generated()
    FIXTURES.mkdir()
    for variant in VARIANTS:
        build_fixture(variant)
    for case in CASES:
        write_case(case)
    for panel_case in PANEL_CASES:
        build_panel_fixture(panel_case)
        write_panel_case(panel_case)


if __name__ == "__main__":
    main()
