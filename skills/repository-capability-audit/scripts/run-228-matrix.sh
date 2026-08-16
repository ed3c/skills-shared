#!/usr/bin/env bash
# Run the full #228 matrix: 90 cells, 3 repositories x 2 hosts x 5 repetitions x 3 arms.
#
# Why this is a script you run rather than something the agent ran: each cell takes
# 3-4 minutes of real model time, and the agent session's background tasks are
# terminated after roughly 10-15 minutes. Ninety cells needs about 5.25 hours of
# uninterrupted execution, which only a terminal you control can give it.
#
# Idempotent by slice: a slice whose result file already exists is skipped, so an
# interrupted run resumes at slice granularity. No cell is ever run twice --
# #228 forbids retries, and slicing partitions the matrix rather than resuming
# inside one.
set -euo pipefail

REPO=/Users/neon/skills-shared
OUT="${1:-$HOME/rca-matrix-228}"
RUNNER="$REPO/skills/repository-capability-audit/scripts/run_pilot_matrix.py"

if [ ! -f "$RUNNER" ]; then
  echo "FATAL: runner not found at $RUNNER" >&2
  exit 1
fi
for binary in claude codex; do
  command -v "$binary" >/dev/null || { echo "FATAL: $binary not on PATH" >&2; exit 1; }
done

REPOSITORIES=("psf/requests" "spf13/cobra" "sindresorhus/slugify")
HOSTS=("claude-code" "codex-cli")

mkdir -p "$OUT"
slice_index=0
for repository in "${REPOSITORIES[@]}"; do
  for host in "${HOSTS[@]}"; do
    slice_index=$((slice_index + 1))
    slug="$(printf '%s' "$repository" | tr '/' '_')__${host}"
    slice_dir="$OUT/$slug"
    if [ -f "$slice_dir/pilot-result.json" ] || [ -f "$slice_dir/matrix-result.json" ]; then
      echo "[$slice_index/6] SKIP $slug -- already complete"
      continue
    fi
    echo "[$slice_index/6] RUN  $slug -- 15 cells, roughly 50 minutes"
    python3 "$RUNNER" \
      --output "$slice_dir" \
      --repetitions 5 \
      --only-repository "$repository" \
      --only-host "$host"
  done
done

echo
echo "All six slices complete. Merge and analyse with:"
echo "  python3 $REPO/skills/repository-capability-audit/scripts/merge_matrix_slices.py --input $OUT"
