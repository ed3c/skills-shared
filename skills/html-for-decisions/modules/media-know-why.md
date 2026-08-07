# Module: html-for-decisions — know-why（媒介、email 邊界、md＝源）

> 屬 [`html-for-decisions`](../SKILL.md)。SKILL.md 有確定性程序＋不變量；本檔＝為何這樣。
> 各 repo 自己的 lineage、worked instance 與移植取捨在該 repo 的 `.skill-bindings/html-for-decisions/`。

## 1. 三受眾媒介矩陣（為何 HTML 只給決策節點）

| 受眾 | 媒介 | 資訊特徵 | 典型落點 |
|---|---|---|---|
| 代理自身 | Markdown for itself | 帳本／迭代軌跡／implementation-notes | 工作沙盒的計劃檔、失敗軌跡目錄 |
| 人類協作者 | Markdown for you | 表格／代碼塊，快速掃描 | README、changelog、慣例文件 |
| 關鍵決策節點 | **HTML for decisions** | 富交互＋quiz，高決策密度 | 決策儀表板、畢業 quiz、人閘佇列視覺化 |
| 外部收件人 | EML 摘要＋HTML／ZIP 附件 | 郵件本文可立即讀，完整證據不受 client 裁切影響 | 跨團隊交接包 |

**HTML 稅**：HTML 產出／維護成本高於 Markdown 一個量級。只有「等人裁」的節點，決策密度才值回這個
稅——過程報告用 HTML＝把稅付在沒有決策的地方。這是判準不是偏好：頁面目的是「裁」→ HTML；是
「讀」→ Markdown。

## 2. 為何 md＝源、HTML＝投影（Markdown-as-Code 自反）

markdown 檔是系統源代碼、其餘皆生成物——這個形套用到決策面：判定／裁決的 SSOT 永遠在對應的 md
檔，HTML 是事件式重生的投影。反向（在 HTML 側改判定）＝製造會漂的第二真相。頁面自帶「非 SSOT」
宣告＋快照日期＝投影的誠實標記。

這條順序被真實走過一輪：儀表板產出 → 人裁 → 裁決先回填計劃 md → 再重生 HTML 佇列狀態。重生成本
≈編輯數個 section＋checker 一次，遠低於重寫，這是「事件式更新而非定期更新」策略成立的原因。
**注意這是機制曾被驗證過的信心，不等於你這個 repo 已經驗證過**——各 repo 第一次真走完一輪人裁
回填，才是本地的吸收成立錨。

## 3. quiz 閘為何綁在決策面上

quiz 測「人」的理解就緒度——merge／admit 前全對才過，強制人腦留在知識環內。放進決策面而非獨立文
件，是因為兩者服務同一個節點：裁決需要理解，理解閘與裁決佇列同頁＝一次交互完成。題庫對準載荷最
重的判定（完成率來源、驗證器隔離命門、判官分頻這類），形式題＝假閘。

## 4. 為何郵件不能只塞完整 HTML

常見郵件客戶端會：移除 JavaScript、改寫 CSS、阻擋 HTML 附件、裁切大型郵件本文。

因此交付拆成三層：摘要作 MIME `text/html` body、完整單檔 HTML 作附件、HTML＋Markdown＋manifest
再封 ZIP。這不是重複三份 SSOT；它們都由同一 config 與 Markdown 重生。

## 5. 決策面與 renderer 的分工

`package_markdown_email.py` 只做確定性轉換、附件與 checksum，不做語意判決。決策摘要與 quiz 由
config 顯式提供，且必須能回指 Markdown。需要重新組織決策內容時可使用 prompt 契約，但仍要先把定案
寫回 Markdown。

## 6. 觀測面與決策面為何必須分家

觀測面是腳本從 log／狀態檔機械投影出來的東西，它的共同紀律（缺一即漂向決策面）：零 LLM 確定性
渲染、無 quiz 機件、非 SSOT 宣告、`--as-of` 外部傳入禁系統時間、`--selftest` 合成正控。

**機器帳 pattern**：板子要投影「規格」（決策規則／心跳／方案）時，不解析散文 md——把規格的機器
可讀形收進一份 state JSON（SSOT 仍是散文檔，JSON＝數值與規則的投影層），板子只讀 JSON。理由：md
解析脆（改寫散文＝板子壞），雙檔分工＝散文給人、JSON 給板，兩者同步由發佈紀律保證。

**禁投影假數**：若為版面美觀補假數字，等於在自己的證據鏈上先破一個洞——null →「未上線（N/A）」
不是 UI 缺陷，是證據紀律在投影端的延伸。

## 7. Mermaid 降級

自包含且 email-safe 的前提下，不載入 Mermaid CDN。Markdown 的 Mermaid fence 會以 code block 顯
示，資料不丟失但不宣稱已圖形化。若日後要 inline SVG，應另加 deterministic renderer 與測試，不得
偷偷引入網路依賴。
