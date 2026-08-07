---
name: loop-harness-standard
description: |
  大小迴圈成對八大基座設計標準——建 macro control plane 或新 op 沙盒(`loop_wiki/evolve-<family>-<op>/`)、選 driver(claude -p / agy / codex)、
  分層 verify(T0 機械/G 閘/holdout)、skill→小迴圈轉換 recipe 前先讀。把概率性 LLM 執行逼到高完成率
  ＝ T0 硬驗證器 × iterate-until-pass × stop-loss(機械閘),被動上下文只降迭代次數非正確性保證。
  觸發詞:建小迴圈、loop_wiki 沙盒、八大基座、Harness、driver 選型、evals 一次性設計、
  planted-defect 檢出率、loop-harness-standard。
  NOT for:記錄現有迴圈的資料流/組件卡(去 harness-wiki);判「該不該造新 skill」(用內建 write-a-skill)。
---

# Skill: loop-harness-standard — 大小迴圈成對八大基座設計標準

> **Role**:大小迴圈的基座標準——
> 建 macro control plane 或一條 `loop_wiki/evolve-<family>-<op>/` 沙盒、選 driver、
> 分層 verify、把單體 skill 轉沙盒化。
> 改基座、加 hook、升驗證器前先對照本圖組件與不變量。
> 與 `harness-wiki（../harness-wiki/SKILL.md）`
> (記錄**有哪些**迴圈的組件卡)職能不同、互指針不重疊。
>
> **結構**:SKILL.md ＝基座組件卡＋迴圈判斷邏輯＋防退化鐵律＋Gotchas;
> 技術規格 know-why 在 [modules/harness-spec.md](modules/harness-spec.md);
> 大小迴圈成對介面與 P0-P10 自動測試經驗在
> [modules/dual-loop-eight-base.md](modules/dual-loop-eight-base.md)，機器契約在
> [data/dual-loop-eight-base.json](data/dual-loop-eight-base.json);
> evals 一次性設計法在
> [modules/evals-design-method.md](modules/evals-design-method.md);
> production-ready seed loop 方法在
> [modules/production-seed-loop.md](modules/production-seed-loop.md);
> 移植帳本在 [modules/retarget-map.md](modules/retarget-map.md);
> **元層失敗前科在 [modules/anti-patterns.md](modules/anti-patterns.md)——動 harness 前先讀**
> (與沙盒 `CLAUDE.md` 紀律 8「開工前先 `ls anti/`」同位;元層無沙盒故落 modules/)。
>
> **活基座(改判定以這些真檔為準)**:`loop_wiki/_template/`
> (標準沙盒骨架)· `loop_wiki/engine.sh`(迭代/stop-loss 引擎)
> · `loop_demo/{agy,claude_agy}`
> (本地 canonical 目錄範例,見下方 Lineage)。
>
> **Lineage**:移植自 antigravity
> `.agents/skills/loop-harness-standard/`——
> **只搬可轉移的方法論,antigravity 自己的歷史證成紀錄
> (D 編號決策帳本、commit 錨、R7/R8/M15-M20 播錯案例)不搬**,
> 那是 antigravity 自己迴圈跑出來的軌跡;
> skill-bettor 未來累積自己的軌跡在 `families/*/changelog/`。
> 逐條映射見 [modules/retarget-map.md](modules/retarget-map.md)。

## When to Use
- 在 skill-bettor 建**一條新演化 op 沙盒**
  (`loop_wiki/evolve-<family>-<op>/`)——照八大基座＋driver 選型接上。
- 把**單體邏輯轉成沙盒化小迴圈**——照 §6 skill→小迴圈 recipe。
- 把已跑通的小迴圈升成**production seed**——先照
  [modules/production-seed-loop.md](modules/production-seed-loop.md)
  補 schema、trigger、route-result、baseline governance、schema replay、
  template promotion、behavior eval、seed scaffold、trend observation、security fallback。
- 改任何基座組件(被動上下文／settings／hooks／驗證器)之前。

## Not For
- ❌ 記錄**現有**迴圈的組件卡/資料流歸屬
  → `harness-wiki（../harness-wiki/SKILL.md）`。
- ❌ 判「該不該造新 skill／怎麼寫」
  → Claude Code 內建 `write-a-skill`
  (本 repo 同時提供 Claude/Codex entry；建立哪一種 skill 仍須採該 carrier 的原生規範，
  不可因共用八基座就混用 frontmatter/封裝)。

## 大小迴圈成對八大基座

Macro host carrier 可為 Claude Code 或 Codex；small-loop driver 可獨立選 `claude -p`、`agy`、`codex`。
carrier 決定 entry/runtime 介面，不決定 Human admit 或真相。兩層的共同 `B1..B8` 介面、owner 與測試契約由
[`data/dual-loop-eight-base.json`](data/dual-loop-eight-base.json) 持有，
`python3 scripts/check_dual_loop_eight_base.py` 物理驗證兩層各恰好八項。

| Base | Macro control plane | Small execution loop |
|---|---|---|
| B1 rules/context | root `AGENTS.md`/`CLAUDE.md`/`ARCHITECTURE.md` | sandbox `CLAUDE.md` + `AGENTS.md` pointer |
| B2 settings/authorization | repo hook 與 gate layer policy | `run.sh` 單發 dispatch、explicit permission、stdin EOF |
| B3 lifecycle/observation | commit/message/push transition | local `logs/`、`anti/`、engine trajectory |
| B4 route discovery | Skill/actor/validator capability catalog | `ROUTES.md`，只列 capability，不存 concrete DAG |
| B5 specialization | composer/judge 的 bounded node selection | typed exchange packet 與 domain-local adapter |
| B6 independent verification | `check_all_skills.py` + plan-package gates | `verify.sh` + good/hollow `selftest.sh` |
| B7 goal contract | versioned intent/requirements/acceptance/budget | `PROMPT.md` target/success/stop-loss |
| B8 state ledger | execution topology/evolution/receipt state | `PLAN.md` iteration/Human edge |

完整責任、正負控制、P0-P10 模組化測試經驗與資料流見
[modules/dual-loop-eight-base.md](modules/dual-loop-eight-base.md)。`run.sh`、分層 verify 與 production-seed
readiness 是基座的實作/延伸，不是第九個治理中心。

## 迴圈判斷邏輯與拓撲(Discover→Plan→Execute→Verify→Iterate)
```mermaid
graph TD
    A[Discover: 讀 PROMPT.md 目標 + CLAUDE.md/PLAN.md] --> B[Plan: 讀演化紀律 + PLAN 避錯]
    B --> C[Execute: driver 整改家族產物 + 更新 PLAN]
    C --> D[Verify: verify.sh 聚合 T0 機械閘 Exit Code]
    D -- SUCCESS Exit 0 --> E[Stop: STATUS candidate, 待人 admit]
    D -- FAILED Exit 2 --> F{已達 stop-loss? no-progress/exhausted}
    F -- YES --> G[Stop: STATUS failed, SURFACE 交人]
    F -- NO --> H[Iterate: 記失敗軌跡至 PLAN, 進下一輪]
    H --> A
    E --> I[畢業段(大迴圈執行,非本沙盒): holdout 只跑一次+Opus fresh 判官+人 merge admit]
```

### 第二編排模式:多-actuator 全語料對齊型(2026-07-21 fold;非取代單沙盒 engine.sh)
單沙盒 engine.sh 迴圈處理「一 target 整改到 verify.sh 綠」。但**全語料實作↔藍圖對齊型**任務
(多對話分片段、每段各判完整度/精度、無單一 target)走**多-actuator 併發編排**——由 **Workflow**
同時 fan-out N 個 Agent(每分片段一 Agent 對齊/驗證,pipeline 逐段獨立)+ **shell**(live server 承接人裁)
+ **Monitor**(串流接收 POST 決策事件)三 actuator 併發,物理性交付「自動提示」處理對齊。
**自動提示能力三面**:①逐段對齊 findings 自動派改善 Workflow(codex 執行+Opus 判官)②對抗式審查
(`/codex:adversarial-review`)findings 自動派修復 Agent ③自動提示啟動任務相關 skill
(judge-loop-chooser 敘述真相 / composer / truth-verify-loop)。
**邊界**:engine.sh 單沙盒=一 target 演化(它明文不跑判官);Workflow 多-actuator=跨段全語料對齊
+活決策面(判官/人閘進迴圈必走 Workflow,非擴 engine.sh——見 Gotchas「codex 在 Workflow 內」條的
載體事實)。**收斂閘仍是人 admit**(多-actuator 只換執行形態,不換「收斂=人裁非自宣」不變量)。
worked instance=harness-wiki 組件卡「dx-adversarial-fix 活對齊決策 cockpit」(拓撲不抄,指針)。
錨:本 session D1–D6 經此閉環接進 check_all_skills(068af77);Workflow fan-out+Monitor 接收+shell
server 三 actuator 併發實跑。

## 防退化鐵律(⚠️＝核心不可簡化)
1. **非互動執行重導向**(⚠️):
   driver 一律 `< /dev/null`——
   `claude -p`／`agy -p` 背景執行無此重導向會偵測 stdin 阻塞、
   無限卡死零輸出。
2. **驗證器／執行者拓撲隔離**(⚠️):
   嚴禁執行寫入的模型自證。
   核心＝「執行者≠判官權重」,隔離在**家族層**——
   跨家族(agy 作者×Opus 判官)自動滿足;
   同家族(Claude author×Claude judge)
   必落地 fresh zero-context subagent(**禁 fork**)。
3. **絕對路徑**:
   driver 跑 `verify.sh`／hooks command 一律絕對路徑;
   相對路徑依 CWD 漂移。
4. **授權自動化**:
   driver `--permission-mode acceptEdits`＋
   全局 hook 對 `verify.sh` 唯讀驗證腳本 allowlist 回核准
   (缺→driver 跑不了 verify.sh、退而讀源碼自證＝完整性風險)。
5. **大／小迴圈沙盒分工**:
   大＝主 session 編排＋每日管線;
   小＝`loop_wiki/` 高頻修改自癒。
   禁在大迴圈根跑演化 op 高頻修正。
6. **小迴圈自包含**:沙盒本地 logs/,不共用大迴圈全域狀態。
7. **編譯與實機驗證**(⚠️):
   Verify 閘除靜態斷言外,必接**真實執行(真 exit code)、禁 LLM 模擬環境**——
   按 target 類型接 evals/runner.py 真跑;
   防靜態過關掩蓋真缺陷。
   **且該 exit code 必須是被驗物的函數,不得是機器狀態或檔案系統位置的函數**
   (環境自足;判準/誤判面/偵測邊界與物理閘見 [harness-spec.md §4.6](modules/harness-spec.md))——
   `[ -x "$HERE/venv/bin/python" ] || fail` 這種 exit 2 完全滿足「真跑、真 exit code、零 LLM」,
   它只是誠實地回答了另一個問題:這台機器有沒有 venv。真實執行是必要非充分。
8. **迭代期間禁 commit**:
   git 快照入 cache scope,commit→prefix 全 miss;
   收斂後才一次性提交。
9. **先驗量尺再信分數**(⚠️;2026-07-19 fold):
   eval 分數出來前先驗「量尺本身對不對」——**低分可能是壞量尺不是弱能力**。
   判準:①headless agent 有沒有跑該任務所需的**工具權限**(`--allowedTools`)?
   ②機讀格式契約 agent **看得到**嗎(不能只活在 mock docstring)?
   錨:aie-context 量尺 v1 首跑 0.4271 =壞量尺
   (headless 無工具權限→代理答對拿不到分;格式契約只在 mock docstring 真代理不可見);
   v2 補工具權限+考卷勘誤(task.md 補回報格式節,鍵名機械抽自 expect pattern 給鍵不給值)→ 0.7083;
   v1 snapshot 標 `-misscale-superseded` 不刪留軌跡,跨量尺不可比不入曲線。
10. **兩層驗證別混**(2026-07-19 fold;鐵律 7「真實執行真 exit code」的邊界):
    selftest good/hollow 正控證的是「機械骨架活著」,
    **不是**「端到端含 LLM 真閉合過」。
    selftest 綠=骨架活(便宜、確定性);
    端到端真跑 exit 0=含 LLM 整條閉合(才是真跑錨)。
    **別把 selftest 綠當端到端通過**——反例:
    transform-loop verify 骨架可寫,端到端真跑掛第一步
    (2026-07-19,詳 sdlc-plan-composer S5 自動閉合驗收)。
11. **trap-ness 靶=no_skill 對照組非 mock**(2026-07-19 fold;spawn-cases 出題基座):
    陷阱要騙的是**no_skill 裸模型對照組**(mock_agent 調真邏輯騙不了它)。
    有效 trap 敗因=「常識/工程直覺與家規反向」
    或「權威流程壓力與不變量衝突」,
    非「缺件誘導大膽」(謹慎先驗自然答對=陷阱被證偽)。
    錨:`loop_wiki/spawn-aie-holdout-cases/anti/`
    (第四條件陷阱對 Sonnet 級三輪證偽);
    fixture 本文禁自述機制/正解(round-1 自爆洩漏教訓)。
12. **production seed 必須可物理計算與可重播**(2026-07-22 fold):
    「完美種子」不是更完整的敘事,而是 input→packet→context→route-result→baseline/trend 的
    物理接線與固定數字能被腳本重算。已解:通用方法升格進
    `modules/production-seed-loop.md`,worked instance=`loop_wiki/evolve-unknown-discovery-plan-truth/`
    以 `scripts/test_production_readiness.sh` + `scripts/compute_dataflow_stats.py --check`
    證明。禁回退:直接改 baseline JSON、把 raw prompt 複製進全景圖、或用單一 prompt 代替
    Match / Generate / Validate / Record / Observe 節點。

## Gotchas(踩坑警告)
- **無聲失敗(Ralph Wiggum)**:
  無硬驗證器時模型會用「已驗證」自欺空轉。
  → 覆蓋率＝planted-defect 檢出率,非行覆蓋;
  checker 分不出 good/hollow → 誠實降級 rubric,不放水。
- **production readiness 不能只靠 selftest 綠**(2026-07-22 fold):
  selftest 綠只證既有判分器活著;production seed 還要證 packet replay、route-result writer、
  baseline-update governance、schema replay、template promotion、behavior eval、seed scaffold、
  trend recorder、unsafe path/command fallback。worked instance 的 T0 錨:
  `loop_wiki/evolve-unknown-discovery-plan-truth/verify.sh` 361/361 +
  `selftest.sh` PASS + `check_all_skills.py` PASS(提交 2847f6a)。
- **有 RED test contract 不等於 implementation 或 outcome**(2026-07-30 fold):
  P10 預註冊 21 case，但 public `validate_measurement` seam 缺失，O3 有 10 個 `AttributeError`。
  已解：補 closed six-graph/ten-metric validator、consumer `--selftest` 與 meta gate，21/21 綠。
  禁回退：用 test 檔存在、fixture 綠或 plan acceptance 冒充真 external receipt/user outcome；P10 真證據未產生
  前必維持 pending。完整 know-why 見 `modules/dual-loop-eight-base.md`。
- **agy quota 耗盡＝零輸出 exit 0**(silent no-op,與缺 policy 同貌)——
  可用性判據＝輸出檔非空且合法、**非 exit code**。
  **已解(2026-07-12):engine.sh 判活 diff 機械化**——
  dispatch 前快照 target,回 0 且無變化→exit 22 SURFACE(正負控實測)。
  **禁回退:判活靠 driver exit code**
  (兩面都不可信:quota 耗盡 exit 0/timeout exit 1 但活已幹完,2026-07-11/12 三題實測)。
- **driver 額度斷供 → fallback 檔位,禁 silent**(2026-07-17 人裁):
  agy→Sonnet(研究)/Haiku(掃描)、codex→Sonnet(author)/Haiku(機械)——
  鏈與禁令=ARCHITECTURE.md §5 fallback 段(指針不重抄);
  fallback 事件記沙盒 `PLAN.md`
  (跨家族 findings 由同家族代打=獨立性降級,必 SURFACE;silent=獨立性洗白)。
  tracer 分層:第一層零額度名單探針(`agy models`/`codex --version`)先擋,
  第二層才 dispatch 判活(上一條判活 diff)。
  判官(Opus)無 fallback,斷供=判決排隊。
- **codex 在 Workflow 內背景化=與 verify race + 殺不死(2026-07-21 fold)**:
  workflow execute phase 用 `agentType:'codex:codex-rescue'` 會 spawn 背景 codex task 就回「started」不阻塞
  → verify 跑時常還沒落地=誤判 rework(有時 race 贏如 dist_safety FP 硬化、有時輸如 diff_executor 首輪)。
  **已解:workflow execute phase 用 Opus-tier default agent 同步內聯 Edit(明令禁 spawn 背景、改完自 grep 確認落地),
  或 verify 明令「等 mtime 穩再驗」;純前景 codex(Bash 直呼 `codex exec`)才可控。禁回退把 codex 背景任務當同步。**
  背景 codex 殺不死坑:`pkill codex-companion.mjs task` 只殺 poller 非本體(本體晚點仍落地——diff_executor 就是被
  「殺掉」的 codex 晚點寫好、結果還好但過程失控),且 poller 跨 workflow 共享(廣義 pkill 誤傷別的 workflow)——
  **禁廣義 pkill codex,要殺殺本體 PID**。並發寫檔時 Opus-tier agent 察覺檔案在腳下被改+自己 Edit 被拒→**正確不
  clobber superior 並發版、改驗證磁碟現態**,非硬遵「你必須 edit」。**Workflow 是唯一能在自動迴圈同時 Agent-分發
  Claude + Bash-呼叫 codex/agy 的載體**(engine.sh 只單 driver+claude -p);判官進迴圈=新編排層 Workflow 非擴 engine.sh。
  錨:[[multi-model-dispatch-verification]] 2026-07-21 段 + diff_executor commit 674490f 誠實揭露。
- **codex dispatch 無壓縮標的,主動壓縮控制＝closed-no-target(2026-07-25 fold)**:
  engine 每輪 dispatch＝**全新 thread 的單一 turn** → 82 dispatch 量測峰值 context median 23.7%/
  p90 42.1%/max 90.8%,91 次派工 **0 次壓縮**(壓縮只在 turn 之間評估,單 turn 不觸發)。
  **已解:壓縮控制標記 closed-no-target(無標的),不是「能力做不到」。**
  同批裁決的跨迭代 `--resume`＝**不做,但阻塞在上游能力**:companion 的 `--resume` 無法指定 thread、
  resume 池以 git root 為界 → 沙盒並行會靜默串線(上游給出 per-thread 出口才可重議)。
  **禁回退:①把 closed 讀成「已評估不值得」而從零重調研壓縮能力(能力清單已存,見下)
  ②在無 per-thread resume 出口下接跨迭代 resume。**
  三條已驗證能力(`thread/compact/start` 有 broker 無 CLI 出口/`model_auto_compact_token_limit` 生效/
  壓縮摘要 encrypted 不可稽核)＋復活條件＋file:line 錨 →
  [modules/harness-spec.md](modules/harness-spec.md) §3.1(指針不重抄)。
- **孤兒接線前對真資產 pre-flight + 反-vaporware 判官硬檢(2026-07-21 fold)**:
  把「存在但未接線」的閘接進常設 commit 閘前**必先對真 repo/真家族跑一次**——判官只驗 selftest+介面會漏「對真資產
  爆假陽性」的 blocker(dist_safety 判官宣 wire-ready,但對 agent-harness/aie-context 爆 565/398 假 FAIL,主 session
  pre-flight 才抓到→先 FP 硬化再接)。**「不在 check_all_skills」≠孤兒**:13 支普查 12 支證實 by-design(clc 子系統/
  per-change 需 diff 基準/主權手動燒 LLM),讀碼+追呼叫者+真跑才判,**禁名對名反推盲接**(盲接會打爛子系統/違反主權)。
  codex build 可能交 **vaporware**(常數定義後零引用死碼+docstring 謊稱 selftest 覆蓋+泛化詞誤擋合法內容,P8 首輪實犯)——
  **反-vaporware verify 四檢:①常數真被主函式引用②selftest 有真 fixture 正控③docstring 不謊④對真 repo FP 掃零誤擋**;
  Opus fresh 判官逐項親跑抓穿。錨:dist_safety bab2d2a / SKILL.md linter 接線 068af77 / [[defense-scripts-orphaned-wiring]]。
- **fresh subagent 判官會被 persona hook 注入**(2026-07-17 實測):
  ponytail SubagentStart fail-open 注入所有 Task 子代理 → T1 zero-context 起點破。
  已解:`PONYTAIL_SUBAGENT_MATCHER` 限縮(T0 三例正控綠)
  +判官型 dispatch 用不匹配的 agent_type。
  **禁回退用無限縮 fail-open 直接派判官**。
  詳=judge-loop-chooser `modules/grounding-and-independence.md` 操作判準 5。
- **祈使任務綁 target**:
  driver prompt＝「把 `<target>` 整改到 verify.sh 綠」+`PROMPT.md` 附為合約;
  餵 `PROMPT.md` 全文當宣告式合約＝driver 讀成規範而不動手
  (antigravity design_governance slice-1.1 記錄的反模式,已在本地 `run.sh` 規避)。
- **已收斂跳過(Skip-if-Converged)**:
  `STATUS: done`/candidates 已核發去重→前置退出,省重複 LLM 調用。
- **agy `--add-dir` 命門**:
  agy 預設 workspace 是自己 scratch、不吃 shell CWD,
  不 `--add-dir` 就寫 scratch。
- **pipe 進 tee 吃 exit code**(2026-07-11 實犯):
  POSIX sh 無 pipefail,`runner | tee` 會讓 G 閘永遠假 PASS。
  已解:先取 rc 再 cat(`loop_wiki/_template/verify.sh`)。
  **禁回退把 verify/runner 直串 tee。**
- **no-progress 訊號必須每輪重算**(2026-07-11 實犯):
  grep 累計 log 單調遞增→stop-loss 永不觸發。
  已解:verify 非綠時輸出 `PROGRESS: <n>` 行,engine 以此判。
  **禁回退用累計計數當進度。**
- **機械分數對語意差異全盲**(2026-07-11 實證):
  5 個無 skill tier 機械分完全齊平(0.5/0.667/0.667),
  語意正誤(捏造機制/evasion)只有 semantic 判官看得到→判官層是 backstop 非裝飾。
  證據:`families/pinescript-audit/evals/candidates/_validation/2026-07-11-semantic-control/MATRIX.md`。
  know-why → [modules/evals-design-method.md](modules/evals-design-method.md) §4。
- **跨家族複核必須唯讀**(2026-07-11 實測):
  agy 3.1 Pro 在 accept-edits 下會動手改 fixture 並宣稱「完全等價可上線」
  (改壞成重繪形態)。
  已解:複核 dispatch 只產 findings、不授予寫入。
  **禁回退給複核角色 accept-edits。**
- **背景批次有 10 分鐘牆**(2026-07-11 實犯):
  >10 分鐘的評測批次整批被砍。
  已解:拆 per-case 任務或按 tier-dispatch 派機械層 subagent 各管一 arm(ARCHITECTURE.md §5)。
  **禁回退單一長批次。**
- **bash `$var` 緊鄰多位元組字=變數名吞位元組**(2026-07-11 實犯 engine.sh):
  `$i。`被解析成未綁定變數 `i�`,
  GREEN 後 exit 1 取代 exit 10(假故障蓋掉真收斂)。
  已解:一律 `${i}` 帶大括號(engine.sh `${i} 必須帶大括號` 註解處)。
  **禁回退裸 `$var` 緊鄰全形字。**
- **機械 checker 字串比對必帶 token 邊界**(2026-07-11 實犯 `_template_dr/check_licenses`):
  「stripe-samples」轉大寫含子串「MPL」被誤判 copyleft——
  假閘會扭曲 driver 的證據選擇(它改用別的 repo 繞過)。
  已解:邊界 regex `(?<![A-Z0-9])M(?![A-Z0-9])`+good fixture 以「machine-samples」鎖回歸;
  帶尾綴標記(`OSL-`)與邊界匹配互斥。
  **禁回退裸子串 `in` 比對。**
- **driver 自記帳不可信**(2026-07-11 實證 agy):
  driver 在沙盒 PLAN.md 自記 PROGRESS 42/120/140,
  超出 verify.sh 口徑上限(54)——內部輪次敘事≠量測。
  誠實帳=engine `_engine-run/trajectory.log`(引擎獨立跑 verify 的記錄)。
  **禁把 driver 自記數字當量測回填。**
- **post-T0 semantic feedback 輪不走 engine**(2026-07-11 實證):
  engine 對已綠 target 走 conform_only 短路(iter-0 綠即 exit 10,不 dispatch)——
  `--feedback` 只在紅 target 迭代中生效。
  已解:修正輪=`run.sh <driver> <target> <findings 檔>` 單發+手動重跑 verify.sh
  (dr-claude-code-skill-market proof-run 實走此路)。
  **禁對已綠 target 用 engine 跑 feedback 輪。**

## Modules
- [modules/dual-loop-eight-base.md](modules/dual-loop-eight-base.md) — paired macro/small B1-B8、
  P0-P10 自動測試模組化經驗與 anti-regression anchor。
- [modules/harness-spec.md](modules/harness-spec.md) —
  目錄結構圖＋設計決策 know-why(驗證器隔離／300 行腐化／cache 不變量／driver 選型),
  只留可轉移方法論。
- [modules/evals-design-method.md](modules/evals-design-method.md) —
  evals 一次性 pre-registered 行為驗證設計法
  (維度×槓桿／runnable-rubric／planted-defect fixtures)。
- [modules/retarget-map.md](modules/retarget-map.md) —
  antigravity → skill-bettor 逐機制映射與誠實帳本。
