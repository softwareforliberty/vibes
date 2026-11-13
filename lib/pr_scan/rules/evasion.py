"""Code that behaves differently when watched: time bombs, environment and
process checks, and anti-debugging. XZ's backdoor checked it ran inside
sshd, and stayed quiet otherwise."""

from __future__ import annotations

from typing import Iterator

from ..model import HIGH, REVIEW, Context
from .common import added, matching, regex

TIME_BOMB = regex(
    r"\btime\s*\(\s*(?:NULL|0|nullptr)?\s*\)\s*[<>]=?\s*\d{9,}",
    r"\d{9,}\s*[<>]=?\s*time\s*\(",
    r"\b(?:datetime|date)\.(?:now|today|utcnow)\(\)[^;\n]*[<>]=?",
    r"\bDate\.now\(\)\s*[<>]=?\s*\d", r"\bnew Date\(\)\s*[<>]",
    r"\bdate\s+\+%[sYmd][^|]*\)?\s*.*-(?:gt|lt|ge|le)\b",
    r"\btime\.Now\(\)\.(?:After|Before)\(",
    r"\b(?:tm_year|tm_mon|tm_mday|getFullYear\(\)|getMonth\(\))\s*[<>=!]=?\s*\d",
    r"\bSystemTime::now\(\)")
ENVIRONMENT = regex(
    r"getenv\s*\(\s*\"(?:CI|GITHUB_ACTIONS|TRAVIS|JENKINS_URL|BUILDKITE|"
    r"GITLAB_CI|CIRCLECI|TF_BUILD|VALGRIND\w*|LD_PRELOAD|TERM|LANG|DISPLAY|"
    r"SSH_\w+|USER|LOGNAME|HOME|container)\"",
    r"environ(?:\.get)?\s*[\[(]\s*[\"'](?:CI|GITHUB_ACTIONS|USER|LOGNAME|"
    r"SSH_\w+|TERM)[\"']", r"process\.env\.(?:CI|GITHUB_ACTIONS|USER)\b",
    r"\[\s*-[nz]\s+\"?\$\{?(?:CI|GITHUB_ACTIONS|TRAVIS|BUILDKITE)\b",
    r"\bgethostname\s*\(", r"\bsocket\.gethostname\(", r"\bos\.hostname\(",
    r"\buname\s*\(", r"\bgetlogin\s*\(", r"\bgetuid\s*\(\s*\)\s*[!=]=",
    r"\bgetpwuid\s*\(", r"/\.dockerenv", r"/proc/1/cgroup")
ANTI_DEBUG = regex(r"\bPTRACE_TRACEME\b", r"\bTracerPid\b",
                   r"\bIsDebuggerPresent\b", r"\bCheckRemoteDebuggerPresent\b",
                   r"\bRUNNING_ON_VALGRIND\b", r"\bvalgrind\b",
                   r"\b__sanitizer_\w+", r"\bsysctl\b.*\bP_TRACED\b",
                   r"\bLD_AUDIT\b", r"/proc/self/status", r"\bgdb\b",
                   r"\bstrace\b", r"\bfrida\b", r"\bdebugger\s*;")
PROCESS = regex(r"\bargv\s*\[\s*0\s*\][^;\n]*(?:strcmp|==|strstr|endswith)",
                r"(?:strcmp|strstr|==)[^;\n]*\bargv\s*\[\s*0\s*\]",
                r"/proc/self/(?:exe|cmdline|comm)\b",
                r"\bprogram_invocation(?:_short)?_name\b", r"\bgetprogname\(",
                r"\"(?:sshd|sudo|login|systemd|su|passwd|init)\"")


def check(ctx: Context) -> Iterator:
    code = [line for line in added(ctx, "source", "build", "ci")
            if "test" not in line[0].classes]
    yield from matching(code, TIME_BOMB, HIGH, "evasion-time",
                        "behaviour that depends on the date, as a time "
                        "bomb's does")
    yield from matching(code, ENVIRONMENT, REVIEW, "evasion-environment",
                        "behaviour that depends on where it runs")
    yield from matching(code, ANTI_DEBUG, HIGH, "evasion-anti-debug",
                        "checks whether it's being debugged or traced")
    yield from matching(code, PROCESS, HIGH, "evasion-process",
                        "checks which program it's running in, as XZ's "
                        "backdoor checked for sshd")
