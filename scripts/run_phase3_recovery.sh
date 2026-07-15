#!/usr/bin/env bash
set -euo pipefail

ROOT="${ROOT:-/home/ubuntu/vlm-bench}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
MANIFEST="${MANIFEST:-$ROOT/data/processed-v2/manifests/development.jsonl}"
DATA_ROOT="${DATA_ROOT:-$ROOT/data/processed-v2}"
BASELINE_DIR="${BASELINE_DIR:-$ROOT/results/recovery-v2-development-baseline}"
SEARCH_BASELINE_DIR="${SEARCH_BASELINE_DIR:-$ROOT/results/recovery-v2-search-baseline}"
SMOKE_DIR="${SMOKE_DIR:-$ROOT/results/recovery-v2-smoke}"
ABLATION_DIR="${ABLATION_DIR:-$ROOT/results/recovery-v2-one-block}"
PHASE3_DIR="${PHASE3_DIR:-$ROOT/results/phase3-interaction-search-qwen25-vl-3b}"
PAIRWISE_DIR="${PAIRWISE_DIR:-$ROOT/results/phase3-pairwise-worker-qwen25-vl-3b}"
LOG_DIR="${LOG_DIR:-$ROOT/logs}"

mkdir -p "$LOG_DIR"
exec 9>"$LOG_DIR/phase3-recovery.lock"
if ! flock -n 9; then
  echo "Another Phase 3 recovery launcher already holds $LOG_DIR/phase3-recovery.lock" >&2
  exit 1
fi

if [[ ! -x "$PYTHON" ]]; then
  echo "Missing Python environment: $PYTHON" >&2
  exit 1
fi
if [[ ! -s "$MANIFEST" ]]; then
  echo "Missing V2 development manifest: $MANIFEST" >&2
  exit 1
fi

export PYTHONPATH="$ROOT/src"
export CUDA_VISIBLE_DEVICES=0
cd "$ROOT"

echo "[$(date -u +%FT%TZ)] validating V2 dataset"
"$PYTHON" scripts/validate_dataset.py --manifest "$MANIFEST" --data-root "$DATA_ROOT"

echo "[$(date -u +%FT%TZ)] running/resuming one-example GPU smoke gate"
"$PYTHON" scripts/run_baseline.py \
  --manifest "$MANIFEST" \
  --data-root "$DATA_ROOT" \
  --output-dir "$SMOKE_DIR" \
  --limit 1

echo "[$(date -u +%FT%TZ)] running/resuming V2 development baseline"
"$PYTHON" scripts/run_baseline.py \
  --manifest "$MANIFEST" \
  --data-root "$DATA_ROOT" \
  --output-dir "$BASELINE_DIR"

echo "[$(date -u +%FT%TZ)] preparing the deterministic Phase 3 search split"
PYTHONPATH="$ROOT/src:$ROOT/scripts" "$PYTHON" - "$MANIFEST" "$PHASE3_DIR" "$BASELINE_DIR" "$SEARCH_BASELINE_DIR" <<'PY'
import json
import sys
from pathlib import Path

from run_phase3_interaction_search import prepare
from vlm_bench.io import read_jsonl, write_jsonl

manifest = Path(sys.argv[1])
phase3_dir = Path(sys.argv[2])
baseline_dir = Path(sys.argv[3])
search_baseline_dir = Path(sys.argv[4])
config = json.loads(Path("configs/phase3_interaction_search.json").read_text(encoding="utf-8"))
search_rows, _ = prepare(
    manifest,
    phase3_dir,
    int(config["search_examples_per_capability"]),
    int(config["seed"]),
)
baseline = {row["id"]: row for row in read_jsonl(baseline_dir / "predictions.jsonl")}
write_jsonl(search_baseline_dir / "predictions.jsonl", [baseline[row["id"]] for row in search_rows])
PY
SEARCH_MANIFEST="$PHASE3_DIR/prepared/search.jsonl"

echo "[$(date -u +%FT%TZ)] running/resuming two one-block ablation shards"
"$PYTHON" scripts/run_layer_ablation.py \
  --manifest "$SEARCH_MANIFEST" \
  --data-root "$DATA_ROOT" \
  --baseline-dir "$SEARCH_BASELINE_DIR" \
  --output-dir "$ABLATION_DIR" \
  --blocks 0-15 \
  --summary-stem blocks-00-15 \
  >"$LOG_DIR/recovery-ablation-00-15.log" 2>&1 &
ablation_low_pid=$!
"$PYTHON" scripts/run_layer_ablation.py \
  --manifest "$SEARCH_MANIFEST" \
  --data-root "$DATA_ROOT" \
  --baseline-dir "$SEARCH_BASELINE_DIR" \
  --output-dir "$ABLATION_DIR" \
  --blocks 16-31 \
  --summary-stem blocks-16-31 \
  >"$LOG_DIR/recovery-ablation-16-31.log" 2>&1 &
ablation_high_pid=$!

cleanup() {
  kill "$ablation_low_pid" "$ablation_high_pid" "${phase3_pid:-}" "${pairwise_pid:-}" 2>/dev/null || true
}
trap cleanup INT TERM EXIT
wait "$ablation_low_pid"
wait "$ablation_high_pid"

for block in $(seq -w 0 31); do
  prediction_path="$ABLATION_DIR/block-$block/predictions.jsonl"
  if [[ ! -s "$prediction_path" ]]; then
    echo "Missing completed ablation predictions: $prediction_path" >&2
    exit 1
  fi
done

common_args=(
  --manifest "$MANIFEST"
  --data-root "$DATA_ROOT"
  --baseline-predictions "$BASELINE_DIR/predictions.jsonl"
  --single-ablation-roots "$ABLATION_DIR"
)

echo "[$(date -u +%FT%TZ)] running search/validation and pairwise workers"
"$PYTHON" scripts/run_phase3_interaction_search.py \
  "${common_args[@]}" \
  --output-dir "$PHASE3_DIR" \
  --stages search,validate \
  >"$LOG_DIR/recovery-phase3-search-validation.log" 2>&1 &
phase3_pid=$!
"$PYTHON" scripts/run_phase3_interaction_search.py \
  "${common_args[@]}" \
  --output-dir "$PAIRWISE_DIR" \
  --stages pairwise \
  >"$LOG_DIR/recovery-phase3-pairwise.log" 2>&1 &
pairwise_pid=$!
wait "$phase3_pid"
wait "$pairwise_pid"

rm -rf "$PHASE3_DIR/pairwise"
cp -a "$PAIRWISE_DIR/pairwise" "$PHASE3_DIR/pairwise"
cp "$PAIRWISE_DIR/pairwise_summary.json" "$PHASE3_DIR/pairwise_summary.json"

"$PYTHON" - "$PHASE3_DIR" "$PAIRWISE_DIR" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

phase3_dir = Path(sys.argv[1])
pairwise_dir = Path(sys.argv[2])
main_state_path = phase3_dir / "pipeline_state.json"
pairwise_state_path = pairwise_dir / "pipeline_state.json"
main_state = json.loads(main_state_path.read_text(encoding="utf-8"))
pairwise_state = json.loads(pairwise_state_path.read_text(encoding="utf-8"))
main_state["stages"]["pairwise"] = pairwise_state["stages"]["pairwise"]
main_state["status"] = "complete"
main_state["completed_at"] = datetime.now(timezone.utc).isoformat()
main_state_path.write_text(json.dumps(main_state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY

PYTHONPATH="$ROOT/src:$ROOT/scripts" "$PYTHON" - "$PHASE3_DIR" <<'PY'
import sys
from pathlib import Path

from run_phase3_interaction_search import write_report

write_report(Path(sys.argv[1]))
PY

trap - INT TERM EXIT
echo "[$(date -u +%FT%TZ)] Phase 3 recovery pipeline complete"
