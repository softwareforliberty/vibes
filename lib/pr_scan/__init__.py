"""Deterministic scan of an untrusted pull request for malicious changes.

The scan reads the pull request only from git objects, through the hardened
wrapper in gitio, so nothing in it runs. It writes an escaped snapshot of the
changed files, a description of every binary, and scan.md, whose findings no
reviewer can clear. See skills/review-pr/SKILL.md.
"""
