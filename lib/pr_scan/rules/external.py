"""Scanners the scan runs when they're installed: gitleaks, for secrets."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import Iterator

from ..escape import ascii_only
from ..gitio import environment
from ..model import HIGH, INFO, Context, Finding


def check(ctx: Context) -> Iterator[Finding]:
    gitleaks = shutil.which("gitleaks")
    if gitleaks is None:
        yield Finding(INFO, "external-not-run", "(scan)", 0,
                      "gitleaks isn't installed, so secrets were checked "
                      "only by the scan's own rules")
        return
    with tempfile.TemporaryDirectory() as scratch:
        report = os.path.join(scratch, "gitleaks.json")
        result = subprocess.run(  # noqa: S603
            [gitleaks, "git", "--no-banner", "--redact",
             f"--log-opts={ctx.base}..{ctx.head}", "--report-format=json",
             f"--report-path={report}", "--exit-code=0", ctx.git.repo],
            env=environment(), stdin=subprocess.DEVNULL, capture_output=True,
            check=False, timeout=600,
        )
        if result.returncode != 0 or not os.path.exists(report):
            yield Finding(INFO, "external-not-run", "(scan)", 0,
                          "gitleaks failed, so secrets were checked only by "
                          "the scan's own rules")
            return
        with open(report, encoding="utf-8") as stream:
            leaks = json.load(stream) or []
    for leak in leaks:
        yield Finding(HIGH, "external-gitleaks", str(leak.get("File", "")),
                      int(leak.get("StartLine") or 0),
                      f"gitleaks found a secret "
                      f"({ascii_only(str(leak.get('RuleID', '')), 40)}) in "
                      f"commit {ascii_only(str(leak.get('Commit', ''))[:12])}")
