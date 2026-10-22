import json
import os
import sys

import pandas as pd


def load_records(path):
    # utf-8 on purpose: Windows would otherwise guess cp1252 and mangle farm names
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_frame(records):
    return pd.DataFrame(records, columns=["farm", "litres", "fat_percent"])


def summarise(df):
    total = round(df["litres"].sum(), 2)
    average_fat = round(df["fat_percent"].mean(), 2)
    return total, average_fat


def main(argv):
    if len(argv) != 2:
        print(f"Usage: python {os.path.basename(argv[0])} churns.json")
        return 1
    path = argv[1]
    try:
        records = load_records(path)
    except FileNotFoundError:
        print(f"Error: file not found: {path}")
        return 1
    except json.JSONDecodeError:
        print(f"Error: {path} is not valid JSON")
        return 1

    df = build_frame(records)
    total, average_fat = summarise(df)
    print(df)
    print(f"Total litres: {total}")
    print(f"Average fat: {average_fat:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

