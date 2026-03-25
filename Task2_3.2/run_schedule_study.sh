#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
RESULTS_DIR="${RESULTS_DIR:-$ROOT_DIR/results}"
REPEATS="${REPEATS:-100}"
N="${N:-100000000}"
THREADS="${THREADS:-16}"
TAU_SCALE="${TAU_SCALE:-0.10}"
EPS="${EPS:-1e-5}"
MAX_ITER="${MAX_ITER:-200000}"
SCHEDULES="${SCHEDULES:-static:0 dynamic:10 dynamic:25 dynamic:50 dynamic:85 dynamic:100 guided:10 guided:25 guided:50 guided:85 guided:100}"

mkdir -p "$RESULTS_DIR"

cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j

RAW_CSV="$RESULTS_DIR/raw.csv"
RAW_TXT="$RESULTS_DIR/raw.txt"

printf "group,variant,size,threads,schedule,chunk,run,time_s,iterations,max_error_to_one\n" > "$RAW_CSV"
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
  for item in $SCHEDULES; do
    schedule="${item%%:*}"
    chunk="${item##*:}"
    for ((run = 1; run <= REPEATS; ++run)); do
      line="$("$BUILD_DIR/$variant" "$N" "$THREADS" "$TAU_SCALE" "$EPS" "$MAX_ITER" "$schedule" "$chunk")"
      printf "variant=%s N=%s threads=%s schedule=%s chunk=%s run=%s %s\n" \
        "$variant" "$N" "$THREADS" "$schedule" "$chunk" "$run" "$line" >> "$RAW_TXT"
      time_s="$(printf '%s\n' "$line" | extract_field time_s)"
      iterations="$(printf '%s\n' "$line" | extract_field iterations)"
      max_error="$(printf '%s\n' "$line" | extract_field max_error_to_one)"
      printf "task3_schedule,%s,%s,%s,%s,%s,%s,%s,%s,%s\n" \
        "${variant^^}" "$N" "$THREADS" "$schedule" "$chunk" "$run" "$time_s" "$iterations" "$max_error" >> "$RAW_CSV"
    done
  done
done

python3 "$ROOT_DIR/../benchmark_tools/analyze_bench.py" \
  --mode schedule \
  --input "$RAW_CSV" \
  --output-dir "$RESULTS_DIR"
