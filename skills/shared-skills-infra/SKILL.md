---
name: shared-skills-infra
description: |
  管理跨 repo 共用的基礎設施 skills：一個名稱要嘛是共用基礎設施（只有一份，住在
  ~/.agents/skills-shared，經 user 層 symlink 讓所有專案看到），要嘛是該 repo 真正差異化的
  自有 skill——不能兩者皆是。repo 自留同名副本會無聲影蓋共用版（兩個 host 的 project skill
  都優先於 user skill），這是同一個修法在五個 repo 被重覆發現的機制。
  觸發詞：共用 skill、skills 基礎設施、skill 漂移、同名影蓋、新 repo 接上共用 skills、
  shared-skills-infra。
  NOT for：某個共用 skill 自己的程序（去那個 skill）；判該不該新建 skill（write-a-skill）。
---

# shared-skills-infra — 共用基礎設施 skills 的治理

## 一條規則

**共用 ≠ 差異化。** 一個 skill 名稱只能是二選一：

| | 住哪 | 誰改 |
|---|---|---|
| **共用基礎設施** | `~/.agents/skills-shared/skills/<name>/`（本 repo，有 git 歷史） | 任一 repo 的執行經驗都回饋到這一份，全體立即受益 |
| **repo 自有** | `<repo>/.agents/skills/<name>/` | 只有該 repo；差異化屬於它自己的大迴圈 |

登記在 [`registry.json`](../../registry.json)（只存**裁決**，不存掃描結果——凍結的 hash 遲早跟現實
不一致）。沒登記的同名多份＝待人裁，不是失敗。

## 為什麼影蓋是無聲的

兩個 host 的 project-level skill 都優先於 user-level。所以某個 repo 在
`.claude/skills/<共用名>/` 放自己的版本時，**不會有任何錯誤**——它只是安靜地取代共用版，
於是那個 repo 的經驗再也回不到共用面，而共用面的修正也到不了它。
五個 repo 現況實測：同名多份 26 個，其中 24 個內容分岔、只有 2 個相同。

## 指令

```bash
INFRA=~/.agents/skills/shared-skills-infra/scripts/shared_skills.py
python3 $INFRA check     # T0：已登記的裁決有沒有被違反（零網路）
python3 $INFRA report    # 決策佇列：同名多份、尚未裁決的清單＋內容 hash
python3 $INFRA link <name>                       # 補上某共用 skill 的 user 層 symlink
python3 $INFRA adopt <name> --from <path> --why "…"   # 把某 repo 的副本收編成共用（搬不刪）
```

`check` exit 0 乾淨｜1 有裁決被違反｜`report` exit 3 有待裁項（**待裁不是失敗**）。

## 新 repo 怎麼接上

不需要接。共用 skills 住 user 層（`~/.agents/skills/` 與 `~/.claude/skills/`），
**所有專案自動看得到，包含未來新增的**。新 repo 要做的只有一件事：
把它登記進 `registry.json` 的 `subscribers`，讓 `report`／`check` 掃得到它，
從此它若偷放同名副本會被抓出來。

## 這個閘刻意不進 CI

它的判準橫跨五個 repo 的絕對路徑與 user 層目錄，**在 CI 容器裡物理上不可重現**。
硬接進 pre-commit 只會製造一個永遠紅或永遠被跳過的假閘。它是本機治理閘，手動或
session 起手跑；要進 CI 得先設計成密封的（例如各 repo 只驗自己那一側）。
