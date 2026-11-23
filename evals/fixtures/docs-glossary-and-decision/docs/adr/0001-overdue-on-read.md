# 1. Work out overdue state when an invoice is read

The library is embedded in hosts that have no scheduler, so nothing in it
runs on a timer: whether an invoice is overdue, and any charge that follows
from it, is worked out from the dates when the invoice is read.
