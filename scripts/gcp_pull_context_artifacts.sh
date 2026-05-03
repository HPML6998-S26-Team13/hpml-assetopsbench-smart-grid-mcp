#!/usr/bin/env bash
# Pull GCP context-batch artifacts over IAP and merge judge score rows safely.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

INSTANCE="${SMARTGRID_COMPUTE_INSTANCE:-}"
ZONE="${SMARTGRID_COMPUTE_ZONE:-}"
BATCH_ID="${SMARTGRID_BATCH_ID:-}"
REMOTE_ROOT="${REMOTE_ROOT:-~/hpml-assetopsbench-smart-grid-mcp}"
DEST_ROOT="${DEST_ROOT:-gcp_artifacts}"
PARALLEL="${PARALLEL:-2}"
DRY_RUN="${DRY_RUN:-0}"
MERGE_SCORES=""

usage() {
  cat <<'EOF'
Usage: scripts/gcp_pull_context_artifacts.sh --instance NAME --zone ZONE --batch-id ID [--dest DIR] [--parallel N] [--dry-run]
       scripts/gcp_pull_context_artifacts.sh --merge-scores PATH

Pull order is small-first: batch manifests/logs, score file, judge logs, then
raw run directories listed in the batch manifest. Score rows merge by
(run_name, scenario_id, trial_index, judge_model, judge_prompt_version).
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --instance) INSTANCE="$2"; shift 2 ;;
    --zone) ZONE="$2"; shift 2 ;;
    --batch-id) BATCH_ID="$2"; shift 2 ;;
    --remote-root) REMOTE_ROOT="$2"; shift 2 ;;
    --dest) DEST_ROOT="$2"; shift 2 ;;
    --parallel) PARALLEL="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --merge-scores) MERGE_SCORES="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "ERROR: unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done

merge_scores() {
  local incoming="$1"
  local target="${2:-results/metrics/scenario_scores.jsonl}"
  python3 - "$incoming" "$target" <<'PY'
import json
import pathlib
import sys

incoming = pathlib.Path(sys.argv[1])
target = pathlib.Path(sys.argv[2])
prompt_default = "assetopsbench-6d-v1"

def key(row):
    return (
        row.get("run_name"),
        row.get("scenario_id"),
        row.get("trial_index"),
        row.get("judge_model"),
        row.get("judge_prompt_version") or prompt_default,
    )

rows = []
seen = set()
if target.exists():
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows.append(row)
        seen.add(key(row))
added = 0
for line in incoming.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    k = key(row)
    if k in seen:
        continue
    rows.append(row)
    seen.add(k)
    added += 1
target.parent.mkdir(parents=True, exist_ok=True)
tmp = target.with_suffix(target.suffix + ".tmp")
tmp.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
tmp.replace(target)
print(f"merged {added} new score row(s) into {target}")
PY
}

if [ -n "$MERGE_SCORES" ]; then
  merge_scores "$MERGE_SCORES"
  exit 0
fi

if [ -z "$INSTANCE" ] || [ -z "$ZONE" ] || [ -z "$BATCH_ID" ]; then
  usage >&2
  exit 2
fi
if ! [[ "$PARALLEL" =~ ^[0-9]+$ ]] || [ "$PARALLEL" -lt 1 ]; then
  echo "ERROR: --parallel must be a positive integer" >&2
  exit 2
fi

DEST_DIR="$DEST_ROOT/$BATCH_ID"
mkdir -p "$DEST_DIR/logs" "$DEST_DIR/results"

scp_cmd() {
  printf 'gcloud compute scp --tunnel-through-iap --zone %q %q:%q %q\n' \
    "$ZONE" "$INSTANCE" "$1" "$2"
}

run_scp() {
  local remote="$1" dest="$2"
  if [ "$DRY_RUN" = "1" ]; then
    scp_cmd "$remote" "$dest"
    return 0
  fi
  gcloud compute scp --tunnel-through-iap --zone "$ZONE" "$INSTANCE:$remote" "$dest"
}

# Small files first so operators quickly get enough state to make decisions.
run_scp "$REMOTE_ROOT/logs/gcp_${BATCH_ID}_manifest.tsv" "$DEST_DIR/logs/" || true
run_scp "$REMOTE_ROOT/logs/gcp_${BATCH_ID}_manifest.jsonl" "$DEST_DIR/logs/" || true
run_scp "$REMOTE_ROOT/logs/gcp_${BATCH_ID}_state.tsv" "$DEST_DIR/logs/" || true
run_scp "$REMOTE_ROOT/results/metrics/scenario_scores.jsonl" "$DEST_DIR/results/scenario_scores.remote.jsonl" || true

manifest="$DEST_DIR/logs/gcp_${BATCH_ID}_manifest.tsv"
if [ "$DRY_RUN" = "1" ]; then
  if [ ! -s "$manifest" ]; then
    echo "# Raw run dirs are read from $manifest when present."
    exit 0
  fi
  awk -F'\t' 'NR > 1 && $4 { print $4 }' "$manifest" | sort -u | while IFS= read -r run_dir; do
    [ -n "$run_dir" ] || continue
    scp_cmd "$REMOTE_ROOT/$run_dir" "$DEST_DIR/"
    scp_cmd "$REMOTE_ROOT/results/judge_logs/$(basename "$run_dir")" "$DEST_DIR/results/judge_logs/"
  done
  exit 0
fi

if [ -s "$DEST_DIR/results/scenario_scores.remote.jsonl" ]; then
  merge_scores "$DEST_DIR/results/scenario_scores.remote.jsonl"
fi

if [ ! -s "$manifest" ]; then
  echo "WARNING: manifest not found after pull: $manifest" >&2
  exit 0
fi

export SMARTGRID_COMPUTE_ZONE="$ZONE"
export SMARTGRID_COMPUTE_INSTANCE="$INSTANCE"

awk -F'\t' 'NR > 1 && $4 { print $4 }' "$manifest" | sort -u | while IFS= read -r run_dir; do
  [ -n "$run_dir" ] || continue
  printf '%s\t%s\n' "$REMOTE_ROOT/$run_dir" "$DEST_DIR/"
  printf '%s\t%s\n' "$REMOTE_ROOT/results/judge_logs/$(basename "$run_dir")" "$DEST_DIR/results/judge_logs/"
done | xargs -n 2 -P "$PARALLEL" sh -c '
  remote="$1"; dest="$2"
  mkdir -p "$dest"
  gcloud compute scp --recurse --tunnel-through-iap --zone "$SMARTGRID_COMPUTE_ZONE" "$SMARTGRID_COMPUTE_INSTANCE:$remote" "$dest" || true
' sh
