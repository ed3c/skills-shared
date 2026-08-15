# HOST-SURFACES — 兩個 host 到底讀哪些檔、依什麼順序、在哪裡會靜默失效

> 每一格都由官方文件錨定，日期＝2026-08-08 查證。**沒有 URL 的斷言不寫進本檔**；
> 版本會動，過期的作法是重查這幾支 URL，不是憑記憶修。
> 來源：
> [Claude Code · memory](https://code.claude.com/docs/en/memory) ·
> [Claude Code · settings](https://code.claude.com/docs/en/settings) ·
> [Codex · AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md.md) ·
> [Codex · advanced config](https://learn.chatgpt.com/docs/config-file/config-advanced)

## 1. 指令文件（context 層）

### Claude Code

由**廣到窄**載入，**全部串接進 context，不互相覆蓋**；同一目錄內 `CLAUDE.local.md` 排在 `CLAUDE.md` 之後。

| 範圍 | 路徑（macOS） | 備註 |
|---|---|---|
| Managed policy | `/Library/Application Support/ClaudeCode/CLAUDE.md` | 個人設定**無法排除**；也可改用 managed settings 的 `claudeMd` 鍵直接內嵌 |
| User | `~/.claude/CLAUDE.md`、`~/.claude/rules/*.md` | rules 早於 project rules 載入 |
| Project | `./CLAUDE.md` **或** `./.claude/CLAUDE.md`、`.claude/rules/*.md` | 兩個位置等價，擇一 |
| Local | `./CLAUDE.local.md` | 個人用，要進 `.gitignore` |

- 從 cwd **往上**逐層走，沿路每個目錄的 `CLAUDE.md`／`CLAUDE.local.md` 都在啟動時整份載入；**cwd 底下**子目錄的則等 Claude 真的讀到那裡的檔案才載入。
- `@path/to/file` import：相對路徑以**含 import 的那個檔**為基準，可遞迴，**最多四跳**。反引號包起來的 `` `@x` `` 不觸發 import。
- **project 層 CLAUDE.md 內指向 cwd 之外的 import＝external import**，第一次會跳核准對話框；拒絕後就永久停用且不再詢問。user 層的 import 不跳。
- `.claude/rules/*.md` 可用 frontmatter `paths:` 做路徑作用域，只有讀到匹配檔案才進 context。
- **Claude Code 不讀 `AGENTS.md`。** 官方兩種接法：CLAUDE.md 內寫 `@AGENTS.md`，或 `ln -s AGENTS.md CLAUDE.md`。
- 驗證載入了什麼：session 內 `/context` 看 **Memory files**；要逐項日誌用 `InstructionsLoaded` hook。

### Codex

| 順位 | 路徑 | 備註 |
|---|---|---|
| 1 | `$CODEX_HOME/AGENTS.override.md`，缺則 `$CODEX_HOME/AGENTS.md`（預設 `~/.codex`） | 該層只取**第一個非空**的 |
| 2..n | 專案根 → cwd 每一層的 `AGENTS.override.md` → `AGENTS.md` → `project_doc_fallback_filenames` | **每個目錄最多取一個檔** |

- 由根往下串接；**越靠近 cwd 的越晚出現，因而覆蓋較早的指引**。
- 沒有「關閉」開關；臨時替換用 `AGENTS.override.md`，刪掉它就恢復。

## 2. 設定（強制層）

### Claude Code `settings.json` — 高到低

1. Managed settings：`/Library/Application Support/ClaudeCode/managed-settings.json`（及 `managed-settings.d/*.json`、`com.anthropic.claudecode` managed preferences）
2. 命令列參數（`--settings` 等）
3. `.claude/settings.local.json`（repo 內，gitignored）
4. `.claude/settings.json`（repo 內，進版控）
5. `~/.claude/settings.json`

**例外：permission 規則是跨層「合併」而不是覆蓋**；`claudeMdExcludes` 陣列同樣跨層合併。`claudeMd` 鍵只有 managed／policy 層生效。

### Codex `config.toml` — 高到低

1. CLI `-c` / `--config`
2. profile
3. **專案層 `.codex/config.toml`**（自專案根走到 cwd，沿路每一個都載入）
4. `~/.codex/config.toml`
5. 內建預設

**專案未被信任時，整個專案 `.codex/` 層（config、hooks、rules）被忽略。** 專案層也不能覆寫 provider 認證、憑證轉址、profile 選擇這類安全敏感項。

## 3. 兩種衰減，機制不同，別混成一句「檔案別太長」

| host | 機制 | 官方原文要點 | 徵狀 |
|---|---|---|---|
| Codex | **靜默截斷** | 合併總量到 `project_doc_max_bytes`（預設 **32 KiB**）就停止加入後續檔案 | 尾端整段**不存在**於 context，而模型與你都不會收到任何訊息 |
| Claude Code | **遵循度衰減** | CLAUDE.md「一律整份載入，不論長度」，但「較短的檔案遵循度較好」，建議每檔 <200 行 | 內容在 context 裡，但被照做的機率下降 |

推論：`~/.codex/AGENTS.md` 是那 32 KiB 的**第一位消費者**——全局法則寫胖，代價是專案根 AGENTS.md 的尾巴被吃掉。這就是「法則層砍到判準＋校準＋一行實例」不是文風偏好，是預算紀律。

## 4. 最強的一條：context 不是強制層

官方原文：Claude 把這些檔案「當作 context，不是 enforced configuration」；要**不論模型怎麼判都擋掉**某個動作，得用 **PreToolUse hook**。

所以：**任何寫成「必須／絕不」的規則，若指不出一個真的會紅的出口（hook、T0 閘、型別、CI），它就只是願望。** 這是「每個呼叫端都要記得的事，綁到它們已共用的那個出口」在 host 層的落點——差別在這裡連「呼叫端」都是模型的注意力，比人更不可靠。

判準（給範例文件用）：

| 想寫的東西 | 落點 |
|---|---|
| 無條件擋掉某動作／某路徑 | `settings.json` 的 `permissions.deny`、PreToolUse hook |
| 每次 commit／每次編輯後必跑 | hook（不是 CLAUDE.md 的一句「請記得」） |
| 判準、取捨、校準門檻 | CLAUDE.md／AGENTS.md（context 本來就該放這個） |
| 只在某類檔案適用的規則 | `.claude/rules/*.md` ＋ `paths:` frontmatter（省預算） |
| 多步驟程序、只在特定任務要 | skill（按需載入，不佔每次啟動的預算） |
