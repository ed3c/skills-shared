#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
entrypoint="${test_dir}/refactor_ab.py"

# 1. 植入缺陷控制先跑：治療體漂移、凍結檔缺席、老強度被弱化、
#    宣稱數字說謊、路徑退回主機投影——每一項都要以自己的名字被拒。
python3 "$entrypoint" --selftest

# 2. 真跑同語料的三臂比較。A 與 B0 會被自己宣告的指令擋住，這是被量到的結果，
#    不是被略過的臂——它們留在 denominator 裡。
python3 "$entrypoint" >/dev/null

echo "PASS knowledge-continuity frozen treatments + matched hermetic A/B"
