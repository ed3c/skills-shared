# CLAUDE.md — skill-bettor(Claude Code host｜Claude-tier 被動上下文派生)

> **家族綁定**:本檔是 **Claude 家族**開啟 skill-bettor 時的被動上下文(Claude Code=大迴圈 host,
> 讀本檔+cascade `~/.claude/CLAUDE.md`)。living-skills 資產工場:skill 家族每日演化(spawn/refine/
> prune)、eval 閘門守質量、訂閱者拉成長中資產;生產線標準=antigravity 大小迴圈八大基座。
> 設計事實**單一 SSOT=`ARCHITECTURE.md`**(對映表/八大基座卡/tier-dispatch/人閘清單/防退化鐵律);
> 本檔=同一事實的 **Opus/Fable-tier 呈現層派生**——換家族措辭、tight 脈絡、零範例、少 "Do not",
> 非另立事實或另一份規則牆。完整表格/鐵律全表/每日管線 → `ARCHITECTURE.md`,本檔只給脈絡+入口+
> 最高頻鐵律、不複述(複述=雙圖漂移;SSOT 改則本檔對映句同步)。規範權威=本地
> `.claude/skills/loop-harness-standard/`(2026-07-11 從 antigravity 移植,見其 `modules/retarget-map.md`);
> canonical 範例=本地 `loop_demo/claude_agy`+`loop_wiki` 活實作(指針不抄)。

## 呈現層派生紀律(本檔 vs SSOT;port 自 antigravity CLAUDE.md⟷AGENTS.md 差異)

antigravity 用 CLAUDE.md(Claude-tier 派生)⟷`AGENTS.md`(SSOT,Sovereignty L1)雙檔分工。
本 repo **鏡像此模型之結構**(主權敘述除外,見末段):現況單 host(Claude-only)故單檔、SSOT 暫由
`ARCHITECTURE.md` 擔;一旦 dual-runnable 即生 `AGENTS.md` 為 **SSOT**,本檔轉為其派生(拓撲移交見末段)。

**設計規範差異**:同一批設計事實只有一個權威源;host 特定的被動上下文檔=該事實的 tier 派生,非第二套事實/第二道規則牆。

**實作差異**(本檔 vs SSOT 該怎麼寫不一樣):

| 面向 | `ARCHITECTURE.md`=SSOT | 本 `CLAUDE.md`=Claude-tier 派生 |
|---|---|---|
| 改什麼動這 | 設計事實(表格/組件卡/管線/鐵律全表) | 措辭/入口(不新增事實) |
| 密度 | 完整 | tight 脈絡+入口+最高頻鐵律 |
| 範例 | 有 | 零(範例=指針到活實作) |
| 措辭 | 中性記錄層 | Opus/Fable-tier、少 "Do not" |

派生鐵律:①禁複述 SSOT 內容(複述=雙圖漂移);②SSOT 改則本檔對映句同步;③tight 是正確性不是風格
(harness-spec §3❷ 實測被動上下文膨脹→注意力 91.6%→71.3%,ARCHITECTURE.md §7 鐵律 8 同錨)。
**未來 AGENTS.md**:dual-runnable 才生(§11);屆時**結構鏡像 antigravity**——AGENTS.md=**SSOT**
(cross-host 權威源),本檔改為派生自 AGENTS.md、`ARCHITECTURE.md` 的 SSOT 角色移交/併入 AGENTS.md,
全 repo 恆保單一 SSOT(拓撲與 antigravity 同構)。**唯一刻意分歧=主權 Claude-anchored**:本 repo Claude-first,
admit/裁決權在人+Claude 主 session,不繼承 antigravity「Gemini=Sovereignty L1、Claude 唯讀 L2」那套。

## 目錄地圖
- `PRODUCT.md` — 產品 SSOT(三層飛輪/雙軌證據鏈/紅線);日常驅動 runbook=
  `.claude/skills/product-ops`(晨檢→op→畢業→publish→輪替)。
- `families/<family>/` — 業務資產(路由器 SKILL.md+子技能+shared 原語+evals+changelog)。
  首個家族:`families/pinescript-audit`(成長曲線原點 2026-07-11:有 skill 1.000 vs 無 0.583)。
- `loop_wiki/` — 小迴圈沙盒;`_template/`(演化 op)與 `_template_dr/`(DR 批次)為八大基座
  骨架,一 op/一題一沙盒(`cp -r` 實例化)。**第二編排模式**=多-actuator 全語料對齊型
  (Workflow fan-out N Agent+shell live server+Monitor 接收 POST 決策併發、物理交付自動提示、
  對抗式 findings 自動派修;活對齊決策 cockpit=`dx-adversarial-fix`,左欄頂顯完整防禦拓撲)——
  規範/拓撲/接收 SSOT 見 `loop-harness-standard`(模式)/`harness-wiki`(組件卡)/
  `html-for-decisions`(channel-B),本檔只入口不複述。
- `proposals/` — DR 隔離區(schema/契約=其 README.md;owner skill=dr-research-loop)。
  **任何家族內容禁引用此處**;7 天未過驗證即歸檔。

## 核心指令
```bash
# 家族 eval(mock 自測/真跑/閘門),在家族目錄下:
python3 evals/runner.py --skill <sub> --set public --agent-cmd "python3 $PWD/evals/mock_agent.py {task}"
python3 evals/runner.py --skill <sub> --set public            # 真跑(agent-cmd 見鐵律:model 釘死)
python3 evals/runner.py --skill <sub> --set holdout --compare evals/baselines/<date>.json
# 小迴圈(engine=迭代/stop-loss;run.sh=單發 dispatch,不自帶迴圈):
loop_wiki/<loop>/selftest.sh                                  # positive control(good/hollow)
loop_wiki/engine.sh <loop> --target <path> [--driver claude|agy]  # exit 10=awaiting-human-admit
```

## 鐵律(其餘承 ARCHITECTURE.md §7 與全局 CLAUDE.md)
1. 知識單向流:proposals → 驗證 → 沙盒 diff → eval 閘 → 人 admit → merge。沒有旁門。
2. holdout 只跑一次(迭代只碰 public);eval 的 agent-cmd/judge-cmd model 必須寫死。
3. merge/畢業/案例輪替永遠人 admit;G 閘全綠=候選,不是 merge 令。
4. 演化迭代一律進 loop_wiki 沙盒,不在本層高頻修改;迭代期間禁 commit。
5. 判官永不 Haiku、永不 agy-as-verdict;同家族 author×judge 必 fresh zero-context subagent(禁 fork)。
6. 放置契約(§7 鐵律 9):新目錄/檔案/腳本先對映 ARCHITECTURE.md §2 槽位或該子樹契約;
   無槽位=先改 §2 再落檔,禁隨手放。T0 閘:`python3 scripts/check_placement.py`。

## tier-dispatch(詳表 ARCHITECTURE.md §5)
Fable=大迴圈編排;Opus=判官/畢業(fresh);Sonnet=演化 author+eval agent(釘死);
Haiku/Flash 3.5=機械(禁 author 禁 verdict);agy Pro 3.1=DR/跨家族複核(只 findings 不 verdict)。
