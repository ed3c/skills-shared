# decision-report.prompt：ix-agy 決策面生成契約

> 本檔是內容編排契約。Markdown 是 SSOT；本 prompt 只允許投影，不允許新增裁決。

## 輸入

- Markdown SSOT：`{{SOURCE_DOCS}}`
- 快照日期：`{{SNAPSHOT_DATE}}`
- Bundle config：`{{CONFIG_PATH}}`
- 輸出 HTML：`{{OUTPUT_PATH}}`

## 角色鐵律

1. 你是投影者，不是判官；每個結論都要能回指 Markdown。
2. 預判、已裁決、Release-reachable、Deployed 必須分開。
3. 沒有 deployment receipt 時固定寫 `Deployed=UNKNOWN`。
4. 頁面必含「本頁為投影非 SSOT」、快照日期與理解 quiz。
5. 零外部資源；inline CSS／JS，CJK 用系統字型。

## Section schema

| # | Section | 必填內容 |
|---|---|---|
| S0 | Masthead | 標題、投影宣告、快照、checked SHAs |
| S1 | 裁決 | 已裁／待裁與人類裁決來源 |
| S2 | Evidence boundary | Release-reachable／Deployed／runtime 三態 |
| S3 | 關鍵風險 | 只列 SSOT 已證風險，附文件指針 |
| S4 | 資料流 | 現況與黃金目標分開，不混圖 |
| S5 | 文件目錄 | config 列出的所有 Markdown，附 SHA-256 |
| S6 | 完整文件 | 逐份完整顯示，不只摘要 |
| S7 | Quiz | 5 題，對準最重判定；全對只代表理解就緒 |
| S8 | Footer | source config、重生命令、投影宣告 |

## 執行

優先使用 deterministic renderer：

```bash
python3 .agents/skills/html-for-decisions/scripts/package_markdown_email.py {{CONFIG_PATH}}
python3 .agents/skills/html-for-decisions/scripts/check_decision_html.py {{OUTPUT_PATH}}
```

renderer 不會自行推論摘要；先把忠於 Markdown 的 `decision`、`summary`、`documents`、`quiz` 寫入 config。checker exit 0 前不得宣稱完成。
