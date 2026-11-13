"""The scan's rules, one module per family.

Each family exports check(ctx), which yields findings. A finding's rule id
starts with its family's name, such as binary-opaque, so the report and the
supply-chain reviewer can group them.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from ..model import SEVERITIES, Context, Finding
from . import (agentcfg, binary, build, ci, config, deps, encoded, evasion,
               exec_, external, gates, gitattrs, gitlevel, history, hooking,
               injection, network, pins, privilege, unicode)

FAMILIES = (config, binary, build, encoded, unicode, agentcfg, gitattrs,
            gitlevel, gates, pins, deps, ci, hooking, exec_, privilege,
            network, evasion, injection, history, external)
# Findings of one rule in one file beyond this are summed up in one line.
PER_FILE = 5


def run(ctx: Context) -> List[Finding]:
    seen = set()
    counts: Dict[Tuple[str, str], int] = {}
    findings: List[Finding] = []
    for family in FAMILIES:
        for finding in family.check(ctx):
            key = (finding.rule, finding.path, finding.line, finding.message)
            if key in seen:
                continue
            seen.add(key)
            group = (finding.rule, finding.path)
            counts[group] = counts.get(group, 0) + 1
            if counts[group] <= PER_FILE:
                findings.append(finding)
    for (rule, path), count in counts.items():
        if count > PER_FILE:
            severity = min((f.severity for f in findings
                            if f.rule == rule and f.path == path),
                           key=SEVERITIES.index)
            findings.append(Finding(
                severity, rule, path, 0,
                f"{count - PER_FILE} more lines like the ones above"))
    findings.sort(key=lambda f: (SEVERITIES.index(f.severity), f.path,
                                 f.line, f.rule))
    return findings
