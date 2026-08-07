#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
checker="$test_dir/../../scripts/check_redaction.py"

# Mechanism control: substring matching works for an arbitrary injected token.
python3 "$checker" --deny-token restricted-origin "$test_dir/fixtures/good"

if python3 "$checker" --deny-token restricted-origin "$test_dir/fixtures/hollow"; then
  echo "hollow fixture unexpectedly passed" >&2
  exit 1
fi

# Policy control: exercise the shipped FORBIDDEN list itself. `--deny-token`
# REPLACES that list, so the cases above would stay green even if FORBIDDEN were
# emptied or misspelled. The token is assembled at run time and written to a temp
# dir so its literal form never lands in this repo — which is the very leak the
# checker exists to prevent.
policy_dir="$(mktemp -d)"
trap 'rm -rf "$policy_dir"' EXIT
python3 - "$policy_dir" <<'PY'
import sys
from pathlib import Path

from_token = "skill" + "-bettor"
Path(sys.argv[1], "leak.md").write_text(
    f"# planted\n\nupstream origin is /Users/neon/{from_token}\n", encoding="utf-8"
)
PY

if python3 "$checker" "$policy_dir"; then
  echo "shipped FORBIDDEN list did not catch the planted upstream identifier" >&2
  exit 1
fi

python3 "$checker" "$test_dir/fixtures/good"
