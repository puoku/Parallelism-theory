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
                "median_time_s": float(row["median_time_s"]) if row.get("median_time_s") else None,
                "speedup": float(row["speedup"]) if row["speedup"] else None,
                "efficiency": float(row["efficiency"]) if row.get("efficiency") else None,
                "karp_flatt": float(row["karp_flatt"]) if row.get("karp_flatt") else None,
                "median_speedup": float(row["median_speedup"]) if row.get("median_speedup") else None,
                "median_efficiency": float(row["median_efficiency"]) if row.get("median_efficiency") else None,
                "median_karp_flatt": float(row["median_karp_flatt"]) if row.get("median_karp_flatt") else None,
            }
    return rows


def fmt(value):
    return "-" if value is None else f"{value:.6f}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mode", choices=["avg", "median"], default="median")
    args = parser.parse_args()

    rows = read_summary(Path(args.summary))
    out_lines = []
    sizes = sorted({size for size, _ in rows.keys()})
    time_key = "avg_time_s" if args.mode == "avg" else "median_time_s"
    speed_key = "speedup" if args.mode == "avg" else "median_speedup"
    eff_key = "efficiency" if args.mode == "avg" else "median_efficiency"
    karp_key = "karp_flatt" if args.mode == "avg" else "median_karp_flatt"

    for size in sizes:
        out_lines.append(f"N={size}, mode={args.mode}")
        out_lines.append("threads,T1,Tp,Sp,Ep,Karp-Flatt")
        t1 = rows[(size, 1)][time_key]
        for threads in THREADS[1:]:
            item = rows.get((size, threads))
            tp = item[time_key] if item else None
            sp = item[speed_key] if item else None
            ep = item[eff_key] if item else None
            kp = item[karp_key] if item else None
            out_lines.append(f"{threads},{fmt(t1)},{fmt(tp)},{fmt(sp)},{fmt(ep)},{fmt(kp)}")
        out_lines.append("")

    Path(args.output).write_text("\n".join(out_lines), encoding="utf-8")


if __name__ == "__main__":
    main()
