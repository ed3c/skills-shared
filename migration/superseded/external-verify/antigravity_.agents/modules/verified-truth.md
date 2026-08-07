# Module: 已查證真相 — Google Antigravity 設定檔 / skill 規範

> 屬 [`external-verify`](../SKILL.md) skill。本檔 = 跑 runbook(SKILL.md 6 步)的**產出快照**。
> ⚠ 這是**會過期的快照**(cc-20260625)。復用前重跑 SKILL.md step 1-2,以官方當下文案為準。

## 已查證真相表

| Claim | 判定 | 信心層 | 鐵錨 |
|-------|------|--------|------|
| canonical 專案設定檔 = **`AGENTS.md`**(大寫);skills 放 **`.agents/skills/`** | ✅ 真 | **CONSENSUS(primary)** | Gemini API doc 原句:"mount files like `AGENTS.md` for instructions and skills under `.agents/skills/`" |
| skill 規範 = **`<name>/SKILL.md` 目錄封裝 + `description` frontmatter(必填,trigger phrase)、`name` 選用** | ✅ 真 | **CONSENSUS(primary)** | 官方 codelab「Getting Started with Antigravity Skills」。詳見 [`antigravity-skill-authoring`](../../antigravity-skill-authoring/SKILL.md) |
| skill scope:專案 `.agents/skills/` · 全域 `~/.gemini/config/skills/` · CLI `~/.gemini/antigravity-cli/skills/` | ✅ 真 | CONSENSUS(primary) | 同上 codelab |
| Antigravity 是真實 agentic 平台(public preview) | ✅ 真 | CONSENSUS(primary) | Google Developers Blog |
| **`GEMINI.md` 存在**(至少 `~/.gemini/GEMINI.md` 全域規則) | ✅ 真 | HARD-SECONDARY | gemini-cli GitHub **Issue #16058** |
| `agents.md` / `skills.md` 概念真實 | ✅ 真 | HARD-SECONDARY | 官方 Codelab 標題 |
| 「官方並沒有 GEMINI.md 這種規範」 | ❌ **假** | — | 被 Issue #16058 直接推翻 |
| `SKILL.md` frontmatter 含 `license/version/tools/metadata` | ⚠ 未證 | FRONTIER-CONTESTED | 那是更廣 Agent Skills 開放標準欄位,Antigravity codelab 未列 |
| 優先序「AGENTS.md → GEMINI.md → defaults」、「2.0 standalone / 預設 Gemini 3.5 Flash」 | ⚠ 未證 | FRONTIER-CONTESTED | 僅見 SEO 聚合摘要,primary 未證實 |

## Sources（★ = primary）
- ★ Antigravity Agent — Gemini API: `https://ai.google.dev/gemini-api/docs/antigravity-agent`
- ★ Getting Started with Antigravity Skills — Codelabs: `https://codelabs.developers.google.com/getting-started-with-antigravity-skills`
- ★ Build with Google Antigravity — Developers Blog: `https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/`
- gemini-cli Issue #16058(`~/.gemini/GEMINI.md` 衝突): `https://github.com/google-gemini/gemini-cli/issues/16058`
- 官方 docs 入口(JS app,WebFetch 未渲染出內文): `https://antigravity.google/docs/skills`
