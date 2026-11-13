"""Writes the workload's contact lists into bench/data/, from fixed seeds."""

import csv
import os
import random
import sys

SIZES = {"small": (3000, 1, 40), "main": (12000, 2, 40),
         "holdout": (8000, 3, 20)}


def write(size: str) -> None:
    rows, seed, domains = SIZES[size]
    generator = random.Random(seed)
    directory = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "data")
    os.makedirs(directory, exist_ok=True)
    with open(os.path.join(directory, f"{size}.csv"), "w", newline="",
              encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(["name", "email"])
        for index in range(rows):
            number = generator.randrange(int(rows * 0.75))
            email = f"user{number}@example{number % domains}.com"
            if generator.random() < 0.1:
                email = f" {email.upper()} "
            writer.writerow([f"Name {index}", email])


if __name__ == "__main__":
    for name in sys.argv[1:] or list(SIZES):
        write(name)
