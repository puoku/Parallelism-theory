#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/build}"
TASKS_PER_CLIENT="${TASKS_PER_CLIENT:-100}"
BENCH_TASKS="${BENCH_TASKS:-5000}"
BENCH_REPEATS="${BENCH_REPEATS:-3}"

cmake -S "$ROOT_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j

(
  cd "$ROOT_DIR"
  "$BUILD_DIR/task3_2" "$TASKS_PER_CLIENT"
  "$BUILD_DIR/task3_2_test"
  "$BUILD_DIR/task3_2_choice_bench" "$BENCH_TASKS" "$BENCH_REPEATS"
)

echo "Done."
