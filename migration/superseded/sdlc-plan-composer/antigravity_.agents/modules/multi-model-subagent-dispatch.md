# Module: sdlc-plan-composer — S4 多模型子代理分治派工

> 屬 [`sdlc-plan-composer`](../SKILL.md) S4。取代原先理論性引用的 `superpowers:subagent-driven-development` /
> `superpowers:dispatching-parallel-agents`（該 plugin 從未在本專案掛號，見 retarget-map.md）。
> **非自動觸發引擎**：S4 只列出「這個 task 交給哪個 backend」的人工決定清單，主會話逐任務手動呼叫下列
> 三個 backend 之一，不存在自動路由/自動派工的迴圈。

## 三個 backend（人手動三選一，非自動判斷）

### Backend 1 — Claude Code 原生 `Agent`/`Workflow` 工具（Opus／Sonnet／Haiku）

harness 內建工具，非外部 plugin：`Agent({model: "opus"|"sonnet"|"haiku", ...})` 單次派工；多階段/需要
determinism 的分治用 `Workflow` 的 `pipeline()`/`parallel()`。這是 superpowers 那個 skill 原本教的「怎麼手動
dispatch fresh subagent per task」的直接替代——現在是 harness 一級能力，不需要一層 skill 說明書教怎麼做。

### Backend 2 — Codex（OpenAI，GPT-5.5／GPT-5.4／GPT-5.4-mini）

**2026-07-17 更新：官方 `codex@openai-codex` plugin（v1.0.6，scope=user 全局，`/codex:setup` 已驗證
就緒）已裝，派工方式改為 plugin 優先，raw CLI 降為 plugin 不可用時的 fallback。**官方 `codex-cli-runtime`
skill 明文：「Prefer the helper over hand-rolled...direct Codex CLI strings」——不要繞過官方維護的
`codex-companion.mjs` runtime 自己刻 `codex exec` 呼叫（它管 auth/job tracking/background/resume，
自己刻等於重造一套會漂移的替代品）。

**主要機制（優先）**：`Agent({subagent_type: "codex:codex-rescue"})`（或直接 `/codex:rescue`
slash 命令）——這是官方唯一入口，內部只做一次 `Bash` 呼叫
`node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task ...`，原樣回傳 stdout，不加工。派工時：

- **model/effort 明確指定**：官方預設不填 `--model`/`--effort`（「Leave unset unless the user
  explicitly requests one」），但 S4 分治委派本身就是「明確要求」的來源，四級 tier 表（見不變量 3）
  可直接指定：`gpt-5.4-mini`（機械/單檔）→ `gpt-5.4`（整合/多檔，medium effort）→ `gpt-5.5` high
  （設計判斷）→ `gpt-5.5` extra high（架構決策/最終審查）——把 `--model <tier 值>`/`--effort <tier 值>`
  寫進轉發給 `codex:codex-rescue` 的請求文字裡（forwarding rules 會原樣帶過 `task` 呼叫）。
- **write-capable 是預設**：不會自動變成唯讀，除非明確要求唯讀/只要 review/diagnosis/research。
- **背景執行**：任務複雜/開放式/預期跑很久 → 請求帶 `--background`；小而明確的任務 → 預設 foreground
  （或帶 `--wait`）。
- **恢復同一條 Codex thread**：接續前一次 rescue 的結果用 `--resume`（內部映射 `task --resume-last`）；
  要全新一輪用 `--fresh`。
- **結果處理**：`codex:codex-rescue` 回傳的是 Codex 原始輸出，**不可被當作 Claude 自己的實作結果加工/
  改寫**（官方 `codex-result-handling` skill 明文：failed/incomplete 的 Codex run 不可被 Claude 接手
  改成自己的實作嘗試；沒有 findings 就明講沒有，不可揣測）。

**Raw CLI fallback**（僅當官方 plugin 未裝/不可用時；2026-07-17 external-verify 對官方
`developers.openai.com/codex/noninteractive` 逐字引用 + 本機 `codex-cli 0.144.5` 直測）：

```bash
codex exec -m gpt-5.5 -c model_reasoning_effort="high" --sandbox workspace-write \
  --add-dir <target-dir> -C <working-dir> --output-last-message <report-file> \
  "<task 的完整 prompt>"
```

model 字串（`gpt-5.5`/`gpt-5.4`/`gpt-5.4-mini`）與 `-c model_reasoning_effort=` 用法來自本機
`~/.codex/config.toml` 驗證 + `openai/codex` 官方 issue tracker 佐證（hard-secondary，非 model 目錄頁
primary 逐字）；預設 sandbox `read-only`，`--full-auto` 已 deprecated；`--output-last-message`/`--json`/
`--output-schema` 做檔案交接；`CODEX_API_KEY` 僅 CI 情境單次注入。`codex --help`/`codex exec --help`
為本機 `0.144.5` 版本輸出，版本升級後重跑核對（同 external-verify「快照會過期」紀律）。

**其他官方 plugin 能力（附註，非本模組核心，不強行接線）**：`/codex:review`（defect-focused）與
`/codex:adversarial-review`（approach/design-challenge-focused）是純只讀 code review，永不自動修——
與本 repo `code-review` skill 角色不重疊，是額外的跨模型家族（GPT vs Claude）獨立觀點，需要時可直接
呼叫；**不接進 `judge-loop-chooser`**（該 skill 明文「代碼產物→直接 code-review，無 code-branch」是
刻意設計邊界，不為塞新功能破壞它）。`codex:codex-rescue`（「Claude 卡住/需要更深根因調查」）跟
`repo-fullstack-debugger` 的存在理由高度重疊，該 skill 已補一條旁註（見其 SKILL.md），非取代其協議。

**codex sandbox 命門（2026-07-19 實測 fold-in）**：codex-companion `task --write` 硬設 `workspace-write` sandbox，**預設保護 dot-dir**——`.agents/`／`.claude/` 的寫入一律 `Operation not permitted`（`docs/`／`loop_wiki/`／`src/` 非 dot 故可寫）。companion `task` 不透傳 `-c`/`--sandbox`，官方鐵律禁手刻 `codex exec` 繞過 → **無法 per-dispatch 解除**。**routing 規則：skill-SSOT（`.agents/`）編輯一律路由 native Claude 家族（Sonnet／claude-p／Opus），codex 只派非 dot 碼（`loop_wiki`／`src`／`docs`）。** 這是 feature 非 bug——codex sandbox 保護 harness 自己的 skill 定義不被外部模型亂寫；skill 編輯本就該 in-family。實證：本 session codex 成功寫 `loop_wiki`（marginal-dispatch）／`docs`（assertions.md），但 `.agents/` skill 編輯 2 次 dispatch 皆 **completed-but-blocked**，改 Sonnet fallback 一次即成。**判活補充**：codex「job completed 但 sandbox 擋寫」＝新失敗貌（非 quota／非內容）——查 `codex-companion.mjs status <job>` 的 blocked 訊息，別只看有無落盤。

### Backend 3 — `agy`（Gemini Pro／Flash，不重複，指既有慣例）

Gemini 分派**不在此重述**——本專案已有成熟的 `agy` 派工慣例（`kb-ingest/agy-pass.sh` +
記憶 `agy execution: --add-dir + accept-edits`），model 字串比照該慣例傳入 `--model`。**agy 只跑 Gemini
系列**（判官/協調角色仍用主 session 的 Claude/Opus，不可指定 agy 跑 Claude 模型——既有記憶已載明）。

**兩級任務複雜度 tier（明示）**：`Gemini 3.5 Flash (High)`（輕量/快速任務）→ `Gemini 3.1 Pro (High)`
（複雜/需要更強推理任務）——兩者皆固定 `High` reasoning，只換模型不換 effort（跟 codex 四級「模型+effort
雙軸遞增」不同，agy 這條軸目前只暴露模型選擇）。

## 不變量

1. **三選一皆人工決定**：S4 產出的是「task → backend」對照表，不是自動路由邏輯；換 backend 是人的判斷，
   不委派給任何一個 backend 自己決定。
2. **file-handoff 優先**：三個 backend 都遵守「大輸出走檔案，不塞回主 session context」——native Agent
   工具本身已如此設計；`codex exec` 用 `--output-last-message`；`agy` 用 `agy-pass.sh` 既有的
   `$OUT` 落檔慣例。
3. **model 選擇看任務複雜度**：沿用 subagent-driven-development 原本的「機械任務用便宜模型、整合/判斷任務
   用中階、架構/設計任務用最強模型」原則——這條紀律平台無關，三個 backend 都適用，明示 tier：

   | 任務複雜度 | Claude native（Agent 工具） | codex exec | agy |
   |---|---|---|---|
   | 機械/單檔轉錄 | haiku | `gpt-5.4-mini` + `medium` | `Gemini 3.5 Flash (High)` |
   | 整合/多檔協調 | sonnet | `gpt-5.4` + `medium` | `Gemini 3.5 Flash (High)` |
   | 設計判斷 | sonnet 或 opus | `gpt-5.5` + `high` | `Gemini 3.1 Pro (High)` |
   | 架構決策/最終整體審查 | opus | `gpt-5.5` + `extra high` | `Gemini 3.1 Pro (High)` |

   派工時**明確指定**model（+ codex 的 reasoning effort）——省略等於隱性繼承主 session 最貴模型，
   silently 打掉這條分級的意義（同 subagent-driven-development 原文「Always specify the model
   explicitly when dispatching a subagent」的紀律）。

   > **target 路徑先於複雜度決定 backend（2026-07-19）**：上表按任務複雜度選 model，但**先看 target 在哪**——`.agents/` skill-SSOT 編輯**不論複雜度一律 native Claude**（codex sandbox 擋 dot-dir，見 Backend 2「codex sandbox 命門」）；codex tier 只適用非 dot 碼（`loop_wiki`／`src`／`docs`）。agy 同受此限（skill 編輯不外包）。

## 方法論（大迴圈 Domain 經驗，2026-07-17 fold-in；可複用於本模組以外的任何多家族派工設計）

**原則一：每個 family 只佔一個 pipeline 階段，別讓同一 family 兼兩個角色**——本模組把
Discover/Plan/Execute/Verify 四階段分給四個獨立家族（agy／Fable5／codex／Opus，見
`loop-harness-standard/modules/harness-spec.md` §9❽），核心理由不是「多用幾個模型」，是**每加一個
獨立家族，就多一層「執行者≠判官」式的天然隔離**——已在 `loop_wiki/design_governance`／`codex_demo`
真跑驗證：codex(執行)×Opus(判官) 是跨家族天然隔離（比 claude-p(執行)×Opus(判官) 同家族還需要
fresh-subagent 額外工序更乾淨）。**這條原則不是本模組專屬**——任何大迴圈委派任務只要有「起草者」和
「審查者」兩個角色，都該先問「這兩個角色能不能落在不同家族」，能就優先選不同家族，非事後才想到
要不要獨立 judge。

**原則二：機械 drift-checker + fresh 獨立判官複核 = 驗證「獨立改寫是否忠實」的通用模式**——
`design_governance` 的 R9 dual-file-drift（比對 agy 獨立寫的 AGENTS.md 是否忠實反映 CLAUDE.md 原有
事實）不是一次性用途，是**任何「同一份 domain 知識被不同家族/不同時間點獨立改寫」場景**都適用的模式：
機械 checker 先抓「表面上看起來不一致」的候選清單（可能有大量假陽性），fresh 獨立判官再對候選清單做
語義複核（過濾假陽性/確認真缺口/抓機械 checker 本身判準寫反的 bug）。2026-07-17 真跑實測：39 條候選
裡機械層抓到的「漂移」多數（~34 條）是假陽性、僅 3 類是真缺口——**如果沒有 fresh 判官這一步，光靠機械
checker 的原始輸出会嚴重高估漂移量**，這是本模式價值所在，非為了排場多找一個模型審一次。

**原則三：多輪收斂測試需要刻意限制單輪範圍**——`codex_demo` 實測發現，強模型單次 dispatch 內建的
agentic iterate-until-pass 太強，自然任務很難逼出 engine 外層的多輪迴圈（no-progress/regress/
restore-best 這些機械路徑因此長期未被真實踩過）。要測試「多輪收斂機械是否真的work」，得**刻意**造一個
單輪範圍受限的 dispatch（如 `ONE_FIX_PER_DISPATCH` 環境變數），而非等一個自然案例湊巧需要多輪——
這條經驗適用於任何要驗證「iterate-until-pass 引擎本身」而非「某個 driver 能力」的測試設計。

**原則四：stub-selftest 綠＋跨家族 code-review 過，都不證 integration——「engine 算好狀態 → 另一沙盒／進程消費」的接縫，last-mile 消費端只有 live 驅動真流程才證。** 2026-07-19 marginal effort-dispatch 實證：`engine.sh` 的 effort-ladder `export ENGINE_ARM_MODEL/EFFORT`，但小迴圈 `run.sh` 從不讀 → 真 codex 每輪跑同一 model＝核心斷線；三 selftest 全綠、Opus 跨家族 code-review 無 critical/major **皆漏**，唯 live 跑（真 codex 穿過真閘，證錨 `loop_wiki/codex_stall/_engine-run/driver.iter1-4.out` 4-rung 真派工 model 逐 rung 換）抓到。通則：凡「上游 export 狀態、下游沙盒消費」的 wiring，消費端必 live 驗、非 stub——這正是 verify skill「跑真流程別只信 test」在多家族派工的落地。基座落地契約見 [`loop-harness-standard`](../../loop-harness-standard/modules/harness-spec.md) §9（effort-ladder last-mile，不重述）。

**原則五：檢索／comprehension 階段的派工紀律（2026-07-19 fold-in；技術實作常需檢索既有實作與接線，此階段有四條命門）。** (1) **Judge 留 output 側**——讓 Opus 判官先消費 retrieval input、之後又判 output＝判自己框定的東西＝Same-Weights 自證，判官獨立性當場污染；檢索綜述交 **Fable**，Judge 只 fresh 判 output（對錨＋spec，未參與 input 塑形）。(2) **handoff 傳 `file:line` 指針、非散文摘要**——codex 有 Read/Bash，**自己開錨重讀**；餵它別人嚼過的散文＝telephone game，摘要≠真碼就整條歪（同「指針不複述」鐵律）。(3) **agy niche＝外部-currency ＋ 跨家族 truth-check，非例行 repo 檢索**——repo-internal 查用 `grepai`（語義）／`serena`（LSP 符號，更準且不搶 `:9333` 單帳號）；agy 只燒在「**只有它能做的**」（即時 web／DR 拉 post-cutoff 事實、不同權重獨立驗某 claim）——事實就是事實、換家族不加分，拿 agy 做例行檢索＝手術刀削鉛筆＋燒最擠的池＋silent-noop 風險（見 S-1 (g) 外部-currency lane）。(4) **小迴圈檢索＝driver 自讀沙盒**（窄、本地，零額外 dispatch）。反-husk 錨＝指真 skill（[`external-verify`](../../external-verify/SKILL.md)／[`repo-agent-native`](../../repo-agent-native/SKILL.md)／[`judge-loop-chooser`](../../judge-loop-chooser/SKILL.md) 三態 grounding），無虛基座。

## Sources（2026-07-17 external-verify 快照，會過期）

- https://developers.openai.com/codex/noninteractive （官方 non-interactive mode 文件，逐字引用於上方
  sandbox/`--json`/`--output-last-message`/`--output-schema`/auth 段落）
- https://github.com/openai/codex/issues/19451 、 https://github.com/openai/codex/issues/16984 、
  https://github.com/openai/codex/issues/20635 （官方 repo issue，佐證 `gpt-5.5`/`gpt-5.4`/`gpt-5.4-mini`
  為真實可設定的 model 字串）
- 本機 `codex --version`（`codex-cli 0.144.5`）／`codex exec --help`／`~/.codex/config.toml`（直測，2026-07-17）
- 官方 `codex@openai-codex` plugin v1.0.6（`~/.claude/plugins/cache/openai-codex/codex/1.0.6/`，本機讀原檔
  直測 2026-07-17）：`skills/codex-cli-runtime/SKILL.md`、`agents/codex-rescue.md`、
  `skills/codex-result-handling/SKILL.md`、`skills/gpt-5-4-prompting/SKILL.md`、
  `commands/{rescue,review,adversarial-review,transfer}.md`；`/codex:setup --json` 本機直測輸出
  （`codex-cli 0.144.5`、ChatGPT login active、`reviewGateEnabled: false`）。
