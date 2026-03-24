#!/usr/bin/env python3

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def avg_dropmax(times):
    if not times:
        return 0.0
    if len(times) == 1:
        return times[0]
    return (sum(times) - max(times)) / (len(times) - 1)


def fmt(value):
    if value is None:
        return "-"
    return f"{value:.6f}"


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, fieldnames, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def analyze_threads(rows, outdir):
    grouped = defaultdict(list)
    for row in rows:
        key = (
            row.get("group", ""),
            row.get("variant", ""),
            row.get("size", ""),
            int(row["threads"]),
        )
        grouped[key].append(float(row["time_s"]))

    series = defaultdict(list)
    for (group, variant, size, threads), times in grouped.items():
        series[(group, variant, size)].append(
            {
                "group": group,
                "variant": variant,
                "size": size,
                "threads": threads,
                "runs": len(times),
                "max_time_s": max(times),
                "avg_time_s": avg_dropmax(times),
                "raw_times": times,
            }
        )

    summary_rows = []
    txt_lines = []

    for key in sorted(series.keys()):
        group, variant, size = key
        items = sorted(series[key], key=lambda item: item["threads"])
        t1 = None
        for item in items:
            if item["threads"] == 1:
                t1 = item["avg_time_s"]
                break

        title = f"group={group}"
        if variant:
            title += f", variant={variant}"
        if size:
            title += f", size={size}"
        txt_lines.append(title)
        txt_lines.append(
            "threads,runs,max_time_s,avg_time_s,speedup,efficiency,karp_flatt"
        )

        for item in items:
            threads = item["threads"]
            avg_time = item["avg_time_s"]
            speedup = (t1 / avg_time) if t1 and avg_time else None
            efficiency = (speedup / threads) if speedup else None
            karp_flatt = None
            if speedup and threads > 1 and speedup != 1.0:
                karp_flatt = ((1.0 / speedup) - (1.0 / threads)) / (
                    1.0 - (1.0 / threads)
                )

            summary_rows.append(
                {
                    "group": group,
                    "variant": variant,
                    "size": size,
                    "threads": threads,
                    "runs": item["runs"],
                    "max_time_s": f"{item['max_time_s']:.12f}",
                    "avg_time_s": f"{avg_time:.12f}",
                    "t1_s": f"{t1:.12f}" if t1 is not None else "",
                    "speedup": f"{speedup:.12f}" if speedup is not None else "",
                    "efficiency": f"{efficiency:.12f}" if efficiency is not None else "",
                    "karp_flatt": f"{karp_flatt:.12f}" if karp_flatt is not None else "",
                }
            )

            txt_lines.append(
                ",".join(
                    [
                        str(threads),
                        str(item["runs"]),
                        fmt(item["max_time_s"]),
                        fmt(avg_time),
                        fmt(speedup),
                        fmt(efficiency),
                        fmt(karp_flatt),
                    ]
                )
            )
        txt_lines.append("")

    write_csv(
        outdir / "summary.csv",
        [
            "group",
            "variant",
            "size",
            "threads",
            "runs",
            "max_time_s",
            "avg_time_s",
            "t1_s",
            "speedup",
            "efficiency",
            "karp_flatt",
        ],
        summary_rows,
    )
    (outdir / "summary.txt").write_text("\n".join(txt_lines), encoding="utf-8")


def analyze_schedule(rows, outdir):
    grouped = defaultdict(list)
    for row in rows:
        key = (
            row.get("group", ""),
            row.get("variant", ""),
            row.get("size", ""),
            int(row["threads"]),
            row["schedule"],
            row["chunk"],
        )
        grouped[key].append(float(row["time_s"]))

    series = defaultdict(list)
    for (group, variant, size, threads, schedule, chunk), times in grouped.items():
        series[(group, variant, size, threads)].append(
            {
                "group": group,
                "variant": variant,
                "size": size,
                "threads": threads,
                "schedule": schedule,
                "chunk": chunk,
                "runs": len(times),
                "max_time_s": max(times),
                "avg_time_s": avg_dropmax(times),
            }
        )

    summary_rows = []
    txt_lines = []

    for key in sorted(series.keys()):
        group, variant, size, threads = key
        items = sorted(series[key], key=lambda item: item["avg_time_s"])
        best = items[0]["avg_time_s"] if items else None

        title = f"group={group}"
        if variant:
            title += f", variant={variant}"
        if size:
            title += f", size={size}"
        title += f", threads={threads}"
        txt_lines.append(title)
        txt_lines.append("schedule,chunk,runs,max_time_s,avg_time_s,relative_to_best")

        for item in items:
            relative = (item["avg_time_s"] / best) if best else None
            summary_rows.append(
                {
                    "group": group,
                    "variant": variant,
                    "size": size,
                    "threads": threads,
                    "schedule": item["schedule"],
                    "chunk": item["chunk"],
                    "runs": item["runs"],
                    "max_time_s": f"{item['max_time_s']:.12f}",
                    "avg_time_s": f"{item['avg_time_s']:.12f}",
                    "relative_to_best": f"{relative:.12f}" if relative is not None else "",
                }
            )

            txt_lines.append(
                ",".join(
                    [
                        item["schedule"],
                        str(item["chunk"]),
                        str(item["runs"]),
                        fmt(item["max_time_s"]),
                        fmt(item["avg_time_s"]),
                        fmt(relative),
                    ]
                )
            )
        txt_lines.append("")

    write_csv(
        outdir / "summary.csv",
        [
            "group",
            "variant",
            "size",
            "threads",
            "schedule",
            "chunk",
            "runs",
            "max_time_s",
            "avg_time_s",
            "relative_to_best",
        ],
        summary_rows,
    )
    (outdir / "summary.txt").write_text("\n".join(txt_lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["threads", "schedule"], required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    rows = read_rows(args.input)

    if args.mode == "threads":
        analyze_threads(rows, outdir)
    else:
        analyze_schedule(rows, outdir)


if __name__ == "__main__":
    main()
