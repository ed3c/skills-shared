# AI Content Note / AI 內容筆記庫

> **繁體中文**：以私有 GitHub Markdown 取代 Google Docs 作為卡片盒筆記的 canonical storage。  
> **English**: Private GitHub Markdown is the canonical storage for the card-based AI content notes; Google Docs remain read-only legacy artifacts.

## Canonical paths / 正式路徑

- Notes / 筆記：[`notes/`](notes/)
- Note index / 筆記索引：[`INDEX.md`](INDEX.md)
- Trigger context and implementation stacks / 專有名詞觸發與落地技術堆疊：[`CONTEXT.md`](CONTEXT.md)
- Open-source ranking / 開源庫評分排行：[`RANK.md`](RANK.md)
- Operating parameters / 執行參數：[`docs/OPERATING_PARAMETERS.md`](docs/OPERATING_PARAMETERS.md)
- Ingestion contract / 收錄契約：[`docs/INGESTION_CONTRACT.md`](docs/INGESTION_CONTRACT.md)
- Citation and asset mapping / 引用與技術資產 mapping：[`docs/CITATION_MAPPING.md`](docs/CITATION_MAPPING.md)
- Google Docs migration map / Google Docs 遷移映射：[`docs/MIGRATION_MAP.md`](docs/MIGRATION_MAP.md)
- Note schema / 筆記 metadata 契約：[`schemas/note-frontmatter.schema.md`](schemas/note-frontmatter.schema.md)

## Storage rule / 儲存規則

**繁體中文**

1. 新筆記直接提交到 default branch；筆記不建立 feature branch。
2. 每篇筆記是一個 Markdown 檔，分類存放於 `notes/<category>/`。
3. Google Sheet 的筆記 URL 必須指向 private GitHub blob URL，不得再建立新的 Google Doc。
4. Google Docs 只保留為 legacy archive；不刪除，直到 checksum、內容與 Sheet URL 全部驗證。
5. 每個技術觀點必須能 mapping 到 `code / llm-model / data / trajectory` 至少一類技術資產。

**English**

1. New notes are committed directly to the default branch; note ingestion does not create feature branches.
2. Each note is one Markdown file under `notes/<category>/`.
3. Google Sheet note URLs must point to authenticated private GitHub blob URLs; new Google Docs are prohibited.
4. Google Docs are retained as a legacy archive until content, checksum, and Sheet URL migration are verified.
5. Every technical claim must map to at least one asset class: `code`, `llm-model`, `data`, or `trajectory`.

## Validation / 驗證

```bash
python3 ai-content-note/scripts/validate_notes.py ai-content-note
```

The validator checks required frontmatter, duplicate IDs and canonical URLs, score bounds, path integrity, and accidental primary Google Docs URLs.
