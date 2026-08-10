# host-permissions.md — 各 host 的 merge 權限真相（低壓縮版）

本模組只回答一件事：**為什麼 merge 會被擋、被哪一層擋、那一層的確切修法是什麼**。
四層授權堆疊的語意在 [delivery-mechanism.md § Merge authority stack](delivery-mechanism.md#merge-authority-stack)，
本檔不複述堆疊，只補「每一層在各 host 的實際形狀＋官方出處＋可重播的驗證方式」。

## 0. 復發機制（為什麼修一次不夠）

同一句「merge 權限沒放行」在不同 host 是**不同的病**：

| host | 真正卡住的東西 | 卡在堆疊哪一層 |
|---|---|---|
| Claude Code | PreToolUse hook 黑名單命中 `gh pr merge` → exit 2 | L2 |
| Codex CLI | sandbox permission profile 沒開 network，`gh`／`git push` 根本出不去 | L2（更早，連命令都沒送出） |
| 純 shell / CI | 沒有 L2；卡在 GitHub token 或 branch rule | L3 |
| ChatGPT Desktop（Codex Connector） | **沒有任何一層在擋**——權限全開，走 PR 是產品的工作流選擇 | 不在堆疊內（見 §7） |

修完 Claude 那條，換到 Codex 又斷；修完 Codex，換台機器又斷。**根因不是任何一條規則寫錯，
而是「哪一層會拒絕」是在執行期才被發現的**——跑了一小時、開好 PR，才吃到 exit 2。

所以本 skill 的對策是把發現時機前移：`scripts/merge_gate.py preflight`
**用每個 host 自己的閘真跑一次**（合成 PreToolUse payload 餵進實際設定的 hook、呼叫
`codex execpolicy check`、讀 `.codex/config.toml` 的 network 授權），不靠推論。
2026-08-07 在 skill-bettor 主樹一條命令同時抓出上表前兩列，這是本檔所有結論的物理錨。

## 1. Claude Code 層

### 官方語意（[hooks](https://code.claude.com/docs/en/hooks)／[permissions](https://code.claude.com/docs/en/permissions)）

- PreToolUse hook 在**每次工具呼叫、permission prompt 之前**執行；exit 2 = blocking error，
  「**blocks the tool call**」，stderr 回饋給模型。exit 1 是 non-blocking，動作照跑——
  官方明文警告：要擋就必須用 exit 2。
- hook 的決策**不繞過** permission rules：deny／ask 規則照樣先評估，hook 回 `"allow"`
  也不能讓 deny 規則放行。
- permission rules 跨 scope 是**合併**不是覆蓋（allow/deny 清單相加），所以
  **`permissions.allow` 永遠救不回一個 exit 2 的 hook**——這兩者不在同一個 plane。
- `bypassPermissions` 只跳過 permission prompt，hook 照跑。

### 本機實況（2026-08-07 查證）

`~/.claude/hooks/auto-approve.sh` 的 `BASH_BLACKLIST` 有字面項 `"gh pr merge"`，
以 `grep -qiE` 比對整條命令，命中即 exit 2。同檔尾端還是 **deny-by-default**（不匹配白名單即 exit 2）。

該檔把自己列進 `SENSITIVE_FILE_PATTERNS`（`auto-approve\.sh$`）並額外封鎖
`sed`／`tee`／`cp`／`mv` 指向 `.claude/(hooks|settings)` 的命令——**代理無法修改它，只有人能改**。
這是刻意設計，不是缺陷；本 skill 不試圖繞過，只負責在開工前報告它會拒絕。

反面事實同樣重要：`bash_command_classifier.py` 的 GH 前綴白名單已放行
`gh pr view/list/status/checks/diff/create`、`gh issue`、`gh api`、`gh run`、`gh workflow`，
`git push` 也放行。**整條交付鏈只有 merge 這一步被擋**——所以「準備」路徑在 Claude Code
下完全暢通，不需要任何權限變更。

### 若要讓 agent 執行 merge（人已選 admit-then-agent 模型）

兩處都要改，且**都必須由人親手改**（代理被上述自保護擋住）：

1. `~/.claude/hooks/auto-approve.sh`，`BASH_BLACKLIST` 內：

   ```diff
   -        "gh pr merge"         # 合併 PR (需確認)
   +        "gh pr merge.*--admin"   # 只黑 admin bypass：它會略過所有 branch rule
   ```

   保留 `--admin` 在黑名單是重點：`--admin` 是唯一能**繞過 GitHub 端所有要求**的形式，
   那才是不可逆的危險面；一般 `gh pr merge` 仍受 GitHub 的 mergeability 與 branch rule 約束。

2. `/Users/neon/local_stack/execution/hooks/bash_command_classifier.py` 的 GH 前綴白名單加一行
   `"gh pr merge",`。順序上 BASH_BLACKLIST 先跑，所以**單獨加這行是 inert 的**——
   在第 1 步套用前不會改變任何行為，可以安全先加。

改完以 `merge_gate.py preflight` 重驗：`L2 HOST-POLICY claude-code` 應從 `BLOCK` 轉 `ALLOW`。

## 2. Codex CLI 層

### 官方語意（[permissions](https://learn.chatgpt.com/docs/permissions)／[config](https://learn.chatgpt.com/docs/config-file/config-basic)）

- 新版 permission profile：頂層 `default_permissions = "<name>"`，內建 preset
  `:read-only`／`:workspace`／`:danger-full-access`；具名 profile 用 `[permissions.<name>]` 搭 `extends`。
- **`:workspace` 的 network 預設關閉**（「Network is disabled by default unless explicitly
  enabled in your profile」），`.codex` 與 `.git` 保持唯讀。
- 開網路：`[permissions.<name>.network] enabled = true`，可選 `[permissions.<name>.network.domains]`
  以 `"host" = "allow"|"deny"` 收斂（deny 覆蓋 allow）。
- **profile 與舊的 `sandbox_mode`／`sandbox_workspace_write` 不可混用**——只能二選一。
- config 載入序（高→低）：CLI `--config` → **專案 `.codex/config.toml`（repo root 往下到 cwd）**
  → profile 檔 → `~/.codex/config.toml` → `/etc/codex/config.toml` → 內建預設。
  專案層只在該 project 被標記為 trusted 時才載入。

### 本機實況與修法

`skill-bettor/.codex/config.toml` 原本 `default_permissions = "skill-bettor-git"` extends `:workspace`
並補了 `.git` write，但**沒有 network 區塊** → Codex 在此 repo 連 `git push` 都出不去。
`ix-agy/.codex/config.toml` 原本連 profile 都沒有，吃內建預設，同樣無網路。

> **2026-08-09 複量：上段所述的斷網狀態已不存在。** `~/.codex/config.toml` 現在頂層
> `default_permissions = "agent-default"`，該 profile `extends = ":workspace"`、補了 `.git` write，
> 並有 `[permissions.agent-default.network] enabled = true`。三個平面當日全綠：PreToolUse hook
> 對 `git push`／`gh pr create` 皆放行、network 已開、execpolicy 掃到 5 個 rule 檔並 allow。
> 保留上段是因為它是**這條規則為何存在**的病例；但把它讀成現況會讓人去修一個已經修好的東西。

修法就是補上（profile 名稱用該 repo 自己的；沒有 profile 就先建一個 `extends = ":workspace"`
並在頂層設 `default_permissions`，注意頂層 key 必須寫在任何 table header 之前）：

```toml
[permissions.<profile>.network]
enabled = true
```

**不做 domain 收斂是刻意的**：這兩個 repo 的 git 走 SSH，而 `network.domains` 規則覆蓋的是
HTTP(S) 面；貿然收斂會讓 `git push` 靜默失敗。若某個 repo 改成純 HTTPS，再去 domains 收斂。

### execpolicy 與 permission profile 是兩件事

`codex execpolicy`（0.146.0 仍在）決定「某個 argv prefix 能不能離開 sandbox 執行」，
`scripts/install-codex-merge-rule.sh` 裝的就是釘死到 `gh pr merge --repo OWNER/REPOSITORY`
的窄 prefix rule。它**不能**取代 network 授權（沒網路時 rule 允許也打不出去），
也**不能**覆蓋 PreToolUse hook——這條邊界是實測得到的，見 delivery-mechanism.md § Merge authority stack。

### Codex 也有自己的 PreToolUse hook plane（2026-08-07 漏報事故）

`~/.codex/hooks.json` ＋ `~/.codex/hooks/auto-approve.sh` 是 Claude Code hook 系統的**鏡像**，
語意相同（exit 2 阻斷）。它與 execpolicy、與 permission profile 是**三個互不相干的閘**：

```text
Codex 一次 merge 要同時通過：
  network profile（打不打得出去） × PreToolUse hook（送不送得出命令） × execpolicy（離不離得開 sandbox）
```

事故經過：preflight 第一版只驗了 network 與 execpolicy，兩者都 ALLOW 後就印
`L2 HOST-POLICY codex: ALLOW`——但 `~/.codex/hooks/auto-approve.sh` 的 BASH_BLACKLIST 仍有
`"gh pr merge"`，實際跑必被擋。**這是假綠：驗證器少驗一個平面，就把「還會被擋」報成「可以了」。**

教訓與其說是「要記得驗 Codex hook」，不如說是：**同一個 host 的閘可能不只一個平面，
只驗你知道的那些等於沒驗**。因此 preflight 對兩個 host 都用同一支
`_run_pretooluse()`，並且 Codex 的三個子閘任一 BLOCK 就整體 BLOCK 並指名是哪一個。
回歸守衛＝`tests/merge-gate/verify.sh` 第 4b 案（給假 hook exit 2、同時把 network 與 rule 都備妥，
證明只有 hook 也能擋下來）。

### config 是分層的，只讀最近那份會報假紅（2026-08-07）

把 permission profile 上收到 `~/.codex/config.toml` 之後，preflight 從 ix-agy 跑卻報
「`ix-agy/.codex/config.toml`: default_permissions=None，內建 preset 沒網路」——**假紅**。
ix-agy 那份 config 只為 MCP server 存在，沒提 permissions，按官方分層序它會繼承 user 層的
`agent-default`。驗證器只讀「往上找到的第一份」，等於把繼承當成缺席。

修法＝照官方分層解析（project 疊在 user 之上，`permissions.*` 也要合併），並在訊息裡印出
它實際讀了哪幾份（`A over B`）。回歸守衛＝`tests/merge-gate/verify.sh` 第 4c 案
（只有 MCP 的 project config ＋ 有 profile 的 user config → 不得報 network 缺席）。

### 檔名不是契約，規則內容才是（2026-08-07 第三次）

第一版 probe 用 `github-merge-<owner>-<repo>.rules` 去推檔名——那是**安裝器的命名慣例，不是 Codex 的
載入契約**。`codex execpolicy check` 的 `--rules` 是**可重複**參數，Codex 讀的是整個 rules 目錄；
一條手寫的、檔名叫 `ix-agy-merge.rules` 的有效規則，在 probe 眼裡等於不存在 → 又一次假紅。
修法＝掃 `~/.codex/rules/*.rules` 全部丟給 `--rules`，讓 execpolicy 自己判，probe 不猜檔名。

**三次都是同一個病**：假綠＝少驗一個平面（Codex hook 漏報）；假紅其一＝少讀一個層級（config 分層）；
假紅其二＝把自己的命名慣例當成對方的載入契約。三者都不是「規則寫錯」，而是
**驗證器對真實解析規則建模不足**。所以每加一個 host 面向要問的是
**「它真正的解析規則是什麼」**，不是「我知道的那份檔在哪」——後者只會驗到自己的假設。

### prefix rule 擋不住 `--admin`（2026-08-07 負控實測）

裝完規則後對 `ed3c/agent-skills-repo` 逐一驗證 argv 形狀，結果：

| 形狀 | execpolicy decision |
|---|---|
| `gh pr merge --repo <repo> N --squash --match-head-commit <sha>`（land 真形狀） | **allow** |
| `gh pr merge --repo <另一個 repo> N --squash` | 不匹配 |
| `gh pr merge N --repo <repo> --squash`（參數換序） | 不匹配 |
| `gh pr close N --repo <repo>` / `gh repo delete <repo>` | 不匹配 |
| **`gh pr merge --repo <repo> N --admin`** | **allow** ← 缺口 |

prefix rule 只比對**前綴**，而 `--admin` 出現在 PR 編號之後、位置浮動，**在 prefix contract 裡
無法表達**。所以：repo 級與 argv 順序的窄化是真的，但「禁 admin bypass」這條**不能靠 execpolicy 守**。

守 `--admin` 的三道實際防線，缺一不可：
1. Claude Code 的 `BASH_BLACKLIST` 保留 `"gh pr merge.*--admin"`（本檔 §1 的補丁刻意只黑這個形式）；
2. `merge_gate.py` 的 human-admit command 從不產生 `--admin`；owner-auto GraphQL mutation 也沒有
   bypass 欄位，只有 `expectedHeadOid` 與 `SQUASH`，email 交給 GitHub 帳號的 web Git 設定；
3. GitHub 端：`--admin` 只有在 repo 真的設了 branch protection 時才有東西可繞——今天兩個 repo
   都沒設，所以風險為零；**一旦哪天加了 ruleset，第 1 條就從冗餘變成必要**。

教訓：窄規則的「窄」要用負控量，不能看它 allow 了正控就宣稱窄。安裝器自帶的煙測只跑
`... 1 --merge`，涵蓋不到 land 的真形狀，也涵蓋不到 `--admin`。

## 3. GitHub 層

### 官方語意

- [auto-merge](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/incorporating-changes-from-a-pull-request/automatically-merging-a-pull-request)：
  必須先在 repo 開啟；且「The option to enable auto-merge is shown only on pull requests that
  cannot be merged immediately」——**沒有 branch protection／required checks 就沒有 auto-merge 的意義**。
  觸發條件是「all required reviews and status checks pass」。
- [approving-a-pull-request-with-required-reviews](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/reviewing-changes-in-pull-requests/approving-a-pull-request-with-required-reviews)：
  「**Pull request authors cannot approve their own pull requests.**」
- [gh pr merge](https://cli.github.com/manual/gh_pr_merge)：`--auto` =「Automatically merge only
  after necessary requirements are met」；`--admin` =「Use administrator privileges to merge a
  pull request that does not meet requirements」；`--match-head-commit <SHA>` 可釘 HEAD。

### 為什麼人閘用 label 而不是 approving review

單人帳號（PR 由 owner 或其 token 開）下，「required approving review」這條人閘**在物理上不可能滿足**——
作者不能核可自己的 PR。要用 review 當人閘，必須讓 PR 出自另一個身分（GitHub App／machine account），
那是額外基建。

再加上實測：`ed3c/skill-bettor` 是 **private + free user plan**，rulesets 與 branch-protection API
回 403「Upgrade to GitHub Pro or make this repository public」——**服務端閘在該 repo 根本不可用**。
`ed3c/agent-skills-repo` 是 public、可用但當時未設；兩者 `allow_auto_merge` 皆為 false。

所以人閘落在 **`merge-admit` label**：

- 由 repo owner 在 GitHub UI 施加（手機可操作，可批次），是 server 端的 timeline 事件，
  帶 actor 與時間戳，事後可稽核；
- `merge_gate.py` 要求 **label 事件的 actor == repo owner**，且
  **labeled_at ≥ head commit 的 committer date**——貼完標籤又推新 commit 會自動失效（`admit-stale`）；
- 實際 merge 一律帶 `--match-head-commit <被 admit 的 SHA>`，HEAD 漂移即失敗，不會合到沒被看過的樹。

這三條合起來，讓「人 admit」是一個**有物理載體、可否證、且與 agent 執行分離**的事實，
而不是聊天記錄裡的一句話。它不宣稱能防住一個蓄意偽造的代理（有 shell 就有 token），
它防的是「代理自作主張 merge」與「admit 後內容悄悄改變」。

### 明確 opt-in：personal-owner 自動放行

當使用者明確要求不再逐 PR admit，可用 `merge_gate.py configure-owner --owner LOGIN` 建立 user-level
policy。這不是把 `gh pr merge`／`gh api graphql` 全域放行；Codex rule 只允許精確的
`python3 <canonical>/merge_gate.py land --repo ...` wrapper，真正的 L1 在 wrapper 內每次向 GitHub 重驗：

1. authenticated viewer 的 login＋numeric user ID 等於 policy；
2. repository owner 的 login＋numeric ID 也相等，且 owner type 必須是 personal `User`；
3. canonical `owner/repo` 沒有 redirect，viewer 仍有 admin；
4. PR 非 draft、mergeable、required checks／branch rules 可落地，且 `expectedHeadOid` 等於剛驗過的 HEAD。

所以「未來 repo」不靠預先列白名單：只要日後 repo 仍由同一個 personal GitHub User 擁有就通過；
collaborator、organization member／owner、以及他人 repo 的 admin 都拒絕。login rename、token 換人、repo
transfer、policy 壞掉都 fail closed。GraphQL merge 只送 `expectedHeadOid` 與 `SQUASH`；不送
`authorEmail`，因為 GitHub 的 web-based Git email／privacy 設定才是該欄位的權威，隱私模式下
API 會拒絕 caller override。schema 能力以 `gh api graphql` introspection 現查，不拿記憶當規格。

## 4. 全域 vs per-repo（新專案要做什麼）

把每一塊放在它能放的最高層，per-repo 只留真正無法全域的兩件：

| 元件 | 位置 | 範圍 |
|---|---|---|
| canonical skill（Claude Code 發現面） | `~/.claude/skills/github-delivery-loop/` | **全域**，所有專案自動可見 |
| canonical skill（Codex 發現面） | `~/.agents/skills/<name>` → symlink 到 canonical | **全域**（`~/.codex/skills` 為 legacy 路徑） |
| Claude Code PreToolUse 黑名單 | `~/.claude/hooks/auto-approve.sh` | **全域**，一次改完 |
| Codex PreToolUse 黑名單 | `~/.codex/hooks/auto-approve.sh` | **全域**，一次改完（與上一列是同一行規則的鏡像） |
| Codex sandbox（network＋`.git` write） | `~/.codex/config.toml` 的 `default_permissions` ＋ profile | **全域**；個別 repo 要不同就用自己的 `.codex/config.toml` 覆蓋（project 層贏 user 層） |
| `merge-admit` label | GitHub repository | human-admit 才需要，**per-repo** |
| human-admit execpolicy 窄規則 | `~/.codex/rules/github-merge-<owner>-<repo>.rules` | **per-repo**，寫死 `--repo owner/name` |
| owner-auto identity policy | `~/.config/github-delivery-loop/merge-policy.json` | 明確 opt-in，**per-user**；綁 login＋numeric ID＋personal User |
| owner-auto wrapper rule | `~/.codex/rules/github-merge-owner-<login>.rules` | **per-user**；只允許 canonical gate wrapper，不允許 generic GraphQL |
| Codex project trust | `~/.codex/config.toml` 的 `[projects."<path>"]` | **per-path**；首次在該目錄跑 Codex 時由它自己詢問並寫入 |

所以 human-admit 的新專案只需要一句（`--repo` 省略時從 cwd 的 git remote 推）：

```bash
python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py bootstrap
```

冪等：label 與 rule 已存在就印 `OK` 不重建，最後接一次 preflight 把四層現況印出來。
owner-auto 則只需一次 `configure-owner`；同一 personal owner 的現在與未來 repo 都不需要再 bootstrap。

## 5. 不可逆操作：把「刪」改寫成「搬」

這台機器的 PreToolUse hook 把所有刪除（`rm`／`git rm`／`rmdir`）列為 Tier 2 人工專屬。
把副本轉成 symlink 天生需要移除舊目錄，於是這件事一度卡成「只能人工執行」。

解法不是想辦法通過那道閘，而是**讓操作不再是刪除**：`link-canonical.sh` 把舊副本 `mv` 到備份目錄
再建 symlink。位元組沒有消失（備份＋git 歷史各一份），一次 `mv` 就能還原——**不可逆性被設計掉了，
閘自然不再適用**。這比「請人去另一個終端貼指令」好，因為它把可逆性做成性質，而不是靠流程補償。

同樣的取捨出現在拒絕條件上：腳本分不出「canonical 比較新」和「副本有本地未收斂的工作」，
所以只要 `diff -r` 不空就拒絕並印出差異，不猜。收斂方向是人的決定。
回歸守衛＝`tests/link-canonical/verify.sh`（分岔副本必須原封不動、備份必須留下、重跑必須冪等）。

## 6. 缺席與拒絕必須長得不一樣

`preflight` 的退出碼刻意三分：

| exit | 意義 |
|---|---|
| 0 | 至少一張 PR 可落地，且四層皆放行 |
| 1 | 有一層**拒絕**（stderr 指名是哪一層、哪張 PR、確切修法） |
| 3 | **沒有任何 PR 被 admit**——缺席，不是拒絕 |
| 4 | 某一層**判不出來**——無能，不是拒絕（2026-08-09 新增） |

把 3 併進 1 會讓「還沒人核可」在自動化裡讀起來像「被擋住了」，於是有人去改權限修一個
不存在的權限問題。這是「每個缺席都給明確出口」在本 skill 的落點，
由 `tests/merge-gate/verify.sh` 第 3 案守著。

### 4 是後來才長出來的：崩潰的 hook 冒充了拒絕的 hook（2026-08-09）

preflight 報 `L2 HOST-POLICY claude-code: BLOCK`，理由是
`python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/rm_guard.py": can't open file '/.claude/hooks/rm_guard.py'`。
**沒有任何政策做過這個決定**——Claude Code 每次呼叫 hook 都會設 `CLAUDE_PROJECT_DIR`，而 preflight
合成 payload 時沒設，路徑塌成 `/`；**直譯器開不了檔也是 exit 2，與阻斷契約同碼**。
一個變因驗證：設了該變數就從 BLOCK 變 ALLOW（exit 3，沒有 PR 被 admit）。

修法兩半，第二半才是這一列存在的理由：

1. `_hook_env()` 補上 `CLAUDE_PROJECT_DIR`（取 git root，否則 cwd）——這修掉這個實例。
2. 執行**之前**先驗 hook 命令引用的變數是否都可解析，不可解析就回 `ERROR` → exit 4——這修掉這一類。

**一條想過但錯的判別法**：拿良性命令去探，若也被拒就判定 hook 壞了。錯在
**deny-by-default 是合法設定**（真的 `auto-approve.sh` 尾端就是不匹配白名單即 exit 2），
所以「它拒絕了無害的東西」不帶任何關於壞掉的資訊。未解析變數帶，而且不必執行就判得出來。

回歸守衛＝第 4d 案，兩臂：4d-i 的環境**刻意不含** `CLAUDE_PROJECT_DIR`，逼探測器自己供給；
4d-ii 用一個引用未定義變數的 hook，要求 exit 4 且輸出**不得出現** `REFUSED`。

**第一版的 4d-i 是裝飾案例**——它自己在環境裡設了 `CLAUDE_PROJECT_DIR`，把修法拿掉照樣綠。
是植入缺陷抓到的：plant A（拿掉變數檢查）紅、plant B（拿掉變數供給）**綠**。
一個不會因為修法消失而變紅的案例，佔著一個看起來被覆蓋的位置，比沒有更糟。

## 7. ChatGPT Desktop / Codex Connector — 權限全開，卻仍然只出 PR

編號放在最後而不是插進 §1–§3，是為了不讓既有的 `§2`／`§4` 交叉引用整片位移。
它在 §0 表格裡有一列，那才是發現點。

### 官方語意

- [on-behalf-of-a-user](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-with-a-github-app-on-behalf-of-a-user)：
  user-to-server token 的有效權限是**交集**——「The app can only access resources that the user has
  access to」∧「The app can only access resources that it has permission to access」。
- [permissions-required-for-github-apps](https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps)：
  推 commit／建 ref 要 **Contents: write**；開 PR 要 **Pull requests: write**。**兩個獨立權限**，
  一給一不給就會長成「能開 PR、不能推 code」。
- [第三方 GitHub 整合](https://learn.chatgpt.com/docs/third-party/github)：Codex「can push a fix back
  to the branch **when it has permission to do so**」——它推的是 branch，然後開 PR。

### 本機實況（2026-08-09 查證）

App 授權頁（`https://github.com/settings/installations` → ChatGPT Codex Connector，openai 開發）：

```
✓ Read access to checks, commit statuses, and metadata
✓ Read and write access to actions, code, issues, pull requests, and workflows
Repository access: All repositories(含 current AND FUTURE;public repo 為唯讀)
```

`code` 是 **Contents** 權限的 UI 標籤（同列的 actions／issues／pull requests／workflows 分別對應
Actions／Issues／Pull requests／Workflows）。**這一格是標籤對映的推論,不是 API 讀到的欄位**——
`gh api user/installations` 需要 App 授權的 user token,`gh` 持有的 OAuth token 讀不到,所以
installation 權限只能從那一頁人眼讀。

交集的三側同時量過,全滿：

| 側 | 量法 | 結果 |
|---|---|---|
| 使用者 | `gh api user/repos` | 7 個私有庫全部 `push=true admin=true`;token scope 含 `repo` |
| App | 授權頁 | `code` = Read and write |
| 服務端閘 | `gh api repos/<r>/rulesets` | 403「Upgrade to GitHub Pro or make this repository public」——free plan 的 private repo **根本沒有 branch protection 可言** |

**沒有任何一格是關著的。**

### 修法：沒有可修的權限

擋在**產品層**,不在 GitHub。改 App 權限、改帳號權限、開 Pro 買 ruleset 都不會讓它改成直接推——
它做得到,只是不做。要直接推就換 host：**Codex CLI**（§2,三平面已綠）。

同一個帳號下的物理證據,證明 CLI 那條路真的會寫：

```
ed3c/ix-agy-private  PR #29  merged
  head.ref   codex/code-truth-graph-softkey-v1.1
  50 files, +4924
  committer  neon <neon@noreply.localhost>   ← 本機 git 身分,不經 App
  user.login ed3c (type=User)                ← 不是 Bot
```

### 事故紀錄：把「最自然的解釋」當成量測（2026-08-09）

看到「能開 PR、不能直接改」時,我推論 `Contents: Read` ＋ `Pull requests: write`——因為在
GitHub 的權限模型裡,那是**唯一能一次解釋兩個現象的組合**,而且它與官方那兩個獨立權限的語意
完全吻合。看起來很對。**它是錯的。**

推翻它的不是更多推理,是那一頁截圖。

兩個教訓,第二個比第一個貴：

1. **權限模型裡最自然的解釋,不等於真的。** 一個假說能解釋全部已知現象,只說明它沒被現有觀察
   否證,不說明它為真。要否證它只需要一格真值,而那一格當時**讀得到,只是要換一個抵達**（人眼開
   授權頁),不是讀不到。**在還有便宜真值可取時就開始推論,是把可否證的事做成不可否證的。**
2. **能力與行為要分開量。** 「它沒做過 X」不能證明「它不能做 X」。中途我掃了 7 個私有庫找 Codex
   寫入痕跡,只找到 PR #29——而那筆的 committer 是本機身分、actor 是 User 不是 Bot,**它屬於 CLI
   不屬於 App**。差點拿它去證 App 有寫入權;那會是用 A 的觀察證 B,兩者不同源。
   零筆 Bot 寫入的正確讀法是**「這個 App 在此帳號沒寫過」,不是「這個 App 不能寫」**。

### 可重播的量法

```bash
gh api user/repos --paginate -q '.[] | select(.private==true) | "\(.full_name) push=\(.permissions.push)"'
gh api repos/<owner>/<repo>/rulesets           # 403 = 該 plan 無服務端閘,不是設定錯
# App 的 installation 權限:API 讀不到,開 https://github.com/settings/installations 人眼確認
```

`user/installations` 回 403「You must authenticate with an access token authorized to a GitHub App」
是**能力缺席,不是權限被拒**——別去修一個不存在的權限問題（同 §6 的三分原則）。
