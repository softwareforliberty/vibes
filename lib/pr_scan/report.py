"""Builds pr-review.md for the maintainer, and comment-draft.md for them to
edit and post themselves, from scan.md and the reviewers' files.

Reviewer files quote the pull request, so every line is checked against the
findings format, and anything else is escaped and marked. The agent that
runs this sees only the counts it prints, never the report.
"""

from __future__ import annotations

import glob
import os
import re
from collections import Counter
from typing import Dict, List, Tuple

from .escape import ascii_only, visible

VERDICT = re.compile(r"\AVERDICT: (APPROVED|CHANGES REQUESTED)\Z")
FINDING = re.compile(r"\A- \[(BLOCKER|MAJOR|MINOR)\] \S.*\Z")
SCAN_LINE = re.compile(r"\A\[(HIGH|REVIEW|INFO)\] (.*?):(\d+): ([a-z0-9-]+): ")
ACCOUNT = re.compile(r"\A- (?:explained|not cleared|confirmed): \S.*\Z")
UNREVIEWED = re.compile(r"\A- \S.*\Z")
SECTIONS = ("FINDINGS", "SCAN", "UNREVIEWED")
LIMIT = 400
LIMITS = """\
## Limits

- The scan and the reviewers find known tricks. An attacker who knows them
  may write a change that passes every one.
- Nothing here can tell whether an upstream release a pin points at is
  itself malicious. Check new releases and keys by hand.
- Nothing here detects social engineering: pressure to merge, or trust
  built up over years.
- CI may already have run this pull request's code on GitHub.
- A reviewer can be misled by text in the pull request. That's why no
  reviewer can clear a HIGH scan finding, and why the files above must be
  inspected by a person.
"""


def build(out: str) -> int:
    scan = read_scan(out)
    reviews = {os.path.basename(path)[:-3]: read_review(path)
               for path in sorted(glob.glob(os.path.join(out, "review", "*",
                                                         "*.md")))
               if not os.path.basename(path).startswith("responses")}
    head = _first_line(os.path.join(out, "head.txt"))
    base = _first_line(os.path.join(out, "base.txt"))
    with open(os.path.join(out, "pr-review.md"), "w", encoding="utf-8") as f:
        f.write(review_text(base, head, scan, reviews))
    with open(os.path.join(out, "comment-draft.md"), "w",
              encoding="utf-8") as f:
        f.write(comment_text(scan, reviews))
    severities = Counter(severity for severity, *_ in scan)
    print("pr-scan report: scan " + " ".join(
        f"{s} {severities.get(s, 0)}" for s in ("HIGH", "REVIEW", "INFO")))
    for name, review in reviews.items():
        counts = Counter(m.group(1) for m in
                         (FINDING.match(line) for line in review["FINDINGS"])
                         if m)
        print(f"pr-scan report: {ascii_only(name, 40)} "
              f"{review['verdict'] or 'NO VERDICT'}: " + ", ".join(
                  f"{s} {counts.get(s, 0)}"
                  for s in ("BLOCKER", "MAJOR", "MINOR"))
              + (f", {len(review['malformed'])} malformed lines"
                 if review["malformed"] else ""))
    return 0


def _first_line(path: str) -> str:
    if not os.path.exists(path):
        return "unknown"
    with open(path, encoding="ascii") as stream:
        value = stream.readline().strip()
    return value if re.fullmatch(r"[0-9a-f]{40}", value) else "unknown"


def read_scan(out: str) -> List[Tuple[str, str, str, str]]:
    found = []
    with open(os.path.join(out, "scan.md"), encoding="ascii") as stream:
        for line in stream:
            line = line.rstrip("\n")
            match = SCAN_LINE.match(line)
            if match:
                found.append((match.group(1), match.group(2), match.group(4),
                              line))
    return found


def clean(line: str) -> str:
    text = visible(line.rstrip())
    return text if len(text) <= LIMIT else text[:LIMIT - 3] + "..."


def read_review(path: str) -> Dict:
    review: Dict = {"verdict": "", "malformed": [],
                    **{section: [] for section in SECTIONS}}
    section = ""
    with open(path, encoding="utf-8", errors="replace") as stream:
        for raw in stream:
            line = clean(raw)
            if not line.strip():
                continue
            verdict = VERDICT.match(line)
            if verdict and not review["verdict"]:
                review["verdict"] = verdict.group(1)
            elif line in SECTIONS:
                section = line
            elif section == "FINDINGS" and (FINDING.match(line)
                                            or line == "- None."):
                review["FINDINGS"].append(line)
            elif section in ("SCAN", "UNREVIEWED") and line == "- None.":
                continue
            elif section == "SCAN" and ACCOUNT.match(line):
                review["SCAN"].append(line)
            elif section == "UNREVIEWED" and UNREVIEWED.match(line):
                review["UNREVIEWED"].append(line)
            else:
                review["malformed"].append(line)
    return review


def review_text(base: str, head: str, scan, reviews: Dict) -> str:
    lines = ["# Pull request review", "",
             f"- Reviewed: `{base}..{head}`",
             f"- Before merging, check the pull request's head is still "
             f"`{head}`, and merge with "
             f"`gh pr merge --squash --match-head-commit {head}`. If it "
             f"moved, review it again.", "",
             "## Scan findings", "",
             "No reviewer can clear a HIGH finding: each needs a person.", ""]
    for severity in ("HIGH", "REVIEW", "INFO"):
        rows = [line for s, _, _, line in scan if s == severity]
        if rows:
            lines += [f"### {severity}", "", *(f"- {r}" for r in rows), ""]
    if not scan:
        lines += ["None.", ""]
    lines += ["## Reviewers", ""]
    for name, review in reviews.items():
        lines += [f"### {ascii_only(name, 40)}: "
                  f"{review['verdict'] or 'no verdict written'}", ""]
        lines += review["FINDINGS"] or ["- No findings section."]
        if review["SCAN"]:
            lines += ["", "How it accounted for the scan's HIGH findings:", "",
                      *review["SCAN"]]
        if review["malformed"]:
            lines += ["", "Lines not in the findings format, escaped:", "",
                      *(f"    {ascii_only(m, LIMIT)}"
                        for m in review["malformed"])]
        lines.append("")
    must = sorted({path for severity, path, _, _ in scan
                   if severity == "HIGH" and not path.startswith("(")})
    lines += ["## Files a person must inspect", "",
              *(f"- `{path}`" for path in must)]
    if not must:
        lines.append("None from the scan.")
    unreviewed = [line for review in reviews.values()
                  for line in review["UNREVIEWED"]]
    lines += ["", "## Not read in full by a reviewer", "",
              *(unreviewed or ["None reported."]), "", LIMITS]
    return "\n".join(lines)


def comment_text(scan, reviews: Dict) -> str:
    lines = ["<!-- Maintainer note, not part of the comment: this draft is",
             "for you to edit and post yourself. If you suspect the pull",
             "request is malicious, consider leaving out the security",
             "findings, so you don't show an attacker what was caught. -->",
             "", "Thanks for the pull request. A review found the following.",
             ""]
    for name, review in reviews.items():
        findings = [line for line in review["FINDINGS"] if line != "- None."]
        if findings:
            lines += [f"**{ascii_only(name, 40).replace('-', ' ')}**", "",
                      *findings, ""]
    flagged = [line for severity, _, _, line in scan
               if severity in ("HIGH", "REVIEW")]
    if flagged:
        lines += ["**Automated checks** flagged these for a closer look:", "",
                  *(f"- {line}" for line in flagged), ""]
    if len(lines) == 7:
        lines.append("Nothing that needs changing.")
    return "\n".join(lines) + "\n"
