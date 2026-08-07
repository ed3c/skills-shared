# AGENTS.md — bettor-arena(Codex 讀取面薄入口)

工程 SSOT＝`ARCHITECTURE.md`:放置契約=§2、鐵律全文=§3。規則原文只住那裡,本檔禁複述,
只留 Codex/跨 host 專屬入口:

- 啟用:`sh bootstrap.sh`(冪等;doctor+相對 hooksPath)。
- skill 內容單份住 `.agents/skills/`(host-neutral 家;.claude/skills 全 symlink 指向它)。
- `.codex/config.toml` 僅可攜 MCP 宣告;host 段(permissions/network/sockets)人補後才可信。
- commit 前:§3 鐵律 2 的 T0 閘;落新檔前:§2 槽位對映。

---

## 工程法則的實證歸屬 (Rule → Evidence Routing)

全局 `~/.claude/CLAUDE.md` 的工程法則不直接指向迴圈目錄——法則層綁死在某個 repo 的
目錄結構上，迴圈改名即斷。**本節是那一跳的落點**：法則指到這裡，這裡指到擁有實證的 Harness。

骨架、各節硬性要求與零網路註冊檢查 → `ix-agy/.agents/modules/agents-md-template.md`

| 法則主題 | 實證 Harness |
|---|---|
| _待填：本 repo 擁有哪一條法則的實證_ | _待填：Harness 路徑 ＋ 該處的可觸發內容摘要（訊號→動作→為何有效）_ |

<!-- 自動偵測到的 Harness（1 個），填表時逐個確認是否擁有法則實證： -->
<!--   loop_wiki/evolve-perfect-seed-repo-factory -->
