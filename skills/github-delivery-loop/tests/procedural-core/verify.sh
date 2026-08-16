#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
checker="$root/scripts/check_procedural_core.py"

python3 "$checker" --root "$root"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
cp -R "$root/." "$tmp/skill"

python3 - "$tmp/skill/SKILL.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
s = s.replace("**DL-04 — Execute local verification.**", "**DL-X04 — Execute local verification.**", 1)
p.write_text(s, encoding="utf-8")
PY
if python3 "$checker" --root "$tmp/skill" >/dev/null 2>&1; then
  echo 'FAIL missing procedure atom was accepted' >&2
  exit 1
fi

rm -rf "$tmp/skill"
cp -R "$root/." "$tmp/skill"
python3 - "$tmp/skill/SKILL.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
needle = "**DL-03 — Bind the evidence contract.**"
s = s.replace(needle, needle + " GitHub Actions billing is universal law.", 1)
p.write_text(s, encoding="utf-8")
PY
if python3 "$checker" --root "$tmp/skill" >/dev/null 2>&1; then
  echo 'FAIL GitHub domain leakage into portable core was accepted' >&2
  exit 1
fi

rm -rf "$tmp/skill"
cp -R "$root/." "$tmp/skill"
python3 - "$tmp/skill/SKILL.md" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
s = s.replace("`bash tests/merge-gate/verify.sh` |", "`documented-only` |", 1)
p.write_text(s, encoding="utf-8")
PY
if python3 "$checker" --root "$tmp/skill" >/dev/null 2>&1; then
  echo 'FAIL hard law without executable assertion was accepted' >&2
  exit 1
fi

echo 'PASS procedural core atoms + domain leakage + executable assertion controls'
