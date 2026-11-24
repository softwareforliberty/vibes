"""tracker's command: reach the project's issue tracker the way its
.vibes-tracker file says, and only as the user approved it.

    tracker check                     is there an approved tracker?
    tracker approve [--allow-program NAME]...
                                      approve it, in your own terminal
    tracker draft                     print a draft for the git remote
    tracker lint <file>               check a draft against the rules
    tracker whoami                    print the user's login
    tracker list                      print each open issue: id, tab, labels
    tracker labels                    print the project's labels
    tracker read <id> --out <file>    save an issue in vibes' format, and
                                      print its id, state and labels
    tracker pr-find <branch>          print the branch's pull request's URL
    tracker closes <id>               print the line that closes an issue
    tracker post <batch file>         run the public operations in a batch

The file, .vibes-tracker at the repository's root, is read from the
default branch, never from the checkout, so a branch can't change what
runs. Each line is a kind, a tab, and its value; # starts a comment:

    issue-id     a regular expression every issue id must match
    closes       the text that closes an issue from a pull request, with {id}
    state-open   the value of read.state that means the issue is open
    token        an environment variable the commands need, such as GH_TOKEN
    host         a host curl may reach
    <operation>  its command: a program and its arguments, with placeholders
    <op>.<field> where a field is in the operation's JSON output

The operations that only read are whoami, list, labels, read, comments
and pr-find; the public ones are comment, label, create-label, close, pr-open,
pr-open-draft and pr-edit, which run only from `tracker post`. A command
is never run by a shell: it can't pipe, redirect or substitute, its
program must be a tracker's own tool, or one the user allowed when
approving, and it can't name a file, except through {body-file}. Each
placeholder fills one whole argument, or part of one, with a value that
is checked first and can't begin with "-". The commands get only PATH,
HOME, the locale, proxies, temporary and configuration directories, and
the token variables the file names.

Field paths are .key for an object's field and [] for each item of a
list, such as .labels[].name. Issues are saved as JSON with id, title,
body, state ("open" or "closed"), labels, url and comments, each comment
with its author and body; nothing an issue says is printed.

Approval is kept in the repository's git directory, never in the
checkout: the file's hash, its text, and any program allowed beyond the
known ones. Any change to the file needs approving again. Approving needs
a terminal, so the user does it in their own; agents have none.

Exits 0; 1 when a command fails or a pull request isn't found; 2 on bad
input or a file that breaks the rules; 3 when the tracker isn't approved
or has changed since; 4 when the project has no .vibes-tracker.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import date
from pathlib import Path
from typing import Any, Sequence

FILE = ".vibes-tracker"
APPROVAL = "vibes-tracker-approved.json"
TEMPLATES = Path(__file__).resolve().parents[2] / "skills" / "tracker" / \
    "templates"
# The tools trackers ship, which a file may run without being allowed one
# by one.
KNOWN_PROGRAMS = ("gh", "glab", "tea", "fj", "berg", "hut", "jira", "acli",
                  "curl")
READ_OPS = ("whoami", "list", "labels", "read", "comments", "pr-find")
PUBLIC_OPS = ("comment", "label", "create-label", "close", "pr-open",
              "pr-open-draft", "pr-edit")
PLACEHOLDERS = {
    "whoami": set(),
    "list": set(),
    "labels": set(),
    "read": {"id"},
    "comments": {"id"},
    "pr-find": {"branch"},
    "comment": {"id", "body-file", "body"},
    "label": {"id", "label"},
    "create-label": {"label", "description", "color"},
    "close": {"id"},
    "pr-open": {"base", "branch", "title", "body-file", "body"},
    "pr-open-draft": {"base", "branch", "title", "body-file", "body"},
    "pr-edit": {"branch", "title", "body-file", "body"},
}
FIELDS = {
    "whoami.login", "list.items", "list.id", "list.labels",
    "labels.items", "labels.name", "read.title",
    "read.body", "read.state", "read.url", "read.labels", "comments.items",
    "comments.author", "comments.body", "comments.skip", "pr-find.url",
}
SETTINGS = {"issue-id", "closes", "state-open", "token", "host"}
REQUIRED = ("issue-id", "closes", "state-open", "whoami", "read",
            "read.title", "read.body", "read.state")
REPEATABLE = {"token", "host"}
# What a command keeps of the environment, besides the tokens.
ENVIRONMENT = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL",
               "LC_CTYPE", "TMPDIR", "TERM", "XDG_CONFIG_HOME",
               "XDG_DATA_HOME", "XDG_CACHE_HOME", "XDG_STATE_HOME",
               "SSL_CERT_FILE", "SSL_CERT_DIR", "HTTP_PROXY", "HTTPS_PROXY",
               "NO_PROXY", "http_proxy", "https_proxy", "no_proxy")
SHELL_WORDS = {"|", "||", "&", "&&", ";", ";;", ">", ">>", "<", "<<", "2>",
               "2>>", "&>", "<<<", "(", ")"}
# curl options that read or write local files, or read another config.
CURL_FILE_OPTIONS = {"-o", "--output", "-O", "--remote-name", "-K",
                     "--config", "-T", "--upload-file", "--netrc-file",
                     "-D", "--dump-header", "-c", "--cookie-jar", "-b",
                     "--cookie", "--trace", "--trace-ascii", "--libcurl",
                     "-E", "--cert", "--key", "--cacert", "--capath",
                     "--output-dir", "-J", "--remote-header-name"}
PLACEHOLDER = re.compile(r"(?<!\{)\{([a-z-]+)\}(?!\})")
# {{ and }} stand for a literal brace, for programs that use braces too.
ESCAPED = re.compile(r"\{\{|\}\}")
# Both at once, so a value filled in is never read for braces.
TOKEN = re.compile(r"\{\{|\}\}|\{([a-z-]+)\}")
PATH_SYNTAX = re.compile(r"^(?:\.|(?:\.[A-Za-z0-9_-]+|\[\])+)$")
URL = re.compile(r"^[a-z]+://([^/:?#@]*)", re.IGNORECASE)
TIMEOUT = 120
MAX_OUTPUT = 20 * 1024 * 1024
MAX_BODY = 64 * 1024


class Refusal(Exception):
    """Something the rules don't allow, or bad input: exit 2."""


class Unapproved(Exception):
    """The tracker isn't approved, or changed since: exit 3."""


class Missing(Exception):
    """The project has no tracker file: exit 4."""


class Failed(Exception):
    """A command failed: exit 1."""


# ── Reading the file ────────────────────────────────────────────────────


class Tracker:
    """A parsed .vibes-tracker."""

    def __init__(self, text: str, extra_programs: Sequence[str] = ()) -> None:
        self.text = text
        self.settings: dict[str, list[str]] = {}
        self.ops: dict[str, list[str]] = {}
        self.fields: dict[str, str] = {}
        self.raw: dict[str, str] = {}
        for number, line in enumerate(text.splitlines(), 1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            kind, tab, value = line.partition("\t")
            kind, value = kind.strip(), value.strip()
            if not tab or not value:
                raise Refusal(f"line {number}: a kind, a tab, then a value")
            seen = kind in self.settings or kind in self.ops \
                or kind in self.fields
            if seen and kind not in REPEATABLE:
                raise Refusal(f"line {number}: {kind} is given twice")
            if kind in SETTINGS:
                self.settings.setdefault(kind, []).append(value)
            elif kind in PLACEHOLDERS:
                self.ops[kind] = self.parse_command(number, kind, value)
                self.raw[kind] = value
            elif kind in FIELDS:
                if not PATH_SYNTAX.match(value):
                    raise Refusal(f"line {number}: {value} isn't a field "
                                  "path such as .labels[].name")
                self.fields[kind] = value
            else:
                raise Refusal(f"line {number}: unknown kind {kind}")
        for kind in REQUIRED:
            if kind not in self.settings and kind not in self.ops \
                    and kind not in self.fields:
                raise Refusal(f"{FILE} has no {kind}")
        try:
            self.id_pattern = re.compile(self.setting("issue-id"))
        except re.error as error:
            raise Refusal(
                f"issue-id isn't a regular expression: {error}") from None
        for name in self.settings.get("token", []):
            if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", name):
                raise Refusal(f"token {name} isn't an environment variable")
        for host in self.settings.get("host", []):
            if not re.fullmatch(r"[A-Za-z0-9.-]+", host):
                raise Refusal(f"host {host} isn't a host name")
        if "{id}" not in self.setting("closes"):
            raise Refusal("closes has no {id}")
        self.extra_programs = tuple(extra_programs)
        for op, argv in self.ops.items():
            self.check_hosts(op, argv)

    def setting(self, kind: str) -> str:
        return self.settings[kind][0]

    def parse_command(self, number: int, op: str, value: str) -> list[str]:
        # Splitting off ( ) ; < > | & where they aren't quoted shows shell
        # syntax even when it's written against a word, as in "list;".
        lexer = shlex.shlex(value, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        lexer.commenters = ""
        try:
            argv = list(lexer)
        except ValueError as error:
            raise Refusal(f"line {number}: {error}") from None
        if not argv:
            raise Refusal(f"line {number}: no command")
        program = argv[0]
        if "/" in program or PLACEHOLDER.search(program) \
                or not re.fullmatch(r"[A-Za-z0-9._-]+", program):
            raise Refusal(f"line {number}: the program must be a plain "
                          f"name, such as gh, not {program}")
        for word in argv[1:]:
            self.check_word(number, op, program, word)
        return argv

    def check_word(self, number: int, op: str, program: str,
                   word: str) -> None:
        where = f"line {number}: {word!r}"
        if word in SHELL_WORDS or "$(" in word or "`" in word \
                or "${" in word:
            raise Refusal(f"{where}: commands run without a shell, so "
                          "there are no pipes, redirections or "
                          "substitutions")
        for name in PLACEHOLDER.findall(word):
            if name not in PLACEHOLDERS[op]:
                raise Refusal(f"{where}: {op} has no {{{name}}}")
        literal = ESCAPED.sub("", PLACEHOLDER.sub("", word))
        if literal.startswith("@") or "=@" in literal or "=<" in literal \
                or literal.lower().startswith("file:") \
                or "file://" in literal.lower():
            raise Refusal(f"{where}: reads a file; only {{body-file}} "
                          "may name one")
        bare = literal.split("=", 1)[-1]
        if bare.startswith(("/", "~")) \
                or ".." in re.split(r"[/=]", literal):
            raise Refusal(f"{where}: names a path; only {{body-file}} may")
        if program == "curl" and literal.split("=", 1)[0] in \
                CURL_FILE_OPTIONS:
            raise Refusal(f"{where}: curl may not read or write files")
        if program == "curl" and re.match(r"^-[A-Za-z]*[oOKTDcbEJ]",
                                          literal) \
                and not literal.startswith("--"):
            raise Refusal(f"{where}: curl may not read or write files")

    def check_hosts(self, op: str, argv: list[str]) -> None:
        if argv[0] != "curl":
            return
        hosts = self.settings.get("host", [])
        urls = 0
        for word in argv[1:]:
            match = URL.match(word)
            if not match:
                continue
            urls += 1
            host = match.group(1)
            if PLACEHOLDER.search(host) or host not in hosts:
                raise Refusal(f"{op}: curl may reach only the hosts the "
                              f"file names, not {host or word}")
            if not word.lower().startswith("https://"):
                raise Refusal(f"{op}: curl must use https, not {word}")
        if urls == 0:
            raise Refusal(f"{op}: curl needs its https address in the "
                          "command, so its host can be checked")

    def programs(self) -> list[str]:
        return sorted({argv[0] for argv in self.ops.values()})

    def unknown_programs(self) -> list[str]:
        return [program for program in self.programs()
                if program not in KNOWN_PROGRAMS]


# ── Where things are ────────────────────────────────────────────────────


def git(*args: str, cwd: Path | None = None) -> str:
    found = subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                           text=True, check=False)
    if found.returncode != 0:
        raise Refusal(found.stderr.strip() or f"git {args[0]} failed")
    return found.stdout


def repository() -> Path:
    try:
        return Path(git("rev-parse", "--show-toplevel").strip())
    except Refusal:
        raise Refusal("not in a git repository") from None


def default_branch(root: Path) -> str:
    """The default branch: where origin's HEAD points, else main or
    master."""
    candidates = []
    try:
        remote = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD",
                     cwd=root).strip()
        candidates.append(remote.split("/", 1)[1])
    except Refusal:
        pass
    candidates += ["main", "master"]
    for branch in candidates:
        try:
            git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}",
                cwd=root)
            return branch
        except Refusal:
            continue
    raise Refusal("can't tell the default branch: no main or master, and "
                  "origin has no HEAD")


def tracker_text(root: Path) -> tuple[str, str]:
    """The file's text on the default branch, and the branch."""
    branch = default_branch(root)
    try:
        return git("show", f"refs/heads/{branch}:{FILE}", cwd=root), branch
    except Refusal:
        raise Missing(f"NO TRACKER: {branch} has no {FILE}") from None


def approval_path(root: Path) -> Path:
    common = Path(git("rev-parse", "--git-common-dir", cwd=root).strip())
    if not common.is_absolute():
        common = root / common
    return common / APPROVAL


def digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def approved_tracker(root: Path) -> Tracker:
    """The tracker, if the user approved exactly this file."""
    text, branch = tracker_text(root)
    path = approval_path(root)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise Unapproved(
            f"NOT APPROVED: {FILE} on {branch} hasn't been approved on this "
            "machine. Run `tracker approve` in your own terminal, from the "
            "repository.") from None
    if record.get("sha256") != digest(text):
        raise Unapproved(
            f"CHANGED: {FILE} on {branch} changed since it was approved on "
            f"{record.get('approved', 'an earlier day')}. Run `tracker "
            "approve` in your own terminal to see the change and approve "
            "it.")
    tracker = Tracker(text, record.get("programs", []))
    unknown = [p for p in tracker.unknown_programs()
               if p not in tracker.extra_programs]
    if unknown:
        raise Unapproved(f"NOT APPROVED: {', '.join(unknown)} isn't allowed")
    return tracker


# ── Running commands ────────────────────────────────────────────────────


def environment(tracker: Tracker) -> dict[str, str]:
    names = list(ENVIRONMENT) + tracker.settings.get("token", [])
    return {name: os.environ[name] for name in names if name in os.environ}


def fill(tracker: Tracker, op: str, values: dict[str, str],
         root: Path) -> list[str]:
    """The operation's argv with its placeholders filled, each value
    checked."""
    argv = tracker.ops.get(op)
    if argv is None:
        raise Refusal(f"{FILE} has no {op}")
    needed = set()
    for word in argv:
        needed |= set(PLACEHOLDER.findall(word))
    if "body" in needed:
        needed.add("body-file")
    checked = {}
    for name in sorted(needed):
        if name not in values:
            raise Refusal(f"{op} needs {name}")
        checked[name] = check_value(tracker, name, values[name], root,
                                    values)
    extra = set(values) - needed - {"body-file"}
    if extra:
        raise Refusal(f"{op} doesn't take {', '.join(sorted(extra))}")
    return [argv[0]] + [TOKEN.sub(
        lambda m: checked[m.group(1)] if m.group(1) else m.group(0)[0], word)
        for word in argv[1:]]


def check_value(tracker: Tracker, name: str, value: str, root: Path,
                values: dict[str, str]) -> str:
    if name == "body":
        value = read_body(values.get("body-file", ""), root)
        if value.startswith("-"):
            raise Refusal("the body can't begin with -")
        return value
    if value.startswith("-"):
        raise Refusal(f"{name} can't begin with -: {value!r}")
    if name == "id":
        if not tracker.id_pattern.fullmatch(value):
            raise Refusal(f"{value!r} isn't an issue id here")
    elif name == "label":
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,49}", value):
            raise Refusal(f"{value!r} isn't a label vibes uses")
    elif name == "color":
        if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
            raise Refusal(f"{value!r} isn't a colour such as 0E8A16")
    elif name in ("title", "description"):
        if not value or len(value) > 256 \
                or any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise Refusal(f"{name} must be one line of at most 256 "
                          "characters")
    elif name in ("branch", "base"):
        found = subprocess.run(["git", "check-ref-format", "--branch",
                                value], cwd=root, capture_output=True,
                               check=False)
        if found.returncode != 0:
            raise Refusal(f"{value!r} isn't a branch name")
    elif name == "body-file":
        return str(body_file(value, root))
    return value


def body_file(value: str, root: Path) -> Path:
    path = (root / value).resolve() if not os.path.isabs(value) \
        else Path(value).resolve()
    allowed = (root / ".vibes").resolve()
    if allowed not in path.parents or not path.is_file():
        raise Refusal(f"{value} must be a file in {root / '.vibes'}")
    if path.stat().st_size > MAX_BODY:
        raise Refusal(f"{value} is over {MAX_BODY // 1024} KB")
    return path


def read_body(value: str, root: Path) -> str:
    return body_file(value, root).read_text(encoding="utf-8")


def run(tracker: Tracker, argv: list[str], root: Path) -> str:
    try:
        found = subprocess.run(argv, cwd=root, env=environment(tracker),
                               stdin=subprocess.DEVNULL,
                               capture_output=True, text=True,
                               timeout=TIMEOUT, check=False)
    except FileNotFoundError:
        raise Failed(f"FAILED: {argv[0]} isn't installed") from None
    except subprocess.TimeoutExpired:
        raise Failed(f"FAILED: {argv[0]} took over {TIMEOUT}s") from None
    if found.returncode != 0:
        tail = "\n".join(found.stderr.strip().splitlines()[-10:])
        raise Failed(f"FAILED: {argv[0]} exited {found.returncode}\n{tail}")
    if len(found.stdout) > MAX_OUTPUT:
        raise Failed("FAILED: the output is too large")
    return found.stdout


def parse_json(text: str, op: str) -> Any:
    try:
        return json.loads(text)
    except ValueError:
        raise Failed(f"FAILED: {op} didn't print JSON") from None


def select(value: Any, path: str) -> list[Any]:
    if path in ("", "."):
        return [value]
    current = [value]
    for key, each in re.findall(r"\.([A-Za-z0-9_-]+)|(\[\])", path):
        following: list[Any] = []
        for item in current:
            if each:
                if isinstance(item, list):
                    following.extend(item)
            elif isinstance(item, dict) and key in item:
                following.append(item[key])
        current = following
    return current


def first_text(value: Any, path: str) -> str:
    found = select(value, path)
    if not found or found[0] is None:
        return ""
    return found[0] if isinstance(found[0], str) else json.dumps(found[0])


def printable(text: str, limit: int = 200) -> str:
    """Text safe to print for the agent: one line, no control
    characters."""
    text = "".join(c for c in text if ord(c) >= 32 and ord(c) != 127)
    return text[:limit]


# ── The commands ────────────────────────────────────────────────────────


def whoami(tracker: Tracker, root: Path) -> str:
    out = run(tracker, fill(tracker, "whoami", {}, root), root)
    if "whoami.login" in tracker.fields:
        login = first_text(parse_json(out, "whoami"),
                           tracker.fields["whoami.login"])
    else:
        login = out.strip().splitlines()[0] if out.strip() else ""
    login = printable(login.strip(), 100)
    if not login:
        raise Failed("FAILED: whoami printed no login")
    return login


def list_issues(tracker: Tracker, root: Path) -> list[str]:
    out = parse_json(run(tracker, fill(tracker, "list", {}, root), root),
                     "list")
    lines = []
    for item in select(out, tracker.fields.get("list.items", "[]")):
        issue = first_text(item, tracker.fields.get("list.id", ".id"))
        if not tracker.id_pattern.fullmatch(issue):
            continue
        labels = [printable(str(label), 50) for label in
                  select(item, tracker.fields.get("list.labels", ".labels"))]
        lines.append(f"{issue}\t{','.join(labels)}")
    return lines


def labels(tracker: Tracker, root: Path) -> list[str]:
    out = parse_json(run(tracker, fill(tracker, "labels", {}, root), root),
                     "labels")
    names = []
    for item in select(out, tracker.fields.get("labels.items", "[]")):
        name = first_text(item, tracker.fields.get("labels.name", ".name"))
        if name:
            names.append(printable(name, 50))
    return names


def read_issue(tracker: Tracker, issue: str, root: Path) -> dict[str, Any]:
    out = parse_json(run(tracker, fill(tracker, "read", {"id": issue}, root),
                         root), "read")
    fields = tracker.fields
    state = first_text(out, fields["read.state"])
    found: dict[str, Any] = {
        "id": issue,
        "title": first_text(out, fields["read.title"]),
        "body": first_text(out, fields["read.body"]),
        "state": "open" if state.lower() ==
        tracker.setting("state-open").lower() else "closed",
        "labels": [label if isinstance(label, str) else json.dumps(label)
                   for label in select(out, fields.get("read.labels", "."))]
        if "read.labels" in fields else [],
        "url": first_text(out, fields["read.url"])
        if "read.url" in fields else "",
    }
    comments_source = out
    if "comments" in tracker.ops:
        comments_source = parse_json(
            run(tracker, fill(tracker, "comments", {"id": issue}, root),
                root), "comments")
    comments = []
    if "comments.items" in fields:
        for item in select(comments_source, fields["comments.items"]):
            if "comments.skip" in fields and any(
                    select(item, fields["comments.skip"])):
                continue
            comments.append({
                "author": first_text(item, fields.get("comments.author",
                                                      ".author")),
                "body": first_text(item, fields.get("comments.body",
                                                    ".body")),
            })
    found["comments"] = comments
    return found


def pr_find(tracker: Tracker, branch: str, root: Path) -> str | None:
    try:
        out = run(tracker, fill(tracker, "pr-find", {"branch": branch},
                                root), root)
    except Failed:
        return None
    if "pr-find.url" in tracker.fields:
        url = first_text(parse_json(out, "pr-find"),
                         tracker.fields["pr-find.url"])
    else:
        url = out.strip()
    return printable(url) or None


def parse_batch(tracker: Tracker, text: str,
                root: Path) -> list[tuple[str, list[str]]]:
    """Every line of a batch, checked before any runs."""
    batch = []
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        op, *pairs = line.split("\t")
        if op not in PUBLIC_OPS:
            raise Refusal(f"batch line {number}: {op} isn't a public "
                          "operation")
        values = {}
        for pair in pairs:
            key, equals, value = pair.partition("=")
            if not equals:
                raise Refusal(f"batch line {number}: {pair!r} isn't "
                              "name=value")
            values[key] = value
        batch.append((line, fill(tracker, op, values, root)))
    if not batch:
        raise Refusal("the batch is empty")
    return batch


class Terminal:
    """The user's terminal, to show the commands on and read the answer
    from."""

    def __init__(self, reading: int, writing: int) -> None:
        self.reader = os.fdopen(reading, "r", encoding="utf-8")
        self.writer = os.fdopen(writing, "w", encoding="utf-8")

    def write(self, text: str) -> None:
        self.writer.write(text)

    def flush(self) -> None:
        self.writer.flush()

    def readline(self) -> str:
        self.writer.flush()
        return self.reader.readline()

    def __enter__(self) -> Terminal:
        return self

    def __exit__(self, *_: object) -> None:
        self.writer.close()
        self.reader.close()


def open_terminal() -> Terminal | None:
    """The user's terminal, or None when there's none, as for an agent."""
    try:
        return Terminal(os.open("/dev/tty", os.O_RDONLY),
                        os.open("/dev/tty", os.O_WRONLY))
    except OSError:
        pass
    if sys.stdin.isatty() and sys.stdout.isatty():
        return Terminal(os.dup(sys.stdin.fileno()),
                        os.dup(sys.stdout.fileno()))
    return None


def approve(root: Path, allowed: Sequence[str]) -> int:
    terminal = open_terminal()
    if terminal is None:
        print("tracker: approving needs a terminal. Run it yourself, in "
              "your own terminal, from the repository.", file=sys.stderr)
        return 2
    with terminal:
        text, branch = tracker_text(root)
        tracker = Tracker(text, allowed)
        path = approval_path(root)
        old = ""
        try:
            old = json.loads(path.read_text(encoding="utf-8")).get(
                "content", "")
        except (OSError, ValueError):
            pass
        say = terminal.write
        say(f"vibes would run these commands for {root}, from {FILE} on "
            f"{branch}:\n\n")
        if old and old != text:
            say("Changed since you last approved it:\n")
            for line in difflib.unified_diff(
                    old.splitlines(), text.splitlines(), "approved",
                    "now", lineterm="", n=1):
                say(f"  {line}\n")
            say("\n")
        for op in READ_OPS + PUBLIC_OPS:
            if op in tracker.ops:
                kind = "reads " if op in READ_OPS else "PUBLIC"
                say(f"  {kind} {op:13} {tracker.raw[op]}\n")
        say(f"\nPrograms: {', '.join(tracker.programs())}\n")
        tokens = ", ".join(tracker.settings.get("token", [])) or "none"
        say(f"Tokens:   {tokens}\n")
        if tracker.settings.get("host"):
            say(f"Hosts:    {', '.join(tracker.settings['host'])}\n")
        unknown = [p for p in tracker.unknown_programs() if p not in allowed]
        if unknown:
            say(f"\n{', '.join(unknown)} isn't a tracker tool vibes knows. "
                "Run again with --allow-program for each if you trust it.\n")
            return 3
        say("\nThe public commands post as you, and run only when you "
            "confirm each batch.\nType approve to approve these commands: ")
        terminal.flush()
        if terminal.readline().strip() != "approve":
            say("Not approved.\n")
            return 3
        path.write_text(json.dumps({
            "sha256": digest(text), "content": text,
            "programs": [p for p in allowed if p in tracker.programs()],
            "approved": date.today().isoformat(),
        }, indent=2) + "\n", encoding="utf-8")
        say("Approved.\n")
    return 0


def draft(root: Path) -> str:
    try:
        url = git("remote", "get-url", "origin", cwd=root).strip()
    except Refusal:
        raise Refusal(
            "NO DRAFT: the repository has no origin remote") from None
    host = re.sub(r"^[a-z+]+://([^@/]*@)?|^[^@]*@", "", url)
    host = re.split(r"[/:]", host, maxsplit=1)[0].lower()
    if host == "github.com":
        name = "github"
    elif "gitlab" in host:
        name = "gitlab"
    else:
        raise Refusal(f"NO DRAFT: no draft for {host}; write one from "
                      "skills/tracker/templates/")
    return (TEMPLATES / f"{name}.tracker").read_text(encoding="utf-8")


def main(argv: Sequence[str]) -> int:
    args = list(argv)
    if not args:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    command, rest = args[0], args[1:]
    try:
        root = repository()
        if command == "approve":
            allowed = []
            while rest[:1] == ["--allow-program"] and len(rest) >= 2:
                allowed.append(rest[1])
                rest = rest[2:]
            if rest:
                raise Refusal("usage: tracker approve [--allow-program NAME]")
            return approve(root, allowed)
        if command == "draft":
            sys.stdout.write(draft(root))
            return 0
        if command == "lint" and len(rest) == 1:
            tracker = Tracker(Path(rest[0]).read_text(encoding="utf-8"))
            print(f"OK: programs {', '.join(tracker.programs())}")
            unknown = tracker.unknown_programs()
            if unknown:
                print(f"UNKNOWN PROGRAMS: {', '.join(unknown)}, which "
                      "approving needs --allow-program for")
            return 0
        tracker = approved_tracker(root)
        if command == "check":
            print(f"APPROVED: {FILE} on {default_branch(root)}")
        elif command == "whoami":
            print(whoami(tracker, root))
        elif command == "list":
            for line in list_issues(tracker, root):
                print(line)
        elif command == "labels":
            for name in labels(tracker, root):
                print(name)
        elif command == "read" and len(rest) == 3 and rest[1] == "--out":
            issue = rest[0].lstrip("#")
            check_value(tracker, "id", issue, root, {})
            out = Path(rest[2])
            out = out if out.is_absolute() else Path.cwd() / out
            if (root / ".vibes").resolve() not in out.resolve().parents:
                raise Refusal(f"--out must be in {root / '.vibes'}")
            found = read_issue(tracker, issue, root)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(found, indent=2) + "\n",
                           encoding="utf-8")
            shown = ",".join(printable(label, 50)
                             for label in found["labels"])
            print(f"READ {issue} {found['state']} {shown}".rstrip())
        elif command == "pr-find" and len(rest) == 1:
            url = pr_find(tracker, rest[0], root)
            print(url or "NONE")
            return 0 if url else 1
        elif command == "closes" and len(rest) == 1:
            issue = rest[0].lstrip("#")
            check_value(tracker, "id", issue, root, {})
            print(tracker.setting("closes").replace("{id}", issue))
        elif command == "post" and len(rest) == 1:
            batch = parse_batch(
                tracker, Path(rest[0]).read_text(encoding="utf-8"), root)
            for line, filled in batch:
                try:
                    run(tracker, filled, root)
                except Failed as error:
                    print(f"FAILED {line.split(chr(9))[0]}: {error}")
                    return 1
                print(f"DONE {printable(line.replace(chr(9), ' '))}")
        else:
            raise Refusal(f"unknown command: {' '.join(args)}")
    except Missing as error:
        print(error)
        return 4
    except Unapproved as error:
        print(error)
        return 3
    except Failed as error:
        print(error)
        return 1
    except (Refusal, OSError) as error:
        print(f"tracker: {error}", file=sys.stderr)
        return 2
    return 0
