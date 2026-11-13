"""New hosts, IP literals, reverse shells, new network use and reads of
secrets: the ways a change can phone home or leak."""

from __future__ import annotations

import ipaddress
import re
from typing import Iterator, List, Set

from ..escape import excerpt
from ..model import HIGH, REVIEW, Context, Finding, matches
from .common import added, hosts, matching, regex, severity_for

IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?![\w.])")
REVERSE_SHELL = regex(r"/dev/(?:tcp|udp)/", r"\bnc\b.*\s-[a-z]*e\b",
                      r"\bncat\b.*--exec|\bncat\b.*-e\b", r"\bsocat\b.*exec:",
                      r"\bmkfifo\b.*\|\s*(?:ba)?sh", r"\bsh\s+-i\b.*[<>]&",
                      r"\bpty\.spawn\(", r"\btelnet\b.*\|\s*(?:ba)?sh")
NETWORK_USE = re.compile(
    r"\bsocket\s*\(|\bconnect\s*\(|\bgetaddrinfo\b|\bgethostbyname\b|"
    r"\burllib\b|\brequests\.\w+\(|\bhttp\.client\b|\bfetch\s*\(|"
    r"\bXMLHttpRequest\b|\bnet\.Dial\b|\bhttp\.(?:Get|Post)\b|\bTcpStream\b|"
    r"\bUdpSocket\b|\bcurl_easy_\w+|\breqwest::|\bhyper::|\bWebSocket\b|"
    r"\bsendto\s*\(|\bres_query\b|\bnslookup\b|\bdig\s+\S|\bhost\s+-t\b")
SECRETS = regex(r"~/\.ssh|\$HOME/\.ssh|\.ssh/id_\w+|/etc/shadow\b",
                r"/etc/sudoers\b", r"\.aws/credentials", r"\.netrc\b",
                r"\.git-credentials", r"\.docker/config\.json",
                r"\.kube/config", r"\.config/gh/hosts", r"\.gnupg/",
                r"\.password-store", r"Library/Keychains",
                r"/proc/self/environ", r"/proc/\d+/(?:mem|environ|maps)",
                r"\b(?:GITHUB|GH|NPM|PYPI|ANTHROPIC|OPENAI|AWS_SECRET|"
                r"GOOGLE|AZURE|CARGO_REGISTRY|DOCKER|SLACK|DISCORD)_\w*"
                r"(?:TOKEN|KEY|SECRET|PASSWORD)\b",
                r"\bsecurity\s+find-generic-password\b",
                r"\bos\.environ\s*\)|\bdict\(os\.environ\)|"
                r"\bprocess\.env\s*\)|JSON\.stringify\(process\.env\)",
                r"\benv\s*\|\s*(?:curl|nc|base64)", r"\bprintenv\s*\|")
SAFE_HOSTS = {"localhost", "example.com", "example.org", "example.net",
              "github.com", "www.gnu.org", "gnu.org", "opensource.org",
              "spdx.org", "www.apache.org", "creativecommons.org", "semver.org",
              "keepachangelog.com", "www.w3.org", "w3.org"}


def public(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_global and not str(ip).startswith(("192.0.2.", "198.51.100.",
                                                    "203.0.113."))


def check(ctx: Context) -> Iterator[Finding]:
    risky = ("build", "ci", "source", "gate", "agent-config")
    new_hosts: Set[str] = set()
    for change, number, text in added(ctx):
        for host in hosts(text):
            if host in SAFE_HOSTS or host in new_hosts or matches(
                    host, ctx.config.allowed_hosts):
                continue
            new_hosts.add(host)
            if not ctx.git.grep(ctx.base, host):
                yield Finding(severity_for(change, risky, REVIEW),
                              "network-new-host", change.path, number,
                              f"a host the project didn't use before: "
                              f"{excerpt(host, 60)}")
        for address in IPV4.findall(text):
            if public(address):
                yield Finding(severity_for(change, risky, REVIEW),
                              "network-ip-literal", change.path, number,
                              f"a public IP address: {excerpt(address)}")
    yield from matching(added(ctx), REVERSE_SHELL, HIGH,
                        "network-reverse-shell",
                        "the shape of a reverse shell")
    yield from matching((line for line in added(ctx)
                         if "test" not in line[0].classes), SECRETS, HIGH,
                        "network-secrets", "reads credentials or secrets")
    for change in ctx.changed("source", "build"):
        if NETWORK_USE.search(change.old_text()):
            continue
        lines: List = [(n, t) for n, t in change.added()
                       if NETWORK_USE.search(t)]
        if lines:
            number, text = lines[0]
            yield Finding(REVIEW, "network-new-use", change.path, number,
                          f"network access in a file that had none: "
                          f"{excerpt(text)}")
