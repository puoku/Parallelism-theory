#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
RESULTS_DIR="${RESULTS_DIR:-$ROOT_DIR/results}"
REPEATS="${REPEATS:-100}"
THREADS_LIST="${THREADS_LIST:-1 2 4 7 8 16 20 40}"
N="${N:-100000000}"
TAU_SCALE="${TAU_SCALE:-0.10}"
EPS="${EPS:-1e-5}"
MAX_ITER="${MAX_ITER:-200000}"

mkdir -p "$RESULTS_DIR"

cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j

RAW_CSV="$RESULTS_DIR/raw.csv"
RAW_TXT="$RESULTS_DIR/raw.txt"

printf "group,variant,size,threads,run,time_s,iterations,max_error_to_one\n" > "$RAW_CSV"
: > "$RAW_TXT"

extract_field() {
  local key="$1"
  awk -v k="$key" '
    {
      for (i = 1; i <= NF; ++i) {
        split($i, a, "=")
        if (a[1] == k) {
          print a[2]
          exit
        }
      }
    }
  '
}

for variant in a b; do
  for threads in $THREADS_LIST; do
    for ((run = 1; run <= REPEATS; ++run)); do
      line="$("$BUILD_DIR/$variant" "$N" "$threads" "$TAU_SCALE" "$EPS" "$MAX_ITER")"
      printf "variant=%s N=%s threads=%s run=%s %s\n" "$variant" "$N" "$threads" "$run" "$line" >> "$RAW_TXT"
      time_s="$(printf '%s\n' "$line" | extract_field time_s)"
      iterations="$(printf '%s\n' "$line" | extract_field iterations)"
      max_error="$(printf '%s\n' "$line" | extract_field max_error_to_one)"
      printf "task3,%s,%s,%s,%s,%s,%s,%s\n" \
        "${variant^^}" "$N" "$threads" "$run" "$time_s" "$iterations" "$max_error" >> "$RAW_CSV"
    done
  done
done

python3 "$ROOT_DIR/../benchmark_tools/analyze_bench.py" \
  --mode threads \
  --input "$RAW_CSV" \
  --output-dir "$RESULTS_DIR"
