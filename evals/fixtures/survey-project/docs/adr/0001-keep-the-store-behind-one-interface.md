# 1. Keep the store behind one interface

Callers save and load orders through `OrderStore` and never see SQL, so the
storage can move off SQLite without touching them.
