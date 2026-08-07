# agent-docs — 每個 repo／host 的 CLAUDE.md 與 AGENTS.md 的集中真源

```
agent-docs/
  manifest.json          誰被管、管哪幾檔、哪些缺席是登記過的、預算數字
  HOST-SURFACES.md       兩個 host 各讀哪些檔、順序、在哪裡靜默失效（官方 URL 錨定）
  _template/             新專案用：CLAUDE.md（一行 import + host 尾巴）、AGENTS.md（路由層骨架）
  <repo 目錄名>/         該 repo 的受管檔；repo 內那份是投影
  _global/claude|codex/  ~/.claude/CLAUDE.md、~/.codex/AGENTS.md
```

方向**永遠**是 `agent-docs → 目標`。目標端直接改，`check` 會判 DRIFT。

```bash
S=~/.agents/skills-shared/skills/forgejo-delivery-loop/scripts/agent_docs.py
python3 $S selftest                 # 先證閘會紅（植入五種缺陷 + 兩個乾淨對照）
python3 $S check                    # T0，零網路
python3 $S diff                     # DRIFT 的逐行差異
python3 $S apply --to-targets --dry-run
python3 $S apply --to-targets       # 寫下去；跑完自動重跑 check
```

## 為什麼只比位元、不比語意

「這兩份說的是同一件事」正是會安靜出錯的那種判斷。2026-08-08 納管當下，
`ts-skill-bettor` 與 `skill-bettor` 的文件已經分岔：大迴圈編排角色不同
（`Opus 5` vs `Fable`），且 `ts-` 的 `AGENTS.md` 還留著已裁決要移進全局法則層的八條設計規範。
兩份都是合法 markdown、都被各自的 host 完整讀進 context、沒有任何機制吭一聲。
`check` 就是那一聲。

**納管採現況逐位元收編，不順手對齊。** baseline 要為真而不是為齊；
兩者該不該收斂成一份是人裁，不由 `apply` 代決。

## 五種輸出互不塌陷

| 輸出 | 意思 |
|---|---|
| `OK` | 受管且位元相同 |
| `DRIFT` / `MISSING` | 受管但不一致／目標端不存在 |
| `ABSENT` | manifest 登記過的缺席（例：ix-agy 沒有 root CLAUDE.md） |
| `UNMANAGED` | manifest 登記過的非目標（例：bettor-arena） |
| `UNREGISTERED` | 目標端冒出沒人裁決的 CLAUDE.md／AGENTS.md — **FAIL**，因為它已經在被 host 載入 |

最後一列是刻意的：沒登記的文件不是「待裁決」，它已經生效了，急迫度不同。
與 `shared_skills.py` 抓未登記 skill 同一個形狀、同一個理由。

## 預算不是文風

`AGENTS.md` 單檔 ≥ `project_doc_max_bytes`（32 KiB）＝ **FAIL**：Codex 到達上限就停止加入後續檔案，
尾巴**靜默消失**。`CLAUDE.md` > 200 行＝ **SURFACE**：整份照載，但遵循度下降。
兩者機制不同，所以嚴重度不同。錨在 `HOST-SURFACES.md` §3。

## 新專案怎麼開

1. `cp _template/{CLAUDE.md,AGENTS.md} agent-docs/<新 repo 目錄名>/`，把 `<...>` 佔位全部填掉
   （**留著佔位＝那一格還沒被想過，不是預設值**）。
2. `manifest.json` 加一筆 target；沒有的檔案登記進 `absent{}`，別留空。
3. 把 repo 路徑加進 `sites.local.json` 的 `projects[]`（機器路徑只住那裡）。
4. `python3 $S apply --to-targets` → `python3 $S check`。

## 誰掛了 pre-commit，誰沒有（缺席要有名字）

閘由各 repo 的 `.githooks/pre-commit` 呼叫 `scripts/pre-commit-agent-docs.sh`，六行轉發，
只在 commit 真的 stage 了 `CLAUDE.md`／`AGENTS.md` 時才跑。

| repo | 狀態 | 理由 |
|---|---|---|
| bettor-arena | 已掛並 commit | — |
| ix-agy | 已掛並 commit（同時首次設 `core.hooksPath`） | 原本無任何 hook |
| skill-bettor | **不掛**（2026-08-08 人裁） | `.githooks/pre-commit` 在它的 `PROTECTED_CONTROL_FILES`（`scripts/validate_molecular_commit_message.py`）內，改它要交 GCR molecular lineage：11 個必填欄＋verification envelope＋canonical plan-package／small-loop／final-repo 路徑。一次 hook 安裝沒有那條血緣，硬編就是假 lineage |
| ts-skill-bettor | **不掛**（2026-08-08 人裁） | 同一份保護名單（TS 版），**再加**一條更硬的：該 repo 2026-08-05 `2478647` 刻意刪掉自己的 `pre-commit`，理由是「無路徑作用域的 hook 讓一個面的關切擋住所有 commit」，且其 header 已論證「a mutable or missing checkout must not decide whether this independent repository can commit」 |

**不要因為「四個 repo 應該一致」就把後兩個補上**——那是裁決，不是漏掉。
兩者的漂移仍被全掃 `check` 抓得到（本輪就抓到 skill-bettor 的 `AGENTS.md`），只是不在 commit 當下擋。
差別是時機不是覆蓋率：**沒有 commit 閘的 repo，靠的是有人記得跑 `check`**——那正是這個閘想取代的東西，所以這兩格是已知的、有名字的弱點，不是均勻的保護。

## 不在管理範圍（刻意，理由在 manifest 的 `unmanaged_by_design`）

`settings.json`／`config.toml` 兩個 host、兩個層級都不鏡像：它們是**強制層**不是 context，
內容錯的代價不同級；且含機器狀態與憑證面，集中鏡像等於把秘密複製到第二個位置。
它們的權威形狀與優先序寫在 `HOST-SURFACES.md` §2。
