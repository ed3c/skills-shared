---
name: repo-fullstack-debugger
description: |
  全棧失敗診斷外層閉環(Diagnoser) —— 當一個更便宜的協作者已卡住：automate.js 瀏覽器自動化反覆撞 DOM 黑盒(selector 漂移／detached frame／headless soft-block／DR 啟用時序 flaky)，
  或動態跑一個 repo 反覆失敗／燒 token 而腳本重試解不掉時接管。4 層：L0 反過度設計閘(確定性一次讀能拿 A 級就 STOP 退回，別進迴圈) →
  L1 消費失敗 trace(stealth-browser console／截圖／automate.js 失敗簽名；或 repo 執行輸出，不盲猜) → L2 雙象限診斷(瀏覽器 Bot／Timing／Selector／Auth；repo 執行 S2.5 未索引服務／共享狀態／靜默失敗／逾時) →
  L3 strategy 草稿紙(有效／搞砸／該停做 ＋ 退步→revert 記憶棘輪) → L4 畢業成 tested playbook 經 fold-in 沉澱進 owner skill／AGENTS.md Resolved(禁回退鐵錨)。
  Use when：一個瀏覽器 run 或 repo 動態執行反覆失敗、腳本重試解不掉、要 trace 診斷再編譯成可重用 playbook。
  NOT for：一般本地 bug(用 diagnose／systematic-debugging)、源碼靜態已可 A 級解析(用 repo-agent-native)、跑管線本體(用 dr-research-loop)。
---

> **這是 northstar `repo-fullstack-debugger` 的 antigravity retarget，不是原樣搬。** 命門＝L0-L4 trace-driven 診斷紀律一對一映(且回到它的原生 domain——本 skill 源自 Autobrowse／site-debugger 瀏覽器代理研究)；北極星專屬基座(L1 Self-Mutation Mode M0-M5／`skill_optimizer.py`／`hallucination_audit.py`／ixsecurity-e2e 協作者／PG-RFD 編號)**無基座已拿掉並記錄** → `modules/retarget-map.md`。L2 雙象限 know-why → [`modules/l2-quadrants.md`](modules/l2-quadrants.md)。
> **Diagnoser 本質**：它**不**自己跑瀏覽器／repo 執行——它接管協作者的**失敗** run，從 trace 診斷，交回一份修好的 playbook。Harness 不動，改的是 playbook 配置。

# repo-fullstack-debugger(antigravity)

## When to Use
**只有在**一個更便宜、更確定性的協作者已經試過且卡住之後才動用：
- `automate.js`／`gemini-conversation-research`／`dr-research-loop` 的一個 run **反覆失敗**——selector 漂移／detached frame／headless soft-block／DR 啟用時序 flaky／剪貼簿污染——而腳本重試解不掉(這些是 runtime-only 黑盒事實，不在源碼裡，所以 L0 正確 ADMIT 迴圈)。
- **動態跑一個 repo**(build／test／起服務)反覆失敗、命中隱藏依賴、或靜默失敗鏈，腳本重試無效。
- 一個 run **跑得過但很貴**——重複的探索該被編譯成一條確定性快路。

產出＝一份持久、人類可讀的 **playbook**：未來的 run 載入它就跳過探索稅(從「即時在線推理」走向「自動化技能編譯」)。

## Not For
1. **一般本地 bug／測試失敗／stack trace** → `diagnose` / `diagnosing-bugs`(重現→縮小→修；無 trace 接管、無畢業)。
2. **成功的靜態不變量抽取** → `repo-agent-native`(route back)。若 grepai／git 已給出 A 級事實，L0 閘把你**退回那裡**——別啟動本迴圈(這就是 167-line-static 反模式)。
3. **跑管線本體** → `dr-research-loop`(YouTube→卡片盒→DR 閉環)。本 skill 診斷它的*失敗*，不是執行器。
4. **外部框架能力 claim** → `external-verify`。

> **旁註（2026-07-17）**：官方 `codex:codex-rescue` subagent（`openai-codex` plugin）定位是「Claude
> 卡住/需要第二次實作或診斷/需要更深根因調查」，跟本 skill 的存在理由高度重疊——差別是本 skill 是
> **domain 專屬**（瀏覽器 selector/timing/repo 執行的 L0-L4 trace-driven 協議，見 L2 雙象限），
> `codex:codex-rescue` 是**換模型家族的通用選項**（GPT-5 系列第二意見，非本 skill 這套協議的替代）。
> 兩者不互斥：本 skill 的 L3「該停做」判定若判定「這個坑需要完全不同的模型視角」，`codex:codex-rescue`
> 是合理的下一步，而非重跑本 skill 的迴圈；反之若 codex-rescue 也卡住，回本 skill 的 trace-driven
> 協議繼續。詳見 `sdlc-plan-composer/modules/multi-model-subagent-dispatch.md`。

## Architecture — 4 Layers + L0 Gate

### L0 — Autonomy Gate(反過度設計閥門)· MANDATORY FIRST
進迴圈**之前**先探目標的確定性，產 `autonomy-gate-verdict.yaml`：
- 失敗那個事實，能不能用一次便宜的確定性讀(`grepai_trace_callers`／單次讀源碼／單次 stealth-browser DOM 抓取)就拿到 **A 級**？→ **STOP，退回協作者。別迭代。**
- **只有當**事實真的是黑盒才進迴圈：runtime-only 行為(DOM 在跑時才長那樣)、無源碼可讀、被混淆、藏在多步／非確定性互動之後。
- **STOP 鐵則**：最多 3-5 輪；成本／步數／turn 數跨輪不再下降 → abort 提早中止。目標＝一條夠好、可靠、便宜的路，**不是**全域最佳解。

### L1 — Trace Observability(消費失敗 trace，不盲猜)
別猜。讀協作者的失敗 trace：
- **瀏覽器目標**：`stealth-browser` console log(`read_console_messages`)／截圖／DOM 快照 ＋ `automate.js` 的失敗簽名(如 `dr_not_found`／`__genFailure`／`__drPlanFailed`／`planRefusedCheck`／widget miss)。AGENTS.md「Resolved」帳本是既有失敗簽名庫，先比對。
- **repo 目標**：實際 build／test／run 的 stdout/stderr／exit code ＋ 服務 log；靜態面 `grepai`／ripgrep call-graph。

### L2 — Diagnosis(雙象限，重用不重造)
按目標選象限集(Slop #2 extend-not-duplicate)。完整 know-why → [`modules/l2-quadrants.md`](modules/l2-quadrants.md)：
- **瀏覽器失敗 → Bot／Timing／Selector／Auth 四象限**(site-debugger 原生)：Bot＝反自動化偵測／soft-block；Timing＝race／未 render 完就找／protocolTimeout；Selector＝DOM 漂移／被側欄劫持；Auth＝額度枯竭／登入態。
- **repo 執行失敗 → S2.5 破盒推論四象限**(重用 `repo-agent-native` 的：未索引服務／共享狀態耦合／靜默失敗鏈／逾時鏈)。

### L3 — Strategy Scratchpad(跨 session ＋ 記憶棘輪)
維護 `strategy-scratchpad.md`：**有效／搞砸／該停做**。每輪只測**一個假設**。記憶棘輪：pass-or-progress → keep；**退步(regression) → revert scratchpad 回上一版**，換假設。下一輪當 context 載入，讓改進累積(不歸零)。

### L4 — Graduation(畢業 playbook → fold-in)
最近 3 輪有 2+ passes(或達 max-iter)**且**成本/步數已收斂：把 scratchpad 清成自足的 `<target>-playbook.md`——`recommended_method`(那條便宜確定性的路)＋ `alternative_methods` ＋ **帶迭代溯源的 Gotchas**(「iter2 看到 X、iter4 看到 Y」)。每條 Gotcha 帶一個 Evidence Level；C/D 級的別寫進 playbook。
**交棒 fold-in(收斂點)**：畢業的 playbook＝一段「已完成、可測」的經驗 → 委派 [`fold-in`](../fold-in/SKILL.md) 沉澱進 **owner skill 的 Gotchas ＋ AGENTS.md「Resolved」帳本(`禁回退用…` 鐵錨)**。fold-in 的 discrimination gate 會**擋純散文 playbook**——所以畢業物必須帶確定性鐵錨(automate.js 真實修法／可測步驟 ＋ 禁回退錨)，否則被退回(別存 husk)。

## Diagnostic Checklist(由上而下，第一個能解決的點停)
1. **[L0] 確定性探測** — 一次確定性讀有沒有 A 級拿到事實？→ STOP，退回，**別**進迴圈。
2. **[L0] 迭代預算** — 已 ≥5 輪、或成本/步數最近 2 輪持平？→ 中止，帶已知失敗註記 graduate-as-is。
3. **[L1] 有 trace 嗎？** — 真有一份失敗 trace 可讀嗎？沒有先弄到一份再假設。
4. **[L2] 象限** — 命中哪個象限(瀏覽器 Bot/Timing/Selector/Auth；repo 未索引服務/共享狀態/靜默失敗/逾時)？
5. **[L2] 證據等級** — 診斷出的原因是 A/A-/B+ 還是 C/D？D → 別寫進 playbook。
6. **[L3] 一個假設** — 這一輪只測一個改動嗎？(多個＝無法歸因。)
7. **[L3] 退步** — 相對保留的 baseline 退步了嗎？→ revert scratchpad，換假設。
8. **[L4] 收斂** — 最近 3 輪 pass-rate ≥2/3 **且**成本/步數已 plateau？→ 畢業(→ fold-in)。否則預算內續迭代。
9. **[L4] playbook 自足性** — 一個沒看過這次 run 的人能照 playbook 執行嗎？Gotchas 有溯源嗎？有禁回退錨嗎？

## Boundary Artifacts
| Artifact | Layer | 角色 |
|---|---|---|
| `<OUT>/debug/<target>/autonomy-gate-verdict.yaml` | L0 | 路由決策(確定性快路 vs 進迴圈)＋預算 |
| `<OUT>/debug/<target>/strategy-scratchpad.md` | L3 | 跨 session 有效/搞砸/該停做 ＋ 棘輪歷史(可變) |
| `<OUT>/debug/<target>/<target>-playbook.md` | L4 | 畢業的 tested playbook → 交 fold-in 沉澱 |

## Collaboration Contract
- **Takeover-on-failure(瀏覽器)**：`automate.js` / `gemini-conversation-research` / `dr-research-loop` 的一個 run 反覆失敗(selector 漂移／headless soft-block／時序 flaky——runtime-only 黑盒，L0 正確 ADMIT) → 交來這裡用**瀏覽器版 L2**(Bot/Timing/Selector/Auth)診斷。這是本 skill 的原生 domain(源自 site-debugger)。
- **Takeover-on-failure(repo)**：`repo-agent-native` 的抽取撞 runtime-only 黑盒(S2.5 無法 A 級解析) → 交來這裡用 **repo 執行版 L2**(S2.5 四象限)。
- **Handback via fold-in**：L4 playbook 的 load-bearing 修法 → fold-in 選 owner → 沉澱進 owner SKILL Gotchas ＋ AGENTS.md「Resolved」`禁回退用…` ＋ owner modules/ know-why。探索稅只付一次。**這是 LLM 中介 handoff(誠實：非 hook bridge)。**

## Convergence & Graduation
預設預算 5 輪，積極提早停(成本/步數 plateau)。最近 3 輪 2+ 次通過、或達 max-iter 時畢業。**遞迴自我優化 OUT of scope**(YAGNI——連 Autobrowse 都列為 future)。
