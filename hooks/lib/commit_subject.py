"""Finds commit subjects longer than the vibes limit of 50 characters.

    python3 -I -S commit_subject.py --command <dir>   # a shell command on stdin
    python3 -I -S commit_subject.py --file <path>     # git's message file

Prints one line for each subject over the limit, its length, a tab and the
subject, and nothing otherwise. A message it can't read for certain, such as
one built from a variable or reused from another commit, passes: the check
must never block a commit it misread.
"""

import os
import re
import shlex
import sys

LIMIT = 50
SEPARATORS = {";", "&", "&&", "|", "||", "\n"}
# git's options that come before the subcommand and take a value.
GIT_VALUE_OPTIONS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                     "--exec-path", "--config-env", "--super-prefix"}
# git commit's options that take the message from elsewhere.
REUSE_OPTIONS = ("-c", "-C", "--reuse-message", "--reedit-message",
                 "--fixup", "--squash", "--template", "-t")
HEREDOC = re.compile(r"<<-?[ \t]*(['\"]?)(\w+)\1[^\n]*\n(.*?)\n[ \t]*\2[ \t]*(?:\n|$)",
                     re.DOTALL)
CAT_HEREDOC = re.compile(r"\A\$\(\s*cat\s+<<-?[ \t]*(['\"]?)(\w+)\1[ \t]*\n"
                         r"(.*?)\n[ \t]*\2[ \t]*\n?\s*\)\s*\Z", re.DOTALL)


def subject(message):
    """The first non-blank line of a message, or None for an empty one."""
    for line in message.splitlines():
        if line.strip() and not line.startswith("#"):
            return line.rstrip()
    return None


def literal(value):
    """The text of a -m value, or None when the shell would change it."""
    match = CAT_HEREDOC.match(value)
    if match:
        return match.group(3)
    if "$" in value or "`" in value:
        return None
    return value


class Commit:
    """What one git commit in a command says about its message."""

    def __init__(self):
        self.messages = []
        self.file = None
        self.unknown = False

    def option(self, word, following):
        """Reads one option, and returns how many words it used."""
        if word in ("-m", "--message", "-F", "--file"):
            if following is None:
                self.unknown = True
                return 1
            self.value(word, following)
            return 2
        for prefix in ("--message=", "--file="):
            if word.startswith(prefix):
                self.value(prefix[:-1], word[len(prefix):])
                return 1
        if word.startswith(REUSE_OPTIONS):
            self.unknown = True
            return 1
        if word.startswith("-") and not word.startswith("--"):
            for i, char in enumerate(word[1:], 1):
                if char in "mF":
                    rest = word[i + 1:]
                    if rest:
                        self.value("-" + char, rest)
                        return 1
                    if following is None:
                        self.unknown = True
                        return 1
                    self.value("-" + char, following)
                    return 2
                if char in "cCt":
                    self.unknown = True
                    return 1
        return 1

    def value(self, option, value):
        if option in ("-m", "--message"):
            self.messages.append(value)
        else:
            self.file = value


def commits(words):
    """Each git commit in a command's words."""
    found = []
    i = 0
    while i < len(words):
        word = words[i]
        if word != "git" and not word.endswith("/git"):
            i += 1
            continue
        i += 1
        while i < len(words) and words[i].startswith("-"):
            i += 2 if words[i] in GIT_VALUE_OPTIONS else 1
        if i >= len(words) or words[i] != "commit":
            continue
        commit = Commit()
        i += 1
        while i < len(words) and words[i] not in SEPARATORS:
            following = words[i + 1] if i + 1 < len(words) else None
            if following in SEPARATORS:
                following = None
            i += commit.option(words[i], following)
        found.append(commit)
    return found


def message_of(commit, command, directory):
    """The commit's message, or None when it can't be read for certain."""
    if commit.unknown:
        return None
    if commit.messages:
        return literal(commit.messages[0])
    if commit.file == "-":
        bodies = HEREDOC.findall(command)
        return bodies[0][2] if len(bodies) == 1 else None
    if commit.file:
        path = os.path.join(directory, os.path.expanduser(commit.file))
        try:
            with open(path, encoding="utf-8") as handle:
                return handle.read()
        except (OSError, UnicodeDecodeError):
            return None
    return None


def words_of(command):
    """A command's words, with each separator a word of its own.

    A heredoc's body is text, not shell, so a lone quote in it, such as an
    apostrophe in a message for -F -, leaves the shell's words unchanged.
    When one makes the command unreadable as a whole, the words are those
    of the command with each heredoc's body cut out.
    """
    try:
        return split(command)
    except ValueError:
        return split(HEREDOC.sub(heredoc_head, command))


def heredoc_head(match):
    """A heredoc's first line, the redirection, without its body."""
    return match.group(0).split("\n", 1)[0] + "\n"


def split(command):
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def long_subjects(messages):
    found = []
    for message in messages:
        line = subject(message) if message is not None else None
        if line is not None and len(line) > LIMIT:
            found.append(line)
    return found


def main(argv):
    if len(argv) != 2 or argv[0] not in ("--command", "--file"):
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 2
    if argv[0] == "--file":
        try:
            with open(argv[1], encoding="utf-8") as handle:
                messages = [handle.read()]
        except (OSError, UnicodeDecodeError):
            return 0
    else:
        command = sys.stdin.read()
        try:
            words = words_of(command)
        except ValueError:
            return 0
        messages = [message_of(commit, command, argv[1])
                    for commit in commits(words)]
    for line in long_subjects(messages):
        print(f"{len(line)}\t{line}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
