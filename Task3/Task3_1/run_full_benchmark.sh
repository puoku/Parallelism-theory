#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
RESULTS_DIR="${RESULTS_DIR:-$ROOT_DIR/results}"
REPEATS="${REPEATS:-100}"
THREADS_LIST="${THREADS_LIST:-1 2 4 7 8 16 20 40}"
SIZES="${SIZES:-20000 40000}"
BIN="$BUILD_DIR/task3_1_matvec_threads"

mkdir -p "$RESULTS_DIR"

cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j

RAW_CSV="$RESULTS_DIR/raw.csv"
RAW_TXT="$RESULTS_DIR/raw.txt"

printf "group,variant,size,threads,run,time_s,init_s,matvec_s,checksum\n" > "$RAW_CSV"
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

for size in $SIZES; do
  for threads in $THREADS_LIST; do
    for ((run = 1; run <= REPEATS; ++run)); do
      line="$("$BIN" "$size" "$threads")"
      printf "N=%s threads=%s run=%s %s\n" "$size" "$threads" "$run" "$line" >> "$RAW_TXT"
      total_s="$(printf '%s\n' "$line" | extract_field total_s)"
      init_s="$(printf '%s\n' "$line" | extract_field init_s)"
      matvec_s="$(printf '%s\n' "$line" | extract_field matvec_s)"
      checksum="$(printf '%s\n' "$line" | extract_field checksum)"
      printf "task3_1,matvec_threads,%s,%s,%s,%s,%s,%s,%s\n" \
        "$size" "$threads" "$run" "$total_s" "$init_s" "$matvec_s" "$checksum" >> "$RAW_CSV"
    done
  done
done

python3 "$ROOT_DIR/../../benchmark_tools/analyze_bench.py" \
  --mode threads \
  --input "$RAW_CSV" \
  --output-dir "$RESULTS_DIR"

python3 "$ROOT_DIR/format_benchmark_table.py" \
  --summary "$RESULTS_DIR/summary.csv" \
  --output "$RESULTS_DIR/table.txt"

echo "Done."
echo "Results:"
echo "  $RAW_CSV"
echo "  $RESULTS_DIR/summary.csv"
echo "  $RESULTS_DIR/summary.txt"
echo "  $RESULTS_DIR/table.txt"
