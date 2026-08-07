# Module: loop-harness-standard — 迴圈工程 Harness 技術規格（跨 agy／Claude Code 雙可跑）

> 屬 [`loop-harness-standard`](../SKILL.md)。SKILL.md＝跨 LLM 基座組件卡＋不變量；本檔＝**兩種完整目錄
> 結構圖（agy 版／Claude Code 融合版）＋設計規範差異＋實作差異＋設計決策 know-why**。
> **核心原則**：同一小迴圈沙盒**兩種 driver 皆可跑**——agy（Gemini-author）讀 `AGENTS.md` 與 agy 側八大
> 基座；`claude -p`（Claude-author）讀 `CLAUDE.md` 與 Claude 側八大基座。兩側是**技術等價物並列**，非二選一。

---

## §1 兩種完整目錄結構圖

### ❶ agy 版八大基座沙盒（ix-agy MVP 保留、materialize 於 `loop_demo/agy`；agy 讀 AGENTS.md）
> 質數迴圈跑通的原始形，agy 執行器 `agy --project <id> -p "..." < /dev/null` 從沙盒 CWD 起載入。

```text
<loop_root>/                          # 迴圈沙盒根（如 loop_wiki/repo_wiki_converge）
├── run.sh / scripts/run_loop_demo.sh # 1  統一調度入口（Orchestrator）
├── PROMPT.md                         # 7  目標規範合約（Goal Spec / Success Criteria）
├── IMPLEMENTATION_PLAN.md            # 8  狀態與 PLAN 帳本（STATUS: executing/done/failed）
├── AGENTS.md                         # 1  規則與 Standing Context（≤300 行防上下文腐化）
├── data.txt                          #    業務變更數據（loop_wiki 中對應 wiki 目錄）
├── .agents/                          #    本地配置目錄
│   ├── settings.json                 # 2  專案設定（"autoExecutionPolicy": "EAGER" 自動授權）
│   ├── hooks.json                    # 3  生命週期鉤子（PostToolUse；payload toolCall.name/args）
│   ├── hooks/on_write.py             #    本地攔截器（軌跡寫本地日誌，絕對路徑）
│   ├── skills.json                   # 4  技能註冊表（CI/協作校驗用，執行非必需）
│   ├── skills/                       # 5  特化技能與 domain 知識（frontmatter 相符才載入）
│   └── agents/verifier.md            # 6  子代理人（/agents 自動發現，隔離審查）
├── scripts/
│   ├── run_loop_demo.sh              #    迴圈調度主程式
│   └── validate_primes.py            #    獨立硬性驗證器（單體，驗 Exit Code）
└── data/log/hook_run.log            #    Hook 寫入攔截日誌
```

### ❷ Claude Code 融合版八大基座沙盒（agy／claude -p 雙可跑）
> **融合雙架構**：同沙盒同時具備 agy 側與 Claude 側八大基座——agy 執行讀 `AGENTS.md`＋`.agents/*`；
> `claude -p` 執行讀 `CLAUDE.md`＋`.claude/*`。`run.sh` 的 driver switch 決定跑哪側。活實例＝
> `loop_wiki/design_governance/`（目前只接 Claude 分支），骨架＝`loop_wiki/_template/`。
>
> **dual-runnable 才雙檔；單家族迴圈禁建第二檔**（活例：design_governance＝Claude-only 僅
> `CLAUDE.md`，無 `AGENTS.md`）。symlink tracer VERIFIED PASS-both（`RETARGET-VERIFIED.md` §
> symlink 補測）後，dual-runnable 沙盒的雙檔預設落地形＝**一實體＋一 symlink**（如
> `CLAUDE.md` → `AGENTS.md`），非兩份各自維護的實體檔——第一實例＝`loop_wiki/agy_demo`
> （其 `CLAUDE.md` 即 symlink→`AGENTS.md`；`claude_agy` 維持雙檔＝canonical 範例，不 symlink）。

```text
<loop_root>/                          # 雙可跑沙盒；driver 家族決定讀哪套被動上下文與基座
├── run.sh                            # 1  調度入口 + driver switch（agy | claude | subagent）
├── PROMPT.md                         # 7  目標規範合約（兩側共用；Guard/Metric/stop-loss）
├── PLAN.md                           # 8  狀態帳本（= agy IMPLEMENTATION_PLAN.md 短名；兩側共用）
├── AGENTS.md                         # 1a【agy 側被動上下文】≤300 行 standing rules（agy 認）
├── CLAUDE.md                         # 1b【Claude 側被動上下文】≤300 行（claude -p 認＋cascade，D5 tracer）
│                                     #     混家族雙檔：domain 事實**單一 SSOT**、另一檔＝呈現層派生（09 I8，防雙圖漂移）
├── .agents/                          #   【agy 側基座】
│   ├── settings.json                 # 2a  autoExecutionPolicy: EAGER
│   ├── hooks.json                    # 3a  PostToolUse；payload toolCall.name/args；絕對路徑
│   ├── skills.json                   # 4a  技能註冊表（可選/CI）
│   ├── skills/                       # 5   domain 技能（兩側目錄 auto-discovery 共用）
│   └── agents/verifier.md            # 6a  agy 隔離審查子代理
├── .claude/                          #   【Claude 側基座】
│   ├── settings.json                 # 2b  permissions；hooks 併入本檔 hooks 鍵（Claude 家族慣例）
│   │                                 #     受全局 hook 保護寫不得 → 授權改走 run.sh --permission-mode CLI 旗標
│   └── agents/verifier.md            # 6b  fresh zero-context subagent（禁 fork；同家族才落地，D6.1）
├── scripts/
│   ├── (run.sh 內 driver switch)     #    agy 分支：agy --project < /dev/null／claude 分支：claude -p --permission-mode acceptEdits < /dev/null
│   └── <fn>.{sh,py}                  #    功能驅動 checker（零 LLM，exit 0/2；scripts↔tests 成對）
│                                     #    例：r9-dual-file-drift.py（AGENTS.md/CLAUDE.md 雙檔漂移 checker）
├── tests/<fn>/                       #    分層驗證（取代 agy 單體 validate_primes.py）
│   └── fixtures/{good,hollow}/       #      fixtures 即測試本體；positive-control：good=PASS ∧ hollow=FAIL（anti-placebo，D8）；selftest.sh generic 調度直呼 scripts/<fn>（wrapper verify.sh 已砍，D8① 實作層重詮釋）
├── evals.json                        #    一次性 pre-registered 行為驗證（維度×槓桿＋planted-defect，D8）
├── verify.sh                         #    T0 聚合：跑全 checker，hard 違規 exit 2、全綠 exit 0（副檔名路由 target 類型）
├── selftest.sh                       #    checker 自檢（每 checker good/hollow 區分才算活）
└── logs/                             #    沙盒本地 log（兩側 hook 導向此）
```

---

## §2 設計規範差異與實作差異（明確列出）

| 基座 | 設計規範差異（為何不同） | agy 側實作 | Claude Code 側實作 |
|---|---|---|---|
| **被動上下文檔名** | driver 家族決定認哪檔——**D5 tracer 實測：`claude -p` 認 subdir `CLAUDE.md`＋cascade parent、不認 AGENTS.md**；**dual-runnable 才雙檔，單家族迴圈禁建第二檔**（活例：design_governance＝Claude-only 僅 `CLAUDE.md`）；dual-runnable 雙檔預設走 symlink（PASS-both，一實體＋一 symlink），非兩份實體各自維護 | `AGENTS.md`（≤300 行） | `CLAUDE.md`（≤300 行）；混家族雙檔則 domain 單 SSOT＋另一檔呈現層派生（09 I8） |
| **授權自動化** | agy 走 settings 政策；Claude 走 CLI 旗標（`.claude/settings.json` 受全局 hook 保護寫不得） | `.agents/settings.json` `"autoExecutionPolicy":"EAGER"` | `run.sh` driver 加 `--permission-mode acceptEdits`（B4 降權 2026-07-11；slice 05 hook 對 verify.sh allowlist 回核准 JSON 後 acceptEdits 得核准 Bash 類 verify.sh，權限面更小）＋全局 hook allowlist |
| **Hook payload** | 兩家 CLI 的 stdin JSON 封裝格式不同 | `data["toolCall"]["name"]`／`["args"]`（非扁平 `tool_name`） | Claude Code hooks payload schema **依現場定**，需 hook 的 loop 才驗欄位名（不預判寫死，Path B-2） |
| **Hook 位置** | Claude 家族把 hooks 收在 settings 內 | 獨立 `.agents/hooks.json` | 併入 `.claude/settings.json` 的 `hooks` 鍵 |
| **技能發現** | agy 有顯式註冊表選項；Claude 純目錄發現 | `.agents/skills.json`（顯式清單，CI/協作用） | `.agents/skills/` 目錄 auto-discovery（frontmatter name/description）；**不設獨立註冊表** |
| **獨立 verifier** | 同家族隔離需求不同（D6.1） | `.agents/agents/verifier.md`（`/agents` 發現，隔離審查） | `.claude/agents/verifier.md`＝fresh zero-context subagent（**禁 fork**）；跨家族時免落地 |
| **驗證器形態** | agy 單體示範；Claude 採三層（機械+行為+邊界） | `scripts/validate_primes.py`（單體硬驗證器） | `scripts/<fn>`↔`tests/<fn>/fixtures`（good/hollow）成對（D8① 實作層重詮釋：wrapper `tests/<fn>/verify.sh` 已砍，02-registry-consolidation.md §B2-B4）＋`evals.json`（一次性行為驗證）＋覆蓋率＝planted-defect 檢出率 |
| **狀態帳本檔名** | 純命名 | `IMPLEMENTATION_PLAN.md` | `PLAN.md`（短名，同職責） |
| **非互動重導向** | 兩家皆需 `< /dev/null`，根因表徵不同 | `agy -p < /dev/null`（無則偵測 stdin 阻塞、無限卡死零輸出） | `claude -p < /dev/null`（tracer VERIFIED exit 0 不 hang） |
| **cache 機制** | 兩家 API 快取模型不同 | Gemini 顯式門檻 2048/4096 tokens＋隱式（2.5/3.5） | Claude Code cache-read ~10%、TTL 5min/1hr、**git 快照入 scope（迭代禁 commit）**、subdir 非穩定快取層（driver 從沙盒 CWD 起才進穩定層，D7） |

> **共用不變的（兩側相同）**：≤300 行被動上下文防腐化（91.6%→71.3%）· prefix 字元級穩定禁動態變數 ·
> 絕對路徑 · 驗證器/執行者拓撲隔離（家族層）· 大小迴圈沙盒分工 · Hook 自包含 · 編譯/實機驗證接真 exit code。

---

## §3 設計決策 know-why（兩側）

### ❶ 為何驗證器（Verify）與執行者（Execute）拓撲隔離？
寫代碼/寫資料的模型自審極寬容——同 prompt/同上下文會「合理化」自欺，改壞既有功能產生無聲 regression。
防線＝硬性、純代碼或外部子代理（agy `validate_primes.py`／`.agents/agents/verifier.md`；Claude
`scripts/<fn>` checker／`.claude/agents/verifier.md` fresh subagent）作 Verify 閘，AI 面對無法用花言巧語
討好的 exit code（0=Success/2=Fail）。核心不變量＝「執行者≠判官權重」，隔離在**家族層**（D6.1）：跨家族
（Gemini 作者×Opus 判官）自動滿足；**同家族（Claude×Claude）必落地 fresh zero-context subagent（禁 fork，
fork 繼承脈絡＝非隔離）**。design_governance pilot 即同家族，semantic 判官逮到 driver Goodhart 機械 R7＝實證。
畢業 semantic 判官對 subtle 集檢出率**已實測**＝12 fresh Opus 5/6（軸別全吻合），漏抓 M19 已 fold-back 雙層
封住；D5 判官 repo 權污染向量隔離後誤報 1/6——見 03-detection-rate-verdict.md。dual-runnable 沙盒派生檔可
symlink（`CLAUDE.md`→`AGENTS.md`，tracer PASS-both 證兩家認）消漂移面；`claude_agy` 維持雙檔＝canonical
範例——見 06-context-file-redesign.md。

### ❷ 為何被動上下文 ≤300 行？
過大常駐上下文使模型定位關鍵約束（Never rules）時注意力被稀釋，任務完成率 **91.6% 暴跌至 71.3%**（ix-agy
實測）。被動上下文只宣告：簡介/stack、核心指令、≤5 條絕對禁止；其餘進 Skills 漸進加載。兩側同此（AGENTS.md
與 CLAUDE.md 皆 ≤300 行）；混家族雙檔時 domain 事實單一 SSOT、另一檔呈現層派生（09 I8，防沙盒內雙圖漂移）。
（此數字錨行數超標的上下文腐化；內容構成的受眾混雜無獨立實測錨，勿引本數字論證後者）

### ❸ 背景程序阻塞（Stdin Hang）與授權
**agy**：`agy -p` 背景執行無聲卡死（CPU 0、零輸出）——CLI 為 interactive TUI 設計，背景無 TTY 時 stdin
仍 open 會阻塞讀取。解＝`< /dev/null` 送 EOF 令其 one-shot 執行退出；且 `.agents/settings.json` `EAGER`
否則等人工核准無限卡（DB Lock）。**Claude**：`claude -p < /dev/null` tracer VERIFIED 不 hang；跑 script
（verify.sh 機械 checker）用 **`--permission-mode acceptEdits`**（B4 降權，2026-07-11）——slice 05 修好
全局 hook 對 loop_wiki verify.sh 的 allowlist，回核准 JSON（`permissionDecision:allow`）後 acceptEdits
下 driver 跑 verify.sh 得明確核准（V3+B4 eval 證 permission_denials=0、收斂/turns 與 bypassPermissions
一致）；driver 的 Bash 面＝default-deny（只 allowlist verify.sh＋classifier 放行）＝權限面更小、幻覺出
的任意 Bash 被擋。安全仍由全局 hook 把關：**bypassPermissions／acceptEdits 皆不繞 hook**（PreToolUse
照跑、BASH_BLACKLIST/DANGER 照擋＝安全不失）；任一 denied 復發→回 bypassPermissions。錨
`loop_wiki/design_governance/run.sh`。

### ❹ Hook payload 解析
**agy** 實測 payload：`toolCall.name`/`toolCall.args`（非扁平 `tool_name`）；`except` 一律回 exit 0（除刻意
Block，否則 Hook 自身解析錯誤會無故中斷正常 Tool）；日誌寫沙盒 `logs/hook_run.log`（絕對路徑）。**Claude
Code** hooks 收在 `.claude/settings.json` 的 `hooks` 鍵，payload schema 依現場定、需 hook 的 loop 才驗欄位名。

### ❺ 嵌套小迴圈沙盒化兩分類
八大基座分**基座引擎本身**（run.sh/settings/hooks/skills.json——控執行權限/生命週期/調度）與**由 Skill 轉換
出的業務狀態元件**（被動上下文/PROMPT/PLAN/skills/tests verify——攜該沙盒業務邏輯與驗證指標）。單體巨型 skill
拆分沙盒化的映射見 §6 與 antigravity-harness-wiki 記錄層全境圖。

---

## §4 driver 選型（D5 ADOPT 定案）
per-loop driver 三態（`run.sh` switch）：① agy（Gemini 作者，kb-ingest 已證）② `claude -p`（Claude 作者，
design_governance 已驗；沙盒放 CLAUDE.md、`--permission-mode acceptEdits`，B4 降權 2026-07-11）③ 對話內 sub-agent（輕量、
無獨立沙盒執行體）。兩迴圈形態：A 內含式（artifact 住 context）≈ 對話內 sub-agent；B verify-inside 嵌入式
（迭代在沙盒外、沙盒一次驗證）≈ loop_wiki 沙盒。**driver permission-mode 命門見 §3❸**。
> **命令層級（D1，本則核心）**：三態 driver **由大迴圈（Claude／Opus 主 session）指揮並選定**——即使小迴圈跑
> `agy` 指令，也是**大迴圈下令令其跑**（`run.sh <driver>` switch）；小迴圈＝被指揮的執行體，不自選 driver。
> **隔離互動**：大迴圈 Opus × agy(Gemini) 小迴圈＝跨家族天然隔離（判官白吃）；× `claude -p` 小迴圈＝同家族 →
> 畢業判須 fresh zero-context subagent（禁 fork，D6.1）。故「Claude 大迴圈指揮 agy 小迴圈」是隔離最乾淨組合。
> 資料流視覺化見 antigravity-harness-wiki `loop-architecture-ssot.md §⓪`。
> **driver fallback 鏈（agy 不可用，2026-07-10）**：首選可為 agy（跨家族隔離紅利），但 **agy 額度耗盡＝零輸出
> exit 0**（silent no-op，與缺 policy 同貌）——**可用性判據＝輸出檔非空且合法、非 exit code**。偵測到 agy no-op
> → **小迴圈 fallback `claude -p`（讀 CLAUDE.md）**。**fallback 改變隔離需求**：agy(Gemini)→claude -p 把跨家族
> 轉**同家族**，大迴圈 fallback 時**必同步切畢業判官為 fresh zero-context subagent（禁 fork，D6.1）**，否則驗證者
> 隔離失守。**大迴圈雙兼容鐵律**：小迴圈可退到 claude，但大迴圈**恆保 agy＋claude 兩套指揮路徑**（`AGENTS.md`／
> agy dispatch 不得因近期偏用 claude 而砍除），否則永久喪失跨家族免費隔離與雙可跑性。

## §5 Verify 三層分層（D8）
①T0 機械（`scripts/<fn>` exit code，零 LLM；`verify.sh`/`selftest.sh` naming-convention glob 探勘直呼、
`tests/<fn>/fixtures/{good,hollow}` 成對驗證——wrapper `tests/<fn>/verify.sh` 已砍，2026-07-10 registry
單一 SSOT，見 `design_governance/CLAUDE.md`）②行為（`evals.json`＝一次性 pre-registered 設計非每輪 LLM
判官；覆蓋率＝planted-defect 檢出率）③邊界（統一腳本枚舉 modules×contracts，借 repo-agent-native 抽取法）。
**selftest 末尾計數勾稽** `scripts/` 檔數須等於 `evals.json` runnable 條數，不等＝registry 漂移 exit 2
（02-registry-consolidation.md §B3）＋**引擎捕 driver `--output-format json`**→`_engine-run/driver.iterN.json`
（turns/cache/denials 自動落帳，NEG-4 解，非手工另跑）——見 01-engine-hardening.md §B1。
**硬條款**（07 N13）：verify 必接真實執行（真 exit code）、禁 LLM 模擬環境。
stop-loss 兩型 no-progress/exhausted → SURFACE 交人。State 件：`trajectories/`（經驗 digest）＋`anti/`（失敗軌跡）
＋`pg/`（問題圖譜 State，失敗模式表＝PG derived 投影，單向 `經驗源→PG→表`）。

### §5.1 oracle-gate／dense-sparse-blind（2026-07-19 命名，概念本已在）
task→質量神諭三態前置閘：**dense**（有 T0 硬驗證器）＝完成⇔軌跡 iterate-until-T0-green（即
`SKILL.md:8` 完成率原式的軌跡化）；**sparse**（pre-registered 判官 checkpoint，
[`evals-design-method.md:3`](evals-design-method.md) 紀律）＝機械層綠∧checkpoint 過；**blind**（無神諭）＝
真跑過∧人 admit 不可約（§9❶ LAND/畢業/merge 三閘，行 214，exit 10）。完成的證＝`_engine-run/driver.iterN.json`
軌跡（上方既有落帳機制，行 165-166），非文字寫完；fold-in 條件性（有 durable 課才 fold）非 gate，
不強制（anti-inflation）。與 judge-loop-chooser 正交：oracle-gate 判驗證標準、四層 tier 判獨立性權重。
checkpoint 記錄格式範本 → `dr-to-mvp/SKILL.md:46`（dual-score 設計分∧實作分，採用不重造）。

## §6 skill→小迴圈轉換 recipe（單體 → 沙盒化）
單體巨型 skill → `loop_wiki/[loop]/` 沙盒 8 列映射：原 SKILL.md 規則→被動上下文（AGENTS.md／CLAUDE.md）＋
PROMPT.md／原 modules/→sandbox modules/／原 scripts/→sandbox scripts/（checker）／原 tests/→
`tests/<fn>/fixtures/{good,hollow}`（scripts/<fn> 為 checker 本體，wrapper `tests/<fn>/verify.sh` 已砍，
verify.sh/selftest.sh 直呼 scripts/<fn>）／原踩坑→PLAN.md／執行設定→`.agents/settings.json`＋
`.claude/settings.json`／調度入口→run.sh。P2 `truth-verify-harness-phase2` 是真實「手工編排→沙盒化」
先例（拓撲同構）。

## §7 cache 不變量（D7，Claude 側）＋技能解耦（D6）
**cache**：①迭代禁 commit（git 快照入 cache scope）②driver 從沙盒 CWD 起（subdir CLAUDE.md 否則進 conversation
層非穩定快取層）③prefix 字元級穩定④sizing 落 min-可快取~≤300 行⑤session reuse。oracle＝`cache_read_input_tokens`
＞0（design_governance pilot 跨 process 命中 CONFIRMED）。誠實錨：cache ~15% 次要優化非降本主軸。**技能解耦
（D6）**：大迴圈調 root orchestration skills × 小迴圈自帶 sandbox domain skills，去 coupling。

## §8 evals 一次性設計法（新維度方法論）
見 [evals-design-method.md](evals-design-method.md)：runnable/rubric 切分、good/hollow positive-control、
planted-defect 檢出率、機械層關不完 Goodhart 需 semantic backstop、分不出降級 rubric 不放水、target-type 路由。
design_governance pilot 三維度（PROMPT/ARCH/STYLE，16 checker＋6 subtle）為活實例。

## §9 大迴圈引擎（D12）＋雙 host 模型（D1′）
> §4 定「per-loop driver 三態＋命令層級（D1）＋fallback 鏈」＝**小迴圈側**怎麼被指揮、退化到哪；本 §9 補
> **大迴圈側**：驅動小迴圈的引擎是什麼、host 由哪個 CLI 定、免費隔離格如何隨 host 翻面。與 §4／§3❶ 及
> antigravity-harness-wiki `loop-architecture-ssot.md §⓪` 命令拓撲互指針、不重抄。

### ❶ 大迴圈引擎＝組合多個編排 skill 驅動小迴圈組合（D12）
大迴圈「自動驅動小迴圈」的引擎**不是單一 orchestrator**，而是**組合多個大迴圈編排 skill**驅動一組小迴圈——組合**異質**：
- **路由型**（本體「只 SURFACE 不執行」）：`unknown-discovery-composer`（四象限×三時段路由）、`judge-loop-chooser`
  （驗證標準＋獨立性 tier 路由）——引擎**讀其路由決定**、不代它執行被路由的 skill。
- **可執行型**：`ds-workflow-loop`（外部引擎 `dsw/*`）、`html-for-decisions`（決策面＋checker scripts）——引擎 **invoke** 之。
- **編排型**：`sdlc-plan-composer`（計劃階段委派各 atomic skill）。

引擎在 skills 間傳中間產物（D6 技能解耦：大迴圈調 root orchestration skills、小迴圈自帶 sandbox domain skills）。

**「自動」的邊界（鐵律）**——引擎自動化只涵蓋**機械層**：dispatch 小迴圈＋跑 `verify.sh` T0 硬驗證器＋
iterate-until-pass＋stop-loss（§5）＋在 skills 間傳中間產物（D6）。**但 LAND-DECISION／畢業判／merge 三類閘
永遠 SURFACE 交人**——源：`unknown-discovery-composer` 不變量 1「不執行被路由的 skill」＋不變量 3
「LAND-DECISION 永遠人」／`judge-loop-chooser`「admit 永遠人」／D3／flywheel 三不變量／全局 NEVER（同
loop-architecture-ssot ⑦「不用模型自主編排/自體驗證」）。**連 admit 都自動化＝D-conflict（違 D3）→ STOP 交人、
不擅自降級**（承 §5 stop-loss SURFACE 紀律：機械閘可自動、人裁閘不可）。

**並行條款（B11，07-nxm-proof-and-boundary.md §B2，2026-07-11）**：多 loop 可各自 `engine.sh` 進程並行
（沙盒隔離已足：各自 CWD／logs／`_engine-run`）；跨沙盒共享僅 agy 額度＋全局 hook，並行時計入預算。
**不另建並行編排機制**（S0-4 反膨脹：不改 engine.sh、不建 job queue、不建 lock）。

### ❷ 2×2 host 模型（每家族有 host 形＋headless 形）
大迴圈 host＝**開啟專案用哪個 CLI**——它決定大迴圈讀哪份被動上下文、以及小迴圈的免費隔離格（§9❸）。

> host 形／headless 形／被動上下文對映 → 見本節 ❼ N×M 表「大迴圈 host／小迴圈 driver／大迴圈讀／小迴圈讀」欄（唯一權威，不重列）。

- Antigravity CLI 開 → 大迴圈 **Gemini-native**（讀 `AGENTS.md`），驅動小迴圈**不必另 spawn agy**（本身已是 Gemini host）。
- Claude Code 開 → 大迴圈**即該 session**（讀 `CLAUDE.md`），某 loop（如 `dr-research-loop`）在 Claude Code 下仍可選
  **spawn `agy`** 跑該段 Gemini 執行＋驅動小迴圈。

Host 形與 headless 形同家族、讀同一份被動上下文檔名；差別只在「開專案 vs 被 spawn」。

### ❸ 隔離翻面（免費跨家族隔離格隨大迴圈 host 翻）
承 §3❶／§4「隔離互動」（判官隔離發生在**家族層**，D6.1）：免費跨家族隔離的小迴圈 driver **隨大迴圈 host 家族
翻面**。引擎 dispatch 小迴圈前**先看自己 host 家族**，才知哪種 driver 白吃隔離、哪種掛 fresh 判官。

> 免費隔離格／同家族格對映 → 見 ❼ N×M 表「隔離（家族層 D6.1）／畢業判官」欄＋對角讀法（唯一權威）。

「Claude 大迴圈指揮 agy 小迴圈」與「Gemini 大迴圈指揮 claude -p 小迴圈」互為鏡像＝隔離最乾淨組合。§4 driver
fallback 鏈是此表在「agy 不可用」時的退化路徑（跨家族→同家族化，須同步切畢業判官為 fresh subagent、禁 fork），不重抄。

### ❹ D1′（D1 修訂；人已顯式 admit，非 STOP）
§4 命令層級（D1）原文「編排＝Claude／Opus 主 session」**廣義化**為：
> **D1′：編排 host ∈ {Claude Code/Opus, Antigravity CLI/Gemini}，依開啟 CLI 定；預設／主＝Claude Code。**

這是人**顯式 admit 的 D 修訂**（非卡住 STOP）；記為 **D1′＝與 D1 相容延伸、非推翻 D1**——D1「小迴圈不自選
driver、由大迴圈指揮並選定」仍成立，只是「大迴圈」不再硬綁 Claude/Opus 單一 host，可為兩家族任一 host。

### ❺ root 雙被動上下文（大迴圈層的雙可跑）
承 §1❷／§2「被動上下文檔名」「混家族雙檔 domain 單一 SSOT」（`_template/` 小迴圈沙盒層的 `AGENTS.md`／
`CLAUDE.md` 並存），**上抬到 repo root（大迴圈層）**：repo root 需

| root 檔 | 讀者（host） | 角色 |
|---|---|---|
| **`AGENTS.md`** | Antigravity CLI／Gemini host | Sovereignty L1＝domain 事實**權威 SSOT** |
| **`CLAUDE.md`** | Claude Code／Opus host | **Fable Stage-3 tight 派生**（脈絡優先／零範例／少 Do-not；09 I8 單一 SSOT 換家族措辭，非另立事實） |

兩檔**並存**＝把 `_template/` 小迴圈層雙檔模式上抬到大迴圈層。root `CLAUDE.md` 已由主 session 建（其頭注宣告
「domain 單一 SSOT＝`AGENTS.md`、本檔＝派生」，host 模型細節指針回本 §9／D12）——本 §9 即它指向的權威展開。

### ❻ tier-dispatch 路由表（D12 引擎按角色分發子代理）
> tier 邊界 know-why 權威在 [`evals-design-method.md §tier 邊界`](evals-design-method.md)＋隔離在 §3❶，本表＝D12 引擎的分發路由投影、不重抄。

| 角色 | tier/model | 家族 | dispatch 機制 | 硬約束 |
|---|---|---|---|---|
| 裁決／LAND-DECISION／畢業判**決** | Opus（或人） | Claude | Agent tool（fresh zero-context）／人 | **永不 Haiku、永不 agy-as-verdict、永不 codex-as-verdict** |
| 計畫／設計／巧妙缺陷播錯／高推理一次性 | Opus／Fable 5 | Claude | Agent tool | 一次性高推理；Fable 5＝計畫階段慣用 tier（見 §9❽ 四家族管線） |
| 小迴圈 driver／author（執行） | claude -p（Sonnet／Opus tier）／agy Pro 3.1／**codex（GPT-5.5 tier，經官方 plugin）**／**grok（binary 直呼，model-pluggable harness）** | Claude／Gemini／**OpenAI**／**grok＝後端家族（proof-run＝Gemini，非固定 xAI）** | `claude -p`／`agy --model gemini-3.1-pro`／**codex 兩種呼法擇一**：對話 session 用 `Agent({subagent_type:"codex:codex-rescue"})` 或 `/codex:rescue`；**非互動 harness script（run.sh，無 Agent tool 可用）改直呼同一支官方腳本** `node <plugin-root>/scripts/codex-companion.mjs task --write "<prompt>"`（`<plugin-root>` 用絕對路徑，不靠 `${CLAUDE_PLUGIN_ROOT}`——只在 live plugin 呼叫情境下保證存在；2026-07-17 `loop_wiki/codex_demo/run.sh` 真接線＋proof run 用此法）——**禁手刻 `codex exec`**，兩種呼法都是走官方 companion runtime，見 sdlc-plan-composer/modules/multi-model-subagent-dispatch.md | family-bound；Flash 3.5 較髒不建議 author；**codex 只透過官方 plugin 派工，回傳原樣不加工（thin forwarder，非 orchestrator）**；**grok＝model-pluggable harness（非 family-locked）**：直呼 `grok -p "<task>" --cwd <沙盒> --output-format json --yolo < /dev/null`（原生讀沙盒 `AGENTS.md`，無 codex 式官方 companion，需 grok 本體 backend 憑證）；隔離家族＝`config.toml` 配置後端（proof-run `gemini-2.5-flash`＝Gemini），跑 xAI 自家模型才算真第四家族；proof-run＝**build+fire 已證、收斂未證**（§9❼ 格 7） |
| 跨家族複核**產 findings** | agy Pro 3.1 | Gemini | `agy --model …`（判成敗看輸出檔非 exit code，quota silent no-op 陷阱） | 只產 findings、**verdict 仍 Opus／人**；truth-verify-loop 的 agy 角色即此列的具體實例 |
| 機械執行（checker／verify／注入／格式勾稽）／**quota-fallback 執行** | 零 LLM 純腳本／Sonnet／Haiku | －／Claude | 純 shell／Agent tool | 匹配低推理、便宜；**agy／codex 額度耗盡時的 fallback executor 落此列（見硬約束⑥）** |

**硬約束 8 條**：
① agy **只跑 Gemini**（Pro／Flash），Opus／Sonnet／Haiku 走 Claude 家族 dispatch，codex 只跑 GPT，**grok＝model-pluggable harness（家族隨 `config.toml` 後端；proof-run 跑 Gemini 後端＝Gemini 家族，非固定 xAI）**－**三 family-locked 家族（Gemini／Claude／OpenAI）＋一 pluggable harness、四種 dispatch 機制**；
② 判官硬地板**永不 Haiku／永不 agy verdict／永不 codex verdict／永不 grok verdict**（driver 皆不裁決）；
③ **D6.1 隔離約束 author＋judge 的 model 組合**（同一 model 兩角色須 fresh-context，否則自欺）；
④ **Flash 3.5 authoring 不建議**；
⑤ **tier 匹配推理需求**——Opus 做機械＝浪費、Haiku 裁決＝抓不到 Goodhart（見 `evals-design-method.md §pilot` D12 slice-1：機械層＋Sonnet-author 未抓、Opus 隔離判官抓到，HOLD 為活證）；
⑥ **quota-fallback 明確降級，非靜默替身**（2026-07-17）：agy／codex 額度耗盡 → fallback 到 Sonnet／Haiku 執行同一任務，且必須在狀態帳本（PLAN.md／NN-slice.md 執行契約段）記一行 `fallback: <agy|codex> quota-exhausted → <sonnet|haiku> (degraded: same-family verify)`；**偵測方式不同**——agy 用「輸出檔是否真的生成」判活（exit code 不可信，quota 耗盡＝零輸出仍 exit 0，見 §記憶 agy-quota-silent-noop）、codex 用官方 plugin 自己回報的失敗訊號（`codex-result-handling` skill：malformed/failed run 會在 stderr 標明，或回報需要 `/codex:setup` 重新認證，非靜默空成功）；
⑦ **fallback 觸發同家族重判**：Codex(執行)×Opus(判官) 或 agy(執行)×Opus(判官) 原是跨家族天然隔離；一旦因④額度耗盡 fallback 到 Sonnet/Haiku 執行，執行者與判官同時變成 Claude 家族——**必須切回③的 fresh zero-context subagent（禁 fork）**，不可誤以為「反正都是 Claude 家族內部，維持原本白吃隔離假設」繼續跑；
⑧ **codex 讀 AGENTS.md 分兩層 tier，不可混用**（2026-07-17 新增）：codex 不像 agy/claude 有檔名綁定的
被動上下文自動載入機制，一律要**明確指示**去讀哪份 AGENTS.md，依情境分兩層——**大迴圈層**（root
`AGENTS.md`，Sovereignty L1 權威 SSOT）：高階 codex（gpt-5.5 以上）在**大迴圈**範疇被當委派執行者
時（如 `sdlc-plan-composer` S4），讀 root `AGENTS.md` 取得**目標導向**指引（少列限制，給任務全貌與
方向，讓高階模型自己規劃怎麼做）；**小迴圈層**（沙盒 local `AGENTS.md`）：codex 在**特定 `loop_wiki/
<name>/` 沙盒**當 driver 被 `run.sh`/`engine.sh` 分派時，讀的是**該沙盒自己的** local `AGENTS.md`
（跟 agy 讀同一份檔案），需要**條列限制＋domain 知識**（checker 判準、verify.sh 路由、不可 commit
等機械細節）——這層任務窄、範圍明確，不適合「目標導向、限制少」的高階框架，需要的是精確的 domain
規則。兩層不可混用：把 root AGENTS.md 的目標導向措辭套進小迴圈 local 會漏掉必要的機械限制；把小迴圈
local 的條列限制套進大迴圈委派會綁死高階模型的規劃空間。落地見 `loop_wiki/design_governance/run.sh`
與 `loop_wiki/codex_demo/run.sh` 的 codex 分支（皆讀沙盒 local AGENTS.md，經 prompt 明確指示「先讀
AGENTS.md」而非假設自動載入——codex 有 Read/Bash 工具，會真的去讀，見兩沙盒 proof run 實測）。

**effort-ladder last-mile 契約（2026-07-19 fold-in，marginal-dispatch slice03 血淚）**：D12 引擎的
effort-ladder（`engine.sh`，`ENGINE_LADDER` opt-in；no-progress 時同族升 rung）`export
ENGINE_ARM_MODEL/ENGINE_ARM_EFFORT`——但 **driver 基座 `run.sh` 必須主動消費這些 env**（傳進實際
driver 調用，如 codex `--model/--effort`），否則 engine 升 rung 只是內部 log、真 driver 每輪跑同一
model＝**last-mile 斷點**。**禁回退用 `run.sh` 不讀 arm env**（＝ladder 空轉、marginal 主張不成立）。
真實現＝`loop_wiki/codex_demo/run.sh` 消費 `ENGINE_ARM_MODEL/ENGINE_ARM_EFFORT`。**live 證**
（`loop_wiki/codex_stall/_engine-run/driver.iter1-4.out`，2026-07-19）：4-rung 全爬，真 codex 派工的
model/effort 逐 rung 真換 `gpt-5.4-mini/medium → gpt-5.4/medium → gpt-5.5/high → gpt-5.5/xhigh`。
**強制 ladder 升格測試技巧**：`verify.sh` 恆 FAIL 逼 no-progress，且 driver 每輪 append 一行含當前 arm
的相異探針（各 rung 不同）以避開 engine 的 diff-based suspected-noop guard（否則「最小編輯不改檔」會誤
觸 exit 22）。此接縫「stub 綠不算數、只 live 可證」的通則 → `sdlc-plan-composer/modules/multi-model-subagent-dispatch.md` 原則四（不重述）。

### ❼ 完整 N×M（host×driver）矩陣＋設計規範/實作差異（§9 收口）
> ❷ host 表與 ❸ 隔離翻面表各為「單軸」半表（❷ 只列 host、❸ 只列隔離）；本 ❼ 把兩軸**笛卡爾交乘成
> host×driver 4 格單表**，每格同時標「大迴圈讀X／小迴圈讀Y／隔離家族／畢業判官／canonical 範例／證成
> 狀態」，並把差異**正交拆兩軸**：設計規範差異隨 **host** 變、實作差異隨 **driver** 變。矩陣只交乘＋指針，
> 不重抄 ❷/❸/§2 逐項；範例一律指 §1 目錄圖與 `loop_demo/` 真檔。

**N×M 矩陣（8 格＝2 host × 4 driver；格 5/6＝2026-07-17 codex driver；格 7/8＝2026-07-17 grok（model-pluggable
harness，家族＝後端）；證成狀態誠實標——格 1/2/5 端到端已證、格 7＝build+fire 已證但收斂未證（backend 憑證阻塞）、
格 3/4/6/8 僅設計未證，見格內備註）**

| # | 大迴圈 host | 小迴圈 driver | 大迴圈讀 | 小迴圈讀 | 隔離（家族層 D6.1） | 畢業判官 | canonical 範例（指 §1／`loop_demo` 真檔） | 證成狀態 |
|---|---|---|---|---|---|---|---|---|
| 1 | Claude Code（Opus） | `claude -p` | root `CLAUDE.md` | 沙盒 `CLAUDE.md` | **same-family**（Claude×Claude） | **fresh zero-context subagent（禁 fork）** | §1❷ 融合版 claude 分支＝`loop_demo/claude_agy`（claude 分支） | **端到端已證**（`loop_wiki/design_governance` slice-1/2 真跑收斂） |
| 2 | Claude Code（Opus） | `agy` | root `CLAUDE.md` | 沙盒 `AGENTS.md` | **cross-family**（Opus×Gemini） | 判官白吃（Opus 直審，跨家族天然隔離） | §1❷ 融合版 agy 分支＝`loop_demo/claude_agy`（agy 分支）／§1❶＝`loop_demo/agy` | **端到端已證**（`loop_wiki/agy_demo` 本 session 真跑） |
| 3 | Antigravity CLI（Gemini） | `agy` | root `AGENTS.md` | 沙盒 `AGENTS.md` | **same-family**（Gemini×Gemini） | **fresh zero-context subagent** | §1❶ agy-native＝`loop_demo/agy`／§1❷ agy 分支＝`loop_demo/claude_agy` | **僅設計未證**（需在 Antigravity CLI host 內實跑才證） |
| 4 | Antigravity CLI（Gemini） | `claude -p` | root `AGENTS.md` | 沙盒 `CLAUDE.md` | **cross-family**（Gemini×Claude） | 判官白吃（跨家族） | §1❷ 融合版 claude 分支＝`loop_demo/claude_agy`（claude 分支） | **僅設計未證** |
| 5 | Claude Code（Opus） | `codex`（2026-07-17 新增） | root `CLAUDE.md` | 無（codex 不認 antigravity 被動上下文檔，規則內嵌 prompt） | **cross-family**（Opus×GPT） | 判官白吃（跨家族天然隔離，畢業判官本身未實跑，見下） | `loop_wiki/codex_demo/run.sh`＋`PLAN.md`（真 proof run） | **端到端已證**（2026-07-17 真 fire `codex-companion.mjs task --write`，hollow target M1+M2 一輪修好，`verify.sh` 獨立複驗 exit 0；畢業判官/多輪迭代/quota-fallback 三者未測，見該 PLAN.md「誠實缺口」） |
| 6 | Antigravity CLI（Gemini） | `codex`（2026-07-17 新增） | root `AGENTS.md` | 同上 | **cross-family**（Gemini×GPT） | 判官白吃（跨家族天然隔離） | 同上 | **僅設計，未在 Antigravity CLI host 驗證**（同格 3/4 的既有誠實缺口） |
| 7 | Claude Code（Opus） | `grok`（2026-07-17 新增，on Gemini backend） | root `CLAUDE.md` | 沙盒 `AGENTS.md`（**grok 原生讀被動上下文**，異於 codex 的 prompt-embedded） | **cross-family**（Opus × grok-on-Gemini＝Gemini 家族） | 判官白吃（跨家族；本 proof 未跑畢業判官） | `loop_wiki/grok_demo/`（AGENTS.md 放規則＋target.md＋verify.sh；grok binary commit 8adf901） | **build+fire 已證、收斂未證**：grok build（commit 8adf901）＋headless fire（讀 config／原生讀沙盒 AGENTS.md／連後端／發 agent 請求）全跑通；但 `verify.sh` exit 0 未達成——卡 grok→Gemini(OpenAI-compat) 憑證傳遞（明文 `"Please pass a valid API key"`，試 per-model env_key／XAI_API_KEY fallback／GROK_MODELS_BASE_URL 三機制皆 400），keyless 結構性阻塞。介於「僅設計」與「端到端已證」之間，**不得標已證** |
| 8 | Antigravity CLI（Gemini） | `grok`（on Gemini backend） | root `AGENTS.md` | 沙盒 `AGENTS.md` | **same-family**（Gemini × grok-on-Gemini）＝需 fresh subagent；**grok 改跑 xAI 後端則翻 cross-family** | fresh zero-context subagent（same-family 時） | 同格 7 沙盒 | **僅設計未證**（同格 3/6 未在 Antigravity CLI host 實跑；且 grok-on-Gemini 在 Gemini host 下為 same-family，隔離紅利消失） |

> **對角讀法**（＝❸ 隔離翻面表「driver 固定、host 翻」的另一視角，互指針不重抄）：同一 driver 隨 host 翻家族
> ——`claude -p` 在 Claude host＝同家族（格 1 掛 fresh subagent）、在 Gemini host＝跨家族（格 4 判官白吃）；
> `agy` 鏡像（格 2 白吃／格 3 掛 fresh）。**免費隔離格＝與大迴圈 host 異家族那一 driver**（Claude host→格 2
> agy／Gemini host→格 4 claude -p）。**證成誠實**：兩 Claude-host 格（1/2）端到端已證；兩 Antigravity-CLI-host
> 格（3/4）目前只有設計＋同構論證，未在 Gemini host 內實跑（antigravity 主 session＝Claude Code，尚無
> Antigravity CLI host run）——不得把「設計已敲定」冒充「已證」。
>
> **codex 是唯一恆自由格的 driver**（格 5/6，2026-07-17 新增）：`claude -p`／`agy` 各自跟其中一個 host **同家族**
> （需掛 fresh subagent），跟另一個 host **跨家族**（判官白吃）——是否白吃**取決於 host**。codex（OpenAI）跟
> Claude host 與 Gemini host **兩邊都跨家族**，兩格都判官白吃，**不隨 host 翻面**——這是加入第三家族後才浮現的
> 性質，本表新增前不存在。**格 5 已由「僅證 plugin 存在」升級為「端到端已證」**（2026-07-17，
> `loop_wiki/codex_demo/`：真 fire `codex-companion.mjs task --write`，hollow target 一輪修好、
> `verify.sh` 獨立複驗 exit 0）——**但只證了「driver 執行」這一段**，畢業判官（Opus fresh zero-context
> 審 codex 產物）、多輪 iterate-until-pass、quota-fallback 三者仍未實跑，見該沙盒 PLAN.md「誠實缺口」，
> **不得把「driver 執行已證」誇大成「整條 4-family pipeline 已證」**。格 6（Antigravity CLI host）仍
> 僅設計，同格 3/4 既有缺口。
>
> **grok（格 7/8，2026-07-17 新增）＝model-pluggable harness，打破「driver＝固定家族」前提**：codex 的「恆自由格」
> 成立**因為 codex family-locked 於 OpenAI**（跟 Claude／Gemini 兩 host 都跨家族）。grok 不 family-lock——隔離家族
> ＝`config.toml` 配置的後端模型。proof-run 跑 **Gemini 後端**（`gemini-2.5-flash`，無 xAI 訂閱）＝**Gemini 家族**，
> 故行為同 agy：跟 Claude host 跨家族（格 7 白吃）、跟 Antigravity CLI host 同家族（格 8 掛 fresh）——**隨 host 翻面，
> 非恆自由**。只有 grok 跑 **xAI 自家模型**才是真正的第四家族、才恆自由（跟三 host 全跨家族）——但那需 xAI 訂閱，未驗。
> **證成誠實**：格 7 只證到「harness build＋fire」（grok binary commit 8adf901 跑起來、原生讀沙盒 `AGENTS.md`、連
> 後端發請求），**driver 收斂（`verify.sh` exit 0）未證**——卡 grok→Gemini OpenAI-compat 憑證傳遞（明文 `"Please
> pass a valid API key"`，同 key 直 curl 通、grok 不通；試 per-model env_key／XAI_API_KEY fallback／
> GROK_MODELS_BASE_URL 三機制皆同 400），keyless 為結構性阻塞（無 xAI 訂閱、非 OpenAI Platform key、codex 的
> ChatGPT OAuth token 協議不匹配不可借）。**不得把「harness 已 fire」誇大成「grok driver 已證」**；活基座
> `loop_wiki/grok_demo/`＋已 build 的 grok binary＋`~/.grok/config.toml`（Gemini 後端模板）已就緒，接對 grok
> 憑證即可一鍵重跑收斂。

**設計規範差異（隨 host 變；host 決定大迴圈側）**——承 ❷ host 表／❸ 隔離表／❺ root 雙被動上下文，不重抄：
- **大迴圈讀哪份 root 被動上下文**：Claude Code host → root `CLAUDE.md`（Fable tight 派生）；Antigravity CLI
  host → root `AGENTS.md`（Sovereignty L1 權威 SSOT）。兩檔並存（❺），host 家族決定認哪份（domain 事實單一 SSOT）。
- **orchestrator 家族**：Claude Code→Opus 主 session；Antigravity CLI→Gemini-native（❷ host 形，本身即 Gemini host）。
- **哪格免費隔離**：host 家族決定哪種 driver 白吃跨家族隔離（❸ 翻面）——Claude host 免費格＝agy 小迴圈（格 2）、
  Gemini host 免費格＝claude -p 小迴圈（格 4）。**引擎 dispatch 前必先看自己 host 家族**，才知哪格白吃、哪格掛 fresh 判官。

**實作差異（隨 driver 變；driver 決定小迴圈側調用）**——承 §2 差異表／§3❸ permission-mode 命門，不重抄：
- **`claude -p`**：`--permission-mode acceptEdits`（B4 降權 2026-07-11；slice 05 hook 對 verify.sh allowlist 回核准 JSON 後 acceptEdits 得核准 Bash 類 verify.sh 機械 checker，§3❸）
  ＋讀**沙盒 `CLAUDE.md`**（driver 從沙盒 CWD 起，D5／D7②）；**slice-1.1 綁 target**（run.sh claude 分支需 `<target>`，把
  祈使任務綁整改對象，非餵 PROMPT.md 全文當宣告式合約）。真接線＝`loop_demo/claude_agy/run.sh` claude 分支。
- **`agy`**：`--mode accept-edits --add-dir <沙盒> --model gemini-3.1-pro`（**命門＝`--add-dir`**——agy 預設
  workspace 是自己 scratch、不吃 shell CWD，不 --add-dir 就寫 scratch 不論有無 --sandbox；`--sandbox` 次要，本 combo
  省——sandbox 是 terminal 限制、非失敗真因，當初真因缺 `--add-dir`）＋讀**沙盒 `AGENTS.md`**（agy 不認 CLAUDE.md，
  檔名綁家族）＋`< /dev/null` 防 stdin hang。可用性判活＝target 經 verify.sh 轉綠、**非 exit code**（quota 耗盡＝零輸出
  exit 0 silent no-op）。真接線＝`loop_demo/claude_agy/run.sh` agy 分支／`loop_demo/agy/run.sh`。
- **`codex`（2026-07-17 新增，已落地 `run.sh`＋`engine.sh`）**：對話 session 用
  `Agent({subagent_type:"codex:codex-rescue"})`（或 `/codex:rescue`）；**非互動 harness script（`run.sh`，
  無 Agent tool 可用）改直呼同一支官方腳本** `node <plugin-root>/scripts/codex-companion.mjs task --write
  "<prompt>"`（**禁手刻 `codex exec`**，兩種呼法都走官方 companion runtime，只是呼叫方不同——真接線＝
  `loop_wiki/codex_demo/run.sh`）；不讀沙盒 `AGENTS.md`/`CLAUDE.md` 被動上下文（codex 是外部模型家族，
  不認 antigravity 檔名慣例，任務說明須完整寫進轉發的 prompt 內，同 agy「檔名綁家族」的鏡像限制，但更
  嚴格——codex 連檔名都不認，純靠 prompt 文字）；可用性判活＝官方 plugin 自己回報的失敗訊號（非 exit
  code；見 §9❻硬約束⑥）。`engine.sh` 已加 `codex` 為第三個合法 `--driver`（family-map `codex→OpenAI`；
  隔離判定邏輯零特判——`HOST_FAMILY` 恆不等於 `OpenAI`，「恆自由格」性質不需額外程式碼）。**兩次真 fire
  proof run**（2026-07-17，`loop_wiki/codex_demo/PLAN.md`）：一次直呼 `run.sh codex`、一次經
  `engine.sh codex_demo --driver codex --host claude`（baseline→dispatch→verify→ADMIT 閘全程真跑，
  exit=10 awaiting-human-admit）；兩次皆一輪收斂，多輪 iterate-until-pass／畢業判官／quota-fallback／
  `--host antigravity` 格 6 仍未測，見該 PLAN.md「誠實缺口」。
- **engine.sh 出口**：新增 `exit 22`（driver-anomaly SURFACE，reason∈{suspected-noop, dispatch-failed}，10/20/21/64
  既有語意保留）——見 01-engine-hardening.md §B4。`verify.sh`/`selftest.sh` 已改 generic naming-convention glob
  探勘直呼 `scripts/<id>`（`tests/<id>/verify.sh` 純轉發 wrapper 已砍）——見 02-registry-consolidation.md §B2。

**目錄結構對映（指針 §1，不重畫）**——4 格各用哪支範例/哪分支：
- **§1❶ agy 版八大基座沙盒（單家族，只 `.agents/*`＋`AGENTS.md`）** materialize 於 `loop_demo/agy`：供**格 3**（Gemini
  host × agy 同家族）主用，亦作格 2 的 agy 側極簡參照。
- **§1❷ Claude Code 融合版（雙可跑，`.agents/*`＋`.claude/*`、`AGENTS.md`＋`CLAUDE.md` 並存）** materialize 於
  `loop_demo/claude_agy`：**格 1／格 4 走 claude 分支**（讀沙盒 `CLAUDE.md`）、**格 2／格 3 走 agy 分支**（讀沙盒
  `AGENTS.md`）——同一融合沙盒的 driver switch 即切分四格中三格，是「同沙盒 dual-runnable」的直接體現。
- **證成落點沙盒（proof run，≠ canonical 目錄範例）**：格 1＝`loop_wiki/design_governance`（claude -p 三維度真跑收斂）、
  格 2＝`loop_wiki/agy_demo`（agy 真跑）；骨架＝`loop_wiki/_template`。canonical 目錄「長怎樣」看 `loop_demo/`、「跑過沒」看 `loop_wiki/` proof run。

> **完成率教義句 canonical 錨**：全文權威＝SKILL.md frontmatter（發現/觸發層）＋evals-design-method.md 頭注（D8 側）；其餘檔引用一律指針，不再複述全文。

### ❽ 四家族管線（Discover→Plan→Execute→Verify，2026-07-17 新增；三家族擴充非推翻既有二家族拓撲）

**這不是新拓撲，是既有 Discover→Plan→Execute→Verify→Iterate（SKILL.md 迴圈判斷邏輯圖）疊加第三家族後的
具名組合模式**——把「driver 一次做完 Plan+Execute」拆成兩個獨立家族分擔，逼近極限的跨家族隔離：

| 拓撲階段 | 家族／tier | 對應 §9❻ 角色列 | 既有先例（非發明，本模式是延伸） |
|---|---|---|---|
| **Discover**（查真相/紮根） | agy（Gemini） | 「跨家族複核產 findings」 | `truth-verify-loop` 的 agy cross-worker 角色（AGENTS.md:39「Fable 編排+Opus/Sonnet/agy-Gemini」） |
| **Plan**（計畫/設計） | Fable 5（或 Opus） | 「計畫／設計／巧妙缺陷播錯／高推理一次性」 | `loop-harness-review-handoff` 已有「Fable 5＝設計/高推理架構評審」（modules/handoff-know-why.md:19） |
| **Execute**（執行/author） | codex（GPT）／claude -p／agy | 「小迴圈 driver／author（執行）」 | 本次新增 codex 選項（見 §9❻ 表）；claude -p/agy 已既有 |
| **Verify**（判官/裁決） | Opus（fresh context，永不 agy／codex） | 「裁決／LAND-DECISION／畢業判決」 | `truth-verify-loop` 判官紀律「fresh context、下限 opus、永不經 agy」；`loop-harness-review-handoff`「agy 永不當判官」 |

**為何 codex-執行×Opus-判官特別乾淨**：見 §9❼ 格 5/6 新增註——codex 對兩個 host 家族都跨家族，是**恆自由格**
（不像 claude -p／agy 各自對其中一個 host 同家族），judge 白吃隔離不看 host 家族。這是四家族管線裡「Execute
用 codex」相對「Execute 用 claude -p」的具體優勢：後者在 Claude Code host 下需要掛 fresh zero-context
subagent（③），前者不需要。

**殘留的同家族細節（誠實揭露，非漏洞掩蓋）**：Fable 5（Plan）與 Opus（Verify）同屬 Claude 家族。這**不違反**
③（D6.1 隔離約束 author＋judge），因為③管的是「執行者與判官」不可同一 model 兩角色自證，而 Fable 5 產出的是
**計畫**、Opus 判的是**執行結果是否達成計畫**——判的對象是 codex/claude-p/agy 的執行產物，不是自證 Fable 5
自己的計畫品質。若某天需求變成「Opus 也要判斷 Fable 5 這份計畫本身寫得好不好」（而非只判執行結果），那就
重新踩進同家族自證區——此時比照③降級為 fresh zero-context subagent，或换 agy/codex 產計畫審查的 findings
輔助（但 verdict 仍 Opus／人，不可反過來讓非 Claude 家族當計畫的最終裁決者，違背「永不 agy/codex-as-verdict」）。

**quota-fallback 對本管線的影響**（見 §9❻硬約束⑥⑦）：Execute 若因 codex 額度耗盡 fallback 到 Sonnet，
Execute（Sonnet）與 Verify（Opus）同時變成 Claude 家族——**此時「codex 恆自由格」的優勢消失**，必須臨時
掛回③的 fresh zero-context subagent，且在狀態帳本明記 `fallback: codex quota-exhausted → sonnet
(degraded: same-family verify)`。Discover 若因 agy 額度耗盡 fallback 到 Sonnet／Haiku 做同一查證任務，
**若該 Discover 隸屬 `truth-verify-loop` 的 TYPE_C 判定**，該迴圈自己的 AGG_RULE 早已明文「跨家族必開，
缺家族＝dispatch-fail」——這是比本管線更嚴的既有硬閘，**不可用本管線的通用 fallback 規則覆蓋它**；只有在
非 `truth-verify-loop` 正式管線的一般性 Discover 用途（如 `sdlc-plan-composer` S-1 或 `autoresearch-composer`
的查證）才適用本管線的寬鬆 fallback。

**現況（誠實揭露，別當作已跑通）**：Execute 這一段（codex driver）**已有端到端 proof run**（見 §9❼
格 5「端到端已證」＋`loop_wiki/codex_demo/PLAN.md`：真 fire、真收斂、經 `run.sh` 與 `engine.sh` 兩條路徑
皆驗證）；但**整條四階段管線串起來**（Fable5 出計畫 → codex 執行 → Opus 判官，三段接力跑一次）**仍未
端到端證過**——目前只證了 Execute 單獨這一段能真跑，Plan→Execute 的交接格式、Execute→Verify 的判官
dispatch，都還是設計層推論，不得混為一談。四個家族的組合本身不是新發明——每一段都已有既有先例（見上表
右欄），本模式只是**把散落各處的先例收攏成一個具名、可複用的四階段組合**，供新建小迴圈直接引用，不必
每次重新論證「這樣分家族安不安全」。

## Gotchas（防回退帳；additive，2026-07-11 harness review remediation）
- **禁回退用 wrapper 層 `tests/<fn>/verify.sh`**（純轉發已砍，generic runner 直呼 `scripts/<id>`；回退＝重造死層）——見 02-registry-consolidation.md §B2。
- **禁回退 driver `bypassPermissions`**（已降 `acceptEdits`＝Bash default-deny 更安全；除非 `acceptEdits` denied 復發，V3/B4-eval `permission_denials=0`）——見 05-hook-permission-fix.md §B4。
- **禁回退「引擎不回滾」**（restore-best 快照已兌現 Guard/discard，不碰 git）——見 01-engine-hardening.md §B2。
- **agy `--model` 須完整顯示名，非 slug**（2026-07-17 首次真 fire 才踩出）：`gemini-3.1-pro` 這種
  slug 形式被本機 agy 拒絕（"invalid --model...not recognized"），須用完整顯示名如
  `"Gemini 3.1 Pro (High)"`（含空格/括號）。`loop_demo/claude_agy`／`loop_demo/agy` 兩個「canonical
  範例」的 agy 分支從建置起就帶著這個錯字，因為兩者的建置範圍都明文「不 fire 真 driver」——canonical
  範例的「已接線」跟「已真跑驗證」是兩回事，不能拿前者當後者的證據，這正是本條要記住的教訓本身。
- **R9 dual-file-drift 對跨語言雙檔天生過不了、非 bug**（2026-07-17，`loop_wiki/design_governance`
  首次真跑 R9）：R9 是純語法層 normalize+set-diff（見其自身 docstring known_limitation），對
  「同一事實、不同語言/措辭」沒有語義判斷力。本次讓 agy 獨立（非逐字翻譯）寫一份英文 `AGENTS.md`
  取代原本詳細的中文 `CLAUDE.md`，R9 對 `CLAUDE.md` 跑 exit 2、39 行「漂移」——經 fresh Opus 判官
  獨立複核，其中 ~34 行是純措辭/語言差異的假陽性、2 行是**該當**因家族而異的合法差異（driver/verifier
  綁定）、真正的內容缺口只有 3 類（外部指標段落、ARCH-R4 降級史、pilot/verifier 歸屬）——修完那 3 類
  後 R9 **仍然 exit 2**（因為 CLAUDE.md 逐條 checker 描述把 `scripts/xxx.sh` 路徑內嵌進中文句子，
  normalize 後的「事實行」跟 AGENTS.md 對應的英文句子在字元層面永遠對不上，不管內容多忠實）。**結論**：
  R9 目前的機械判準對「合法跨語言呈現層改寫」場景會**恆常 FAIL**，這不是本次沒改好，是這個 checker
  的設計假設（同語言措辭微調）沒 cover 跨家族換語言的情境——同一類「機械判準不夠、該降 rubric」的
  先例已有 ARCH-R4→ARCH-S4（見同沙盒 AGENTS.md／CLAUDE.md 該節）；R9 是否也該比照降級為 semantic
  judge 專屬的 rubric（而非每輪硬 gate），是本沙盒下一步待人裁的 follow-up，本條先誠實記録現象、不
  現場改判準（改判準本身要走 D8 Gate 3「checker 分不出 good/hollow → 修 checker 或降級」的既有程序，
  非本輪範圍）。
- **多輪收斂路徑首次真證**（2026-07-17，`loop_wiki/codex_demo/target3.md`）：codex 單次 `task`
  dispatch 內建 iterate-until-pass 太強，自然任務很難逼出 engine 外層的多輪迴圈；新增
  `ONE_FIX_PER_DISPATCH=1` 環境變數（刻意限制單輪只修一條違規，預設關閉不影響常態行為）才真的跑出
  3 輪 keep/keep/CONVERGED 的軌跡。no-progress 與 regress-discard 兩條子路徑仍未被任何真跑觸發過
  （見 `loop_wiki/codex_demo/PLAN.md`「仍未證」）。

### ❾ driver 反饋物理投遞 parity（iteration_auto_context 必到每個 driver；SKILL 鐵律 9 的 know-why）

**現象（cc-20260724 實測）**：迴圈的自動提示反饋（engine `--feedback` 寫出的 `_engine-run/exchange-context.<id>.md`＝iteration_auto_context）在 `run.sh` dispatch 時，claude／agy 分支把 `$CONTEXT` **inline 注入** prompt（見 `run.sh` line 25-30 的 `if [ -n "$CONTEXT" ]` 塊），但 **codex 分支自建靜態 `CODEX_PROMPT`（只列「去讀 AGENTS.md…」）完全不引用 `$CONTEXT`** → 跨家族 driver 收不到迴圈回授＝**神經連結斷**。engine.sh line 112 把 feedback 當 `$3` 傳給 run.sh，claude/agy 用到、codex 丟掉。

**為何是 per-driver 而非一次搞定**：claude/agy 走 `claude -p "$PROMPT_TEXT"`／`agy -p "$PROMPT_TEXT"`（PROMPT_TEXT 已含 CONTEXT）；codex 走 `node codex-companion.mjs task --write "$CODEX_PROMPT"`，是**另一組 prompt 建構**，不共用 PROMPT_TEXT。所以每加一個 driver 家族都要**各自**把反饋注入其 prompt 建構路徑。

**修法（鐵律 9）**：codex 分支在 `exec node` 前補與 claude/agy 同構的 `if [ -n "$CONTEXT" ] && [ -s "$CONTEXT" ]; then CODEX_PROMPT="$CODEX_PROMPT\n\nExchange context to satisfy:\n$(cat "$CONTEXT")"; fi`。

**測法＝黑箱 parity（零真 LLM）**：PATH 前置 stub 假 `claude`/`agy`/`node`，捕捉 run.sh `exec` 出去的**真實 argv**（＝該 driver 實收 prompt），斷言含反饋 marker；三 driver 皆須 ✅＋負向控制（無反饋不憑空注入）。錨 `loop_wiki/evolve-unknown-discovery-plan-truth/scripts/test_driver_feedback_parity.sh`（進 selftest）。此測法是「driver dispatch 不可被誤簡化掉反饋線」的守衛——改 run.sh dispatch 時它先紅。

---

*本檔自足：agy 側寫法源起 ix-agy MVP、canonical 範例材化於 `loop_demo/agy`（不依賴外部 ix-agy 檔）；Claude Code 側為 antigravity 擴展並驗證（D5 tracer＋
design_governance pilot）。與 antigravity-harness-wiki 記錄層互指針不重疊。*
