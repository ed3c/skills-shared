# Module: repo-fullstack-debugger — L2 雙象限診斷 know-why

> 屬 [`repo-fullstack-debugger`](../SKILL.md)。Layer B：SKILL.md 只留確定性程序 ＋ pointer，象限推理框架寫這裡。

L2 的核心：**別重造推理引擎，選對象限集**。目標決定用哪一組四象限——瀏覽器失敗用 site-debugger 原生的 Bot/Timing/Selector/Auth，repo 執行失敗用 `repo-agent-native` 的 S2.5 四象限。兩組是**同構的**(都在問「失敗的黑盒事實屬哪一類」)，這就是本 skill 能同時接兩種協作者的原因。

## A. 瀏覽器象限(Bot / Timing / Selector / Auth)

上游的 `automate.js`「Resolved」帳本(AGENTS.md)是這四象限的**實據庫**——每條已解失敗先比對，命中就直接載入已知修法，別重新探索。

| 象限 | 失敗簽名(上游實例) | 診斷起手 | 已知修法錨 |
|------|---------------------------|---------|-----------|
| **Bot**(反自動化偵測／soft-block) | Google headless soft-block；DR 模式對某 query 回「having a hard time fulfilling」；YouTube 純文字 URL `CONNECTION_LIMITED` | 換 headed／換附件路徑；`planRefusedCheck` 早退重試 | AGENTS.md DR 拒絕條、`aistudio-youtube-embed` 附件路徑 |
| **Timing**(race／未 render 完就找／protocolTimeout) | DR item 還沒 render 完就被找 → `dr_not_found`；`protocolTimeout < waitForFunction` → CDP timeout；固定 timeout 誤砍長輸出 | 輪詢等 render(N×間隔)＋整段重試；停滯感知輪詢(非固定 timeout)；`protocolTimeout` 放寬 | AGENTS.md protocolTimeout 條、停滯感知輪詢條 |
| **Selector**(DOM 漂移／被側欄劫持) | finder 用 document 全域 `.find()` 被左側欄歷史對話劫持；DR toggle 從頂層移進「更多工具」子選單 | **所有 finder 限定在 composer(`input-area-v2`)＋彈出選單(`.cdk-overlay-container`)內**，結構隔絕側欄；chip 鐵錨驗收 | AGENTS.md DR-enable 側欄劫持條 |
| **Auth**(額度枯竭／登入態) | 3.5 Flash 每日額度枯竭 vs DR 啟用 flaky 誤判停 run | 唯讀開模式挑選器截圖確認 `Flash`(活) vs `Flash-Lite`＋額度訊息(枯竭)；「gap 失敗但主 DR 成功」≠ 枯竭 | AGENTS.md 額度枯竭誤判條 |

**鐵律**：瀏覽器象限的 root-cause 判別錨是**失敗簽名文字 ＋ live DOM**，不是「字數短／慢」等間接徵狀(那些會誤判——如把 AI Studio 生成截斷當短影片、把思考期 len=0 當卡住)。

## B. repo 執行象限(S2.5 四象限，重用 repo-agent-native)

當協作者是 `repo-agent-native` 的抽取撞 runtime-only 黑盒(源碼讀不出的行為)，用它的破盒推論四象限：

| 象限 | 問題 | 診斷起手 |
|------|------|---------|
| **未索引服務**(Unindexed Service) | 服務 A 呼叫的 B 沒被索引，B 的行為/前提不在 A 源碼裡 | 分類 INTERNAL(可再索引) / EXTERNAL_INFRA(協議規格推論) |
| **共享狀態耦合**(Shared State Coupling) | 「這服務讀了什麼？誰寫的？」——DB read 而非 write | 找 DB read；temporal_constraint；failure_mode |
| **靜默失敗鏈**(Silent Failure Chain) | 200 但實際沒成功，下游哪個 timeout 先觸發、可觀測嗎 | fire-and-forget 三問(端對端成功？哪 timeout？可觀測？) |
| **逾時鏈**(Timeout Chain) | timeout 常數的值由什麼外部 SLA 隱性決定 | 從已知 timeout 推 implicit_bound |

框架細節見 `repo-agent-native/modules/extraction-methodology.md` §S2.5(單一 SSOT，本表只指路由)。

## 為何 L0 閘對兩象限都必要(反 167-line-static 反例)

site-debugger 原文的警告：**大多數失敗其實有一條便宜確定性的路，只是被錯過了**。167 行靜態 HTML 被當黑盒過度工程＝反例。L0 就是把「便宜確定性可解」和「真黑盒必迭代」分開的閥門——瀏覽器象限尤其容易 over-engineer(一次 `read_console_messages`＋一次 DOM 抓取常就給 A 級答案，別急著開 5 輪迴圈)。L4 讓「真黑盒」那類只付一次探索代價(編譯成 playbook → fold-in)。
