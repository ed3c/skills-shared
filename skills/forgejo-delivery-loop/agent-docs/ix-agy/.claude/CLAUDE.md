# CLAUDE.md — ix-agy 編排層（Claude host 面）

<!-- 由 forgejo-delivery-loop 集中管理。SSOT = agent-docs/ix-agy/.claude/CLAUDE.md。
     直接改 repo 內這份會被 `agent_docs.py check` 判 DRIFT；改 SSOT 再 apply。 -->

> **三軸分工，各 host 看它該看的那一面**。這是刻意的選擇性擺放，不是資訊遺失：
>
> | 檔案 | 軸 | 回答 | 誰讀 |
> |---|---|---|---|
> | 全局 `~/.claude/CLAUDE.md` | 時間／資料流 | 一次工作怎麼流動 | Claude |
> | `AGENTS.md` | 空間／基座 | 東西住在哪個結構位置 | Codex |
> | **本檔** | **觸發／編排** | **什麼情況該喚起誰** | **Claude** |
> | Harness `modules/` | — | 完整實證與可觸發動作 | 兩者按需 |
>
> 判斷歸屬：**判準**寫全局、**位置**寫 `AGENTS.md`、**時機與取捨**寫這裡、**實例**寫 Harness。
>
> **能力清單哪裡都不抄**：有哪些 skill，真源是目錄本身（`~/.agents/skills-shared/skills/`、
> `.agents/skills/`、`.claude/skills/`，`ls` 即得）。文件裡抄一份就是第二真源，必然漂移——
> 實測舊表有三個標成 `CRITICAL` 的名字在三個來源都查無實體。本檔只寫**取捨**，不寫**清單**。

---

## §1 階段 × skill — 在資料流的哪一段該想起誰

本節**不列清單，只標時機**：同一個 skill 在哪一段該被想起。段名沿用全局
`~/.claude/CLAUDE.md` 的六段，不自創分段。下表提到的名字都是**舉例**，
以目錄實況為準——新增 skill 不必回頭改這張表，它記的是段與情境的對應。

| 全局 CLAUDE.md 的段 | 該想起的 skill | 觸發情境 |
|---|---|---|
| **§1 入料** | `repo-agent-native`、`external-verify`、`knowledge-continuity` | 進一個沒讀過的 repo／遇到 post-cutoff 或無 URL 的官方 claim／文件讀者需靠記憶補 |
| **§2 構形** | `codebase-design`、`design-an-interface`、`sdlc-plan-composer` | 要設計模組介面／多階段工作需先規劃再動手 |
| **§3 閘門** | `tdd`、`github-delivery-loop`（及 gitlab／forgejo 姊妹）、`ios-testflight-ship` | 動手實作前／要把產物綁上追蹤面／要發佈 |
| **§4 觀測** | `diagnosing-bugs`、`diagnose`、`repo-fullstack-debugger` | 執行後拿到失敗 trace；先判是一般 bug、硬 bug 還是反覆失敗的黑盒（判準見 §3） |
| **§5 判定** | `judge-loop-chooser`、`truth-verify-loop`、`path-b-reduction`、`code-review` | 有 deliverable 要判／claim 集要逐字驗／出現平滑抽象敘事／有 diff 要審 |
| **§6 落帳** | `fold-in`、`html-for-decisions`、`antigravity-harness-wiki` | 一段經驗完成要沉澱／要產人閘證據包／迴圈拓撲有變動 |

**跨段的路由器**（不屬單一段，用來決定要走哪段）：`unknown-discovery-composer`（起手在迷霧中）、
`autoresearch-composer`（有界指標迭代）、`dr-to-mvp`（冷啟動新家族）。

---

## §2 讓位規則 — 多個 skill 同時匹配時誰優先

每個共用 skill 的 `description` 都帶 `NOT for:` 段，那**就是**讓位聲明。組合起來的優先序：

| 情境 | 走這個 | **讓位給**，不要走 |
|---|---|---|
| 一般本地 bug／測試失敗 | `diagnosing-bugs`（便宜閘） | 不要開 `diagnose`／`repo-fullstack-debugger` |
| 硬 bug：不可重現／flaky／效能回歸／需建重現 | `diagnose` | 不要停在 `diagnosing-bugs` 空轉 |
| 反覆失敗、腳本重試解不掉、要編譯成可重用 playbook | `repo-fullstack-debugger` | 不要用一般診斷 |
| 源碼靜態一次讀就能拿 A 級 | `repo-agent-native` | 不要進任何診斷迴圈（L0 反過度設計閘） |
| 單一外部 claim 查證 | `external-verify` | 不要為此開 `truth-verify-loop` 迴圈 |
| 選驗證標準／獨立性 tier | `judge-loop-chooser` | 不要在 `dr-research-loop`／`truth-verify-loop` 裡自訂 |
| 一般 code diff 審查 | `code-review` | 不要用 `judge-loop-chooser` |
| 該不該新建 skill | 內建 `write-a-skill` | 不要用 `fold-in`／`loop-harness-standard` |
| 記錄既有迴圈拓撲 | `antigravity-harness-wiki` | 不要用 `loop-harness-standard`（那是**建**新迴圈） |
| debug／security／TDD／設計辯論 | 各自的原生治理 skill | `autoresearch-composer` 明文讓位，不接管 |

**判準一句話**：`loop-harness-standard` 是「建」、`antigravity-harness-wiki` 是「記」、
`fold-in` 是「折回既有」——三者常被混用，因為它們都碰迴圈目錄。動作動詞不同就不是同一個 skill。

---

## §3 開不開迴圈 — 迴圈工程的啟發式

小迴圈（`loop_wiki/<name>/`）成本不低：八大基座要齊、T0 硬驗證器要寫、stop-loss 要設。
**不是每個任務都值得**。

**該開**：
- 同一類判斷要重複做很多次，且**判錯有代價**（需要機械閘而非人盯）
- 概率性 LLM 執行需要被逼到高完成率（T0 硬驗證器 × iterate-until-pass × stop-loss）
- 需要 planted-defect 檢出率這種**可量化**的收斂指標

**不該開**：
- 一次性任務——直接做，別為它建基座
- 判準還沒穩定——先手做幾次，讓判準浮現，再固化成驗證器
- 只是想記錄知識——那是 `antigravity-harness-wiki` 或 owner module 的事，不需要迴圈

**開之前必答**（`PROMPT.md` 的 B7 契約）：target 是什麼、success 怎麼**機械**判定、
stop-loss 在哪一步觸發。三個答不出來就還不到開的時候。

> 建立程序 → `loop-harness-standard`；記錄拓撲 → `antigravity-harness-wiki`；
> 交接給獨立 reviewer → `loop-harness-review-handoff`。

---

## §4 風格與專屬紀律

全局 `~/.claude/CLAUDE.md` 末行點名「項目專屬機制寫在各項目自己的 `.claude/CLAUDE.md`」，指的是這一節。

### Code Style Conventions

#### Python
- Type hints for all public functions; PEP 8, line length 100
- Docstrings: Google style
- Test naming: `test_<function>_<scenario>`

#### Shell Scripts
- Use `set -euo pipefail` at start
- Quote all variables: `"$var"`
- Use absolute paths (no `cd` commands)

#### Markdown
- Chinese preferred for documentation
- Use YAML frontmatter for agents
- Anchor points format: `ANCHOR-XXX-NNN`

### Operation Boundaries

#### Never
- Modify `.env` or credentials files
- Force push to main branch
- Delete `.git` directory
- Modify system files outside project
- Modify files under '/Users/neon/TrueMe_iOS' (Must remain 100% pristine under all circumstances)
- 絕對不能修改後端服務（`ixsecurity/auth52-service` 等 Go 代碼），後端應保持 100% pristine。

> 其餘操作邊界（Allowed Operations／Confirmation Required 細則）→ [.agents/modules/operation-boundaries.md](../.agents/modules/operation-boundaries.md)

**這些是硬約束，不是取捨**：需要改時是先解除邊界，不是繞過。

### SSOT 指針紀律

- 本檔與 `AGENTS.md` 都**只放指針，不存副本**。MCP／Skills／Problem Graph 的結構規範 SSOT 在
  `.agents/modules/harness-config.md`；操作邊界細則在 `.agents/modules/operation-boundaries.md`；
  主權分層在 `.agents/modules/sovereignty.md`。
- **提示詞單一真源**：嚴禁拷貝／複製 prompt，會造成雙圖漂移。需要複用就指過去。
- **嚴禁簡化已實裝的閉環架構**（`antigravity-harness-wiki` 的 Anti-Simplification Gate）。
- **Claude skill forwarders 零邏輯**：`.claude/skills/<name>/SKILL.md` 只指向同名 canonical skill，
  不得夾帶自己的程序——夾帶就是第二份真源。
- **共用 skill 不得在 repo 內自留同名副本**：兩個 host 的 project skill 都優先於 user skill，
  自留會**無聲影蓋**共用版（→ `shared-skills-infra`）。
- **提到 skill 名前先確認有實體**：`ls` 三個來源（共用／`.agents/skills/`／`.claude/skills/`）
  或確認是內建。**提一個不存在的 skill，會讓人以為那件事有人管**——這也是本檔
  不維護能力清單的理由：清單會漂移，目錄不會。

---

## §5 元層設計 — 為什麼是這個結構

**新增一個東西時，它該落在哪一軸？** 依這條決策鏈：

```
它是跨專案都成立的判準嗎？
  是 → 全局 ~/.claude/CLAUDE.md（不放實例、不寫死目錄）
  否 ↓
它回答「東西在哪」嗎？（位置、註冊、目錄結構、基座落點）
  是 → AGENTS.md（不存能力清單、不存實證副本）
  否 ↓
它回答「什麼時候用哪個」嗎？（時機、取捨、讓位、風格、邊界）
  是 → 本檔
  它只是「有哪些可用」嗎？→ **哪裡都不寫**，去 ls 目錄；抄清單就是製造第二真源
  否 ↓
它是某條法則的完整實證／可觸發動作清單嗎？
  是 → 對應 Harness 的 modules/（並在 AGENTS.md §4 加一列指過來）
```

**三軸為什麼不能合併**：合併後每次找東西都要掃全檔，而「找不到」與「不存在」變得
不可區分——這正是全局法則 §5 判定段要防的同形兩態。分軸的代價是三處都要維護，
收益是**每一處的缺席都看得出來**（`AGENTS.md` 少一個 Harness 是數量對不上，
本檔少一個階段映射是那一段空著）。

**能力清單為什麼三處都不放**：它的真源是**目錄本身**——`ls` 一下就是最新的，
而文件抄一份就永遠落後一步。抄本的失敗方式特別惡劣：漂移後它**看起來仍然權威**
（實測三個標成 `CRITICAL` 的名字查無實體），讀者不會去質疑一張排版整齊的表。
**能用確定性指令即時取得的，不寫進文件**；文件只寫指令答不出來的東西——取捨、時機、為什麼。

**落帳回流**：任何一次推翻都要回頭改三處（Harness 補紀錄、`AGENTS.md` 主題若變更新、
法則被證偽就改寫）。只改 Harness 不動法則，下次照舊犯。

---

## §6 Claude host 專屬

- **強制層**：`.claude/settings.json` 與 `~/.claude/hooks/auto-approve.sh` 的閘。
  規則要不論模型怎麼判都成立，就寫成 hook，不是寫成本檔的一句「必須」。
  已知會擋的：`rm` 強制刪除（Tier 2 需人工）、`cd` 開頭指令、寫入 `auto-approve.sh` 自身、
  未列入 allowlist 的 MCP 工具。**被擋不是繞過的理由，是改 allowlist 或請人執行的訊號。**
- **按需載入**：多步驟程序放 skill（只在被觸發時才佔預算），不放本檔。
  路徑作用域規則放 `.claude/rules/*.md` ＋ frontmatter `paths:`。
- **Skill forwarders**：`.claude/skills/<name>/SKILL.md` 零邏輯，只指向同名 canonical skill；
  `.claude/commands/delivery.md` 僅保留 `/delivery` 相容別名。夾帶程序就是第二份真源。
- **個人層**：`CLAUDE.local.md`（要進 `.gitignore`）；跨 worktree 共用個人偏好改用
  `@~/.claude/<file>.md` import——gitignored 的 local 檔只存在於它被建立的那個 worktree。
- **驗載入**：session 內 `/context` 看 **Memory files** 清單。
  **本檔與 import 進來的 AGENTS.md 有沒有被讀到，是可查證的事實，不是可以假設的事。**
