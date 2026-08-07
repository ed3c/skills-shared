---
name: repo-wiki-converge
description: |
  把「任意 repo → Opus 級理解 wiki」變一鍵收斂流程時使用 — 在既有 openwiki-distilled
  kb-ingest/repo-wiki.workflow 之上，加「Opus 判官 × Gemini 作者」judge-loop。Gemini（agy --sandbox，
  人起火）寫與精修，Opus（本 Claude Code session，非 agy）對 ground truth 逐 claim 驗證、產證據化缺口
  清單、認證收斂，迭代到 Opus 級再 ingest 進 KB。實測 repoprompt-ce 用 Gemini 3.1 Pro 兩輪收斂（66→85→91）。
  觸發詞：repo wiki 收斂、任意 repo 生 wiki、judge-loop 精修 repo 文檔、Gemini 收斂到 Opus、
  repo 掌握全覆蓋、kb-ingest repo wiki、Opus 判 Gemini repo。
  何時用：要對一個可讀 repo 產 Opus 級 wiki 並進 KB 時。
  NOT for：抽 Gemini 對話（gemini-conversation-research）；查證單一外部 claim（external-verify）；
  造或改 skill（antigravity-skill-authoring）。完整 agy／Opus／openwiki 執行經驗與 5 條收斂原則在 modules/。
---

# Skill: repo-wiki-converge — 任意 repo → Opus 級 wiki（Opus 判官 × Gemini 作者 judge-loop）

> **Role**: 對一個**可讀的 repo**，用「便宜 Gemini 作者 + Opus 判官」迴圈產出 Opus 級理解 wiki 並進 KB。
>   Gemini 海量讀碼/寫頁/照缺口精修（免費、由人起火），Opus 對 ground truth 逐 claim 驗證、定完成標準、
>   認證收斂。**收斂 = Opus 判官認證，不是作者自己說了算。**
> **結構**: SKILL.md = 一鍵收斂流程（確定性步驟）+ 不變量 + Gotchas；agy／Opus／openwiki 執行 know-why、
>   5 條收斂原則、Flash-vs-Pro 實據在 [modules/execution-and-convergence.md](modules/execution-and-convergence.md)。
> **SSOT / 活基座（每個都真存在，這是本 skill「非 husk」的鐵錨）**:
>   - CREATE pass = [`kb-ingest/repo-wiki.workflow.md`](../../../kb-ingest/repo-wiki.workflow.md)（openwiki-distilled，深理解 workflow）。
>   - REFINE pass 指令 = [`kb-ingest/refine.prompt.md`](../../../kb-ingest/refine.prompt.md)；JUDGE 程序/rubric = [`kb-ingest/judge.prompt.md`](../../../kb-ingest/judge.prompt.md)。
>   - T0 pre-verifier = [`kb-ingest/verify-claims.sh`](../../../kb-ingest/verify-claims.sh)（機械檢 anchor/quote/frontmatter/Why-tag,FAIL 零判官成本退回;agy-pass.sh 每 pass 後自動跑）；成本帳本 = [`kb-ingest/engine-baseline.md`](../../../kb-ingest/engine-baseline.md)。
>   - Gemini 作者 runner（Claude 或人，從 host project CWD）= [`kb-ingest/agy-pass.sh`](../../../kb-ingest/agy-pass.sh) `<create|refine> <TARGET> <OUT> <GEMINI_MODEL>`。
>   - 缺口清單 SSOT = `<OUT>/_judge/gaps-latest.md`（Opus 每輪寫，作者每輪讀）。
>   - 進 KB = `python3 -m indexing.ingest_repodoc_cli <OUT>/repo_wiki/<slug>/`。
>   - 反幻覺查證工具 = [`external-verify`](../external-verify/SKILL.md)（判官對 post-cutoff 事實時借用）。
> **Lineage**: CREATE workflow port 自 langchain-ai/openwiki 的 agent prompt。judge-loop 兩軸（judge 標準 ×
>   獨立性）與 [`judge-loop-chooser`](../judge-loop-chooser/SKILL.md) 同源哲學（recipe-not-engine、人出閘）。
>   **實測基座**：repoprompt-ce（2224 檔）Pro 3.1 兩輪收斂 66→85→91，round-2 覆蓋 ≥ Opus 單發（見 module）。

## 🚩 STOP — 你在合理化（違反即停）
| 念頭 | 現實 |
|---|---|
| 「作者說 8 頁都寫好了、印了 DONE，收斂了」 | ❌ 作者自評無效；只有 **Opus 判官對 repo 驗證後**才算數（Flash 曾印 DONE 卻沒寫檔） |
| 「頁面讀起來很完整、符號都很具體，過」 | ❌ 具體符號正是幻覺藏身處；判官必 `git grep`／`git show` 逐個驗，別讀 wiki 判 wiki |
| 「這個 why 很合理，留著」 | ❌ 無 git 出處的 why = 腦補；不標 unverified 就是往 KG 灌毒（Flash 造過「Git history reveals…100k files」） |
| 「Flash 較快免費，直接當作者、判官隨便看」 | ⚠️ Flash 會收斂,但 create 散更多捏造具體值（100k/50k/errno13）→ 判官必獵數字、可能多輪;Pro 較乾淨（見 module 實據） |
| 「agy 反正能跑，policy／CWD 隨便」 | ❌ 沒 host-project EAGER policy、或 `--new-project`、或非 host CWD → silent no-op 謊報 DONE（見 Gotchas 三要件） |

## When to Use
- 有一個**可讀 repo**（本地 clone）要產 Opus 級理解 wiki 並進 antigravity KG。
- 一份既有 repo wiki 品質不夠、要迭代精修到「完全掌握」（逐子系統覆蓋 + 每個 why 接地）。

## Not For
- ❌ 研究一個 **Gemini 對話**的隱性知識 → [gemini-conversation-research](../gemini-conversation-research/SKILL.md)（不同上游）。
- ❌ 查證單一外部 claim 真假 → [external-verify](../external-verify/SKILL.md)（本 skill 判官的工具，非替代）。
- ❌ 造／改 skill 或 skill 規範 → [antigravity-skill-authoring](../antigravity-skill-authoring/SKILL.md)。
- ❌ 把經驗 fold 進既有 skill／AGENTS.md → [fold-in](../fold-in/SKILL.md)。
- ❌ 用 DR 當 repo 掌握主幹（漏斗倒置）——源碼是 SSOT，DR 只補外部缺口。

## 不變量（違反即停）
1. **agy = Gemini only；判官 = 本 session（Opus），絕不用 agy 跑判官。** agy 執行:從設好 `autoExecutionPolicy=EAGER`／proceed-in-sandbox 的 **host project CWD** 跑、**無 `--new-project`**、`--sandbox` → **Claude 或人皆可起火**（三要件缺一即 silent no-op 謊報 DONE）。（見記憶 agy-execution-sandbox-human-fired）
2. **判官對 ground truth 驗證**，不讀 wiki 判 wiki：抽樣驗檔/符號存在、**每個 cited sha 用 `git show` 驗它掛對 claim**（對 sha 錯 claim = 隱性誤引）、read-only 沒破。
3. **每個 why 必 git-cite 或標 unverified**——硬門檻。無出處卻當事實 = 自動 FAIL（KG 分不出事實與猜測）。
4. **精修外科化**：作者只動缺口清單點名項；判官 diff round-to-round 快照抓回歸。
5. **全歷史 clone**（never `--depth 1`）；shallow = rationale 接地崩。
6. **收斂 = Opus 認證，且 ≥90 是「必要非充分」**：分數 ≥90 ∧ 零事實錯 ∧ 零未標腦補 ∧ 無漏承重子系統只是**准許考慮認證**;到 90 後判官必跑 **≥90 protocol**（① meta-審計「我沒查什麼」② 對抗式再破一次 ③ 認證本身過獨立性 tier ④ 升層決策），任一冒缺陷即 `CONVERGED=false` 續迴圈。`CONVERGED=true` 只認證 **wiki（理解粒度）**非逐檔窮盡掌握（見 `kb-ingest/judge.prompt.md` + module §2.1）。

## 確定性程序（一鍵收斂流程）
1. **Clone 全歷史 + 定位置**：`git clone <url> /Users/neon/antigravity/repo/<repo_name>/<repo_name>`（絕不 `--depth 1`；TARGET＝該 clone，basename＝slug）。**OUT＝`/Users/neon/antigravity/repo/<repo_name>/`**（durable，**絕不放 /tmp**；產物 `repo_wiki/`、`invariants/`、`_judge/` 都落此。`/repo/` 已 gitignore）。
2. **CREATE pass（Gemini 作者）**：**從 host project CWD**（設好 EAGER policy）跑
   `bash kb-ingest/agy-pass.sh create <TARGET> <OUT> "Gemini 3.1 Pro (High)"`——Claude 直接跑或人 `!` 起皆可。產出 `<OUT>/repo_wiki/<slug>/`。
3. **JUDGE（我，Opus session）**：step 0 先看 `_judge/preverify-latest.md`（agy-pass.sh 已自動跑 verify-claims.sh;FAIL＝直接用該報告當 gap list 退回,不燒判官 token 重推導）→ 照 [`kb-ingest/judge.prompt.md`](../../../kb-ingest/judge.prompt.md) 只裁機械檢不了的（覆蓋完整性/機制忠實度/slug/回歸 diff）—— 對 TARGET+git
   逐 claim 驗證、五軸打分、寫 `<OUT>/_judge/gaps-latest.md`（首行 `CONVERGED=<t/f> SCORE=<int>` + 證據化缺口）。gap-list lint：判官種子也是 claim（兩起實測,見 judge.prompt.md）。
4. **未收斂 → REFINE pass（Gemini 作者，Claude 或人從 host CWD）**：`bash kb-ingest/agy-pass.sh refine <TARGET> <OUT> "Gemini 3.1 Pro (High)"`
   （讀 gaps-latest.md 外科式關閉）→ 回步驟 3。記錄每輪分數（軌跡 = 「幾輪收斂」）。
5. **收斂（判官寫 CONVERGED=true）→ INGEST**：`python3 -m indexing.ingest_repodoc_cli <OUT>/repo_wiki/<slug>/`。

## Gotchas
- **`agy --sandbox -p` 執行三要件（缺一即 silent no-op 謊報 DONE，實測）**：① host project 設 `autoExecutionPolicy=EAGER`／proceed-in-sandbox + fileAccessPolicy ALLOW ② **無 `--new-project`**（開新 project = 沒 policy）③ 從 **host project CWD** 跑（policy 綁 project，/tmp CWD 也 no-op）。三者齊 → Claude／人皆可真執行。（agy-execution-sandbox-human-fired）
- **Flash 3.5 可當作者但 create 較髒**：它 create 散落捏造具體值（100k files／50k lines／errno 13），需**會獵捕捏造數字的判官**逐輪清、可能多 1 輪;但**執行一旦通它會收斂**（實測 62→84,關缺口、標 unverified、不 re-confabulate git 歸因）。**Pro 3.1 略優**（create 較乾淨、詞彙貼 Opus、較少輪）。實據 → module。
- **作者 tiering 判準（給 orchestrator,非 keyword router）**：create 與**含新頁/新章**的 refine → Pro（新自由度＝捏造溫床,superpowers run round-2 實測 8/8 缺陷全在新頁）;**純外科 line-fix** refine（gap 全點名、無新自由度）→ Flash 可。判官永不 tiering（不變量 1）。
- **連 Pro 在 create 都會腦補一顆 why**（native-tree/eager-loading）——是判官在 r1 逼它標 unverified 才擋下。
  **判官不是可選項**；沒判官就出貨腦補。
- **對 sha、錯 claim = 誤引**：判官必 `git show <sha>` 驗它支持所掛 claim，不能只驗 sha 存在。
- **`": "`（冒號+空格）出現在 frontmatter description 任一處 → skill 被靜默跳過**；多行用 `|` block scalar + 全形「：」。
- **`\|` 在 `grep -E`／`pgrep` 下是字面、非「或」**（本 cycle 踩兩次，誤判成 0）——ERE 用 `|`。
- **agy `--dangerously-skip-permissions` 對 AI 起火被分類器硬擋**（加 `--sandbox` 也擋）——所以 Claude 走 **`--sandbox` + host-project EAGER policy**（非 skip-permissions）那條路執行,兩者別混。
- **REFINE 也是 miscite 溫床,不只 create**（cc-20260723 contractbench r2 兩處）：Pro refine 修 WHY 段會把 advisory 挑最壞讀法（`(src: SOP2)`＝把外部文件名當錨→T0 H2 硬 FAIL）＋對檔錯行 miscite（掛 DESIGN-SCORE cut-6 行冒充 failure-split 依據）;**判官種子污染第 3 例**（evalgate r2「MVP sandbox #1」＝r1 判官 gap 措辭被原封轉錄進 wiki）——判官寫 gap 避免可被抄錄的具名縮寫/序號。帳＝`repo/{evalgate,contractbench}/_judge/`。

## Modules
- [modules/execution-and-convergence.md](modules/execution-and-convergence.md) — agy（`--sandbox`／proceed-in-sandbox／人起火／`--new-project`／`--add-dir`）× Opus 判官 × openwiki 執行 know-why；5 條收斂設計原則；Flash-vs-Pro 實測數據；成本邏輯；repoprompt-ce 收斂 cycle 帳本。
