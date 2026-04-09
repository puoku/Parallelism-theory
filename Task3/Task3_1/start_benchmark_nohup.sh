#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="${LOG_FILE:-$ROOT_DIR/benchmark.log}"
PID_FILE="${PID_FILE:-$ROOT_DIR/benchmark.pid}"

cd "$ROOT_DIR"

nohup bash "$ROOT_DIR/run_full_benchmark.sh" > "$LOG_FILE" 2>&1 &
PID=$!
printf "%s\n" "$PID" > "$PID_FILE"

echo "Started benchmark in background."
echo "PID: $PID"
echo "Log: $LOG_FILE"
echo "PID file: $PID_FILE"
echo "Check progress with:"
echo "  tail -f \"$LOG_FILE\""
