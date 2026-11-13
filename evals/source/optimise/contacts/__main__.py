"""The command line: python3 -m contacts <dedupe|summary> <file.csv>."""

import csv
import sys

from contacts.dedupe import dedupe
from contacts.summary import summary


def main(argv: list) -> int:
    if len(argv) != 2 or argv[0] not in ("dedupe", "summary"):
        print("usage: python3 -m contacts <dedupe|summary> <file.csv>",
              file=sys.stderr)
        return 2
    command, path = argv
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        fields = reader.fieldnames or []
        rows = list(reader)
    if command == "summary":
        print(summary(rows))
        return 0
    writer = csv.DictWriter(sys.stdout, fieldnames=fields,
                            lineterminator="\n")
    writer.writeheader()
    writer.writerows(dedupe(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
