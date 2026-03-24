#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
RESULTS_DIR="${RESULTS_DIR:-$ROOT_DIR/results}"
REPEATS="${REPEATS:-100}"
THREADS_LIST="${THREADS_LIST:-1 2 4 7 8 16 20 40}"
NSTEPS="${NSTEPS:-40000000}"
BIN="$BUILD_DIR/task2_integrate_omp"

mkdir -p "$RESULTS_DIR"

cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j

RAW_CSV="$RESULTS_DIR/raw.csv"
RAW_TXT="$RESULTS_DIR/raw.txt"

printf "group,variant,size,threads,run,time_s,result,error\n" > "$RAW_CSV"
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

for threads in $THREADS_LIST; do
  for ((run = 1; run <= REPEATS; ++run)); do
    line="$("$BIN" "$NSTEPS" "$threads")"
    printf "nsteps=%s threads=%s run=%s %s\n" "$NSTEPS" "$threads" "$run" "$line" >> "$RAW_TXT"
    time_s="$(printf '%s\n' "$line" | extract_field time_s)"
    result="$(printf '%s\n' "$line" | extract_field result)"
    error="$(printf '%s\n' "$line" | extract_field error)"
    printf "task2,integrate,%s,%s,%s,%s,%s,%s\n" \
      "$NSTEPS" "$threads" "$run" "$time_s" "$result" "$error" >> "$RAW_CSV"
  done
done

python3 "$ROOT_DIR/../benchmark_tools/analyze_bench.py" \
  --mode threads \
  --input "$RAW_CSV" \
  --output-dir "$RESULTS_DIR"
