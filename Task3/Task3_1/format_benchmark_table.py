#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path


THREADS = [1, 2, 4, 7, 8, 16, 20, 40]


def read_summary(path: Path):
    rows = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (int(row["size"]), int(row["threads"]))
            rows[key] = {
                "avg_time_s": float(row["avg_time_s"]),
                "speedup": float(row["speedup"]) if row["speedup"] else None,
            }
    return rows


def fmt(value):
    return "-" if value is None else f"{value:.6f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    rows = read_summary(Path(args.summary))
    out_lines = []
    sizes = sorted({size for size, _ in rows.keys()})

    for size in sizes:
        out_lines.append(f"N={size}")
        out_lines.append("threads,T1,Tp,Sp")
        t1 = rows[(size, 1)]["avg_time_s"]
        for threads in THREADS[1:]:
            item = rows.get((size, threads))
            tp = item["avg_time_s"] if item else None
            sp = item["speedup"] if item else None
            out_lines.append(f"{threads},{fmt(t1)},{fmt(tp)},{fmt(sp)}")
        out_lines.append("")

    Path(args.output).write_text("\n".join(out_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
