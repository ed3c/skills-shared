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

## 與絕對路徑解耦

版控的 `registry.json` **只存裁決，不存任何機器路徑**；路徑全在 `sites.local.json`
（gitignored）或旗標。所以這個 checkout 放在哪個目錄都能用，clone 到別台機器也一樣。

| 事實 | 住哪 | 進 git？ |
|---|---|---|
| 誰是共用、誰是 repo 自有、為什麼 | `registry.json` | ✅ |
| user 層兩個 surface 在哪、要治理哪些專案、哪些專案的 Claude 側要轉發樁 | `sites.local.json` | ❌ |
| canonical 在哪 | 由 `__file__` 推導 | — |

## 指令

```bash
INFRA=~/.agents/skills/shared-skills-infra/scripts/shared_skills.py
python3 $INFRA install --project <repo> [--project …] [--claude-forwarder <repo-name>]
python3 $INFRA check     # T0：已登記的裁決有沒有被違反（零網路）
python3 $INFRA report    # 決策佇列：同名多份、尚未裁決、以及延後裁決的清單＋內容 hash
python3 $INFRA link <name>
python3 $INFRA adopt <name> --from <path> --why "…" [--defer <repo>] [--dry-run]
python3 $INFRA merge <name> --from <path> --from <path> [--from …] [--dry-run]
```

exit 0 乾淨｜**1 有裁決被違反／工具拒絕**｜**3 待人裁或無事可做**（`report` 有待裁項、
`merge` 有衝突或根本沒東西可折）。1 與 3 永遠不可互換：把「沒東西可做」印成 1，
看的人會去找一條不存在的違規。

## 收編前先聯集（`merge`）

多份分岔要合成一份時，**規則是聯集，不是投票**。只有一份版本擁有的檔案無條件保留——
第一次收斂用內容 hash 多數決，整個模組因此消失；而那個「多數」還是假的：三份裡有兩份
是同一血統的批次匯入。聯集不會被算錯的票數騙。

| 情況 | 行為 | exit |
|---|---|---|
| 只有一份版本有這個檔 | 一律進聯集。工具**從命令列**重數一次來源，少一個就 `DROPPED` | 0 |
| 各版位元組相同 | 取一份 | 0 |
| 同名而內容異 | 印雙方**實際位元組數**／hash／路徑＋逐段 diff，**不自動選**，等人 accept／override | 3 |
| 全部檔案都要人裁、canonical 又還不存在 | 什麼都不建（空目錄＝一場看起來已完成的合併） | 3 |
| 兩個 `--from` 指到同一血統／只剩一份版本 | 沒東西可折。訊息指向 `adopt` | 3 |
| 同名一邊是檔、一邊是目錄 | **動工前**就拒絕並說要改名哪一邊，不留 `.merging` 殘骸 | 1 |
| `--from` 指的路徑不是目錄 | 這是壞掉的請求，不是空的請求 | 1 |
| 真的掉了檔案／位元組被改 | 半成品留在 `.<name>.merging`，canonical 不動 | 1 |

exit 3 **不是唯讀**：沒衝突的那部分照樣物化進 canonical，衝突檔保留 canonical 既有位元組
（漏掉它＝用省略的方式刪掉一個沒人裁的檔）。唯一什麼都不建的 exit 3 是上表第四列。

**重數從命令列開始，不從計劃開始**：驗證會把每個 `--from` 重新解析一次。若改用規劃器已經
解析好的清單，一個「解析時就掉了一個 `--from`」的缺陷會拿它自己捏造的清單來對帳——聯集縮水
卻回報成功，正是當初弄丟模組的那個形狀。

**目的地本身也算一份版本**：canonical 已有的同名檔只會被 diff，不會被覆寫。被取代的
canonical 一律搬進 `--backup-dir`（預設 `$TMPDIR/shared-skills-superseded`），不刪；
同一天第二次合併另立紀錄，不會蓋在第一份上。
只有一份來源、目的地又還不存在＝那是 `adopt`（它還會登記），不是 `merge`。

**聯集的單位是檔案**：沒有任何檔案的空目錄不會被帶進 canonical（git 本來就記不住空目錄），
但會印一行 `NOTE` 點名它——讓它消失在 exit 0 底下，就是這個動詞存在要防的那種悄悄變少。

## clone 下來怎麼接線

```bash
git clone <private-repo> ~/.agents/skills-shared
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/shared_skills.py \
  install --project ~/proj-a --project ~/proj-b --claude-forwarder proj-b
```

`install` 做三件事：把路徑寫進 `sites.local.json`、把每個共用 skill 連上 user 層兩個 surface
與各專案、最後跑一次 `check`。**冪等**，換機器或搬動 checkout 後重跑即復原
（symlink 存的是路徑，搬完舊連結會先以 `WRONG-TARGET` 報錯而不是靜默指錯地方）。

新專案只要 `install --project <新 repo>`。共用 skills 其實在 user 層就已對所有專案可見；
專案層那份 symlink 是給**該 repo 自己的閘與文件用路徑引用**的，不是給發現用的。

### 兩種專案側形態（用參數選，不自動猜）

| 形態 | 產生什麼 | 給誰 |
|---|---|---|
| 預設 | `<repo>/.claude/skills/<name>` symlink | 大多數 repo |
| `--claude-forwarder <repo>` | 帶 `disable-model-invocation` 與 `$ARGUMENTS` 的轉發樁 | 家規要求樁內容的 repo（實例：ix-agy 的 `check_skill_forwarders.py`） |

專案側一律用**絕對路徑**指向 canonical：相對的 `.claude → ../../.agents` 一跳，
在 fork 過的 repo 會解析到它自己的本地副本而不是 canonical——連結會靜默指錯東西。

## 延後裁決（`deferred_in`）

收編某個 skill 時，若某些 repo 的版本**不在這次裁決範圍內**，用 `--defer <repo>`：
它們的副本原地保留、登記進 `deferred_in`，`check` 不當違規、`report` 持續列為待辦。
掃掉它們＝替人裁決；不記錄＝讓閘對一個沒人回答的問題長紅。兩者都不誠實。

## 這個閘刻意不進 CI

它的判準橫跨五個 repo 的絕對路徑與 user 層目錄，**在 CI 容器裡物理上不可重現**。
硬接進 pre-commit 只會製造一個永遠紅或永遠被跳過的假閘。它是本機治理閘，手動或
session 起手跑；要進 CI 得先設計成密封的（例如各 repo 只驗自己那一側）。
