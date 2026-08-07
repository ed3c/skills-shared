# html-for-decisions：媒介與 email 邊界

## 三種受眾

| 受眾 | 媒介 | 原因 |
|---|---|---|
| Agent／工程師 | Markdown | diff 友善、可搜尋、可作 SSOT |
| 人類裁決者 | 自包含 HTML | 高決策密度、表格、目錄與 quiz 同頁 |
| 外部收件人 | EML 摘要＋HTML／ZIP 附件 | 郵件本文可立即讀，完整證據不受 client 裁切影響 |

HTML 維護成本高於 Markdown。只有人閘或正式交接值得付這個成本；普通進度報告保持 Markdown。

## 為何 Markdown 是源

本 repo 的 source、invariant、PRD 與裁決都以 Markdown 版控。HTML 是事件式投影：它可以被刪除後重生，不能承擔獨有結論。頁面上的「本頁為投影非 SSOT」與快照日期，就是防止雙圖漂移的誠實標記。

## 為何郵件不能只塞完整 HTML

常見郵件客戶端會：

- 移除 JavaScript；
- 改寫 CSS；
- 阻擋 HTML 附件；
- 裁切大型郵件本文。

因此交付拆成三層：摘要作 MIME `text/html` body、完整單檔 HTML 作附件、HTML＋Markdown＋manifest 再封 ZIP。這不是重複三份 SSOT；它們都由同一 config 與 Markdown 重生。

## 決策面與 renderer 的分工

`package_markdown_email.py` 只做確定性轉換、附件與 checksum，不做語意判決。決策摘要與 quiz 由 config 顯式提供，且必須能回指 Markdown。需要重新組織決策內容時，可使用 prompt 契約，但仍要先把定案寫回 Markdown。

## Mermaid 降級

自包含且 email-safe 的前提下，不載入 Mermaid CDN。Markdown 的 Mermaid fence 會以 code block 顯示，資料不丟失但不宣稱已圖形化。若日後要 inline SVG，應另加 deterministic renderer 與測試，不得偷偷引入網路依賴。

## Lineage

核心機制來自一份外部 Claude skill 的唯讀快照；來源 repo 名稱與本機絕對路徑依交付脫敏規則不落盤。本 repo 的技術遷移差異見 [retarget-map.md](retarget-map.md)。
