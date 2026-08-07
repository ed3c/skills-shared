# execution-and-convergence — agy × Opus × openwiki know-why + 5 收斂原則 + Flash-vs-Pro 實據

> know-why for [../SKILL.md](../SKILL.md). SKILL.md 是確定性流程；本檔是「為何這樣跑、為何收斂、實測到什麼」。

## 1. 執行模型（誰用什麼跑）

| 角色 | 誰 | 怎麼跑 |
|---|---|---|
| **作者 / 精修** | Gemini（agy） | `agy --sandbox --add-dir <TARGET> --add-dir <OUT> -p "<prompt>" --model ...`，**從 host project CWD、無 `--new-project`**；Claude 或人皆可起火 |
| **判官 / 審計** | Opus | 本 Claude Code session（**非 agy**），照 `kb-ingest/judge.prompt.md` |

**agy 旗標紀律**（實測得出）：
- `--sandbox` = macOS Seatbelt，deny-default，只授權 workspace 子路徑，`.git` 列 dangerous-paths（防**破壞性寫**、讀不擋），網路為 inference 放行。這是 OS 級硬邊界，不靠審批提示。
- `--new-project` 隔離，避免繼承別的 project 上下文；`--add-dir <TARGET>` 把 target 唯讀掛進 workspace。
- **CWD 必中性**（scratch，非 TARGET 內）：CWD 設在 target 內會被 target 自己的 `AGENTS.md`/`CLAUDE.md` 劫持指令。agy-pass.sh 用 `cd <OUT>` + `--add-dir` 正是為此。
- **不用 `--dangerously-skip-permissions`**：對 **AI 起火**被 auto-mode 分類器硬擋（加 `--sandbox` 也擋，它認 token）。對**人起火**可用，但既定模型選 proceed-in-sandbox。

**proceed-in-sandbox（甜點權限模式）**：changelog 原文「Auto-approves terminal commands that run inside the secure sandbox, requesting manual approval only when a command attempts to bypass the sandbox.」→ 沙盒內命令自動放行、只有逃逸才手批。**但它是 TUI 選的權限模式、隨 project 持久化，不是 headless CLI 旗標**。⚠ **headless `--sandbox -p` 未設此 policy → tool 呼叫靜默不執行、還謊報 DONE**（實測 probe 檔沒寫）。所以要嘛該 project 先設好，要嘛人在互動 session 選它再驅動。

**執行模型（實測翻案）**：分類器硬擋 AI 起 `--dangerously-skip-permissions`（自我提權防線，加 `--sandbox` 也擋）。但 **`--sandbox`（不帶 dangerous flag）+ 從 host project（`autoExecutionPolicy=EAGER`／proceed-in-sandbox + fileAccessPolicy ALLOW）CWD + 無 `--new-project`** → **Claude 可直接執行、tool 真跑**（probe4 實證寫入 `HELLO_AGY_EAGER`；probe6 證不被 host 的 AGENTS.md 劫持）。三要件缺一（policy 未設／`--new-project` 開新 project／非 host CWD）即 **silent no-op 謊報 DONE**。判官（我）永遠不用 agy 跑，只審計。

## 2. 五條讓迴圈收斂的設計原則（天真迴圈會漏的）
1. **缺口清單要具體 + 帶證據**（file:line／sha／exact-fix）。模糊回饋不收斂——證據化清單讓作者精準關閉、2 輪搞定。
2. **判官對 ground truth 驗證，不讀 wiki 判 wiki**。`git grep` 驗符號存在、`git show <sha>` 驗 sha 掛對 claim。不驗證的判官只會蓋章放行貌似合理的謊。
3. **「完全掌握」= 判官從 repo 自身導出的子系統清單**（source-layout doc／top-level 源碼目錄／build manifest），否則迴圈在半成品上宣布勝利。
4. **unverified 標記當硬門檻**——把腦補轉成誠實 hedge，KG 才能分辨事實與猜測。這是產出能安全 ingest 的關鍵。
5. **精修外科化 + 快照 diff 抓回歸**——只動被點名項；「整份重寫」型精修會 thrash 並重新引入錯誤。

## 2.1 ≥90 時判官做什麼（收斂 ≠ 蓋章；wiki 收斂 ≠ repo 掌握）
**≥90 ＝「作者撞到判官 rubric 天花板」，不是「repo 沒剩東西可學」。** 收斂閘是 mastery 的**代理**，判官的**徹底度**才是真天花板。所以到 90 判官**不准只蓋章**，跑 4 步（judge.prompt.md「≥90 protocol」），任一冒出缺陷/洞就 `CONVERGED=false` 續迴圈：
1. **Meta 完整性審計**：問「我沒查什麼？」→ 驗一批**這輪還沒 grep／git-show 過**的檔/符號/斷言（尤其 wiki 未被抽到的）。有洞 = 清單/抽樣太淺 → 擴，不認證。
2. **對抗式破壞**：收斂 = 「再也找不到新缺陷」，非分數到 90。主動再獵一個捏造具體值/未標 why/漏掉的不變量。找到 → FAIL（光看分數 = Goodhart）。
3. **獨立性檢查**：判官又判又仲裁 = Same-Weights（[[judge-loop-chooser]]）。90 的**認證本身**要過獨立性 tier——確定性 recheck（grep/git 逐條）／跨家族 fresh-context 重讀／人 spot-check。別憑語感自我認證。
4. **天花板 + 升層決策**：`CONVERGED=true` 只認證 **wiki（理解粒度）**，非逐檔窮盡掌握。目標＝理解 → ingest；目標＝**完整代碼掌握** → wiki 是**入口層**，往外升到分層 artifact，各跑各的閘。

**分層真相（別把「wiki 收斂」當「repo 掌握」；完整階梯 + handoff SSOT → [`kb-ingest/mastery-ladder.md`](../../../kb-ingest/mastery-ladder.md)）**：
`L1 理解 wiki（本 skill）→ L2 [repo-agent-native](../repo-agent-native/SKILL.md) source-anchored 不變量 → L3 /specs-as-code 完整掌握＋規格`（旁：understand-anything 結構 KG／repo-fullstack-debugger runtime 黑盒）。L1 收斂 = 第 1 層綠燈，不是全綠；**升層是 demand-pull（人/goal 決定），非自動 chain**。handoff：L1 的子系統圖/`covers` **種子** L2 的 SCOPE，但 facts 仍源碼 A 級（funnel 不倒置，wiki 不當事實源）。

## 3. Flash vs Pro（作者選型；repoprompt-ce 實測）
**兩者皆可當作者；Pro 3.1 略優。** 實據（含一次已翻案的預判——誠實留痕）：

| | Flash 3.5 (High) | Pro 3.1 (High) |
|---|---|---|
| create 事實接地 | 近乎滿分（符號/檔/target 幾乎全真） | 佳（13 符號全真），但有 1 事實錯（"Apple swift-sdk"，實為 provencher fork） |
| **rationale 誠信** | 🔴 **偽造 why + 假 git 出處**：「Git history reveals … removed due to rendering regressions on large workspaces (100k+ files)」——git 全無此說、100k 是捏的、未標 unverified | 🟡 create 也腦補一顆（eager-loading），但判官 r1 逼它改標 unverified |
| **refine 迭代** | 🟢 **會收斂**（實測 62→84：關缺口、標 unverified、不 re-confabulate git 歸因）。⚠ 早前「10 輪 no-op ＝凍結」是 `--new-project` + 首跑空 log 的**機制假象，已翻案** | 🟢 **會收斂 + 自癒**（surgical-update 第 5 輪自抓 "Apple"→"community"；refine 2 輪到 Opus 66→85→91） |
| 詞彙（KG merge 適配） | 抽象、易裂（agent-coordination vs agent-orchestration…） | 最貼 Opus（context-engineering/agent-orchestration/source-layout…） |

要點：**兩者都收斂，差在 create 乾淨度。** Flash create 散更多捏造具體值（100k files／50k lines／errno 13）→ 吃更嚴的「獵數字」判官；Pro create 較乾淨、詞彙貼 Opus。**判官必開，且必逐輪掃捏造具體值**（不只抓「Git history reveals」這種明顯的）。實測收斂輪數其實**相同**（Pro 66→85→91、Flash 62→84→91，各 2 個真 refine）——差的是**每輪判官要獵的量**與 create 詞彙貼合度，不是輪數。

## 3.1 作者選型 × 逐輪分配（cost/speed 最佳化；quality 由判官保證）
**關鍵洞察：判官（Opus）是品質保證，作者模型只決定成本與輪數、不決定品質。** 兩者都收斂到判官 ≥90 門檻 → 選型是省錢/省輪的最佳化，不是品質賭注。「貼近 Opus」由**判官門檻**保證，與作者選型無關。

**治理原則：貴/乾淨模型放在「品質會複利」的地方（create），便宜模型放在「機械式」的地方（refine）。**
- **CREATE（round 0）= Pro**：create 的乾淨度與詞彙**向後複利**——乾淨 base = 判官要獵的捏造值少 + Opus-aligned 詞彙 = 省一輪 slug 正規化。
- **REFINE（round 1..N）= Flash**：refine 是「照 gap list 外科式關閉」，機械式、便宜/快。實測 Flash refine **外科**（round-3 只動被點名 2 檔、零新捏造、零 regression），在乾淨 base 上不引入新腦補。
- **升級到 Pro-refine 只在**：Flash 對某 gap 連試不下（plateau），或判官發現它引入捏造快過關閉。實測沒發生。

**排名（快/省 → 慢/貴）**：
1. **Pro create + Flash refines（建議）**：1 個 Pro run + N 個便宜 Flash run；乾淨複利 base + 機械式便宜 refine。最佳 cost/quality。
2. **全 Pro**：最乾淨、判官最省力，但 Pro run 最多。Pro 便宜時用。
3. **全 Flash**：per-run 最便宜，但要**最嚴的獵數字判官** + 可能多一輪 slug 正規化。
4. **Flash create + Pro refine（最差）**：Flash 髒 create 逼 Pro 花 refine 清「Pro-create 本可避免」的髒。別。

**逐輪配方**：`create=Pro → refine₁..ₖ=Flash（判官每輪必獵捏造數字）→ 僅 plateau 時某輪換 Pro`。

## 4. 收斂軌跡（repoprompt-ce，2224 檔，Pro 3.1 作者 × Opus 4.8 判官）
| 輪 | 分 | 頁 | 這輪 |
|---|---|---|---|
| create | 66 | 6 | 基線：Apple-swift-sdk 事實錯、3 library 名錯、native-tree why 腦補未標、幾乎無 git 引用、缺 agent-runtime/MCP內部/Sentry/security |
| refine 1 | 85 | 8 | 修 Apple→community、library 名；補 8 個真 sha（sha→claim 全對）；native-tree why 改標 unverified；掃齊子系統 |
| refine 2 | **91 ✅** | 8 | 純外科（只動 4 頁、零回歸）：修最後 1 library straggler、covers 貼對、加 ContextBuilder/token-budget/workflow 段。過門檻 |

**2 輪精修達 Opus 級**，且 round-2 覆蓋 **≥ 我的 Opus 單發**（Pro 掃到 Chat/Search/Settings/Security，5 頁 Opus 反而沒鋪這廣）。

## 5. 成本邏輯（真正省錢點）
Opus 只花在**審計**（讀 + `git` 驗 + 缺口清單，便宜），永不花在**寫作**（貴）；Gemini 免費做海量寫作/讀碼。
於是 **N 輪便宜作者 + N 輪便宜 Opus 審計 → Opus 級產出**，遠低於「1 次 Opus 全寫」。中型 repo 抓 2–3 輪判官預算。

## 6. openwiki lineage
CREATE pass（`kb-ingest/repo-wiki.workflow.md`）distilled 自 langchain-ai/openwiki 的 agent prompt（`src/agent/prompt.ts`），改成 (a) 跑第三方 repo (b) runner-agnostic (c) 產 YAML frontmatter 供 KG ingest。硬需求：**全歷史 clone**（shallow = 無 git 可挖 = rationale 崩）、runner 必須有 repo 檔案系統 + shell 存取（chat-only LLM 給個 URL 做不到深理解）。

## 7. 誠實帳本（非 husk / 拿掉了什麼）
- **判官是 session 內的 Opus，不是 agy 的 Claude 模型**（使用者明示 agy 只跑 Gemini；agy 內雖有 Claude Opus 4.6，不用）。judge.prompt.md 是「Opus 在 session 跑」的程序，非 agy prompt。
- **`/tmp/rwbench/*`（本 cycle benchmark 產物）不是 durable 基座**——durable 工具已 fold 進 `kb-ingest/`（agy-pass.sh / refine.prompt.md / judge.prompt.md）+ 既有 repo-wiki.workflow.md。引 /tmp = 死 husk。
- **無機器閘 for 收斂判定**：收斂靠 Opus 判官判斷力 + 不變量，非確定性 lint。gaps-latest.md 首行的 `CONVERGED=` 是判官寫的證據，非自動閘。
- 記憶交叉引用：[[agy-runs-gemini-only]]、[[agy-execution-sandbox-human-fired]]、[[opus-judged-gemini-refine-loop]]。
