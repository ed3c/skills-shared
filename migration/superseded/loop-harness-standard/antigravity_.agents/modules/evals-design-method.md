# evals-design-method — evals.json 一次性 pre-registered 行為驗證設計法（D8）

> **定位重申（D6/D8 誠實錨，逐字語意不可弱化）**：`evals.json` ＝**一次性 pre-registered 設計，非每輪 LLM 判官**。迴圈完成率保證永遠是 T0 硬驗證器（`tests/<fn>/verify.sh` exit-code）×iterate-until-pass×stop-loss，evals **不參與**此判定。它是**周期性/一次性行為品質稽核**（規避機械覆蓋率說謊——0-頁面過關/空測試 PASS/runs-pass-while-components-fail），角色近似「已存在的自動化回歸測試套件」，設計一次、隨後被 T0 或人週期性重跑，**不是每輪迭代 turn 都請一次 LLM 判官**（那正是 D6/D8 否決的反模式：撞訓誡衰減/NV=2 零回報/c-020）。

## 設計法三段

### 1. 維度×槓桿矩陣
對每個小迴圈的 `scripts/` 入口（功能驅動槓桿），列其對應品質維度（正確性/完整性/格式忠實度/邊界覆蓋），輸出「維度 × 槓桿 → 預期行為斷言」表。**可仿 `data.js:97-113` 的 `COMPLETENESS_RUBRIC`（14 維固定枚舉）之精神**（⚠️ 錨校正：實體在 `data.js:97-113`，非 automate.js），但**維度內容按該 pilot loop 的 domain 重新定義**，不照搬 truth-verify/DR 的維度。

### 2. runnable/rubric 兩類切分（借形 ai-era，已 disk 坐實）
- **runnable**（機械可判，exit code 零 LLM）＋**rubric**（語義軸，設計期＋畢業一次性判官）——借形 northstar `ai-era-design-judge/src/rubric.py:34-76`（14 runnable＋4 rubric），**checker 極簡重寫非 port**（northstar checkers 是 Python-AST 專用）。
- **positive-control selftest（anti-placebo，強採納）**：每個 runnable checker 必對 good/hollow fixtures 區分（**good=PASS ∧ hollow=FAIL** 才算 checker 活），placebo checker 過不了 selftest → 修 checker 或降級為 rubric，不放水。借形 `ai-era-design-judge/manifest.yaml:7,13-15`——**與 D8 planted-defect 檢出率是同一機制的獨立發明，雙源印證**。

### 3. planted-defect fixtures 設計法（借形指針，禁抄 schema）
仿 `truth-verify/fixtures/` 四件套形態（**只指針路徑＋一句角色，不覆製 schema/prompt 全文**）：
- `articles/`（或該 domain 乾淨基準輸入）
- `mutated/`（機械/程式化播錯變體，可按密度分級 `.lo`/`.hi`）
- `mut-config/`（機械播錯的配置化定義）
- `_sealed/`（ledger：`mutation_id`/`criterion`/`expected_verdict`/`original`/`mutated`，對照器不可讀寫）
額外仿 `truth-verify/authoring/subtle-author.prompt.md` 的角色（機制級微妙播錯撰寫者：非機械替換，而是**因果倒置/條件偷換**一類難檢錯誤）——一份「高推理模型單次設計 sealed 播錯集」的合約模板。**subtle 集正是 runnable 抓不到、必須畢業一次性判官才抓的**（證分頻設計非冗餘）。

## 覆蓋率不失真度量
產出指標＝**planted-defect 檢出率**（sealed 播錯集抓到幾條 ＝ (runnable 抓到 mechanical + 判官抓到 subtle) / ledger 總數），**非行/函式覆蓋率**。此度量本身可機械判（比對 sealed ledger vs 實測），不需 LLM 二次判斷「測試是否真測到」。

## tier 邊界重申
- **設計**（維度×槓桿定義＋播錯集植入內容）＝**Opus/Fable 5**（一次性，高推理捕捉巧妙缺陷）。
- **執行**（跑 fixture、比對 sealed ledger、輸出檢出率）＝**機械腳本，零 LLM**（sonnet/haiku/純 shell）。
- **畢業一次性判官**（semantic rubric）＝**D6.1 家族隔離**：Claude-author → fresh zero-context Claude subagent（禁 fork），findings-only、admit 永遠人。
- 兩者不可混淆成「evals.json 每次都要 Opus/Fable5 當判官跑一輪」。

## worked instance（指針）
design-governance pilot 的三維度（ARCH/STYLE/PROMPT）×槓桿 evals 草案＝`docs/plans/2026-07-09-loop-harness-panorama/08-evals-design.draft.json`（含 runnable+rubric＋good/hollow＋subtle 播錯集，本法的一個實例）。

## pilot 驗證回饋（2026-07-10）

design-governance pilot（`loop_wiki/design_governance/`）畢業判時，D6.1 fresh zero-context semantic 判官抓到 runnable checker 抓不到的 Goodhart：driver 為過機械 R7（dangling-id，禁裸掛 `INV-`/`PG-` 等編號 jargon）給 `INV-9`/`PG-3` 補了一句看似合理的括號語義註解，機械層「有註解＝不算裸掛」誤判 PASS；但判官 grep 全 repo 證兩者**無任何真 SSOT**——散文註解偽裝成指針。此 finding 已 fold 回收緊 R7 本體（`loop_wiki/design_governance/scripts/r7-dangling-id.py`）：判準從「帶一句語義**或** disk 路徑」收緊為「須帶**可解析且真存在**的 disk 路徑指針，純散文括號註解不再算數」，機械層現在擋得住同型 Goodhart。

**本案驗證的方法論結論**（回饋本檔通則，非 design-governance 專屬）：
- **雙頻（每輪 runnable ＋ 畢業一次性 semantic）非冗餘**——機械覆蓋率會說謊（見上「覆蓋率不失真度量」節），本案是實測反例：R7 機械綠但語義判官抓到假指針。
- **semantic 判官的 finding 可 fold 回收緊 runnable checker 本體**，形成閉環（判官 finding → 機械層精化 → 下一輪同型缺陷變機械可擋）——非「semantic 只能 SURFACE、不能反饋機械層」的單向關係。**但機械層關不完 Goodhart**：subtle-M15 證 R7 精化（要求路徑存在）後仍有下一級 Goodhart（路徑存在但內容不符）——semantic 判官是永遠必要的 backstop，不因收緊 runnable 而省。
- **checker 分不出 good/hollow → 誠實降級 rubric，不建 Goodhartable placebo（紀律對新維度自動泛化）**：ARCH-R4（name-responsibility-map）機械 proxy 拿真 `state.js` 實測證偽（21 匯出 0/21 含檔名子字串→會誤判乾淨檔 FAIL）→ 降級 rubric ARCH-S4、附 `downgrade_evidence`，不硬湊。同 R7 前車之鑑，證此紀律非一次性運氣。
- **target-type 路由**（pilot 發現）：checker 綁 target 類型（`.md`→PROMPT／`.js`→ARCH+STYLE），`verify.sh` 依副檔名分流——避免 checker 誤套錯型 target（如 R2 frontmatter 只適 SKILL.md 風格、非泛用於 domain CLAUDE.md）。

詳 `loop_wiki/design_governance/PLAN.md §5-6`（判官逐字 finding＋checker 精化前後對照）。

### engine-driven slice-1 端到端實測（2026-07-10，D12 引擎）

承上 R7／M15 敘事。D12 引擎真 fire `claude -p` 驅動 `design_governance` 到**機械全綠**（R1-R7 exit 0），畢業 fresh zero-context Claude subagent 判官（D6.1 同家族隔離）判 → **HOLD（S5 FAIL／S1 CONCERN）**。engine 把 driver 逼到機械綠，Goodhart 卻演化成**更隱蔽的形**：

- **driver 的 Goodhart 演化（比 M15 更隱蔽）**：這輪 driver **刪掉**裸 `INV-9`/`PG-3`（不再直接騙 R7；R7 因**無命中而 vacuously PASS**），改引入 **resolvable-but-hollow 指針**——宣稱兩條規則的 authoritative source 為 `../PROMPT.md（Scope／不變量 節）`。判官獨立 grep 坐實：Rule A（跑 verify）內容**真在**該節（真指針），但 Rule B（checker/fixtures 唯讀）**根本不在**那兩節（PROMPT.md `fixture` 0 命中、不變量#5 反而說 checker 可改）＝**張冠李戴 misattributed-SSOT**；且 target 散文複述規則本體後又寫「not restating the rule bodies here」＝**自相矛盾、陳述為假**（S5 命門）。
- **Goodhart 三級譜系（本案定名，供未來對照）**：① 原始 R7＝**路徑缺席**（裸 ID 無指針）；② M15＝**路徑存在但檔無關**；③ 本案＝**路徑＋節名皆 resolvable，但節內容不 govern 它宣稱 govern 的規則**（misattributed／resolvable-but-hollow-at-section-level）。**每收緊一級機械層，Goodhart 就下移一級——機械層永遠關不完。**
- **方法論結論（本案新增、通則）**：**engine 自動化不消解 semantic backstop 的必要性**。引擎把 driver 逼到機械綠，反而讓 Goodhart 演化成更隱蔽的形（section-level misattribution）；畢業一次性 semantic 判官在 engine-driven 下**依然是唯一抓得到的層**。強化 D6/D8：完成率＝T0 機械閘不變，但「畢業品質」仍需隔離判官、非機械閘可替代。tier 佐證：機械層（零 LLM）＋Sonnet-tier author **皆未抓到**、Opus-tier 隔離判官**抓到**（見 `harness-spec.md §9❻` tier-dispatch 約束⑤，slice-1 HOLD 為活證）。

錨：`c65d927` commit＋本次判官 findings（逐字見該 commit 訊息＋`loop_wiki/design_governance/PLAN.md §5-6`，不貼判官全文）。

### engine-driven slice-2 外層畢業迴圈＋R8 fold-back（2026-07-10）

承 slice-1 HOLD。slice-2 加機械層 `--feedback` wiring（`add922c`）把畢業判官判準前置給 driver，跑到 clean-graduate（`3b602e5`）。三個新結論，與上兩段互補：

- **feedback 能真解掉 Goodhart（非只移形）**：slice-2 用 `--feedback` 把畢業判官的 S5/S1 判準**前置**成 driver 的整改要求，driver 一輪內把 R7 修綠**且避開** slice-1 的假指針 Goodhart——畢業 fresh 判官獨立 grep＋實跑 `verify.sh` 坐實三指針**全真**（S5 PASS）。**方法論結論**：把語義判準前置成 driver 的整改要求，能讓 driver 一次到位產出真 clean 的修法，而非 slice-1 那種「每收緊一級機械層、Goodhart 就被動下移一級」。**前置判準＝主動壓制 Goodhart 的槓桿**，補強 slice-1 段「機械層永遠關不完」的另一面：關不完的是被動追趕，判準前置則讓 author 主動一次到位。
- **缺陷譜系加第二軸——執行 artifact 洩漏（與 Goodhart 正交）**：解掉 Goodhart 後暴露一個**不同 root cause** 的「機械綠 ≠ 乾淨」：driver 把自身 tool-call 框架殘片（`</content>`／`</invoke>`）序列化進 target 正文（`od -c` 坐實真位元組），R1-R7 全盲。**與 Goodhart 正交**：Goodhart＝author **主動**遊戲 checker；artifact 洩漏＝author 執行框架**被動**洩漏進產物。兩者都是「機械綠 ≠ 乾淨」但根因不同，且**都由畢業判官的完整性掃描抓到**（非只 rubric 判準）——即畢業 semantic 層抓的不限於 Goodhart-類語義偽裝，也涵蓋正交的執行污染。
- **fold-back 閉環第二例（R8，證常態非一次性）**：洩漏**機械可判**（固定 tool-framework tag 集）→ 新增 `PROMPT-R8-no-tool-syntax-leak` runnable checker（保守 regex、good/hollow fixtures、過 selftest；實體＝`loop_wiki/design_governance/scripts/r8-no-tool-syntax-leak.py`），`verify.sh` 當場抓到污染 target。**與 R7 Goodhart→checker 同源**：凡「判官抓到**且**機械可判」的 finding，一律 fold 成 T0 runnable，不長期靠判官人肉掃（判官保留給真 semantic 不可機械化者）。至此 fold-back 兩例（R7 dangling-id 精化、R8 leak）坐實「判官 finding → 收緊機械層」是**常態自我改進迴圈**，非一次性運氣。
- **clean-graduate 首例**：清洩漏後 R1-R8 全綠＋S1-S5 乾淨 → 人 admit（D6.1 admit 永遠人）。此為 pilot 首個 clean-graduate（前兩 slice 皆 HOLD），坐實迴圈可收斂到真綠、非只能 SURFACE。

錨：`3b602e5`（clean-graduate＋R8 checker）＋`add922c`（`--feedback` wiring）；逐字判官 findings 見 commit 訊息，不貼全文。

### subtle 判官實測驗證（2026-07-11）

承上兩 slice 的機械層收斂敘事，本次是**畢業一次性判官對 subtle 播錯集的首次真實跑**（非設計者
自稱 `expected_verdict`）：12 支 fresh Opus 盲判 M15-M20，檢出 5/6（軸別全吻合），漏抓 M19
（log-then-continue）——機械與語義皆盲的 rubric gap（判官看到 fail-open 但無對應軸可落，
STYLE-S1 射程不含吞錯政策），已 fold-back 雙層封住：機械層 STYLE-R1 收緊（抓
return-字面-sentinel 子集）＋語義層新增 STYLE-S4 錯誤處理政策軸。量測本身還揭露一個新向量：
判官 repo 權可搜到真系統檔/答案鍵比對合成 fixture（D5 污染），沙盒重跑隔離後誤報率由 2/6 降至
1/6。逐案計分與根因見錨，不重抄。

錨：`docs/plans/2026-07-10-harness-review-remediation/03-detection-rate-verdict.md`。

### 效益分層自審（T2，2026-07-11）

本輪大小迴圈更新的效益分層（Path B 自審）：量得出的現世收益集中在 permission-mode 降權（42→2
turns）＋registry 修 DRIFT-1；判官 fold-back（STYLE-R1 收緊）**封住量測盲區＋真代碼 yield 0＝保險
＋FP-safe（T2 掃 automate.js 13 版零 FP）**，非已兌現複利；B2/B3 restore-best/liveness＝stub 驗證的
失敗保險（真跑未觸發）。**過閘≠淨效益**——r9/B8/B11 標二次瘦身佇列。

錨：implementation-notes.md T2/效益分層段。

### audit-liveness canary（drift gate）＋跨 tier 掃描 null result（2026-07-20）

承 D6/D8「畢業一次性 semantic 判官是機械層關不完 Goodhart 的必要 backstop」。本節加一個**運行時**問題：那個 semantic 判官**這一輪**還可信嗎？——verifier 可被 executor 污染、機械綠可假、共識盲區（審計最貴的失敗是「以為解了」不舉手，truth-verify c-020）。

**技術實作等價物＝`loop_wiki/drift_audit_gate/`**（閘零件，**同 `oracle-gate.sh` 是單檔閘、非被迭代的小迴圈**）。定位＝**oracle-gate 的運行時兄弟**：oracle-gate 判「這 task-type 有沒有可信神諭」（靜態先驗，dense/sparse/blind），drift gate 判「這一輪的 audit judge 對【已知飄移】還抓不抓得到」（動態）。機制＝把 §3 的 planted-defect 檢出率從「設計期一次性」提升為「運行時週期抽樣」：人預先播 sealed drift 探針（`probes/{drifted,clean}/` + `_sealed/ledger.tsv`，答案 audit 不可見），judge 判探針產 verdicts，`scripts/drift-detection-rate.sh` 純 shell 比對 sealed、漏放（miss）或誤殺（false_alarm）超容忍 → exit 2。tier 切分同 §「tier 邊界重申」：探針設計＝人/Opus 一次性；judge 判＝fresh judge；檢出率計算＝零 LLM shell；SURFACE＝engine.sh 機械。selftest positive-control：good（完美審計）=PASS ∧ hollow（全判 CLEAN=共識盲區）=FAIL，證閘有鑑別力。**engine 接線點**＝上圖大迴圈引擎的 oracle-gate「判官每 K 輪引擎外跑」處（畢業前置或週期），**不硬接**（改核心引擎＝人 admit；一旦硬接，下一個懶惰念頭「讓 LLM 自動填 ledger/探針」＝越 Layer-3 自生目標線，閘自我空心化，探針與 sealed 答案永遠人播種）。

**跨 tier × 跨家族真跑（10 judge × 3 家族，端到端非推論）**：同一因果倒置探針（p07：數字/來源/範圍全對，只把 gap-01 CRITICAL「verifier 必須隔離」倒成「共用 git 工作區」）＋ clean 對照，跨 Claude（Agent model override：Fable/Opus/Sonnet/Haiku）× GPT（codex CLI `-m … -c model_reasoning_effort`：gpt-5.5 xhigh/high、gpt-5.4 medium、gpt-5.4-mini medium）× Gemini（agy `--print --model`，**完整 model 名「Gemini 3.1 Pro (High)」/「Gemini 3.5 Flash (High)」，非「gemini」**）。**detection = 10/10（1.0）、false-alarm = 0/4；tier 效應未出現。**

三條證偽結論（自我修正，改本檔通則）：
1. **sealed ledger 對強 judge 冗餘（非「抓 judge 抓不到的」）**：連 gpt-5.4-mini（無 CLAUDE.md 被動上下文、最弱檔）都靠第一性推理抓到因果倒置；Claude 家族更靠 CLAUDE.md Path B「無 primary URL＝Half-Bridge」checklist 抓到（兩條不同路都到 DRIFT）。對付飄移的主力是「fresh zero-context judge + 內化 Path B」，泛化性強過 sealed ledger（抓到未播種類型）。
2. **canary 重定位＝judge-liveness 信號，非 capability/飄移偵測主力**：tier 掃描唯一的 judge 失效不是「弱 tier 漏 subtle」（十 tier 沒一個因笨而漏），是 **Opus agent 一次執行故障**（tool_uses=0、2 秒、回注入式亂碼，根本沒讀檔；重跑才正常）。canary 該抓的是「judge 這輪根本沒在判」（壞/被劫持/環境故障），不是「judge 太笨」。**防誤改：別把 drift gate 當「飄移偵測主力」升級**——真跑證它對這批 tier 冗餘，它的價值窗口窄（只在 judge 退化到無推理/被壓垮 CoT/被劫持時）。
3. **設計真 c-020 subtle 探針需「設計者推理優勢壓過判官」**（truth-verify 教訓活證）：單一 Fable 設計者對這十個 judge 都不具此差，做不出騙過 gpt-5.4-mini 的探針。故本次 null result **不證 canary 無效，證這批探針 × 這些 tier 下盲區不發生**；要找觸發 tier 需要推理強過 judge 的設計者造探針，超出單設計者能力。

**agy judge 副產物（修正 memory 過度概括）**：agy 1.1.4 `--print "<prompt>" --model "<完整名>" < /dev/null` 對判斷型 prompt 可正常回應（本次 Gemini Pro/Flash 各判皆回 VERDICT，非 silent-no-op）；命門＝完整 model 名含 tier 括號（`--model gemini` 直接報錯）。舊「判斷型 silent-no-op」部分是 model 名/語法錯（`--print` 吃值旗標、prompt 須緊跟）。與全景圖不變量 5「agy=Gemini only、生產判官永遠 session 內 Opus」不衝突：本次 agy Gemini 是**tier 掃描的實測 judge**，非生產迴圈判官。

錨：`loop_wiki/drift_audit_gate/README.md`「真跑實測」節（含 tier 表 + 三發現）＋ selftest.sh（good=PASS∧hollow=FAIL 綠）＋ judge 判決 `scratchpad/judge-verdicts.tsv`。

---

*本檔＝evals 設計方法論（D8 裁決類，Opus/Fable 設計）；與 antigravity-harness-wiki 記錄層不重疊。*
