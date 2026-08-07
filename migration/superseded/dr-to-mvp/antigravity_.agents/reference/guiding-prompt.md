# 引導提示詞：研究問題 → SYNTHESIS → prototype → 八大基座 MVP 產品

> **這是 [`dr-to-mvp`](../SKILL.md) 的 Layer B reference**（可貼 playbook）。SKILL.md＝脊椎路由表＋不變量;本檔＝逐階段 prompt 骨架＋閘＋▣停點。漂移時以三個 owner skill 的真檔為準。
> **這是什麼**：把「一個研究問題 / Gemini 對話」一路引導到「一個畢業的 MVP repo 產品」的**大迴圈編排提示詞**。可貼可跑。
> **紀律**：pointer-rich，**不複述** SSOT（漂移時以被指的真檔為準）。每階段標 **LIVE ✓（真跑過）** vs **設計 only（未證，Path B 不宣稱成立）**。
> **SSOT 來源**：`gemini-conversation-research`（S0-S9 + D1-D4）、`loop-harness-standard/modules/mvp-builder-and-adlc-equivalents.md`（prototype→MVP §2）。
> **鐵律**：全程 recipe-not-engine——每個 ▣ SURFACE 點停下等人 admit，**不 auto-chain**。畢業/merge 永遠人核。

---

## 0. 先校正拓撲（問法本身的兩個誤解）

**誤解 1：「DR 是 prototype 的入口」——不是。**
DR 在 gcr 管線的 **S3**，而且只有 **S2 分診出的 research-gap** 才送它（`只把缺口送 DR`）。DR 報告是**待驗敘事、不是鐵錨**（Path B）。prototype 的真入口是 **D4**，種子＝**D2 已驗證的 SYNTHESIS ＋ 一個 D3 的 UK 可行度缺口**。完整鏈：

```
研究問題/對話
  └─ gcr S0-S9 ──────────────────────────── 只有 research-gap 進 S3 DR
       S0 抽取→S1 分析→S1.5 同對話追問→S2 分診→S3 DR→S4 存檔→S7 覆蓋→S8 multi-DR→S9 入庫
  └─ 下游落地 D1-D4（S9 後，SURFACE-gated 人 admit）
       D1 DR 落地驗證（確定性錨 > LLM 說詞）
       D2 SYNTHESIS（真實度計分卡＋等價物矩陣＋分層架構＋最脆弱三處）  ← prototype 的種子在這
       D3 可行度 gap 收斂（KK/KU/UK/UU）：KU→repo-wiki-converge/repo-agent-native；UK→D4
       D4 prototype 端到端（推導→實測）                              ← prototype 真入口在這
  └─ MVP-builder（prototype→產品）
       ① SYNTHESIS=設計分 answer-key → ② setup-prototype.sh --mvp → ③ 種子成 src/+verify.sh
       → 小迴圈 run.sh <driver> fresh zero-context → verify.sh 閘 → 畢業 dual-score → 人 LAND-DECISION
```
> DR 是「填外部知識缺口」的一步，不是主幹；把 DR 當事實直接做設計＝幻覺入庫（downstream-landing 反模式 1）。

**誤解 2：「prototype」是一個東西——其實有兩種，別混。**

| | **D4 驗證型 prototype** | **MVP 種子 prototype** |
|---|---|---|
| 問的問題 | 一個 UK 可行度缺口（「做出來才知」） | 已驗證，要長成耐久產品 |
| 歸宿 | 答完 absorb（ANSWER→NOTES.md/SYNTHESIS）；artifact **留存作驗證錨**（gitignored `prototype/`，自帶獨立 git），**永不升格 src/** | 升格進 `src/`，八大基座迭代 |
| 全局 skill | `~/.claude/skills/prototype`（一命令、surface state、混壞 case） | `setup-prototype.sh --mvp` 八大基座 |
| cutplan 實例 | `prototype/llm-timeline-editing/OpenTimelineIO/`（G4/G5） | `prototype/llm-timeline-editing/cutplan/` |

**所以「交給八大基座做 MVP」＝拿一個已驗證的種子 prototype（不是拿 DR、不是拿①驗證型 prototype 的半成品），跑 MVP-builder ①②③。**

> **know-why：①不是「拋棄式」，是驗證過的技術實作等價物**（2026-07-20 修正）。舊措辭「答完即刪」被 territory 反證——G4/G5 的 `OpenTimelineIO/` 從未被刪，且被 SKILL.md 引為 LIVE 錨。Path B 論證：刪掉 artifact，SYNTHESIS「此 UK 已實測關閉」的 claim 便失去可重驗的確定性鐵錨，退化回敘事。兩種 prototype 消歧的 load-bearing 軸從來是**升格路徑**（①的半成品永不進 `src/`，只有②升格），不是壽命。①的 scope guard 不變：只為答一個 UK 缺口而建、答完就收，別長成半個產品。artifact 歸宿＝留在 gitignored `prototype/`（自帶獨立 git）＋ bundle 快照進 `reference/anchors/`（`scripts/audit-anchors.sh` 機械核路徑存在＋快照未落後）。

---

## 1. 大迴圈引導提示詞（逐階段可貼；每段＝指針＋prompt 骨架＋閘＋▣SURFACE）

### Phase R — 研究到可信 SYNTHESIS　【LIVE ✓ cc-20260711 首次端到端】
> SSOT：gcr `SKILL.md` S0-S9 表 ＋ `modules/downstream-landing.md` D1-D2。**照那兩處做，別在這裡重述**。

```
1. 判模式：有 Gemini/AI Studio URL → Mode A；只有研究主題+上下文 → Mode B（主動開對話 Q&A）。
2. 跑 S0-S9（複用 automate.js DR 引擎，禁重造 monitor+retry）。產物給絕對路徑（AUP：主會話不讀原文全文）。
3. D1 落地驗證（主 session=Opus 編排+判官；子代理分層 Sonnet/Haiku；agy 從 CC 非互動 session 不可靠→跳過，
   確定性錨補位）：每條 load-bearing claim → GitHub API / registry proxy / release-sha256 硬證，
   存在性 VERIFIED ≠ perf/framing 對（分開判）。反幻覺走 external-verify。
4. D2 合成 SYNTHESIS：真實度計分卡（marketing<vendor<primary）＋技術等價物矩陣（+存在性+成熟度+license 欄）
   ＋分層架構＋最脆弱三處＋格式/工具選型矩陣。設計原則從查證反推（把「精準」責任從 LLM 移到確定性中介層）。
   ▣ 若下游要商用+零 copyleft：等價物每元素過授權/專利合規軸（code 授權 + model card 分開查 + codec 專利
      + 科技巨頭 permissive 選）→ external-verify/modules/license-patent-compliance.md。開源≠可商用零義務。
```
**閘**：SYNTHESIS 每條 load-bearing claim 有確定性錨或明標 UNVERIFIED（無錨＝Half-Bridge，不宣稱）。
**▣ SURFACE**：SYNTHESIS 給人核——哪些 claim CONTRADICTED、哪些留待 prototype 實測。
> **know-why：跑 DR 前先查既有同主題 SYNTHESIS**（autopilot-bridge 2026-07-11 實證）。對話與 `gemini_research/gcr/` 既有產物同主題時，該處的機械錨（GitHub API 星數/活躍度、release sha256、CONTRADICTED 裁決）**已驗，複用不重跑**——只對「新對話相對既有的增量具名實體」做 D1。實例：autopilot-bridge 的 maestro-runner/WDA/devicectl 全複用 `b6d196-SYNTHESIS.md` 的裁決，D1 只新驗 headless/Canvas/autopilot 三軸。**反面教訓**：判官一度盲錨對話裡沒出現的 `pymobiledevice3`/`go-ios`（領域常識工具），被子代理 grep 揪出「0 命中」撤回——印證 external-verify「錨定 source 自身 bibliography、禁盲搜」，**增量 D1 只錨對話真引用的實體**。

### Phase G — 可行度 gap 收斂 → D4 驗證型 prototype　【LIVE ✓（cutplan G4/G5）】
> SSOT：`unknown-discovery-composer` 四象限 ＋ `downstream-landing.md` D3/D4 ＋ 全局 `~/.claude/skills/prototype`。

```
5. D3 盤點 SYNTHESIS 自身可行度未知（KK/KU/UK/UU）：
   KU（讀源可答）→ repo-wiki-converge(L1 wiki)→repo-agent-native(L2 不變量)。
      ⚠ 深研真實參考實作常「反證」DR 中心論點（最高價值揭露；實測：真 AI 剪輯 agent 繞過交換格式直接 render）。
   UK（做出來才知）→ 第 6 步。   UU → 盲點 pass。
6. D4 對每個 UK gap 跑驗證型 prototype：
   bash kb-ingest/setup-prototype.sh <plan> <repo> [pip...]   （預設輕量模式，非 --mvp）
   紀律：標 PROTOTYPE、一命令跑、每步 surface state、**混入該擋的壞 case** 實測防護真起作用、誠實留白
   （明寫「本 prototype 未證什麼」）。答完 → NOTES.md 記問題+裁決 → **fresh 判官原始重算 spot-check（先於 absorb）** → absorb 回 SYNTHESIS；artifact **留存作驗證錨**（不刪、不升格）。
```
**閘**：claim 從「推導」升「實測」（實測揭露 nuance，例：EDL 多軌非 silent-lossy 而是 loud raise）。
**▣ SURFACE**：哪個 UK 缺口已被實測關閉、SYNTHESIS 更新到第幾版——人決定「夠不夠格開 MVP」。
> **know-why：某類 v1 種子可跳過 D4 驗證型**（autopilot-bridge 2026-07-11 實證）。§0 兩種 prototype 消歧的接縫——當 v1 的 UK 核心**本身就是要進 `src/` 長成產品的②MVP 種子**（而非①答完留錨的驗證型），對它跑 D4 是多餘的：那個 UK 直接在 Phase M 小迴圈用 mock 純內部層驗即可。實例：autopilot glue 的「閉環是否收斂」是 UK，但 glue 本身就是 MVP `src/`，於是用 mock maestro-runner + fixture JUnit 在 Phase M hermetic 層驗（stop-loss/收斂/失敗簽名），不先建驗證型。**判準**：UK 是否可由「即將成為 src/ 的種子」自身承載——是則跳 D4、直接 Phase M；否（UK 是種子外的可行度問題，如 headless/Canvas 遠端手法）則仍走 D4 各自實測。
> **know-why：D4 判官閘序＋pre-registration＋流程型 skill 量測（2026-07-20 skill-evals-governance 實證）**。(1) **ANSWER→判官→absorb 閘序不可倒**：本次先 absorb 再補判官，D4 判官原始重算仍抓出 1 處實質數字失真（儀器碼 50-skill 外推常數誤標 23-skill 全艙）＋1 處歸因缺口（地板效應漏斷言脆性子因）——absorb 先行＝失真已入 SYNTHESIS 才被撈回。(2) **期望表 pre-registration 證據**＝獨立 commit 先於 run，或至少 mtime＋內在核對（預測有 MISS＝非事後擬合）；單一混合 commit 不足證（判官裁 ADJUSTED）。(3) **流程型/行為指引型 skill 的效能量測正解＝行為遵循消融**（乾淨 cell 雙臂量紀律軸轉移），非任務完成 gym benchmark（人 admit 閘＋疆域依賴＝類別錯配）；實錨 dr-to-mvp 自測 delta +2.16/4 軸、最強軸＝獨立判官 6/6 vs 0/6。錨＝`docs/plans/2026-07-20-dr-to-mvp-skill-evals/{G-D4-judge-verdict.md,adherence-ablation/}`；方法 SSOT＝`antigravity-skill-authoring/modules/skill-verification-methodology.md` §行為指引型。

### Phase M — 種子 prototype → 八大基座 MVP　【LIVE ✓（cutplan：SC1-17、118 tests、五真整合 RIP）】
> SSOT：`loop-harness-standard/modules/mvp-builder-and-adlc-equivalents.md` §2 架構 ＋ §3/§4 效益/優化。**照它，別重述八大基座規範**。

```
7. ① 定設計分 answer-key：SYNTHESIS §3 golden-path + §3.2 fragile + G5 盲點 → DESIGN-SCORE.md 對照表
      （每格 done/designed-cut/MISS；MISS=設計分 FAIL）。這是「畢業設計分判官」的機械答案卡。
8. ② scaffold 八大基座：
      bash kb-ingest/setup-prototype.sh --mvp <plan> <mvp_repo> [pip...]
      生：PROMPT.md(#7 目標契約=SC清單+guard+stop-loss+dual-score 畢業閘) · PLAN.md(#8 狀態帳本) ·
          CLAUDE.md(#1 driver 被動上下文) · run.sh(調度 <driver> <target>) ·
          verify.sh(#6 T0 硬閘：design-gate + pytest 分層 + e2e，--fast/full 兩層) · DESIGN-SCORE.md ·
          dispatches/(輸入側紀錄) · scripts/ · tests/(good/hollow fixtures) ·  venv + 獨立 git。
9. ③ 把第 6 步驗證過的種子 prototype 移進 src/，補 verify.sh 第一條回歸測試（實作分 T0 起點）。
10. 小迴圈 iterate-until-pass × stop-loss（大迴圈=主 session=D12 engine 驅動）：
    for 每個 open SC：
      a. 寫 dispatches/round-NN.md 逐字 brief（輸入側紀錄——唯一答案洩漏向量+可審計性；Fable #2）。
      b. 派 fresh zero-context driver（Agent tool subagent，執行者≠判官、禁 fork；鐵律 3/D6.1）整改 src/+加回歸測試。
      c. 判官（主 session Opus）獨立驗：跑 verify.sh full + --fast、git diff 確認零 src 弱化/零測刪除、
         **實質 spot-check 該輪的核心新 claim**（別只信 exit 0）。exit0 LIVE→commit 進獨立 git→下一 SC；
         exit2→記 PLAN 失敗軌跡，達 stop-loss(3 無進展)→▣SURFACE 人。
      ⚠ 判官永不外包、永不用 agy（agy=Gemini only，判官永遠 Opus）。改既有測試需 PLAN `HUMAN-AUTHORIZED:` 條目。
11. 畢業：設計分（DESIGN-SCORE 零 MISS，跑 fresh subagent 設計分判官、**不餵 big-loop rationale**）
    ∧ 實作分（verify.sh full LIVE exit0）→ 兩軸皆綠。
```
**閘**：dual-score AND（降維/移除某 SC 仍須過設計分＝證明是 designed-cut 非漏做）。
**▣ SURFACE（終點，必停）**：畢業＝人 LAND-DECISION admit。admit 後 **homing**：MVP 現住 gitignored `/prototype/`＝單機孤本，
　人 admit 後須搬離（上 remote 或入 `/repo/`）；並把畢業產品自身跑 repo-agent-native L2 回填 v2 PROMPT Guard-Metric（產品化閉環出口不懸空）。
> **know-why：homing 目的地不存在時的 fallback**（autopilot-bridge 2026-07-12 實證）。「上 remote 或入 /repo/」假設 repo 有一個非-gitignored 的 durable home。但有些 repo（如 ix-agy＝DR/影片管線 repo）**無 remote、`/repo/` 也 gitignored**（是被測 App clone 區）——兩條落點皆不成立。fallback＝**MVP 併入「對應 owner skill」的 `reference-impl/` 子目錄**（畢業產品即該 skill 的參考實作）：移除獨立 .git 作普通目錄、4-commit 歷史導出 `CHANGELOG.md`、venv 靠 nested `.gitignore` 擋，與 skill 一起進主 repo 版控→脫離孤本。**硬體/真機類 e2e 無設備時標 `deferred(needs-hardware)`,homing 不因此卡住**（編排邏輯 hermetic 全驗即可 merge;真機閉合待設備）。實例：autopilot-bridge→`ios-agent-autopilot/reference-impl/`（ix-agy d4f4e35）。相關記憶 [[mvp-skill-exit-ix-agy-dot-agents]]。

---

## 2. 誠實接縫（Path B——別在未證的關節上鋪平滑敘事）

| 接縫 | 狀態 | 出處 |
|---|---|---|
| Phase R（gcr S0-S9 + D1-D2） | **LIVE ✓** cc-20260711 首次端到端（Maestro iOS 真機 DR→ios-realdevice-automation skill 全綠） | downstream-landing §LIVE |
| Phase G（D3/D4 prototype） | **LIVE ✓** cutplan G4/G5（OpenTimelineIO round-trip 實測） | mvp-builder §LIVE 錨 |
| Phase M（prototype→MVP §2） | **LIVE ✓ ×3** cutplan（SC1-17、118 tests、五真整合 RIP、授權合規、Fable-5 review 過）＋ autopilot-bridge（2026-07-11，跨 repo 落 ix-agy，SC1-7、51 tests、判官 32 抽查、畢業 skill `run-all` 綠）＋ harness-core（2026-07-12，跨 repo 落 skill-bettor，SC1-8、117 tests、判官揭洞整改一輪、雙分綠人 admit） | mvp-builder §LIVE 錨 |
| **DR→skill 產物「自動接」八大基座的完整程序** | **設計 only / 預留**——待首次真跑「skill→小迴圈」再 fold-back 填實，此前只指針不臆造 | downstream-landing step 6【預留】 |
| **N×M host×driver 覆蓋** | **3 driver 格 LIVE ✓**（cc-20260711）：Claude host × {subagent（cutplan）, claude, agy}——claude／agy 的 `run.sh` 分支已於 `_mvptest/demomvp` 真跑補證。**仍未證**＝Antigravity-CLI host | mvp-builder §4 N×M |
| **dual-score 設計分判官** | **LIVE ✓ 首次跨完整畢業**（2026-07-11 autopilot-bridge）：fresh opus 設計分判官（不餵 big-loop rationale）掃 DESIGN-SCORE 判 PASS ＋ 實作分 `verify.sh` exit0 ＝ AND 綠;副產區辨「needs-hardware 誠實接縫 ≠ scope descope」。**第二燒**（2026-07-12 skill-bettor harness-core）：18 行 13P/5CUT/0MISS＋7 獨立探測;同役判官抓到 verify 綠但語義反轉的真缺陷（round-05 handled 全域洗白→整改閉環）;**同次 evals-gate W1**＝設計分判官給 PASS 卻主動揭 HIGH 安全洞（證據防偽 mode-downgrade 繞過）→**編排者裁 FAIL 不帶缺口畢業**→round-06b 整改→獨立複審 E5 攻擊向量確認 CLOSED（判官不只抓洞、更逼「不帶已知缺口畢業」）。**三燒** skillgate（agy 偽造 HUMAN-AUTHORIZED 被判官 diff 撤）見 mvp-builder | mvp-builder §3;harness-core／evals-gate `DESIGN-JUDGE-VERDICT.md` |
| **homing** | **手動,且目的地依 repo 而定**：畢業 MVP 搬離 gitignored /prototype/ 仍靠人。**ix-agy 型（無 remote／`/repo/` 也 gitignored）**：SYNTHESIS「上 remote 或入 /repo/」兩條皆不成立→MVP 併入對應 owner skill 的 `reference-impl/`（移除獨立 .git、歷史導 CHANGELOG、venv 靠 nested .gitignore 擋）進主 repo 版控;硬體類 e2e 無設備標 deferred(needs-hardware) 不卡 homing（實例 2026-07-12 autopilot-bridge→`ios-agent-autopilot/reference-impl/`，ix-agy d4f4e35）。**families 型（living-skills 家族 repo）**：→ `families/<f>/shared/runtime/<mvp>/` 隨家族 checked-in、子技能＝使用/建構型指向不複製、跨模組路徑 `__file__` 相對（skill-bettor harness-core／evals-gate 0e9ea32）。**三型譜＋共通不變量（搬完 verify 必綠）見 mvp-builder §4(h)** | mvp-builder §4(h) |
| **design-gate ↔ 畢業後 SC** | 已知縫：cutplan SC14/SC15 有測守著但沒進 PROMPT.md `[x]` 清單→design-gate 掃不到（belt-and-suspenders 只 scope 在 SC1-13 畢業契約） | cutplan round-17 commit note |

> 補證已跑（cc-20260711）：trivial SC1 red-pin → `run.sh claude` 與 `run.sh agy` 各真驅 driver 建 src → verify 綠;副產 design-gate HUMAN-AUTHORIZED 模板假匹配 bug 揪出＋修（三處 grep 錨到 `^- round <N> HUMAN-AUTHORIZED:`）。剩 Antigravity-CLI host 未證。

---

## 3. 一頁速查（最小命令序列）

```bash
# Phase R：研究 → SYNTHESIS（gcr skill；DR 走 automate.js，判官=Opus，錨>LLM）
#   → gemini_research/gcr/<conv-id>-SYNTHESIS.md（含真實度計分卡+等價物矩陣+license 欄）

# Phase G：UK gap 實測（驗證型）
bash kb-ingest/setup-prototype.sh <plan> <seed_repo> [pip...]     # 預設輕量；答完 absorb→SYNTHESIS→留錨

# Phase M：種子 → 八大基座 MVP
bash kb-ingest/setup-prototype.sh --mvp <plan> <mvp_repo> [pip...]  # 生八大基座+DESIGN-SCORE+dispatches+獨立git
#   迴圈：write dispatches/round-NN.md → 派 fresh driver 整改 src/ → 判官跑 verify.sh full+--fast+spot-check
#         → commit 獨立 git → 下一 SC；stop-loss 3 → SURFACE
#   畢業：DESIGN-SCORE 零 MISS(設計分判官) ∧ verify.sh exit0(實作分) → ▣ 人 LAND-DECISION → homing 搬離 /prototype/
```

**跑前必查**：`pgrep -fl automate.js`（Phase R 的 DR 不可與 dr-research-loop 影片管線同跑同一 :9333）。
**每個 ▣ 停**：recipe-not-engine，人 admit 才續下一 Phase。
