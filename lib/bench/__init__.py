"""bench: measures whether a change made a program faster, and by how much.

It runs a benchmark harness against two trees in interleaved pairs, compares
the samples with a bootstrap confidence interval, and decides a verdict from
the noise an A/A run measured, so no agent has to judge timings by eye.
"""
