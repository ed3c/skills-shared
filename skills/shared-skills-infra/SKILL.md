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
python3 $INFRA bind <name> --repo <repo> [--upstream <來源>]   # 釘／重釘 binding
```

`check` exit 0 乾淨｜1 有裁決被違反｜3 有欠帳（binding 過期、治理中的 repo 不在磁碟上、
槽位名已不在登記表）——**欠帳＝欠一次動作，不是壞掉**；`report` exit 3 有待裁項（**待裁不是失敗**）。
`install` 結尾就是跑一次 `check` 並原封回傳它的碼（含 3）：接線說 0、閘說 3，就是這個閘要終結的無聲狀態。

## binding：body 通用、binding 綁宿主

判準一句話：**原封不動搬到另一個 repo，它還為真嗎？不為真就是 binding。**
槽位＝`<repo>/.skill-bindings/<name>/`——目錄，因為一次 retarget 產生多份記錄（取捨帳、
舊版快照、該 repo 的全景圖）。其中 `binding.md` 是契約，四欄缺一不可：

```yaml
skill: <name>            # 與槽位同名；不同名＝這份記錄是從別處抄來的，已就地失真
upstream: <來源>          # 從哪個上游 retarget 過來
retargeted_at: <日期>
body_version: <retarget 當下共用 body 的內容 hash>   # 由 bind 蓋章，不手算
```

三態在輸出與 exit code 都長得不一樣——混在一起就是「每次踩到才發現」的成因：

| 狀態 | 判準 | 出口 |
|---|---|---|
| 未 retarget | 槽位不存在 | 計入 `BINDINGS … not retargeted`，exit 0。**缺席不是壞掉**：用共用 body 的通用形態 |
| 已 retarget | `body_version` == 現行 body hash | 計入 `BINDINGS … current`，exit 0 |
| binding 過期 | `body_version` ≠ 現行 body hash | `SURFACE BINDING-STALE`，exit 3 |
| 記錄本身壞了 | 缺 `binding.md`／缺欄位／`skill:` 與槽位不符／frontmatter 區塊沒收尾 | `FAIL BINDING-INCOMPLETE`，exit 1 |

還有兩種「看不到」，它們一律計數＋surface，絕不併進上面任何一格——沉默地消失就跟「全部乾淨」
長得一模一樣：

| 狀態 | 判準 | 出口 |
|---|---|---|
| 治理中但不在磁碟 | `sites.local.json` 有這個 repo，機器上沒有 | `SURFACE UNREACHABLE-PROJECT`＋`PROJECTS … unreachable`，exit 3 |
| 槽位名已不在登記表 | `.skill-bindings/<name>/` 的 `<name>` 未登記為共用 | `SURFACE ORPHAN-BINDING`，exit 3（改名／除籍會一次讓五個 repo 的帳本靜音） |

`body_version` 是「不想反覆返工」的機制答案：body 一動，`check` 立刻列出**所有**過期
binding——返工從「每次踩到才發現」變成有清單的一次性動作。對齊完跑 `bind` 重釘即可：
`upstream` 會被記得，frontmatter 以下的散文原封不動保留（那才是 retarget 帳本本體）。

`bind` 寧可拒絕也不抹平——每一種被拒的情形，寫下去的都是「沒有任何閘會再看一眼」的記錄：

| 拒絕 | 為什麼 |
|---|---|
| repo 不在 `sites.local.json` 的 `projects` | `check` 不會去別處看 |
| repo 在 `deferred_in` | 它跑自己那份副本，沒有共用 body 可釘；`check` 也刻意不讀它的 binding |
| repo 不在磁碟上 | 槽位的 `mkdir -p` 會把打錯的路徑變成一個 repo |
| 首次 binding 沒給 `--upstream` | 記了 retarget 卻沒記從哪來 |
| 既有記錄已是 `BINDING-INCOMPLETE` | `bind` 只重釘、不修：就地改寫會把 FAIL 變成 PASS，並繼承那份外來記錄的 `upstream`——**假的來歷通過閘，比失敗更糟** |
| 蓋出來的內容讀回來不是 `current` | 例如 `--upstream` 夾帶 `---` 或換行會提早收掉 frontmatter；**先蓋章再斷言＝每次拒絕都順手毀掉它拒絕寫的那份帳本** |

被拒的寫入**一個位元組都不落地**：`bind` 先寫 `.binding.md.staged`、用 `check` 同一支判定函式讀回來判，
過了才 `os.replace` 原子換上；不過就把暫存檔收掉，`binding.md` 保持原樣。

治理集合從哪來也一併釘死：`bind` 刻意**沒有** `--project` 旗標（旗標會整組取代已治理集合，等於讓寫入方
自己宣告目標「已治理」，一步跨過上表第一條），而 `--sites` 是同一扇門再往外一步——集合就住在那個檔案裡，
手寫一份指名目標 repo 即可。因此 `bind` 只接受 `check` 預設會讀的那個 `sites.local.json`，其餘一律拒絕：
**寫入方信任的治理集合，必須就是閘之後會走的那一個。**
槽位裡只有舊版快照、沒有 `binding.md`，仍然可以 `bind`（bindings 本來就多檔）——拒絕的是**讀起來是假的**記錄，
不是「檔案不只一份」。

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
