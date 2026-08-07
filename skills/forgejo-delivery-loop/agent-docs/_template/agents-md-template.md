# AGENTS.md 範本 — 基座路由控制面

> 每個擁有 Harness 或工程法則實證的 repo，其 `AGENTS.md` 都照這個骨架。
> 實作範例＝本 repo 的 `AGENTS.md`（ix-agy）。**範本只給骨架與判準，不複製內容**——
> 複製會造成雙圖漂移（提示詞 SSOT 單一真源守則）。

## 為什麼是這個順序

`AGENTS.md` 與另外兩份規則檔互為經緯，**軸各不同**。B1 rules/context 要求 Macro control plane
備齊三件（`AGENTS.md`／`CLAUDE.md`／`ARCHITECTURE.md`），少一件那個職責就只能靠記憶補：

| | 軸 | 排列依據 | 回答的問題 |
|---|---|---|---|
| `~/.claude/CLAUDE.md`（全局） | **時間／資料流** | 入料→構形→閘門→觀測→判定→落帳 | 一次工作怎麼流動 |
| `AGENTS.md`（本範本） | **空間／基座** | B7→B1→B2→B4→B5→B3→B6→B8 | 東西住在哪個結構位置 |
| `<repo>/.claude/CLAUDE.md` | **觸發／編排** | 階段 × skill、讓位、開不開迴圈 | 什麼情況下該喚起誰 |

找一條法則走資料流軸，找一個組件走基座軸，判「現在該用哪個 skill」走觸發軸。
三軸在 §4 交會：法則主題 → 擁有實證的 Harness。

**歸屬判準**：判準寫全局、位置寫 `AGENTS.md`、時機與取捨寫編排層、實例寫 Harness。
同一個 skill 會在 `AGENTS.md` 出現一次（屬哪個基座）、在編排層出現一次（何時喚起）——
**這不是重複**：知道它屬 B1 不等於知道什麼時候該跑它。

## 骨架

```
§0 座標系      四層分工表（法則層／路由層／編排層／實證層）＋各層的軸，寫明「缺一層就斷」
§1 八大基座    Macro ↔ Small 資料流圖 + 對照表 + 本 repo 各基座的實體落點
§2 Harness 註冊表   本 repo 全部迴圈，逐個列位置／觸發詞／領域
§3 MCP Tools Index  一行 SSOT 指針（B4），不存副本
§4 工程法則的實證歸屬   法則主題 → Harness（全局 CLAUDE.md 指過來的落點）
§5 本 repo 專屬  Overview／Sub-projects／Sovereignty／Resolved
```

## 這份檔**不**負責什麼

四樣東西看起來像 `AGENTS.md` 的事，其實屬編排層（`<repo>/.claude/CLAUDE.md`）：

| 不放這裡 | 放哪 | 為什麼 |
|---|---|---|
| 能力清單（有哪些 skill、Strength／Triggers） | **哪裡都不放** —— `ls` 三個 skill 目錄即得 | 抄一份就是第二真源，必然漂移 |
| hook 清單、`.claude/rules/`、`CLAUDE.local.md` | `CLAUDE.md`（Claude host 專屬） | 換一個 host 就不成立 |

**反過來，這些「看似該歸 CLAUDE.md」的內容必須留在本檔**：階段×時機、讓位規則、
開不開迴圈、Code Style、Operation Boundaries、法則實證映射。
理由是物理的，不是偏好：**Codex 只讀 `AGENTS.md`，不讀 `CLAUDE.md`**
（錨：`agent-docs/HOST-SURFACES.md` §1）。放進 `CLAUDE.md` ＝讓 Codex 永久失明，
而失明**不會有任何機制吭聲**——兩份都是合法 markdown、都被各自 host 完整載入。
安全關鍵的邊界（不可改的目錄、不可 force push）尤其不能移出本檔。

判準：**能用確定性指令即時取得的（清單、數量）→ 不寫進任何文件**；
**隨情境變動的（時機、取捨）→ 編排層**；**只隨目錄結構變動的（位置、註冊）→ 本檔**。
抄清單的失敗方式特別惡劣：漂移後它**看起來仍然權威**——ix-agy 實測舊表有三個標成
`CRITICAL` 的 skill 名在三個來源都查無實體，而沒有人會去質疑一張排版整齊的表。

## 各節的硬性要求

**§0 座標系** — 必須出現字串 `工程法則的實證歸屬`，否則全局法則層 grep 不到這個 repo。
四層職責都要寫「不做什麼」欄：法則層不指目錄、路由層不存實證副本、
編排層不重複能力清單、實證層不重述法則。「不做什麼」比「做什麼」更能防越界，
因為越界都是從「順便也寫一下」開始的。

**§1 八大基座** — 圖與表都要。圖給資料流方向感（B7 契約在最上、B8 落帳在最底），
表給 Macro/Small 兩層對照。本 repo 每個基座的實體位置逐項標 `— B<n>`，
沒有實體的基座要顯式寫「無」，不可省略——省略與缺席在讀者眼中同形。

**§2 Harness 註冊表** — **全部**列出。新建 Harness 未登記＝沒有人找得到它，等同不存在。

數量對帳時**不能只數 `PROMPT.md`**——有三種東西也有 `PROMPT.md` 卻不是小迴圈，
各自要有明確出口，否則檢查會誤報（ix-agy 實測：裸數 10，真 Harness 7）：

| 也有 `PROMPT.md` 但不是小迴圈 | 為什麼 |
|---|---|
| repo 根 `PROMPT.md` | 那是 **Macro control plane 自己的 B7 契約**（當前 goal），不是被它管的迴圈 |
| gitignored throwaway（`prototype/` 等） | 用完即棄，登記它等於承諾維護它 |
| 玩具 demo（`loop_demo/` 等） | 沒有八大基座，不是 Harness |

判準是「**有沒有自己的八大基座**」，不是「有沒有 `PROMPT.md`」。

**§3 MCP Tools Index** — 只留一行指向該 repo 的 SSOT 模組，本節不存副本。
能力目錄不在這裡（見上一節「這份檔不負責什麼」）。

**§4 實證歸屬** — 每列＝「法則主題 | 擁有實證的 Harness ＋ 該處的可觸發內容摘要」。
摘要要寫**動作**（訊號→動作→為何有效），不寫案例敘事——只堆案例的 module 卡住時不會被想起。
本 repo 沒有的法則實證，用一行 `> 其他 repo 擁有的法則實證：…` 指出去，不留空白。

**§5 專屬** — 放最後。它是這個 repo 獨有的事，對其他 repo 沒有路由價值。

## 註冊檢查（零網路）

```bash
# 這個 repo 需要註冊嗎？（有 loop 或有自有 skill 就需要）
find <root> -maxdepth 3 -name PROMPT.md -path "*loop*" | grep -c .
ls -d <root>/.agents/skills/*/ 2>/dev/null | grep -c .

# 註冊了嗎？
grep -q "工程法則的實證歸屬" <root>/AGENTS.md && echo registered || echo MISSING

# Harness 全登記了嗎？（兩數必須相等）
# 只數迴圈沙盒根「之下」的，藉此排除 repo 根契約、gitignored throwaway、玩具 demo。
# maxdepth 要涵蓋分組層：ix-agy 的 loop_wiki/subproject-ixsecurity-e2e/<loop>/ 是第 3 層，
# 假設扁平寫成 -maxdepth 2 會漏掉整組（實測漏 5 個，只數到 2）。先確認你的巢狀深度。
find <root>/<迴圈沙盒根> -maxdepth 3 -name PROMPT.md | grep -c .   # ix-agy 是 loop_wiki/
sed -n '/## §2/,/^---/p' <root>/AGENTS.md | grep -c '^| \*\*'

# 編排層在嗎？（B1 三件的第二件）
test -f <root>/.claude/CLAUDE.md && echo ok || echo "MISSING 編排層"
```

## 不適用的情況

無 Harness、無自有 skill 的 repo **不需要**這個骨架——強加會製造空表格，
而空表格與「還沒填」在讀者眼中同形。判準是「有沒有東西可路由」，不是「是不是一個專案」。
