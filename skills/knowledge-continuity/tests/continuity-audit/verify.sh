#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${test_dir}/../.." && pwd)"
checker="${skill_dir}/scripts/check_knowledge_continuity.py"
gate="${skill_dir}/scripts/assert_continuity_audit.py"
work="$(mktemp -d "${TMPDIR:-/tmp}/work.XXXXXXXX")"
trap 'rm -rf "$work"' EXIT

# 1. 語意閘自身的正負控：每個植入缺陷都要以自己的名字被拒。
python3 "$gate" --selftest

# 2. 真跑一次產出→驗收的通路，而不是只驗閘。合規文件的紀錄必須綠。
(
  cd "$skill_dir"
  python3 "$checker" tests/check-knowledge-continuity/fixtures/good/doc.md \
    --quiet --audit-json "$work/good.json" >/dev/null
)
python3 "$gate" --audit "$work/good.json"

# 3. 有斷點的文件同樣要能產出**合法**紀錄：閘擋的是說謊的紀錄，不是壞文件。
#    hollow 文件的 exit code 非零，所以這一步不能被 set -e 吃掉。
(
  cd "$skill_dir"
  python3 "$checker" tests/check-knowledge-continuity/fixtures/hollow/doc.md \
    --quiet --audit-json "$work/hollow.json" >/dev/null || true
)
python3 "$gate" --audit "$work/hollow.json"
python3 - "$work/hollow.json" <<'PY'
import json, sys
record = json.load(open(sys.argv[1], encoding="utf-8"))
assert record["mechanical"]["exit_code"] == 2, "斷點文件的紀錄宣稱 exit 0"
assert record["mechanical"]["total_breaks"] > 0, "斷點文件的紀錄宣稱零斷點"
assert record["convergence"] == "MECHANICAL_ONLY", "機器自己宣告了收斂"
PY

# 4. 機械層全綠的紀錄仍然不得被寫成收斂——這是 SKILL.md 的法則，現在由閘執行。
python3 - "$work/good.json" "$work/converged.json" <<'PY'
import json, sys
record = json.load(open(sys.argv[1], encoding="utf-8"))
record["convergence"] = "CONVERGED"
json.dump(record, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
PY
if python3 "$gate" --audit "$work/converged.json" 2>/dev/null; then
  echo "機械層全綠被寫成 CONVERGED 卻通過了閘——人判斷層形同不存在" >&2
  exit 1
fi

echo "PASS knowledge-continuity continuity-audit shape + semantic gate"
