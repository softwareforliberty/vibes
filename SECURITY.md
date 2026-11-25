# Security

vibes runs hooks and agents on your machine, so a flaw in it can matter.
Thanks for reporting one privately.

## Report a vulnerability

Report it through GitHub's private vulnerability reporting: on the
repository's **Security** tab, choose **Report a vulnerability**, or go
straight to
[the report form](https://github.com/softwareforliberty/vibes/security/advisories/new).
Only you and the maintainer see it. Please don't open a public issue or
discussion for it.

Say what's wrong, how to reproduce it, the vibes version, the agent and
your operating system, and what someone could do with it. The reply, and
any fix, come in the same private report, which is made public once a fix
is released.

## What counts

Anything that lets vibes do what it's meant to stop, for example:

- a change that gets past the commit gate, or a gate check that can't fail;
- a hook that lets an agent do what it should refuse, such as writing to a
  path it protects, or a read-only reviewer changing a file;
- a malicious pull request that `/vibes:review-pr` passes as safe, when
  [security/malicious-changes.md](security/malicious-changes.md) covers
  what it does;
- vibes' own code running something it shouldn't, or sending data
  somewhere it shouldn't.

## Supported versions

Only the latest release gets fixes. Until 1.0, a fix comes in a new
release, not as a patch to an older one.
