# PRD #1 切片帳本 — body／binding 拆分的待辦清單

PRD #1 自陳約 25 個切片、跨多個 session。這份帳本存在的理由只有一個：**沒有清單的多 session 工作，
每次開工都要重新普查一次才知道自己在哪裡**，而重新普查的成本高到讓人改為憑印象動手——那正是 #1
一開始要修的那種錯誤。

本檔記的是**量測值**，不是計畫。每一格都可以用底下那幾條命令重跑出來；跑出不同的值，以命令為準，
改本檔。

## 重新量測（零網路）

```bash
python3 scripts/check_body_neutrality.py --repo-root .      # 中性化棘輪
python3 scripts/check_binding_stale.py --repo-root .        # 本 repo 自己的 binding
python3 skills/shared-skills-infra/scripts/shared_skills.py check
python3 migration/hotfix_union.py --selftest
bash skills/shared-skills-infra/tests/verify.sh
```

各訂閱 repo 的 binding 要另外指 body 所在（見下方「已知阻擋 B2」）：

```bash
python3 scripts/check_binding_stale.py \
  --repo-root <consumer> --body-root <consumer>/.agents/skills
```

## 範圍：只剩三個外部 repo

| repo | 狀態 |
|---|---|
| `bettor-arena` | 在範圍內 |
| `ix-agy` | 在範圍內 |
| `antigravity` | 在範圍內 |
| `skill-bettor` | **擁有者於 2026-08-18 明令排除**，本遷移不再讀它、不再動它 |
| `ts-skill-bettor` | 同上 |

PRD 原文按五個 repo 寫（含「核心三 repo 多數決」那段病理分析）。排除兩個之後，
**PRD 的多數決病理描述仍然成立**（它記的是已發生的損害），但任何「三份取多數」的**做法**在
剩下的三個 repo 上更不成立：`bettor-arena` 手上是逐字副本、沒有獨立血統。聯集仍是唯一合法規則。

## 機制現況（2026-08-18 量測）

| PRD 要求的機制 | 狀態 | 實際位置 |
|---|---|---|
| `body-not-neutral` 閘 | PASS | [`../skills/shared-skills-infra/scripts/check_body_neutrality.py`](../skills/shared-skills-infra/scripts/check_body_neutrality.py)，`scripts/` 有薄轉發 |
| `binding-stale` 閘 | PASS | [`../skills/shared-skills-infra/scripts/check_binding_stale.py`](../skills/shared-skills-infra/scripts/check_binding_stale.py) |
| 兩閘併入 `check` | PASS | `shared_skills.py` 的 `_body_and_binding()`：中性化 FAIL、binding SURFACE，權重不同 |
| 聯集合併器 | PASS | [`hotfix_union.py`](hotfix_union.py)，`--selftest` 含 good/hollow 與計數斷言 |
| `.skill-bindings/<name>/` 槽位 | PASS（機制）／FAIL（資料） | 三個 repo 共 12 個槽位存在，**12 個全部不符四欄契約**，見阻擋 B1 |
| 命令生成器 | PASS（新增於本切片） | `shared_skills.py commands [--apply]` |
| registry `commands` 別名 | 機制 PASS／資料 ABSENT | 生成器讀 `commands: []`；**目前沒有任何 entry 登記別名**，見阻擋 B3 |

### 與 PRD 字面的三處差異（刻意，需人裁）

1. **`body-not-neutral` 是棘輪，不是硬性 0 命中。** PRD 寫「命中即 FAIL」。實作改為
   `evals/body-neutrality.json` 記每檔今日欠額，只准降不准升。理由寫在該檔 docstring：第一天跑會噴
   數百行，硬 FAIL 的唯一結局是被關掉。今日實測 **17 行、15 個 portable 檔**（起點 868／399）。
   PRD 驗收條件「回報 0 命中」**尚未達成**，但方向被機械鎖住。
2. **registry 停在 `v2`，沒有升 v3。** PRD 的 v3 ＝ 加 `commands` ＋ 移除 `repo_owned`。`commands`
   已可用（讀取端做完，schema 對未知鍵寬容）；`repo_owned` 的移除依賴切片 23／24 建出兩個 private
   repo，那還沒發生。**做一半就叫 v3，比留在 v2 更糟**——版本號會宣稱一個不存在的形狀。
3. **`commands` 生成器不掛進 `install`。** PRD 說「`install` 多一個 target」。目前 `install` 不呼叫它：
   三個 repo 的 `.claude/commands/` 共 30 個檔，多數是手寫、含真正的 host binding（例如 `ix-agy`
   的 `fold-in.md` 寫著該 repo 的 owner 候選清單）。掛進 `install` 會讓下一次 `install` 去碰它們。
   生成器本身**永遠不覆寫非自己產出的檔**（靠 marker 判定），碰到手寫檔走 SURFACE；等那些檔的
   binding 搬進 `.skill-bindings/` 之後再掛進 `install`。

## 已知阻擋（做下一片之前要先處理的）

- **B1 — 12 個 live binding 槽位全部不符契約。** 量測：`bettor-arena` 4 個、`ix-agy` 3 個、
  `antigravity` 5 個。其中 **10 個根本沒有 `binding.md`**，另 2 個（兩個 repo 的
  `html-for-decisions`）寫的是 `body_commit: <短 git sha>` 而非 `body_version: <sha256>`。
  也就是說 **`stale` 這個狀態今天沒有任何生產端會發射**：三態機只有 selftest 在構造它。
  「閘寫好了」與「閘量到東西」是兩件事，目前只有前者。
- **B2 — 閘找不到 consumer 的 body（已修）。** `check_binding_stale.py` 原本把 body 寫死在
  `<repo-root>/skills`，而 consumer 的 body 在 `.agents/skills/`。結果是：一個**寫得完全正確**的
  consumer binding 會被回報成「binds a skill that is not in the shared body」——用一個跟它無關的
  理由。本切片加了 `--body-root`，selftest 有 consumer 形狀的正反對照。
- **B3 — `delivery` 這個別名在不同 repo 指向不同 skill。** `ix-agy/.claude/commands/delivery.md` 指
  `github-delivery-loop`，`bettor-arena/.claude/commands/delivery.md` 指 `forgejo-delivery-loop`。
  registry 的 `commands` 是全域映射，表達不了「同名別名各 repo 指不同 skill」。
  **這是人裁題**，不是實作題：要嘛統一語意，要嘛別名下放成 per-repo binding。在裁決之前，
  registry 不登記任何別名，生成器只產全名。
- **B4 — `product-reverse-engineering-loop` 未登記。** #357 讓它進了 `skills/`，但 `registry.json`
  沒有它，`shared_skills.py check` 因此 FAIL（`UNREGISTERED`）——正是 #13 那條規則要抓的形狀。
  補一列 entry 需要一句 `why` 裁決（shared 還是 repo-owned），所以留給它的擁有者，本帳本只記錄。
- **B5 — 一個真正的影蓋副本還在。** `antigravity/.agents/skills/dr-research-loop` 是一份 18KB 的
  本地 body，不是 forwarder，也不是 symlink。registry 對 `dr-research-loop` 的 `why` 早就寫了這件事
  待手動移除。其餘 consumer surface 全部量測為 symlink 或單檔 forwarder stub。

## 切片表

狀態欄用本 repo 的證據詞彙。`binding` 欄記的是 `.skill-bindings/<name>/` 槽位存在於哪些 repo，
**存在不等於有效**——目前全部卡在 B1。

| # | 切片 | body 在 shared | binding 槽位 | 狀態 | 下一步 |
|---|---|---|---|---|---|
| 0 | hotfix 聯集 | — | — | PASS | 已完成；`superseded/` 是對帳依據 |
| 1 | `harness-wiki` | 否（`repo_owned: each`） | 無 | SKIPPED_BY_POLICY | ruling 8 把它改判 repo-owned，改由切片 23／24 承接 |
| 2 | `sdlc-plan-composer` | 是 | 無 | NOT_EXERCISED | 抽 binding、釘 `body_version` |
| 3 | `fold-in` | 是 | 無 | NOT_EXERCISED | 同上；`ix-agy` 的 `commands/fold-in.md` 含 binding 要一併搬 |
| 4 | `external-verify` | 是 | 無 | NOT_EXERCISED | 同上 |
| 5 | `autoresearch-composer` | 是 | 無 | NOT_EXERCISED | 同上 |
| 6 | `loop-harness-review-handoff` | 是 | 無 | NOT_EXERCISED | 同上 |
| 7 | `truth-verify-loop` | 是 | 無 | NOT_EXERCISED | 同上 |
| 8 | `path-b-reduction` | 是 | 無 | NOT_EXERCISED | 同上 |
| 9 | `dr-research-loop` | 是 | `antigravity` | FAIL | 先解 B5 影蓋副本，再補 `binding.md` |
| 10 | `judge-loop-chooser` | 是 | 無 | NOT_EXERCISED | 抽 binding |
| 11 | `unknown-discovery-composer` | 是 | 無 | NOT_EXERCISED | 抽 binding |
| 12 | `repo-agent-native` | 是 | `bettor-arena` | FAIL | 槽位無 `binding.md`（B1） |
| 13 | `skill-authoring` | 否（`repo_owned: each`） | 無 | SKIPPED_BY_POLICY | 同切片 1，改由 23／24 承接 |
| 14 | `knowledge-continuity` | 是 | 無 | NOT_EXERCISED | ruling 8 的「新入 shared」已完成；binding 未抽 |
| 15 | `product-ops` | 否（`repo_owned: each`） | 無 | SKIPPED_BY_POLICY | 同切片 1 |
| 16 | `loop-harness-standard` | 是 | `ix-agy`, `antigravity` | FAIL | 兩槽都無 `binding.md`；PRD 另註 antigravity vendored venv 要先排除 |
| 17 | `repo-wiki-converge` | 是 | `ix-agy` | FAIL | 槽位無 `binding.md` |
| 18 | `forgejo-delivery-loop` | 是 | `bettor-arena` | FAIL | 槽位無 `binding.md` |
| 19 | `forgejo-loop-ops` | **否** | 無 | ABSENT | 只存在於 `superseded/`；沒進 shared 也沒登記 repo-owned，需人裁 |
| 20 | `repo-fullstack-debugger` | 是 | `antigravity` | FAIL | 槽位無 `binding.md` |
| 21 | `github-delivery-loop` | 是 | 無 | NOT_EXERCISED | 抽 binding；與 B3 的 `delivery` 別名同一題 |
| 22 | `dr-to-mvp` | 是 | `antigravity` | FAIL | 槽位無 `binding.md` |
| 23 | `gemini-conversation-research` | 是 | 無 | NOT_EXERCISED | PRD 標為最大分岔之一（13 檔） |
| 24 | `html-for-decisions` | 是 | `ix-agy`, `antigravity` | FAIL | 兩槽用 `body_commit` 而非 `body_version`（B1）；PRD 標最大分岔 |
| 25 | 建 `ed3c/skills-ix-agy` | — | — | HUMAN_ADMIT_REQUIRED | 建 repo 要人；切片 1／13／15 都等它 |
| 26 | 建 `ed3c/skills-antigravity` | — | — | HUMAN_ADMIT_REQUIRED | 同上；搬入時排除 vendored 目錄 |

> 編號比 PRD 的 0–24 多兩格：PRD 的 15–19 那一列塞了七個名字，這裡一名一列，
> 因為一個切片就是一個 skill 的閉環——那是 PRD 自己的定義。

## 一個切片算做完的判準（PRD 原文，未放寬）

1. `shared_skills.py check` 綠（含兩個閘）
2. 該 skill 自帶的 `tests/` 綠
3. 每個訂閱 repo 自己的閘綠
4. 聯集報告可對帳到 `superseded/`：**沒有任何檔案在遷移中滅失**
5. 新增的閘要有 good／hollow 正負對照（本 repo 既有慣例：閘沒有 hollow fixture 不算完成）
