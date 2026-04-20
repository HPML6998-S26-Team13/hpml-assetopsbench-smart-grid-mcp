#!/bin/bash
# Open a 2x2 tmux dashboard for a SmartGridBench run directory.
#
# Usage examples:
#   bash scripts/tmux_watch_run.sh --job-id 8848287
#   bash scripts/tmux_watch_run.sh --run-id 8848287_pe_self_ask_mcp_baseline_smoke
#   bash scripts/tmux_watch_run.sh --run-dir benchmarks/cell_Y_plan_execute/raw/8848287_pe_self_ask_mcp_baseline_smoke

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/tmux_watch_run.sh [--job-id JOB_ID] [--run-id RUN_ID] [--run-dir PATH] [--session NAME] [--reset]

Options:
  --job-id JOB_ID    Slurm job id; used for logs/exp_<JOB_ID>.out and to infer the run dir if needed.
  --run-id RUN_ID    Run directory basename, e.g. 8848287_pe_self_ask_mcp_baseline_smoke.
  --run-dir PATH     Explicit run directory under benchmarks/.../raw/.
  --session NAME     Override tmux session name. Default: watch-<run-id-or-job-id>.
  --reset            Recreate the tmux session if it already exists.
  -h, --help         Show this help.

Notes:
  - If your local terminal advertises xterm-ghostty, this script downgrades TERM to xterm-256color
    before launching tmux so the remote host accepts it.
  - Pane layout:
      top-left: shell in repo root
      bottom-left: Slurm stdout (if present), otherwise live job status for interactive runs
      top-right: harness.log
      bottom-right: vllm.log if present, else GPU live view (local or via srun --jobid)
EOF
}

JOB_ID=""
RUN_ID=""
RUN_DIR=""
SESSION_NAME=""
RESET_EXISTING="0"

while [ "$#" -gt 0 ]; do
  case "$1" in
    --job-id)
      JOB_ID="${2:?missing value for --job-id}"
      shift 2
      ;;
    --run-id)
      RUN_ID="${2:?missing value for --run-id}"
      shift 2
      ;;
    --run-dir)
      RUN_DIR="${2:?missing value for --run-dir}"
      shift 2
      ;;
    --session)
      SESSION_NAME="${2:?missing value for --session}"
      shift 2
      ;;
    --reset)
      RESET_EXISTING="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if ! command -v tmux >/dev/null 2>&1; then
  echo "ERROR: tmux is not installed on this host." >&2
  exit 1
fi

if [[ "${TERM:-}" == "xterm-ghostty" ]]; then
  export TERM="xterm-256color"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

apply_session_defaults() {
  local session_name="$1"
  tmux set-option -t "$session_name" mouse on >/dev/null 2>&1 || true
  tmux set-option -t "$session_name" history-limit 200000 >/dev/null 2>&1 || true
  tmux set-window-option -t "$session_name" mode-keys vi >/dev/null 2>&1 || true
  tmux set-option -t "$session_name" allow-rename off >/dev/null 2>&1 || true
  tmux set-option -t "$session_name" automatic-rename off >/dev/null 2>&1 || true
  tmux set-option -t "$session_name" allow-set-title off >/dev/null 2>&1 || true
  tmux set-option -t "$session_name" pane-border-status top >/dev/null 2>&1 || true
  tmux set-option -t "$session_name" pane-border-format " #{pane_index}:#{pane_title} " >/dev/null 2>&1 || true
}

find_run_dir_by_pattern() {
  local pattern="$1"
  mapfile -t matches < <(find benchmarks -type d -path "*/raw/${pattern}" | sort)
  if [ "${#matches[@]}" -eq 0 ]; then
    return 1
  fi
  if [ "${#matches[@]}" -gt 1 ]; then
    printf 'ERROR: multiple run directories matched %s:\n' "$pattern" >&2
    printf '  %s\n' "${matches[@]}" >&2
    exit 1
  fi
  printf '%s\n' "${matches[0]}"
}

if [ -n "$RUN_DIR" ]; then
  if [ ! -d "$RUN_DIR" ]; then
    echo "ERROR: run directory not found: $RUN_DIR" >&2
    exit 1
  fi
else
  if [ -n "$RUN_ID" ]; then
    RUN_DIR="$(find_run_dir_by_pattern "$RUN_ID")" || {
      echo "ERROR: could not find run directory for run id: $RUN_ID" >&2
      exit 1
    }
  elif [ -n "$JOB_ID" ]; then
    RUN_DIR="$(find_run_dir_by_pattern "${JOB_ID}_*")" || {
      echo "ERROR: could not infer run directory for job id: $JOB_ID" >&2
      exit 1
    }
  else
    echo "ERROR: one of --run-dir, --run-id, or --job-id is required." >&2
    usage >&2
    exit 1
  fi
fi

RUN_DIR="$(cd "$RUN_DIR" && pwd)"
RUN_ID="${RUN_ID:-$(basename "$RUN_DIR")}"
if [ -z "$JOB_ID" ] && [[ "$RUN_ID" =~ ^([0-9]+)_ ]]; then
  JOB_ID="${BASH_REMATCH[1]}"
fi
SESSION_NAME="${SESSION_NAME:-watch-${RUN_ID}}"
SESSION_NAME="${SESSION_NAME//[^A-Za-z0-9_.:-]/-}"

SLURM_LOG=""
if [ -n "$JOB_ID" ] && [ -f "$REPO_ROOT/logs/exp_${JOB_ID}.out" ]; then
  SLURM_LOG="$REPO_ROOT/logs/exp_${JOB_ID}.out"
fi

HARNESS_LOG="$RUN_DIR/harness.log"
VLLM_LOG="$RUN_DIR/vllm.log"

if [ ! -f "$HARNESS_LOG" ]; then
  echo "ERROR: harness log not found: $HARNESS_LOG" >&2
  exit 1
fi

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
  if [ "$RESET_EXISTING" = "1" ]; then
    tmux kill-session -t "$SESSION_NAME"
  else
    apply_session_defaults "$SESSION_NAME"
    tmux select-pane -t "$SESSION_NAME:0.0" -T "run" >/dev/null 2>&1 || true
    tmux select-pane -t "$SESSION_NAME:0.1" -T "slurm" >/dev/null 2>&1 || true
    tmux select-pane -t "$SESSION_NAME:0.2" -T "harness" >/dev/null 2>&1 || true
    tmux select-pane -t "$SESSION_NAME:0.3" -T "vllm" >/dev/null 2>&1 || true
    exec tmux attach -t "$SESSION_NAME"
  fi
fi

tmux new-session -d -s "$SESSION_NAME" -c "$REPO_ROOT"
apply_session_defaults "$SESSION_NAME"
tmux split-window -h -t "$SESSION_NAME:0"
tmux split-window -v -t "$SESSION_NAME:0.0"
tmux split-window -v -t "$SESSION_NAME:0.1"
tmux select-layout -t "$SESSION_NAME:0" tiled

tmux send-keys -t "$SESSION_NAME:0.0" "printf '\033]2;run\033\\\\'; cd '$REPO_ROOT'; printf 'Run dir: %s\nHarness: %s\n' '$RUN_DIR' '$HARNESS_LOG'" C-m
tmux select-pane -t "$SESSION_NAME:0.0" -T "run"

if [ -n "$SLURM_LOG" ]; then
  tmux send-keys -t "$SESSION_NAME:0.1" "printf '\033]2;slurm\033\\\\'; cd '$REPO_ROOT'; tail -f '$SLURM_LOG'" C-m
elif [ -n "$JOB_ID" ]; then
  tmux send-keys -t "$SESSION_NAME:0.1" "printf '\033]2;slurm\033\\\\'; cd '$REPO_ROOT'; while true; do clear; date; printf '\nNo logs/exp_${JOB_ID}.out found. This run looks interactive (srun + direct bash), so there is no batch stdout file to tail.\n\n'; if command -v squeue >/dev/null 2>&1; then squeue -j '$JOB_ID' -o '%.18i %.9P %.8j %.8u %.2t %.10M %.10l %.6D %R'; else printf 'squeue not available on this host.\n'; fi; sleep 5; done" C-m
else
  tmux send-keys -t "$SESSION_NAME:0.1" "printf '\033]2;slurm\033\\\\'; cd '$REPO_ROOT'; printf 'No Slurm log configured. This usually means the run was launched directly with bash rather than sbatch, or logs/exp_<jobid>.out is missing.\n'" C-m
fi
tmux select-pane -t "$SESSION_NAME:0.1" -T "slurm"

tmux send-keys -t "$SESSION_NAME:0.2" "printf '\033]2;harness\033\\\\'; cd '$REPO_ROOT'; tail -f '$HARNESS_LOG'" C-m
tmux select-pane -t "$SESSION_NAME:0.2" -T "harness"

if [ -f "$VLLM_LOG" ]; then
  tmux send-keys -t "$SESSION_NAME:0.3" "printf '\033]2;vllm\033\\\\'; cd '$REPO_ROOT'; tail -f '$VLLM_LOG'" C-m
  tmux select-pane -t "$SESSION_NAME:0.3" -T "vllm"
elif [ -n "$JOB_ID" ]; then
  tmux send-keys -t "$SESSION_NAME:0.3" "printf '\033]2;gpu\033\\\\'; cd '$REPO_ROOT'; if command -v srun >/dev/null 2>&1; then srun --jobid '$JOB_ID' --overlap bash -lc 'if command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi -l 2; else printf \"nvidia-smi is not available inside the allocation shell.\\n\"; fi'; else printf 'srun not available on this host, so GPU monitoring cannot attach to job $JOB_ID.\n'; fi" C-m
  tmux select-pane -t "$SESSION_NAME:0.3" -T "gpu"
else
  tmux send-keys -t "$SESSION_NAME:0.3" "printf '\033]2;gpu\033\\\\'; cd '$REPO_ROOT'; if command -v nvidia-smi >/dev/null 2>&1; then nvidia-smi -l 2; else printf 'nvidia-smi is not available on this host, and no Slurm job id was provided for an srun attach.\n'; fi" C-m
  tmux select-pane -t "$SESSION_NAME:0.3" -T "gpu"
fi

exec tmux attach -t "$SESSION_NAME"
