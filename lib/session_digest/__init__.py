"""session_digest: a compact digest of a Claude Code session's transcript.

A transcript is too large to read whole and too verbose to count by eye, so
this lists every tool call on one line with a reference, such as m12 for the
main agent's twelfth call or a3.7 for the seventh call of the third
subagent, and totals what a retrospective needs: replies, calls, failures,
hook blocks, repeated calls and the largest results. A reference leads back
to the call's full input and result.
"""
