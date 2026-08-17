#!/usr/bin/env bash
# Run the #230 leave-one-rule-out live ablation: 13 rules x 2 hosts = 26 cells.
#
# Why this is a script you run rather than something the agent ran: each cell
# takes several minutes of real model time and the agent session's background
# tasks are terminated after roughly 10-15 minutes -- the same reason
# run-228-matrix.sh is a human-run terminal script, see there for the full
# rationale.
#
# Idempotent by slice: a rule/host pair whose receipt already exists is
# skipped, so an interrupted run resumes at slice granularity. No cell is run
# twice.
#
# This wires generated treatment files into run_agent_cell.py. It does not
# decide LIVE_MODEL_SUPPORTED/NOT_SUPPORTED -- that admission decision reads
# the resulting receipts against modules/agent-effectiveness.md's thresholds,
# and evals/live-evidence-state.json is only ever updated from real receipts,
# never from this script's exit code.
set -euo pipefail

REPO=/Users/neon/skills-shared
SKILL_ROOT="$REPO/skills/repository-capability-audit"
OUT="${1:-$HOME/rca-ablation-230}"
TREATMENTS_DIR="$OUT/treatments"
RUNNER="$SKILL_ROOT/scripts/run_agent_cell.py"
GENERATOR="$SKILL_ROOT/scripts/generate_ablation_treatment.py"

if [ ! -f "$RUNNER" ]; then
  echo "FATAL: runner not found at $RUNNER" >&2
  exit 1
fi
for binary in claude codex; do
  command -v "$binary" >/dev/null || { echo "FATAL: $binary not on PATH" >&2; exit 1; }
done

mkdir -p "$OUT"
python3 "$GENERATOR" --skill-file "$SKILL_ROOT/SKILL.md" --output-dir "$TREATMENTS_DIR"

RULES=()
for n in $(seq -w 1 13); do
  RULES+=("RCA-0$n")
done
HOSTS=("claude-code" "codex-cli")

slice_index=0
total=$(( ${#RULES[@]} * ${#HOSTS[@]} ))
for rule_id in "${RULES[@]}"; do
  for host in "${HOSTS[@]}"; do
    slice_index=$((slice_index + 1))
    receipt="$OUT/${rule_id}__${host}.receipt.json"
    if [ -f "$receipt" ]; then
      echo "[$slice_index/$total] SKIP ${rule_id}__${host} -- already complete"
      continue
    fi
    echo "[$slice_index/$total] RUN  ${rule_id}__${host}"
    echo "  treatment file: $TREATMENTS_DIR/candidate_minus_${rule_id}.md"
    echo "  wire this into run_agent_cell.py --profile candidate_minus_${rule_id} \\"
    echo "    --treatment-file $TREATMENTS_DIR/candidate_minus_${rule_id}.md --output $receipt"
    echo "  (agent/evaluator command and identity flags are host-specific; see" \
         "modules/agent-effectiveness.md's generic execution adapter section)"
  done
done

echo
echo "All $total cells enumerated. This script prints the exact run_agent_cell.py"
echo "invocation shape per cell rather than executing it, because the agent/evaluator"
echo "command for claude-code and codex-cli is a host-specific adapter that must be"
echo "supplied, not invented here (#230's own receipt binding requires named identities)."
echo "Once receipts exist under $OUT, bind them into evals/live-evidence-state.json's"
echo "rules[RCA-0XX].pairs the same way an existing pair is recorded there."
