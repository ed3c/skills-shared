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
2. `merge_gate.py` 的 `merge_command()` 從不產生 `--admin`，也沒有任何旗標可以要求它產生；
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

## 4. 全域 vs per-repo（新專案要做什麼）

把每一塊放在它能放的最高層，per-repo 只留真正無法全域的兩件：

| 元件 | 位置 | 範圍 |
|---|---|---|
| canonical skill（Claude Code 發現面） | `~/.claude/skills/github-delivery-loop/` | **全域**，所有專案自動可見 |
| canonical skill（Codex 發現面） | `~/.agents/skills/<name>` → symlink 到 canonical | **全域**（`~/.codex/skills` 為 legacy 路徑） |
| Claude Code PreToolUse 黑名單 | `~/.claude/hooks/auto-approve.sh` | **全域**，一次改完 |
| Codex PreToolUse 黑名單 | `~/.codex/hooks/auto-approve.sh` | **全域**，一次改完（與上一列是同一行規則的鏡像） |
| Codex sandbox（network＋`.git` write） | `~/.codex/config.toml` 的 `default_permissions` ＋ profile | **全域**；個別 repo 要不同就用自己的 `.codex/config.toml` 覆蓋（project 層贏 user 層） |
| `merge-admit` label | GitHub repository | **per-repo**（server 端物件，無法全域） |
| execpolicy 窄規則 | `~/.codex/rules/github-merge-<owner>-<repo>.rules` | **per-repo**（prefix rule 必須寫死 `--repo owner/name`；要全域就得放寬成任意 repo，等於放棄窄化） |
| Codex project trust | `~/.codex/config.toml` 的 `[projects."<path>"]` | **per-path**；首次在該目錄跑 Codex 時由它自己詢問並寫入 |

所以新專案只需要一句（`--repo` 省略時從 cwd 的 git remote 推）：

```bash
python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py bootstrap
```

冪等：label 與 rule 已存在就印 `OK` 不重建，最後接一次 preflight 把四層現況印出來。
它**只做那兩件 per-repo 的事**——全域那五列不歸它管，改動全域＝治理事件，由人執行。

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

把 3 併進 1 會讓「還沒人核可」在自動化裡讀起來像「被擋住了」，於是有人去改權限修一個
不存在的權限問題。這是「每個缺席都給明確出口」在本 skill 的落點，
由 `tests/merge-gate/verify.sh` 第 3 案守著。
