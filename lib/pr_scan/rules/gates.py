"""Weakened checks: feature probes, suppressions, ignore lists, skipped or
deleted tests, removed hardening and bypassed verification."""

from __future__ import annotations

import re
from typing import Iterator, List, Set, Tuple

from ..escape import excerpt
from ..model import HIGH, REVIEW, Context, Finding
from .common import added, matching, regex, removed

# Feature-detection probes: XZ disabled Landlock with a stray "." in one.
PROBE = regex(r"\bcheck_(?:c|cxx)_source_(?:compiles|runs)\b",
              r"\bcheck_(?:include_files?|symbol_exists|function_exists|"
              r"type_size|struct_has_member|prototype_definition)\b",
              r"\btry_(?:compile|run)\b",
              r"\bAC_(?:COMPILE|LINK|RUN|PREPROC)_IFELSE\b",
              r"\bAC_(?:CHECK_(?:FUNCS?|HEADERS?|DECLS?|LIB|TYPES?|MEMBERS?)|"
              r"SEARCH_LIBS|TRY_(?:COMPILE|LINK|RUN))\b",
              r"\b(?:cc|cxx|compiler)\.(?:compiles|links|run|has_function|"
              r"has_header|has_header_symbol|check_header|has_argument|"
              r"get_define)\s*\(",
              flags=re.IGNORECASE)
PROBE_SPAN = 40
SUPPRESSION = regex(
    r"\bnoqa\b", r"\bNOLINT", r"\bnosec\b", r"eslint-disable",
    r"shellcheck\s+disable", r"#!?\[allow\(", r"@SuppressWarnings",
    r"type:\s*ignore", r"pylint:\s*disable", r"//\s*nolint", r"rubocop:disable",
    r"swiftlint:disable", r"clang-format\s+off", r"#\s*pragma\s+(?:GCC|clang)\s+"
    r"diagnostic\s+ignored", r"@ts-(?:ignore|expect-error|nocheck)",
    r"istanbul\s+ignore", r"pragma:\s*no\s*cover", r"\bNOSONAR\b",
    r"gitleaks:allow", r"trivy:ignore", r"\bnosemgrep\b", r"\bnoopengrep\b",
    r"\bskipcq\b", r"lgtm\s*\[", r"codeql\[", r"\bphpcs:ignore", r"@phpstan-",
    r"\bcoverity\[", r"\bNOLINTNEXTLINE\b")
SKIP = regex(r"@pytest\.mark\.(?:skip|xfail)", r"\bunittest\.skip",
             r"\bpytest\.skip\(", r"@(?:Ignore|Disabled)\b",
             r"\b(?:it|describe|test)\.(?:skip|only|todo)\(",
             r"\bx(?:it|describe|test)\(", r"\bt\.Skip(?:Now|f)?\(",
             r"#\[ignore\]", r"^\s*skip(?:\s|$)", r"\bGTEST_SKIP\b",
             r"\bDISABLED_\w+", r"\bself\.skipTest\(", r"\bt\.skip\(")
ASSERT = re.compile(r"\bassert|\bexpect\(|\b(?:ASSERT|EXPECT)_|\bassert_\w+|"
                    r"\[\s*\"?\$(?:status|output)|\brefute\b|\bshould\b|"
                    r"\bt\.(?:Error|Fatal)|\bcheck\(|\bREQUIRE\(", re.IGNORECASE)
HARDENING = re.compile(r"-fstack-protector[\w-]*|-D_FORTIFY_SOURCE=[1-3]|"
                       r"-fPIE\b|-fpie\b|(?<![\w-])-pie\b|-z,?\s*relro|"
                       r"-z,?\s*now|-fcf-protection[\w=-]*|-fsanitize=[\w,-]+|"
                       r"-Werror\b|-fstack-clash-protection|"
                       r"-ftrivial-auto-var-init=\w+|-mbranch-protection=\S+|"
                       r"_GLIBCXX_ASSERTIONS|-Wformat-security|-fno-plt|"
                       r"-Wl,--as-needed|-fzero-call-used-regs=\S+|"
                       r"-fstrict-flex-arrays=\d")
WEAKENING = regex(r"-fno-stack-protector", r"-U_FORTIFY_SOURCE",
                  r"-D_FORTIFY_SOURCE=0", r"-z,?\s*execstack", r"-z,?\s*norelro",
                  r"-z,?\s*lazy", r"(?<![\w-])-no-pie\b", r"-fno-(?:PIE|pie)\b",
                  r"-Wno-error\b", r"-fno-sanitize", r"-fno-stack-clash",
                  r"(?<![\w-])-w(?:\s|$)", r"-fno-cf-protection",
                  r"-Wl,--no-as-needed.*-Wl,--allow-shlib-undefined")
VERIFY = r"(?:sha\d+sum|shasum|b2sum|md5sum|cksum|gpgv?|cosign|minisign|" \
         r"signify|ssh-keygen\s+-Y|check_?sha\w*|verify\w*|cmp|openssl\s+dgst)"
BYPASS = regex(VERIFY + r"\b.*(?:\|\|\s*(?:true|:|exit\s+0)\b|;\s*true\b|"
               r"2>\s*/dev/null\s*\|\|)",
               r"\bset\s+\+e\b",
               r"\bcurl\b.*\s(?:-k|--insecure)\b", r"--no-check-certificate",
               r"GIT_SSL_NO_VERIFY", r"sslVerify\s*=\s*false",
               r"\bverify\s*=\s*False\b", r"NODE_TLS_REJECT_UNAUTHORIZED",
               r"PYTHONHTTPSVERIFY\s*=\s*0", r"InsecureSkipVerify\s*:\s*true",
               r"--trusted-host", r"strict-ssl\s*=?\s*false",
               r"--allow-unauthenticated", r"--nogpgcheck",
               r"gpgcheck\s*=\s*0", r"--skip-verify", r"--no-verify\b",
               r"--insecure-skip-tls-verify", r"CURLOPT_SSL_VERIFY(?:PEER|HOST)"
               r"\s*,\s*0", r"ssl_verify\s*=\s*false", r"check_hostname\s*=\s*"
               r"False", r"CERT_NONE", r"rejectUnauthorized\s*:\s*false",
               r"--disable-content-trust", r"DOCKER_CONTENT_TRUST\s*=\s*0",
               r"--ignore-signatures", r"trusted\s*=\s*yes",
               flags=re.IGNORECASE)
VERIFY_STEP = re.compile(VERIFY + r"\b", re.IGNORECASE)
IGNORE_FILE = re.compile(r"(?:^|/)(?:\.trivyignore|\.gitleaksignore|"
                         r"\.semgrepignore|\.opengrepignore|vulture_whitelist"
                         r"\.py|\.snyk|\.bandit|\.secrets\.baseline|"
                         r"\.osv-scanner\.toml|osv-scanner\.toml|\.grype\.ya?ml|"
                         r"\.nsprc|\.auditignore|deny\.toml|\.cargo-audit\.toml|"
                         r"audit\.toml)\Z")
EXCLUDE = re.compile(r"\b(?:exclude|ignore|skip|disable|allow|per-file-ignores|"
                     r"extend-ignore|whitelist|allowlist|baseline|"
                     r"suppress)\w*\b", re.IGNORECASE)
CORE_GATES = re.compile(r"(?:^|/)scripts/(?:check|audit|check-requirements)\Z")


def check(ctx: Context) -> Iterator[Finding]:
    yield from _probes(ctx)
    yield from matching(added(ctx), SUPPRESSION, REVIEW, "gates-suppression",
                        "silences a check")
    yield from matching(added(ctx, "test"), SKIP, REVIEW, "gates-skip",
                        "skips or narrows tests")
    yield from matching(added(ctx, "build", "ci", "gate", "source"), WEAKENING,
                        HIGH, "gates-hardening-weakened",
                        "turns off a hardening or safety flag")
    yield from _removed_flags(ctx)
    yield from matching(added(ctx), BYPASS, HIGH, "gates-verify-bypassed",
                        "skips or ignores a verification")
    for change, number, text in removed(ctx, "build", "ci", "gate"):
        if VERIFY_STEP.search(text) and not any(
                VERIFY_STEP.search(new) for _, new in change.added()):
            yield Finding(HIGH, "gates-verify-removed", change.path, number,
                          f"removes a verification step: {excerpt(text)}")
    for change in ctx.files:
        if IGNORE_FILE.search(change.path):
            yield Finding(HIGH, "gates-ignore-list", change.path, 0,
                          "a security scanner's ignore list changed")
        elif "gate" in change.classes:
            yield Finding(HIGH if CORE_GATES.search(change.path) else REVIEW,
                          "gates-config", change.path, 0,
                          "a check or its configuration changed")
            for number, text in change.added():
                if EXCLUDE.search(text):
                    yield Finding(REVIEW, "gates-exclusion", change.path,
                                  number, f"adds an exclusion: "
                                  f"{excerpt(text)}")
        if "test" in change.classes and change.deleted and (
                "test-data" not in change.classes):
            yield Finding(REVIEW, "gates-test-deleted", change.path, 0,
                          "a test file is deleted")
    yield from _asserts(ctx)


def _probe_lines(text: str) -> Set[int]:
    lines: Set[int] = set()
    for number, line in enumerate(text.split("\n"), start=1):
        if PROBE.search(line):
            lines.update(range(number, number + PROBE_SPAN))
    return lines


def _probes(ctx: Context) -> Iterator[Finding]:
    for change in ctx.changed("build"):
        new_lines = _probe_lines(change.new_text())
        old_lines = _probe_lines(change.old_text())
        hits: List[Tuple[int, str]] = [
            (number, text) for number, text in change.added()
            if number in new_lines]
        hits += [(number, text) for number, text in change.removed()
                 if number in old_lines]
        for number, text in hits[:1]:
            yield Finding(HIGH, "gates-feature-probe", change.path, number,
                          f"changes a feature-detection probe; one broken "
                          f"character silently turns the feature off, as "
                          f"XZ did to Landlock: {excerpt(text)}")


def _removed_flags(ctx: Context) -> Iterator[Finding]:
    for change in ctx.changed("build", "ci", "gate"):
        before = set(HARDENING.findall(change.old_text()))
        after = set(HARDENING.findall(change.new_text()))
        for flag in sorted(before - after):
            yield Finding(HIGH, "gates-hardening-removed", change.path, 0,
                          f"removes the hardening flag {excerpt(flag)}")


def _asserts(ctx: Context) -> Iterator[Finding]:
    for change in ctx.changed("test"):
        lost = sum(1 for _, text in change.removed() if ASSERT.search(text))
        gained = sum(1 for _, text in change.added() if ASSERT.search(text))
        if lost > gained:
            yield Finding(REVIEW, "gates-asserts-removed", change.path, 0,
                          f"{lost - gained} fewer assertions: check none "
                          f"was weakened")
