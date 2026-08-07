# Module: fold-in — know-why + northstar → antigravity retarget 映射

> 屬 [`fold-in`](../SKILL.md) skill。SKILL.md 有確定性程序＋不變量;本檔 = 為何這樣、lineage、完整 retarget 映射表。
> 查證方法 → [`external-verify`](../../external-verify/SKILL.md)。

## 1. 為何 fold,不造新（Slop #2 / anti-inflation）

「能力」不是被收集出來的,是被**調用**出來的（northstar RIP：不改變 runtime 行為的能力不是能力）。每段經驗都新建一個 skill,antigravity 這種 6-skill 規模會迅速漂成 **catalog 墳場**：一堆沒人 activate、彼此重疊、description 互相搶語義觸發的 husk。fold 的默認立場是——**先假設既有 owner 能吸收它**,只有證明「真有未覆蓋 niche」才由 `antigravity-skill-authoring` 出閘新建。這把「新建」從隨手動作降級成需要人核的例外。

判據不是「經驗多不多」而是 **grounding**：一段確定性修法 fold 進 owner 的 Gotchas＋module,是全顆粒度推進（demand-scoped ✅）;造個空殼 skill 把散文塞進去等它被 surface,是 supply-push 增殖（❌）。

## 2. Layer A/B 為何分（DDR-205 lineage）

antigravity 的漸進載入：skill 的 **metadata（frontmatter）被索引供語義選取**,body ＋ `modules/` 在該 skill 被選中前**不載入**。所以：

- **Layer A（SKILL.md）= 確定性事實／程序／Gotcha**：被載入時要能立刻照著做,不夾雜長篇 rationale。胖 SKILL.md = 每次 activate 都付 know-why 的 token,且淹沒可執行程序。
- **Layer B（modules/）= know-why**：為何這樣修、根因論證、取代史 —— 只在真要理解時才 lazy-load。

這與 `dr-research-loop`、`antigravity-skill-authoring` 的 dogfood 一致（SKILL slim ＋ modules/ 拆分,範式參 northstar `skill-conformance-hub`）。

## 3. durable home 非 ephemeral —— 為何逼「畢業」

對話（以及隨手筆記、全域 memory 的無-home floor）是 **ephemeral**：下個 session 不保證載入,load-bearing 的操作課會**蒸發**。antigravity 已經有一個對的 durable home —— **AGENTS.md「Resolved」防回退帳本**：它把「症狀＋根因＋修法＋禁回退鐵錨」寫成頂層、每 session 載入的索引,正是為了「別讓血淚換的教訓被回退」。

所以 fold-in 的第 5 不變量逼「畢業」：behavioral／操作課 → Resolved 或 owner Gotchas;跨階段方法論 → dr-research-loop。**home 是 AGENTS.md / SKILL / module,不是對話**。這對應 northstar fold-in 的「別 park MEMORY.md 等它留」——差別只在 antigravity 的 durable home 叫「Resolved」而非 CLAUDE.md-slim rule。

## 4. discrimination gate —— 為何要 automate.js 鐵錨（否則 husk）

吸收一段「修法」最容易的自欺：把散文（「已優化 DR 啟用」「提升了穩定性」）寫進 skill,但 `automate.js` 裡根本沒有對應實現,或實現了但沒有可回退偵測的鐵錨。這是 Half-Bridge —— 讀起來平滑,實際不可宣稱成立。

antigravity 的確定性鐵錨（Path B 意義的 exit-code 等價物）是：
1. **automate.js 真有該邏輯**（偵測／自癒／重試函式真的在,`node --check` 過,best：live 實測跑一次）。
2. **AGENTS.md「Resolved」記一條 `禁回退用 <舊法>`** ＋ live 實測數字（如「10148 字」「17068 字真報告」「chip 出現」）。

有這兩者,「吸收成立」才有判別力（一個「連接但不判別」的假吸收 —— 光有散文沒有 automate.js 實現 —— 會被鐵錨抓出）。無鐵錨 → gate 擋下,退回,別存 husk。對應 northstar 的 PG-156 discrimination-gated / PG-155 別信來源自證。

## 5. northstar → antigravity retarget 完整映射表

port 的命門：northstar `/fold-in` 是 **Claude Code 斜線命令**（`.claude/commands/fold-in.md`）,body 把重活全委派給 northstar 專屬基座。antigravity 是**另一平台**（Google Antigravity `.agents/skills/`,authoring skill line 19 明文牆開 Claude 格式）。原樣搬 = 引用不存在基座的死 husk。以下是逐機制 retarget：

| northstar 機制 | antigravity 對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| Claude Code 命令 `.claude/commands/fold-in.md`（`$ARGUMENTS` `--target` `--apply`） | Antigravity skill `.agents/skills/fold-in/SKILL.md`（activate_skill / Skill 調用,無 $ARGUMENTS） | antigravity 唯一的 skill 機制;無斜線命令面。經驗以自然語言在 activate 時描述,不用旗標。 |
| M70 / `skill_match`（rag-local cosine≥0.65 自動 dominator 閘） | 手動語義選 owner（6 skill ＋ AGENTS.md 候選,決策樹在 §程序） | antigravity 的 6 skill 未進 rag-local 索引;規模小到肉眼可選,自動化 overkill。 |
| actuator = `skill-conformance-hub` create/adjust | actuator = `antigravity-skill-authoring`（adjust owner） | 各自平台的 skill 規範 SSOT / 該不該新建的裁決者。換名委派,精神相同。 |
| Layer A/B（`skill.md` 事實 ＋ `modules/` know-why） | 完全相同（`SKILL.md` slim ＋ `modules/`） | antigravity 疊加在官方規範上的本 repo 慣例本就 copy 自 northstar skill-conformance-hub。直接沿用。 |
| 經驗吸收 home = CLAUDE.md-slim rule / SSOT module | home = **AGENTS.md「Resolved」防回退帳本** ＋ owner SKILL Gotchas | 兩者都是「頂層、每 session 載入、逼畢業不蒸發」的 durable index,只是檔名/慣例不同。 |
| global `problem-graph/` ＋ skill `pg/` 路由（PG-NNN） | **拿掉** —— 問題進 AGENTS.md「Resolved」或 owner Gotchas | antigravity 無 PG 系統。硬造 pg/ = 引入不存在的雙圖（PG-103）。 |
| `.northstar/run-all-tests.sh` ＋ `boundary_coverage_audit.py` | **拿掉／換** —— `node --check automate.js` ＋ frontmatter/slim 檢查 ＋ live 實測 | antigravity 無 test runner（只有 puppeteer automate.js）。驗證錨換成 node syntax check ＋ live 跑。 |
| Pattern Card #1 materializer（P0 檔禁直接 Edit） | **拿掉** —— AGENTS.md / SKILL.md 直接 Edit | antigravity 無 auto-approve.sh P0 保護。無護欄 → 自審更嚴補償。 |
| PG-156 discrimination-gated / PG-155 別信來源自證 | 確定性邏輯必在 automate.js ＋ AGENTS.md 禁回退鐵錨,否則 husk（§4） | 同一紀律,鐵錨從「reverse-mutant eval」換成「automate.js 實現 ＋ 禁回退條 ＋ live 數字」。 |
| MEMORY.md floor（無-home meta-cognitive） | 全域 Antigravity memory `[[...]]`（如 `[[no-duplicate-video-selection]]`）floor 同理 | 兩者都只留無 durable home 的判斷守則;有 home 的一律畢業。 |

### 拿掉的東西不是「簡化」而是「不引入不存在的基座」

northstar fold-in 的 PG 路由、boundary 測試、materializer 在 northstar 是活的（有對應基座）。在 antigravity 它們**沒有基座** —— 保留它們 = 讓 skill 引用一堆跑不動的東西 = 正是 northstar CLAUDE.md 反的 supply-push husk（RIP / PG-103）。retarget 的正確姿勢是：能一對一映的映（Layer A/B、actuator、durable home），沒對應物的**誠實拿掉並記錄**（PG、測試 runner、materializer），別留半橋。

## 6. 為何 fold-in 要 boundary-aware（掌握系統邊界）＋ 技術等價物判斷通則

fold-in 早期世界觀是「把經驗塞進一組**扁平的 N 個 skill**」。但 antigravity harness 已長成**遞迴迴圈組合**（見 [`antigravity-harness-wiki`](../../antigravity-harness-wiki/SKILL.md)）：L1 理解／L2 不變量／L3 規格＋橫切驗證＋內容收穫源,各自閉合、各有獨立收斂閘、可疊加可遞迴。這對 fold-in 有兩個硬後果:

1. **系統邊界是活的,不是硬數字**。SKILL.md 舊寫「6 個 skill」在真值已 13 時就是 stale,更糟是讓 routing **結構性看不見**新迴圈（repo-wiki-converge／repo-agent-native／antigravity-harness-wiki…）當 owner 候選。修法不是改成「13」（下次又 stale）,而是**讓 owner 候選源＝讀全景圖組件卡**——全景圖本就是那份「系統邊界的單一真相」。fold-in 每次先讀它,才叫「掌握系統邊界」。

2. **fold-in 是最主要的變異操作,所以是最大漂移源**。全景圖存在的唯一理由＝防雙圖漂移（改某階段 skill 時閉環／不變量／prompt 被誤改誤簡化）。而 fold-in 正是那個「改某階段 skill」的操作。若 fold 動了某迴圈的閘／資料流歸屬／不變量／prompt 指針卻沒回同步全景圖,那張**防漂移的地圖自己先漂**——最諷刺的 husk。故不變量 6 逼「fold 完回核組件卡＋不變量清單」,且**只改指針永不抄內容**（抄＝製造會漂的第二份,正是全景圖鐵律）。方向是單向的:fold-in 這端「知道去同步」全景圖;全景圖那端的反向紀律（「改某 stage skill 後回核本圖」）本就在它自己的 Gotchas——兩端咬合,不重複承載。

**技術等價物判斷（§5 retarget 的通則化）**：§5 是「northstar→antigravity 逐機制判 1:1 可映 vs 無基座誠實拿掉」的一個實例。它其實是每次 fold 的**通用判別閘**:吸收任何元素前,對照**目標平台真實基座**判——(a) 有 1:1 技術等價物 → 映;(b) 無對應基座 → 誠實拿掉並記錄,**絕不留半橋**（引用不存在基座的散文＝死 husk,RIP／PG-103）。反身版就是不變量 6 的反-husk 錨:fold-in 指向的 SSOT（如全景圖）**必須是真檔案**——指向 phantom 基座＝自己造 husk。這把「automate.js 鐵錨」（§4,行為類 fold 用）與「指向真基座」（方法論／路由類 fold 用）統一成同一條 discrimination:**吸收成立 ⟺ 錨在真實基座上**,只是行為類的基座是 automate.js＋Resolved,方法論類的基座是被指向的真 SSOT 檔。

## Sources / Lineage
- northstar `/fold-in`：`/Users/neon/northstar/.claude/commands/fold-in.md`（DDR-205 Layer A/B、Slop #2、PG-103/155/156）。
- antigravity 慣例：[`antigravity-skill-authoring`](../../antigravity-skill-authoring/SKILL.md) ＋ [`AGENTS.md`](../../../../AGENTS.md)「Resolved」段。
