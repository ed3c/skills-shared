#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
checker="$test_dir/../../scripts/check_knowledge_continuity.py"

# 1. 偵測器自我控制：四條規則各自的正負控，以及圖／程式碼區塊不得誤報。
python3 "$checker" --selftest

# 2. 合規文件必須全綠。這份 fixture 刻意把四種斷點都「寫對」，
#    所以它同時是「規則不會誤傷正常寫法」的證明。
python3 "$checker" "$test_dir/fixtures/good/doc.md" --quiet

# 3. 斷點文件必須紅，而且四條規則要各抓到至少一個——
#    只有總數會叫不夠，那樣單一規則壞掉會被其他規則掩蓋。
hollow_out="$(python3 "$checker" "$test_dir/fixtures/hollow/doc.md" --quiet || true)"
echo "$hollow_out"
for rule in KC-01 KC-02 KC-03 KC-04 KC-05; do
  if ! grep -qE "^\[FAIL\] $rule" <<<"$hollow_out"; then
    echo "$rule 沒有在斷點 fixture 上轉紅——該規則可能已失效" >&2
    exit 1
  fi
done

# 4. 退出碼契約：有斷點必須非零，否則接進迴圈時不會擋。
if python3 "$checker" "$test_dir/fixtures/hollow/doc.md" --quiet >/dev/null; then
  echo "斷點文件的 exit code 是 0，迴圈將無法偵測失敗" >&2
  exit 1
fi
