# contacts

Cleans up exported contact lists.

```sh
python3 -m contacts dedupe contacts.csv > clean.csv
python3 -m contacts summary contacts.csv
```

`dedupe` keeps the first row for each email address, ignoring case and
surrounding spaces, and writes the rows in their original order. `summary`
prints how many rows, unique addresses and domains the file has.

Run the tests with `scripts/check`.
