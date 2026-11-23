"""repro: decides whether a bug's reproduction fails reliably, and fast.

A reproduction is a command that exits 1 while the bug is present, 0 once
it's gone, and 125 when it can't tell, as git bisect run expects. repro runs
it several times and gives one verdict, so no agent has to judge by eye
whether the bug reproduces.
"""
