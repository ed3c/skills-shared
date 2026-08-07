# Module: repo-agent-native — 抽取方法論 know-why(S2.5 破盒推論 / OPBE / Evidence Level)

> 屬 [`repo-agent-native`](../SKILL.md)。Layer B：SKILL.md 只留確定性程序 ＋ pointer，深度推理框架寫這裡(progressive loading，被選中前不載)。

## Evidence Level 為何這樣分(污染傳播直覺)

北極星原理：一個事實的**證據來源**決定它能不能被下游當事實傳播。A→A 安全；D→any 高風險(用一個沒源碼支撐的猜測去推別的結論 = 幻覺鏈)。antigravity 無機器污染矩陣，但**直覺不變**：抽取時每步問「這是我讀到的(A)、追蹤到的(A-)、語義命中的(B+)、還是我在猜(C/D)」。C/D 進頁面只能標 `inferred`／`unverified`，不能寫成 `INV-xxx [A]`。這就是 source_ref 鐵律的認識論理由——沒有 `檔：行`，你不知道自己在傳播事實還是幻覺。

## S2.5 破盒推論五步(完整框架)

觸發：S2 Pass 4 的 `outgoing-calls` 出現 `indexed: false` 的 callee，或某服務行為無法從已讀源碼解釋。核心原則：**你讀了服務 A 的源碼，但 A 呼叫了 B；B 的行為／前提／失效模式是 A 的「隱含依賴」，不在 A 的源碼裡。破盒推論＝主動從已知事實推導它們。**

1. **未索引服務識別**：對每個 `indexed:false` callee 分類 —— `INTERNAL_SERVICE`(同生態另一 repo，可再索引→排下輪 S1) / `EXTERNAL_INFRA`(DynamoDB/APNS/NATS-server/Redis，不可索引→用協議規格推論) / `AMBIGUOUS`(需讀更多源碼)。
2. **共享狀態耦合偵測**：關鍵問「這服務讀了什麼資料？誰寫的？」——找 DB **read** 而非 write。輸出 `coupling`：store／table／writer(service+fn+Evidence)／reader(service+field+Evidence)／`temporal_constraint`(如 registration 必須先於 push)／`failure_mode`(如 gopush 讀到 stale BundleId → 錯 APNS 路由 → 靜默逾時)。
   - **DB-mediated Routing 子模式**：`getApiKey(domain, apiName)` 且 `apiName` 由 request param 算 → 不同 apiName → 不同 DB row → 不同 config → **完全不同的 runtime 驗證行為**。標 `IMPL-DB-xxx`，未查 DB 前 Evidence=C。
3. **靜默失敗鏈推導**：對每個 fire-and-forget／async 呼叫問三題 —— Q1 呼叫者收到的 success 是否代表端對端成功(APNS 200＝接受，非投遞成功)？Q2 若靜默失敗，哪個 timeout 先觸發？Q3 該 timeout 可觀測嗎(log/metric/trace)？
4. **逾時鏈推導**：每個 timeout 常數的值由什麼外部 SLA 隱性決定？寫 `implicit_bound`(如 `AUTH52_NATS_TIMEOUT + gopush_latency + user_response < ASYNC_MESSAGE_TIMEOUT`)。
5. **循環依賴檢查**：「函數庫在服務 A，但執行路徑從服務 B 觸發」→ 可能 B→A HTTP 呼叫 / A 是 gateway / 共享 module(code reuse 非 runtime dep)。讀觸發點源碼定案。

每條隱含依賴：`id`／`type`／`callee`／`known_facts`(帶 Evidence)／`inferred_prerequisites`／`silent_failure_chain`／`resolution_status`(UNRESOLVED 需索引 callee 才升 CONFIRMED)。

## OPBE(Optional Param Branch Exhaustion) — 為何 Pass 3 不夠

Bug Scar 教訓：handler 的 `const { email, password, serviceType, ... } = req.body` 中**每個 optional param 都可能是 routing key**，觸發完全不同代碼路徑／DB lookup／驗證邏輯。只讀 endpoint＋required params＝漏掉成功／失敗分支。

OPBE 三步：① ripgrep `req\.body|const {.*} = req\.` 列**所有** param；② ripgrep 所有 `if/switch` 對這些 param 的判斷；③ 追某 param 到下游(如 `apiName` → `getApiKey`)。輸出每個 routing param 的 value → {apiName, authPath, verifiedCheck, db_dependency, Evidence, source_ref}。

**四個盲點(北極星 blackhorse login post-mortem，防護內建)**：
| 盲點 | 根因 | 防護 |
|------|------|------|
| 只讀失敗路徑 | 從錯誤往上找，未從 handler 往下枚舉全部分支 | OPBE 強制枚舉 |
| optional param 被忽略 | 假設 request body＝`{email,password}` 是完整 spec | 讀 destructuring 列 ALL params |
| 常數未關聯 handler | `const xxxServiceType` 在檔頂、不在 handler 附近 | 檔頂常數掃描 |
| DB routing 不可見 | `getApiKey(apiName)` 的 DB 行為差異讀不出 | 標 IMPL-DB-xxx，Evidence=C 直到查 DB |

## 8 條 implicit-design probe(Codebase Design Mastery，推理紀律)

對「完全掌握」型抽取，除了不變量還問 8 個設計決策問題(⟂ S2.5 的隱含**依賴**，這 8 條問**設計決策**)：seam(邊界在哪) / determinism(哪裡確定性、哪裡機率) / platform(平台假設) / bounded-loop(迴圈有界嗎) / trust(信任邊界) / ergonomics(誰用、怎麼用) / typed-errors(錯誤型別化嗎) / framework-idiom(沿用框架慣例嗎)。每個答案同樣要 `source_ref`。

**雙重 Evidence-Level 教訓(gotcha)**：grep-dist-chunk ＋ 單次觀察能 **OBSERVE** 失敗，但**不足以 ATTRIBUTE** root-cause——歸因要回源碼。而 behavior/perf claim 連源碼讀＋窄 probe 都會 over-reach——這類要**完整真跑(RIP)** 才定案。鐵律：歸因要回源碼；behavior/perf 要真跑，別靠靜態讀腦補。

## Empty-Output 為何 fail-loud

北極星 Bug Scar #339：`invariants: []` 空殼靜默進 KB = silent Half-Bridge，下游把「沒抽到」誤讀成「沒有不變量」。防護：0 產出時**必**寫 `extraction_failure_reason`，SURFACE 標 `EMPTY_FAILED`。這是 Path B 紀律的實例——沒有確定性鐵錨(至少 1 個帶 source_ref 的不變量)就不可宣稱抽取成立。
