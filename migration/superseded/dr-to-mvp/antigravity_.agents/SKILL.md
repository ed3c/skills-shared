---
name: dr-to-mvp
description: |
  把「一個研究問題／Gemini 對話」一路編排到「一個畢業的 MVP repo 產品」時使用——串起三個既有 skill 的
  端到端脊椎：Phase R 研究到可信 SYNTHESIS（gcr S0-S9＋D1-D2）→ Phase G 可行度 gap 收斂＋驗證型 prototype
  實測（D3-D4）→ Phase M 種子 prototype 進八大基座迭代成 MVP（loop-harness-standard mvp-builder ①②③
  ＋小迴圈 iterate-until-pass×stop-loss＋dual-score 畢業）。**recipe-not-engine**：每 Phase 間 SURFACE 停點人
  admit,非 auto-chain;DR 是 gap-filler 非主幹、非 prototype 入口;prototype 有兩種（D4 驗證型 vs MVP 種子）別混。
  findings／產物給絕對路徑,畢業／homing 永遠人核。
  何時用：要把研究成果系統性長成一個耐久 MVP 產品、或要一份 DR→prototype→MVP 的完整引導提示詞時。
  觸發詞：研究到 MVP、prototype 做成產品、DR 到 MVP、SYNTHESIS 落地成 repo、八大基座做 MVP、
  MVP-builder 引導提示詞、大小迴圈做終端產品、dr-to-mvp。
  NOT for：只研究對話不做產品（gemini-conversation-research）、只建單條迴圈規範（loop-harness-standard）、
  只 fold 經驗進既有 skill（fold-in）、只選驗證 tier（judge-loop-chooser）。可貼 playbook → reference/guiding-prompt.md。
---

# Skill: dr-to-mvp — 研究問題 → SYNTHESIS → prototype → 八大基座 MVP 的編排脊椎

> **Role**：把一個研究問題一路引導到畢業 MVP 產品的**大迴圈編排脊椎**。它**不擁有任何 Phase 的內部**（那些在三個 owner skill）——只擁有 **R→G→M 的定序、phase 間的 SURFACE handoff gate、兩種 prototype 消歧、誠實接縫帳本**。**recipe-not-engine**：每 Phase 間停下等人 admit,不 auto-chain。**它不是 turnkey auto-engine,是人核 recipe。**
> **結構**：SKILL.md＝Phase 路由表＋SURFACE gate＋不變量;可貼的逐階段 playbook（prompt 骨架＋閘＋▣停點＋接縫帳本）在 [reference/guiding-prompt.md](reference/guiding-prompt.md)。
> **三個 owner skill（脊椎只指針,不複述其內部;漂移以它們為準）**：
>   - Phase R → [gemini-conversation-research](../gemini-conversation-research/SKILL.md)（S0-S9 ＋ [`modules/downstream-landing.md`](../gemini-conversation-research/modules/downstream-landing.md) D1-D2）
>   - Phase G → 同上 D3-D4 ＋ 全局 prototype skill（`~/.claude/skills/prototype`，user-level 不在本 repo）＋ `kb-ingest/setup-prototype.sh`
>   - Phase M → [loop-harness-standard](../loop-harness-standard/SKILL.md) [`modules/mvp-builder-and-adlc-equivalents.md`](../loop-harness-standard/modules/mvp-builder-and-adlc-equivalents.md) §2 ＋ `setup-prototype.sh --mvp`
> **LIVE 錨（反-husk）**：① `prototype/llm-timeline-editing/cutplan/`（R→G→M 全鏈真跑過一次：SYNTHESIS→G4/G5 種子→八大基座 SC1-17、118 tests、五真整合 RIP、授權合規、Fable-5 review 過）。② `/Users/neon/ix-agy/prototype/ios-agent-autopilot/autopilot-bridge/`（2026-07-11 第二次全鏈：增量 SYNTHESIS 複用既有同主題 `b6d196` 機械錨→autopilot glue 種子直進 src/→八大基座 SC1-7、51 tests、判官 32 抽查、dual-score 綠→畢業守門 skill `ios-agent-autopilot`（跨 repo 落 ix-agy）`run-all` 全綠）。

## When to Use
- 有一份研究成果（或一個要研究的問題）要**系統性長成一個耐久 MVP repo 產品**。
- 要一份 **DR→prototype→MVP 的完整引導提示詞**當大迴圈編排腳本。

## Not For
- ❌ 只研究一個 Gemini 對話、不做產品 → [gemini-conversation-research](../gemini-conversation-research/SKILL.md)（本 skill 的 Phase R 就是委派它）。
- ❌ 只建／改一條迴圈的工程規範本體 → [loop-harness-standard](../loop-harness-standard/SKILL.md)（Phase M 委派它,不定義基座）。
- ❌ 只把一段**已完成**經驗 fold 進既有 skill／AGENTS.md → [fold-in](../fold-in/SKILL.md)。
- ❌ 只選某 deliverable 的驗證 tier → [judge-loop-chooser](../judge-loop-chooser/SKILL.md)。
- ❌ 把 loop-harness 架構 review 交接給新 session → [loop-harness-review-handoff](../loop-harness-review-handoff/SKILL.md)。

## §0 拓撲校正（動手前先破兩個常見誤解）
1. **DR 不是 prototype 入口**：DR 在 gcr 的 **S3**,只有 S2 分診的 research-gap 才送它;DR 報告＝待驗敘事非鐵錨。prototype 真入口＝**D4**,種子＝**D2 已驗 SYNTHESIS ＋ 一個 D3 的 UK 缺口**。
2. **prototype 有兩種別混**：① **D4 驗證型**（只為答一個 UK 缺口而建,ANSWER absorb→SYNTHESIS;artifact 留存作驗證錨——不是拋棄式,是驗證過的技術實作等價物——**永不升格 src/**）② **MVP 種子**（已驗證,升格進 `src/` 用八大基座長成產品）。**「交給八大基座」＝拿②,不是拿 DR、不是拿①的半成品。**
> 完整圖＋對照表 → [reference/guiding-prompt.md](reference/guiding-prompt.md) §0。

## 確定性程序（三 Phase,每 Phase 間 ▣SURFACE 人 admit）
1. **Phase R — 研究到可信 SYNTHESIS**〔LIVE ✓〕：判 Mode A/B → gcr S0-S9（DR 走 `automate.js` 不重造）→ D1 落地驗證（**確定性錨＞LLM 說詞**,判官＝Opus,agy 不當判官）→ D2 SYNTHESIS（真實度計分卡＋等價物矩陣＋分層架構＋最脆弱三處）。▣ 若商用零 copyleft：等價物過授權／專利軸（[external-verify](../external-verify/SKILL.md)）。**閘**：每 load-bearing claim 有錨或明標 UNVERIFIED。**▣** SYNTHESIS 給人核。
   > **檢索三態 grounding + 派工紀律（指針，2026-07-19 fold；seam-not-merge，不重抄）**：Phase R 的 gcr/DR（external 事實）與 Phase G D3 的 repo-wiki-converge/repo-agent-native（repo-internal）＝檢索兩態；本 skill 已有「確定性錨＞LLM」+ external-verify 的**實質**，但**顯式三態分類 + agy-niche + 派工紀律**見 [`sdlc-plan-composer`](../sdlc-plan-composer/SKILL.md) (g) 外部-currency lane ＋ `modules/multi-model-subagent-dispatch.md` 原則五——**repo-internal→grepai/serena（不燒 agy）；external/post-cutoff→external-verify+agy(Gemini web/DR)；[推論] 不可當 SYNTHESIS 前提；判官不先消費 retrieval input 再判產物；handoff 傳 file:line 指針非散文**。（dr-to-mvp Phase R/G 是**採用方**，同 §5.1 完成契約鏈：指針引用、不 merge。）
2. **Phase G — gap 收斂＋驗證型 prototype 實測**〔LIVE ✓〕：D3 四象限（KU→[repo-wiki-converge](../repo-wiki-converge/SKILL.md)/[repo-agent-native](../repo-agent-native/SKILL.md),**真實作常反證 DR 論點**;UK→prototype）→ D4 `bash kb-ingest/setup-prototype.sh <plan> <repo>`（預設輕量,混壞 case 實測防護真起作用,答完 **ANSWER 先過 fresh 判官原始重算 spot-check 再 absorb**→SYNTHESIS→**artifact 留錨不升格**,見 §0.2）。**▣** 哪些 UK 已實測關閉、夠不夠開 MVP。
3. **Phase M — 種子→八大基座 MVP**〔LIVE ✓〕：① SYNTHESIS→`DESIGN-SCORE.md`（設計分 answer-key）→ ② `bash kb-ingest/setup-prototype.sh --mvp <plan> <mvp_repo>`（生八大基座＋獨立 git）→ ③ 種子進 `src/`＋`verify.sh`(實作分 T0)→ 小迴圈：每輪 write `dispatches/round-NN.md`→派 **fresh zero-context driver（禁 fork）**整改 src/→**判官(Opus)** 跑 verify.sh full+--fast＋git-diff 零弱化＋**實質 spot-check 核心 claim**→exit0 commit 獨立 git／stop-loss 3 → SURFACE。**閘**：dual-score AND（設計分∧實作分）。**▣（終點必停）** 畢業＝人 LAND-DECISION → homing 搬離 gitignored `/prototype/` → **homed 後接 per-repo 落地後續**（型譜＋慣例帳→[mvp-builder §4(h)](../loop-harness-standard/modules/mvp-builder-and-adlc-equivalents.md)，指針不重述;antigravity ②型＝完整 repo-wiki-converge 至 ingest，確定性後步、判官閘在該迴圈內）。
> 可貼 prompt 骨架逐階段 → [reference/guiding-prompt.md](reference/guiding-prompt.md) §1。

## 不變量（違反即停）
1. **recipe-not-engine,每 Phase 間人 admit**：不 auto-chain R→G→M;畢業／merge／homing 永遠人核（human-exit-gate）。
2. **DR 是 gap-filler 非主幹非 prototype 入口**;把 DR 報告當事實直接設計＝幻覺入庫（Path B：待驗敘事非鐵錨,錨＞LLM）。
3. **兩種 prototype 別混,分軸＝升格路徑非壽命**：D4 驗證型答完留錨、永不升格;只有已驗證種子才升格 MVP。
4. **判官＝Opus,永不外包給 driver／作者／agy**（agy＝Gemini only）;判官可跑**主 session 或 fresh Opus 子代理**（後者＝「編排者不自判」角色純化模式,2026-07-23 ai-dev-governance 使用者矩陣 19 審 LIVE;鐵芯不變＝執行者≠判官≠編排者）;fresh zero-context driver **禁 fork**（鐵律 3／D6.1）;**判官別只信 exit 0,實質 spot-check 該輪核心 claim,探測必自造 fixture**（driver 綠測可能剛好繞開失效模式、甚至驗證 bug 本身——LIVE ×2,見 mvp-builder 帳）。
5. **dual-score AND 才畢業**：降維／移除某 SC 仍須過設計分（證明是 designed-cut 非漏做）。
6. **脊椎 pointer-only,不複述 owner 內部,不臆造預留段**：三 Phase 內部 SSOT 在三個 owner skill,漂移以它們為準;**downstream-landing step6 預留的「DR→八大基座 auto-chain」不填實**（待首次真跑再 fold-back）。反-husk 錨＝上方所有指針指真檔＋cutplan LIVE 錨。

## Gotchas（誠實接縫,Path B——別在未證關節鋪平滑敘事）
- **N×M：Claude host × {subagent, claude, agy} driver 三格已 LIVE**（subagent＝cutplan;claude／agy＝2026-07-11 `prototype/_mvptest/demomvp` 真跑補證——副產 design-gate HUMAN-AUTHORIZED 模板假匹配 bug 揪出＋修）;**仍未證**＝Antigravity-CLI host。全鏈 R→G→M 已 5 次（cutplan／autopilot-bridge／skill-bettor harness-core＋evals-gate／skillgate;**完整帳＋各次 delta 見 [mvp-builder](../loop-harness-standard/modules/mvp-builder-and-adlc-equivalents.md) LIVE 錨帳，脊椎不逐次維護計數避免 stale**——快照計數 vs 持續 homing/新跑必脫鉤,fold-back 前先跑漂移審計,機械化＝`scripts/audit-anchors.sh`）。skill-bettor 跑（2026-07-12）首例：跨 repo 落點 `ANTIGRAVITY_PROTOTYPE_ROOT`＋DR 語料型 Phase R（121 主題分類→cluster 深整合,無新 DR）＋多 MVP 串行＋homing 進 `families/agent-harness/shared/runtime/`（第三 homing 型,子技能=使用/建構型）;皆 Claude host × subagent driver。
- **dual-score 設計分判官首次 LIVE-fire 跨完整畢業**（2026-07-11 autopilot-bridge）：fresh opus 設計分判官（不餵 big-loop rationale）掃 DESIGN-SCORE 判 PASS ＋ 實作分 `verify.sh` exit0 ＝ dual-score AND 綠;副產區辨「**needs-hardware 誠實接縫 ≠ scope descope**」（真機無硬體→e2e deferred 追 PLAN、非 SYNTHESIS §2 descope;兩者依據不同源,別混報）。第二燒 2026-07-12 harness-core（18 行 13 PASS/5 CUT-OK/0 MISS,判官 7 獨立探測）——同役實證**判官「別只信 exit 0」抓到 verify 全綠但語義反轉的真缺陷**（round-05 `handled` 全域讀法洗白後續失敗→時序規則整改→同腳本複驗閉環;錨＝該 repo `PLAN.md` Failure traces＋`DESIGN-JUDGE-VERDICT.md`）。
- **Phase R 先查既有同主題 SYNTHESIS 再決定跑不跑 DR**：對話與既有 gcr 產物同主題時,複用已驗機械錨、只做增量 D1（autopilot-bridge 複用 `b6d196`:maestro-runner/WDA/devicectl 存在性不重跑,只驗新軸具名實體）——防重跑已驗 DR＝Path B 錨＞重複敘事。know-why → reference §Phase R。
- **Phase G 某類種子可跳 D4 驗證型**：當 v1 種子本身即要進 `src/` 的②MVP 種子（非①驗證型）,Phase G 的 D4 對它不適用,唯一 UK 直接在 Phase M 小迴圈用 mock 純內部層驗（autopilot-bridge:glue 閉環用 mock maestro-runner 驗,不先建驗證型）。know-why → reference §Phase G。
- **DR→skill auto-chain＝預留未填**（downstream-landing step6）;**homing 手動、目的地依 repo 而定**——repo 無 remote／`/repo/` gitignored 時（如 ix-agy）MVP 併入對應 owner skill 的 `reference-impl/` 進主 repo（實例 `ios-agent-autopilot`,d4f4e35）,know-why→reference §Phase M homing。
- **Phase R 跑前必 `pgrep -fl automate.js`**：DR 不可與 dr-research-loop 影片管線同跑同一 `:9333` 帳號。
- **Phase G absorb 先於判官＝實錘失真源**（2026-07-20 skill-evals-governance 跑）：先 absorb 再補判官,D4 判官原始重算仍抓出 1 處實質數字失真（儀器碼 50-skill 外推值誤標 23-skill 全艙）＋1 處歸因缺口——閘序＝ANSWER→判官→absorb（不變量 4「別只信 exit 0」的 Phase G 面）;錨＝`docs/plans/2026-07-20-dr-to-mvp-skill-evals/G-D4-judge-verdict.md`。
- **一鏈多 MVP 的 designed-cut 分流必立雙向帳**（2026-07-23 ai-dev-governance 首例）：甲 MVP cut 掉的 golden-path 元素若分流到乙 MVP,甲記 cut@PLAN、**乙的 DESIGN-SCORE 必列該元素為 done 且設計分判官追承接兌現**（LIVE：evalgate cut-4/5→contractbench,判官 r1 真追）——分流無收方帳＝縮窄洗白,正是設計分閘要抓的形態。完整 run 帳→mvp-builder §4 LIVE 錨帳。
- **反-husk**：本脊椎的價值＝定序＋handoff gate＋兩種 prototype 消歧＋接縫帳本,**不是**重造三 Phase;若哪天開始複述 owner 內部＝漂移,以 owner 為準。

## Reference
- [reference/guiding-prompt.md](reference/guiding-prompt.md) — 泛化可貼引導提示詞 playbook：§0 拓撲校正＋兩種 prototype 對照表 · §1 Phase R/G/M 逐階段（SSOT 指針＋prompt 骨架＋閘＋▣SURFACE）· §2 誠實接縫帳本（LIVE ✓ vs 設計 only）· §3 一頁速查命令序列。
- [reference/anchors/](reference/anchors/) — LIVE 錨 git bundle 快照（cutplan／OpenTimelineIO 成功程序完整歷史;還原＝`git clone <bundle> <dir>`）。漂移審計＝[scripts/audit-anchors.sh](scripts/audit-anchors.sh)（錨路徑存在＋有 git 歷史＋bundle 未落後）。
