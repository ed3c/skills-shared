# `<repo>/.claude/CLAUDE.md` 範本 — 編排層

> B1 rules/context 要求 Macro control plane 備齊三件：`AGENTS.md`（路由層）、
> **`CLAUDE.md`（本範本）**、`ARCHITECTURE.md`。少一件，那個職責就只能靠記憶補。

## ⚠️ 先讀：host 讀取範圍決定內容落點

| Host | 讀 | **不讀** |
|---|---|---|
| **Codex** | `AGENTS.md`（根→cwd 每層串接） | `CLAUDE.md` |
| **Claude Code** | `./CLAUDE.md` **或** `./.claude/CLAUDE.md`（等價，擇一） | **`AGENTS.md`** |

錨：`agent-docs/HOST-SURFACES.md` §1（官方 URL 已在該檔錨定）。

**推論**：任何**跨 host 都該成立**的內容——階段×時機、讓位規則、Code Style、Operation Boundaries、
法則實證映射——放進 `CLAUDE.md` 就等於讓 Codex 永久失明，而失明**不會有任何機制吭聲**。
安全關鍵的邊界（不可改的目錄、不可 force push）尤其不能放這裡。

所以本檔的正解是**薄的**：

```
@AGENTS.md          ← 一行 import，內容只有一份，雙圖漂移在結構上不可能發生
                       （相對路徑以含 import 的檔為基準：放 .claude/ 下要寫 @../AGENTS.md）
＋ 只放「換一個 host 就不成立」的東西
```

**這不是把三軸退回兩軸**：三軸是**內容的分類**（判準／位置／時機），不是**檔案的分配**。
時機軸完整保留，只是住在 `AGENTS.md` 的一節裡——那是唯一兩個 host 都讀得到的地方。
> 實作範例＝ ix-agy 的 `.claude/CLAUDE.md`。**範本只給骨架與判準，不複製內容**——
> 各 repo 的 skill 組合與讓位規則不同，複製會造成雙圖漂移。

## 它為什麼必須獨立存在

全局 `~/.claude/CLAUDE.md` 末行明文寫著「項目專屬機制寫在各項目自己的 `.claude/CLAUDE.md`」——
**規範早就定義了它，卻長期零生產者**。這是「多態型別要驗生產端」的同型：定義在、生產端不在，
而從下游完全看不出來（沒有人會因為缺這個檔而報錯，只會每次重新靠記憶決定用哪個 skill）。

三軸各答一問，判斷歸屬看動詞：

| 檔案 | 軸 | 回答 | 不做什麼 |
|---|---|---|---|
| 全局 `~/.claude/CLAUDE.md` | 時間／資料流 | 一次工作怎麼流動 | 不放實例、不寫死目錄 |
| `<repo>/AGENTS.md` | 空間／基座 | 東西住在哪個結構位置 | 不存實證副本 |
| **本檔** | **觸發／編排** | **什麼情況下該喚起誰** | **不重複能力清單** |
| Harness `modules/` | — | 完整實證與可觸發動作 | 不重述法則 |

**同一個 skill 在 `AGENTS.md` 與本檔各出現一次，不是重複**：前者說它屬哪個基座（結構位置），
後者說什麼時候該跑它（時機）。知道 `repo-agent-native` 屬 B1，不等於知道何時該喚起它。

## 骨架

```
第一行         @AGENTS.md（或 @../AGENTS.md）——沒有它，Claude 面讀不到路由層的任何內容
§1 強制層      .claude/settings.json 的 hook 清單：哪幾個、各擋什麼
§2 按需載入    多步驟程序放 skill（只在觸發時佔預算）；路徑作用域規則放 .claude/rules/*.md ＋ paths:
§3 個人層      CLAUDE.local.md（要 gitignore）；跨 worktree 共用改用 @~/.claude/<file>.md
§4 驗載入      /context 看 Memory files——本檔有沒有被讀到是可查證的事實，不是可假設的事
```

**以下這些不放本檔**（放了 Codex 就看不到）：階段×時機、讓位規則、開不開迴圈、
Code Style、Operation Boundaries、法則實證映射、Harness 註冊表——**全部住 `AGENTS.md`**。

若本 repo 刻意不 import（Claude 面與 Codex 面要分岔），把理由寫在本檔，
並在 `AGENTS.md` 登記「兩份如何保持同步」的那個**會紅的出口**。**沒有出口就別分岔。**

§1→§2 是編排層自己的小資料流：**何時用 → 衝突選誰**。

**沒有「能力目錄」這一節，這是刻意的**：有哪些 skill 可用，真源是目錄本身
（`~/.agents/skills-shared/skills/`、`<repo>/.agents/skills/`、`<repo>/.claude/skills/`，`ls` 即得）。
文件抄一份就是第二真源，必然漂移，而抄本的失敗方式特別惡劣——漂移後它**看起來仍然權威**
（ix-agy 實測：舊表三個標成 `CRITICAL` 的名字在三個來源都查無實體）。
**能用確定性指令即時取得的，不寫進文件**；文件只寫指令答不出來的東西：取捨、時機、為什麼。

## 各節的硬性要求

**§1 階段 × skill** — 段名**必須沿用全局 CLAUDE.md 的六段**（入料→構形→閘門→觀測→判定→落帳），
不可自創分段，否則兩份檔對不上話。每段列該 repo 實際會用到的 skill ＋觸發情境；
**該 repo 用不到的段要顯式寫「無」**——省略與「還沒填」在讀者眼中同形。
不屬單一段的路由器（迷霧起手、指標迭代、冷啟動）另列一組，別硬塞進某一段。

**§2 讓位規則** — 每列兩欄：`走這個` / `讓位給，不要走`。
**來源是各 skill `description` 的 `NOT for:` 段，不是自創**——那些聲明本來就存在，
只是散在數十份 `SKILL.md` 裡，本節把它們收攏成一張可查的表。
容易混淆的同族要給一句判準（例：`loop-harness-standard` 是「建」、`harness-wiki` 是「記」、
`fold-in` 是「折回既有」——動作動詞不同就不是同一個 skill）。

**§3 開不開迴圈** — 該開／不該開**都要寫**，只寫該開會讓人以為迴圈越多越好。
必須有「開之前必答」的前置三問，對應 B7 契約：target 是什麼、success 怎麼**機械**判定、
stop-loss 在哪一步觸發。答不出來就還不到開的時候。

**§4 風格與專屬紀律** — 只放**指針**，不存副本；每條指到該 repo 的 SSOT 模組。
硬約束（不可修改的目錄、不可繞過的閘）要標明「這是硬約束，不是取捨」——
需要改時是先解除邊界，不是繞過。

**§5 元層設計** — 決策鏈寫成可逐步回答的判斷樹（是／否 → 落哪一軸），不寫成散文。
必須解釋「為什麼不能合併成一份」：合併後找東西要掃全檔，而**「找不到」與「不存在」
變得不可區分**。分軸的代價是多處維護，收益是**每一處的缺席都看得出來**。

## 自檢

```bash
# 段名有沿用全局六段嗎？（應為 6）
grep -oE "入料|構形|閘門|觀測|判定|落帳" <root>/.claude/CLAUDE.md | sort -u | grep -c .

# 有沒有誤抄能力清單？（兩處皆應為 0：清單的真源是目錄，不是文件）
grep -c "Strength\|Triggers" <root>/.claude/CLAUDE.md
grep -c "Strength\|Triggers" <root>/AGENTS.md

# 提到的 skill 名有幽靈嗎？（扣掉內建後應為空）
#   把三個來源的 ls 結果存成 skills-real.txt，再比對文中以反引號標記的名字
{ ls -1 ~/.agents/skills-shared/skills/; ls -1 <root>/.agents/skills/;
  ls -1 <root>/.claude/skills/; } 2>/dev/null | sort -u > /tmp/skills-real.txt
grep -oE '`[a-z][a-z0-9-]{4,}`' <root>/.claude/CLAUDE.md | tr -d '`' | sort -u \
  | comm -23 - /tmp/skills-real.txt

# 三軸互指閉合嗎？（三數皆應 > 0）
grep -c "~/.claude/CLAUDE.md" <root>/.claude/CLAUDE.md
grep -c "AGENTS.md"           <root>/.claude/CLAUDE.md
grep -c ".claude/CLAUDE.md"   <root>/AGENTS.md
```

## 不適用的情況

沒有自有 skill 組合、也沒有迴圈的 repo **不需要**這個檔。
本檔的價值全來自「有多個候選要選」——只有一條路時，編排層是空的儀式。
判準與 `AGENTS.md` 範本一致：**有沒有東西可路由**，不是「是不是一個專案」。
