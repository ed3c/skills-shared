# AGENTS.md - ix-agy (Antigravity Meta-Repository)

> **Format**: Vercel AGENTS.md Standard v3.0 (Antigravity Adapted) · **Purpose**: Passive context injection for AI coding agents (Antigravity CLI)

## Project Overview

**ix-agy** is the central meta-repository and Harness for the `subproject-ixsecurity-e2e` integration, fully migrated to the Antigravity CLI standard. It orchestrates the End-to-End testing and diagnostic infrastructure across multiple iOS, Android, and server components.

| Attribute | Value |
|-----------|-------|
| Tech Stack | Python 3.11+, Bash, TypeScript, Antigravity CLI |
| Primary Runtime | Apple Silicon (macOS) |
| Core Skill | `subproject-ixsecurity-e2e` |

## Sub-Project Associations

This repository is tightly coupled with and orchestrates the following workspaces:
1. **TrueMe_iOS** (`/Users/neon/TrueMe_iOS`): Main iOS Client.
2. **TrueMe_Android** (`/Users/neon/TrueMe_Android`): Main Android Client.
3. **ixsecurity** (`/Users/neon/ixsecurity`): Backend microservices.
4. **ixsecurity-samples** (`/Users/neon/ixsecurity-samples`): Sample applications.
5. **ix-spec-runner** (`/Users/neon/ix-spec-runner`): iOS SDK Living Specification (provides `ios-test-automation`).
6. **test_automation_ai** (`/Users/neon/test_automation_ai`): Android Agentic AI Testing (provides `android-test-automation`).
7. **loop_wiki/subproject-ixsecurity-e2e** (`/Users/neon/ix-agy/loop_wiki/subproject-ixsecurity-e2e`): Modularized nested loops sandboxes (D2 mode, No Free Coffee Agora room, APNs/ECDSA, Android, Parity checking).

---

## Antigravity Harness Configuration

> **Modularized Section**: Please refer to `.agents/modules/harness-config.md` for the single source of truth regarding MCP servers, Skills, and Problem Graph directory structures.
> **Loop Composite Map & Anti-Simplification Gate**: Please refer to [antigravity-harness-wiki](file:///Users/neon/ix-agy/.agents/skills/antigravity-harness-wiki/SKILL.md) for the overarching Loop Engineering roadmap (Big Loop vs. Mini-Loops). **任何變更皆嚴禁簡化已實裝的閉環架構，且嚴禁拷貝/複製 prompt 以免造成双图漂移（提示詞 SSOT 單一真源守則）。**

- **Config Path**: `.agents/mcp.json`
- **Skills Path**: `.agents/skills/`
- **Claude Skill Forwarders**: `.claude/skills/<name>/SKILL.md`（零邏輯，只指向同名 canonical skill）；
  `.claude/commands/delivery.md` 僅保留 `/delivery` 相容別名。
- **Mini-Loop Sandboxes**: Each workspace subproject or loop in `loop_wiki/` implements the 8-Harness standard with its own CWD isolation, EAGER execution rules, and page-specific tests in `.agents/skills/[skill_name]/tests/[page]/[function]/verify.sh` to prevent functional regression.

---

## Code Style Conventions

### Python
- Type hints for all public functions; PEP 8, line length 100
- Docstrings: Google style
- Test naming: `test_<function>_<scenario>`

### Shell Scripts
- Use `set -euo pipefail` at start
- Quote all variables: `"$var"`
- Use absolute paths (no `cd` commands)

### Markdown
- Chinese preferred for documentation
- Use YAML frontmatter for agents
- Anchor points format: `ANCHOR-XXX-NNN`

---

## Operation Boundaries

### Never
- Modify `.env` or credentials files
- Force push to main branch
- Delete `.git` directory
- Modify system files outside project
- Modify files under '/Users/neon/TrueMe_iOS' (Must remain 100% pristine under all circumstances)
- 絕對不能修改後端服務（`ixsecurity/auth52-service` 等 Go 代碼），後端應保持 100% pristine。

> 其餘操作邊界（Allowed Operations／Confirmation Required 細則）→ [.agents/modules/operation-boundaries.md](.agents/modules/operation-boundaries.md)

---

## Available Skills & Triggers

| Skill | Strength | Triggers |
|-------|----------|----------|
| **test-driven-development** | **CRITICAL** | "TDD", "test driven" |
| **systematic-debugging** | **CRITICAL** | "debug", "error", "bug" |
| **verification-before-completion** | **CRITICAL** | "verify", "complete" |
| **subproject-ixsecurity-e2e** | STRONG | "ixsecurity E2E", "iOS / 2FA / push" |
| **problem-graph-indexer** | STRONG | "problem graph", "解法路由" |
| **antigravity-harness-wiki** | STRONG | "harness 全景", "多迴圈 SSOT", "迴圈組合" |
| **loop-harness-standard** | STRONG | "八大基座", "迴圈工程", "hooks.json", "settings.json" |
| **repo-wiki-converge** | STRONG | "wiki 收斂", "Gemini 判官", "Opus 收斂" |
| **repo-agent-native** | STRONG | "不變量抽取", "source-anchored", "隱含依賴" |
| **judge-loop-chooser** | STRONG | "驗證路由", "三態 grounding", "獨立性階梯" |
| **fold-in** | STRONG | "fold-in", "經驗折疊", "Resolved 帳本" |
| **loop-harness-review-handoff** | STRONG | "迴圈審查交接", "Fable 5 review", "fresh-session 獨立審計", "八大基座 review" |
| **ios-testflight-ship** | STRONG | "TestFlight", "上架", "fastlane", "iOS archive", "Any iOS Device" |
| **ios-simulator-automation** | STRONG | "iOS 模擬器", "idb", "simctl", "模擬器自動化", "OOBE 自動化", "權限彈窗" |
| **html-for-decisions** | STRONG | "決策儀表板", "HTML for decisions", "email bundle", "Markdown 打包寄送", "quiz 閘" |

## MCP Tools Index
> SSOT = [.agents/modules/harness-config.md](.agents/modules/harness-config.md)（MCP servers／Skills／Problem Graph 目錄結構規範，本節不存副本）。

## Sovereignty
> 主權分層架構（L2 Access Rules／Axiom Summary）→ [.agents/modules/sovereignty.md](.agents/modules/sovereignty.md)

## Subproject Loops (大小迴圈設定與執行規範)
### 觸發與啟動詞 (Triggers)
* **全域大迴圈 (Big Loop)**: `"run global composite loop"`, `"執行全域大迴圈"`, `"harness 全景"`, `"執行大迴圈"`
* **特化沙盒小迴圈 (Small Loops)**: `"run subproject sandbox loop"`, `"執行子項目沙盒小迴圈"`, `"d2-e2e-loop"`, `"no-free-coffee-loop"`, `"apns-ecdsa-loop"`, `"android-e2e-loop"`, `"parity-check-loop"`
* **方法論迴圈 (Methodology Loops)**: `"抵達方式"`, `"業務不變量真相"`, `"靜態綠燈但實際壞掉"`, `"invariant 被推翻"`, `"invariant-reach-graph"`
> 泛用執行程序（設定 Prompt→啟動 Harness→驗證狀態→經驗折疊）→ [loop-harness-standard modules/harness-spec.md §6](.agents/skills/loop-harness-standard/modules/harness-spec.md)

### 工程法則的實證歸屬 (Rule → Evidence Routing)
全局 `~/.claude/CLAUDE.md` 的工程法則不直接指向迴圈目錄——法則層綁死在某個 repo 的目錄結構上，迴圈改名即斷。**本節是那一跳的落點**：法則指到這裡，這裡指到擁有實證的 Harness。

| 法則主題 | 實證 Harness |
|---|---|
| 多態型別要驗生產端／綠燈值多少看抵達／觀察對象與待證對象要同源／要記得的事綁到共用出口／量測工具的綠燈也是宣稱 | [invariant-reach-graph](loop_wiki/invariant-reach-graph/.agents/skills/invariant-reach-graph/SKILL.md) — 方法論在 `modules/`，逐案實證在 `domain/`，兩者由該 SKILL.md 串連且不得合併 |
| OOBE／REOOBE 金鑰素材覆寫的 Android domain 事實 | [android_e2e_loop soft-key-vault-overwrite](loop_wiki/subproject-ixsecurity-e2e/android_e2e_loop/.agents/skills/android-e2e-loop/modules/soft-key-vault-overwrite.md) |
| 送進一次性資源前先驗素材形狀／搜不到不等於不存在 | [android_e2e_loop email-voip-registration-ceremony §11](loop_wiki/subproject-ixsecurity-e2e/android_e2e_loop/.agents/skills/android-e2e-loop/modules/email-voip-registration-ceremony.md) |
| 自動化操作與測試腳本住在它驗證的那個 Harness 內 | [android_e2e_loop/scripts/](loop_wiki/subproject-ixsecurity-e2e/android_e2e_loop/scripts/) — OOBE 真機驅動四支（`activate-r2-account.py`／`capture-r2token.sh`／`realdevice-oobe-drive.sh`／`realdevice-force-oobe-drive.sh`），2026-08-08 自 `ixsecurity-samples/scripts/` 遷入；`.r2tokens.env` 由 `**/.r2tokens.env` 擋在版控外 |

## Resolved Issues & Gotchas
> 已依 fold-in doctrine (B) 全遷至 owner modules（00:F-13/F-17 SSOT 收斂，2026-07-10）；索引與無主教訓全文 → [.agents/modules/resolved-ledger.md](.agents/modules/resolved-ledger.md)
