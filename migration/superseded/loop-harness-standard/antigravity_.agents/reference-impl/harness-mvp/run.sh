#!/usr/bin/env bash
# run.sh <driver> <target> [feedback_file]  — 八大基座 dispatcher (Fable-5: bind target, no hardcoded SC)
set -uo pipefail; cd "$(dirname "${BASH_SOURCE[0]}")"
DRIVER="${1:?driver: claude|agy|subagent}"; TARGET="${2:?target: absolute path the driver modifies}"
FB=""; [ -n "${3:-}" ] && [ -f "${3}" ] && FB="$(cat "${3}")"
read -r -d '' TASK <<EOF || true
Small-loop driver. Read CLAUDE.md/PROMPT.md/PLAN.md and TARGET=${TARGET}. Close ONE open SC; add a regression
test; append outcome to PLAN.md. Do NOT weaken verify.sh or delete passing tests.
${FB:+Graduation-judge feedback to address:
$FB}
EOF
case "$DRIVER" in
  claude) exec claude -p "$TASK" --permission-mode acceptEdits < /dev/null ;;
  agy) exec agy --mode accept-edits --add-dir "$(pwd)" -p "$TASK" < /dev/null ;;
  subagent) printf '%s\n' "$TASK" ;;
  *) echo 'usage: run.sh <claude|agy|subagent> <target> [feedback]' >&2; exit 64 ;;
esac
