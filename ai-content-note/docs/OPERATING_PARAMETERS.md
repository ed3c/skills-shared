# Operating Parameters / 執行參數

| Parameter | Value | 說明 / Description |
|---|---|---|
| `storage_backend` | `private-github-markdown` | GitHub Markdown 是 canonical；Google Docs 只讀 legacy。 |
| `repository_full_name` | `ed3c/skills-shared` | Current writable private repository. |
| `repository_root` | `ai-content-note/` | Isolated namespace for the knowledge base. |
| `target_dedicated_repository` | `ed3c/ai-content-note` | Move target when repository-creation access exists. |
| `branch_policy` | `direct-default-branch` | 筆記不建 branch、不開 PR；直接更新 default branch。 |
| `sheet_id` | `1i1y4116id0l-CFYR0g1wPbYYMr6bAU18I85yOAcaG0M` | Ranking and orchestration state. |
| `run_schedule` | `daily ~09:00 Asia/Taipei` | 每日約 09:00。 |
| `max_sources` | `50` | 最多 50 個來源。 |
| `max_items_per_source` | `300` | 每來源最多 300 筆。 |
| `notes_per_source_per_run` | `1` | 每來源每次最多一篇新筆記。 |
| `update_mode` | `incremental-newest-first-then-backfill` | 先最新，再向舊內容回溯。 |
| `dedupe_keys` | `canonical_url + content_id + github_path` | 禁止重複筆記。 |
| `source_text_requirement` | `full-text-or-transcript` | 不得只依摘要或搜尋片段。 |
| `note_prompt` | `v6.6-cyberpunk` | Intelligent Compression OFF; One Case, One Card. |
| `note_url_scheme` | `https://github.com/<owner>/<private-repo>/blob/<default>/<path>` | Sheet 寫 authenticated private blob URL。 |
| `legacy_doc_policy` | `retain-read-only` | 遷移完成後不再更新 Google Docs；暫不刪除。 |
| `required_languages` | `zh-Hant + English` | Governance and parameter documents are bilingual. |

## Write transaction / 寫入交易

1. Read Sheet state and dedupe keys.
2. Fetch full source text.
3. Generate v6.6 cards.
4. Write one Markdown note and metadata.
5. Commit directly to default branch.
6. Verify private blob URL.
7. Replace Sheet note URL and update status/time.
8. Append execution log.

Any failure before step 6 leaves the Sheet URL unchanged. / 第 6 步前失敗，不得修改 Sheet URL。
