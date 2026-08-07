#!/usr/bin/env bash
# verify.sh — harness-mvp T0 hard gate (八大基座 分層驗證). Exit 0=PASS, 2=FAIL. Fable-5 mechanisms baked in.
#   --fast : hermetic only (skip real integrations / heavy models) for the iterate inner loop.
set -uo pipefail; HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"; PY="$HERE/venv/bin/python"
FAST=false; [ "${1:-}" = "--fast" ] && FAST=true
fail() { echo "VERIFY: FAIL — $1" >&2; exit 2; }
[ -x "$PY" ] || fail 'no venv python'
"$PY" -c 'import pytest' 2>/dev/null || "$HERE/venv/bin/pip" install --quiet pytest >/dev/null 2>&1

# design-gate (Fable-5): every [x] SC must have a tests/ reference; any deleted/changed EXISTING test must
# leave a PLAN.md HUMAN-AUTHORIZED mark. NOTE: --diff-filter=MD scopes this to Modified/Deleted only — a purely
# ADDED test file (even if staged) must NOT trip the gate (skillgate cc-20260711: new tests aren't a weakening).
# ⚠ E2 (cc-20260712): this grep is an AUDIT TRIPWIRE, NOT enforcement of "human" — a driver CAN write the mark
# (round-10 agy forged one). The REAL gate is the judge reviewing git diff before commit (that caught the forgery);
# recipe-not-engine = commit gate always human. Don't over-claim "design-gate enforces".
for sc in $(grep -oE '\[x\] SC[0-9]+' "$HERE/PROMPT.md" 2>/dev/null | grep -oE 'SC[0-9]+'); do
  grep -rwqE "$sc" "$HERE/tests/" 2>/dev/null || fail "design-gate: $sc marked done but no tests/ reference"
done
if git -C "$HERE" rev-parse --git-dir >/dev/null 2>&1; then
  changed=$(git -C "$HERE" diff --name-only --diff-filter=MD -- 'tests/*' 2>/dev/null; git -C "$HERE" diff --cached --name-only --diff-filter=MD -- 'tests/*' 2>/dev/null)
  if [ -n "$changed" ] && ! grep -qE '^- round [0-9]+[a-z]* HUMAN-AUTHORIZED:' "$HERE/PLAN.md" 2>/dev/null; then
    fail "design-gate: existing test(s) changed [$changed] but no HUMAN-AUTHORIZED entry in PLAN.md"
  fi
fi

echo "VERIFY: pytest"
if $FAST; then "$PY" -m pytest "$HERE/tests" -q -m 'not integration' || fail 'pytest (fast) red'
else "$PY" -m pytest "$HERE/tests" -q || fail 'pytest red'; fi
echo "VERIFY: PASS"; exit 0
