#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="${LOG_DIR:-$ROOT_DIR/task2_full_run_logs}"
MASTER_LOG="$LOG_DIR/master.log"

mkdir -p "$LOG_DIR"

timestamp() {
  date +"%Y-%m-%d %H:%M:%S"
}

log() {
  printf "[%s] %s\n" "$(timestamp)" "$*" | tee -a "$MASTER_LOG"
}

run_task() {
  local name="$1"
  local dir="$2"
  local script="$3"
  local task_log="$LOG_DIR/${name}.log"

  log "START ${name}"
  (
    cd "$dir"
    bash "$script"
  ) >"$task_log" 2>&1
  log "DONE ${name} (log: $task_log)"
}

: > "$MASTER_LOG"

log "Full Task2 benchmark run started"
log "ROOT_DIR=$ROOT_DIR"
log "LOG_DIR=$LOG_DIR"

run_task "Task2_1" "$ROOT_DIR/Task2_1" "./run_full_benchmark.sh"
run_task "Task2_2" "$ROOT_DIR/Task2_2" "./run_full_benchmark.sh"
run_task "Task2_3" "$ROOT_DIR/Task2_3" "./run_full_benchmark.sh"
run_task "Task2_3_2" "$ROOT_DIR/Task2_3.2" "./run_schedule_study.sh"

log "All Task2 benchmarks completed successfully"
log "Result folders:"
log "  $ROOT_DIR/Task2_1/results"
log "  $ROOT_DIR/Task2_2/results"
log "  $ROOT_DIR/Task2_3/results"
log "  $ROOT_DIR/Task2_3.2/results"
