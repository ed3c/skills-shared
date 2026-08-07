@AGENTS.md

# CLAUDE.md — `<repo>`（Claude host 專屬尾巴）

<!-- 由 forgejo-delivery-loop 集中管理。SSOT = agent-docs/<repo>/CLAUDE.md。
     直接改 repo 內這份會被 `agent_docs.py check` 判 DRIFT；改 SSOT 再 apply。 -->

> **為什麼是一行 import 而不是第二份內容**：Claude Code **不讀 `AGENTS.md`**，官方給的接法
> 就是在 CLAUDE.md 內寫 `@AGENTS.md`（或 `ln -s AGENTS.md CLAUDE.md`）。用 import 的話
> 內容只有一份，兩個 host 讀到的必然一致——**雙圖漂移在結構上不可能發生**，不必靠誰記得同步。
> 錨：[code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)。
> 代價要知道：import 的檔案照樣整份進 context，省的是漂移不是預算（HOST-SURFACES §3）。
>
> 若本 repo 選擇不 import（例如 Claude 面與 Codex 面刻意分岔），把理由寫在這裡，
> 並在 AGENTS.md §9 登記「兩份如何保持同步」的那個會紅的出口。**沒有出口就別分岔。**

## 本檔只放 Claude Code 專屬的東西

上面 import 進來的 AGENTS.md 是跨 host 的全部內容。以下只寫**換一個 host 就不成立**的事：

- **強制層**：`.claude/settings.json` 的 hook 清單 → `<列出哪幾個 hook、各擋什麼>`。
  規則要不論模型怎麼判都成立，就寫在這裡指到的 hook，不是寫成本檔的一句「必須」。
- **按需載入**：多步驟程序放 skill，不放本檔——skill 只在被觸發時才佔預算。
  路徑作用域的規則放 `.claude/rules/*.md` ＋ frontmatter `paths:`，只有讀到匹配檔案才進 context。
- **個人層**：`<repo>/CLAUDE.local.md`（要進 `.gitignore`）；跨 worktree 共用個人偏好請改用
  `@~/.claude/<file>.md` import，因為 gitignored 的 local 檔只存在於它被建立的那個 worktree。
- **驗載入**：session 內 `/context` 看 **Memory files** 清單。
  **本檔有沒有被讀到，是可查證的事實，不是可以假設的事。**

## 落檔前

新目錄／新檔案先對映 `<SSOT>` 的槽位契約；無槽位＝先改契約再落檔。
T0 閘：`<placement gate 指令>`。
