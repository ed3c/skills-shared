# Note Frontmatter Schema / 筆記 Frontmatter 契約

Required keys / 必填：

- `id`: stable content ID; unique.
- `title`
- `source_name`, `source_type`, `source_url`, `canonical_url`
- `published_at`: `YYYY-MM-DD`
- `monetization_score`: integer `1..100`
- `monetization_modes`
- `note_status`: `completed | blocked | pending`
- `note_version`: currently `v6.6-cyberpunk`
- `language`: `zh-Hant`
- `technical_terms_language`: `en`
- `categories`: primary and secondary category.
- `mapping_targets`: subset of `code`, `llm-model`, `data`, `trajectory`.
- `github_path`: must equal the repository-relative file path prefixed by `ai-content-note/`.
- `legacy_google_doc_id`, `legacy_google_doc_url`
- `citation_mapping_status`: `pending | partial | complete`

The Markdown body starts after the closing `---` and contains only v6.6 cards.
