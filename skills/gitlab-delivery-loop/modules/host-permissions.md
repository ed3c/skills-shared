# host-permissions.md — 各 host 的 GitLab merge 權限真相（低壓縮版）

本模組只回答一件事：**為什麼 `glab mr merge` 會被擋、被哪一層擋、那一層的確切修法是什麼**。
四層授權堆疊的語意在 [delivery-mechanism.md § Merge authority stack](delivery-mechanism.md#merge-authority-stack)，
本檔不複述堆疊，只補「每一層在各 host 的實際形狀＋官方出處＋可重播的驗證方式」。

L2（host shell policy）與 github-delivery-loop **機制完全相同**——同樣兩個 host、同樣的
hook 平面、同樣的 Codex 三子閘。差別在 L1／L3／L4，因為那三層是 GitLab 的。

## 0. 復發機制（為什麼修一次不夠）

同一句「merge 權限沒放行」在不同 host 是**不同的病**：

| host | 真正卡住的東西 | 卡在堆疊哪一層 |
|---|---|---|
| Claude Code | PreToolUse hook 黑名單命中 → exit 2 | L2 |
| Codex CLI | sandbox network 沒開／execpolicy 無規則／Codex 自己的 hook | L2（三個互不相干的子閘） |
| 純 shell / CI | 沒有 L2；卡在 glab token scope 或 protected branch | L3 |

修完一個 host，換到另一個又斷。**根因不是任何一條規則寫錯，
而是「哪一層會拒絕」是在執行期才被發現的**——跑了一小時、開好 MR，才吃到 exit 2。

對策是把發現時機前移：`scripts/gitlab_merge_gate.py preflight`
**用每個 host 自己的閘真跑一次**（合成 PreToolUse payload 餵進實際設定的 hook、呼叫
`codex execpolicy check`、按官方分層序讀 `.codex/config.toml` 的 network 授權），不靠推論。

## 1. Claude Code 層

### 官方語意（[hooks](https://code.claude.com/docs/en/hooks)／[permissions](https://code.claude.com/docs/en/permissions)）

- PreToolUse hook 在**每次工具呼叫、permission prompt 之前**執行；exit 2 = blocking error，
  「blocks the tool call」，stderr 回饋給模型。exit 1 是 non-blocking，動作照跑——
  官方明文警告：要擋就必須用 exit 2。
- hook 的決策**不繞過** permission rules：deny／ask 規則照樣先評估。
- permission rules 跨 scope 是**合併**不是覆蓋，所以
  **`permissions.allow` 永遠救不回一個 exit 2 的 hook**——兩者不在同一個 plane。
- `bypassPermissions` 只跳過 permission prompt，hook 照跑。

### 本機實況（2026-08-07 實跑，非推論）

把整條 glab 交付鏈合成 PreToolUse payload 餵進**實際設定的 hook**，兩個 host 全數放行：

```text
claude-code (1 hook)   codex (1 hook)
  allow  glab auth status            allow  ...（同左，逐項相同）
  allow  glab repo view -F json
  allow  glab issue list / create
  allow  glab mr list / create
  allow  glab label create
  allow  glab api --hostname ...
  allow  glab mr merge -R ... --sha ... --auto-merge=false --yes
  allow  git push origin HEAD
```

對應的靜態事實：兩個 host 的 `auto-approve.sh` 的 `BASH_BLACKLIST` 裡
**只有 `gh pr merge.*--admin` 一條與 merge 相關，沒有任何 `glab` 條目**。

**這與 GitHub 側的歷史不同，要當成已知事實而不是「忘了設」**：
GitHub 那邊曾整條被 `"gh pr merge"` 字面黑掉，後來收斂成只黑 `--admin`
（因為 `--admin` 是唯一能繞過 GitHub 端所有要求的形式）。
`glab mr merge` **沒有 `--admin` 這種旗標**——GitLab 端沒有等價的「以管理員身分無視所有要求」
CLI 開關，所以這裡沒有對應的東西要黑。L2 對 GitLab 是開的，擋的責任全落在
**L1（Owner 的 merge-admit label）** 與 **L3（protected branch／required approvals）**。

真正該檢查的因此不是「hook 有沒有黑 glab」，而是「那個專案在 GitLab 端有沒有設保護分支」。
若某個專案沒設保護分支、又沒有人閘，那 L1 就是唯一的閘——這是可接受的設計，
但必須是**知道**的，不是預設沒人看。

### 若某天要收緊

要讓 agent 不能自行 merge，改 `BASH_BLACKLIST` 加一條 `"glab mr merge"` 即可（**必須由人親手改**：
該檔把自己列進 `SENSITIVE_FILE_PATTERNS` 並封鎖指向 `.claude/(hooks|settings)` 的
`sed`／`tee`／`cp`／`mv`，代理無法修改它）。改完以 `preflight` 重驗，
`L2 HOST-POLICY claude-code` 應從 `ALLOW` 轉 `BLOCK`。

## 2. Codex CLI 層

### 官方語意（[permissions](https://learn.chatgpt.com/docs/permissions)／[config](https://learn.chatgpt.com/docs/config-file/config-basic)）

- 新版 permission profile：頂層 `default_permissions = "<name>"`，內建 preset
  `:read-only`／`:workspace`／`:danger-full-access`；具名 profile 用 `[permissions.<name>]` 搭 `extends`。
- **`:workspace` 的 network 預設關閉**，`.codex` 與 `.git` 保持唯讀。
- 開網路：`[permissions.<name>.network] enabled = true`。
- **profile 與舊的 `sandbox_mode`／`sandbox_workspace_write` 不可混用**。
- config 載入序（高→低）：CLI `--config` → **專案 `.codex/config.toml`** → profile 檔 →
  `~/.codex/config.toml` → `/etc/codex/config.toml` → 內建預設。

### 本機實況（2026-08-07）

network 已在 user 層 profile 開啟、Codex hook 放行，所以 preflight 直接落到第三個子閘：

```text
L2 HOST-POLICY codex: BLOCK -- no rule in /Users/neon/.codex/rules allows this merge
  (5 file(s) checked) -- run install-codex-merge-rule.sh --host gitlab.com --project ...
```

`~/.codex/rules/` 現有 5 檔：`default.rules`、三個 `github-merge-*.rules`、
以及一個手寫的 `ix-agy-merge.rules`。**沒有任何 GitLab 規則**，所以 Codex 這條線
在裝規則前不能 merge GitLab。這不是錯誤，是尚未 bootstrap。

裝法（`bootstrap` 會自動呼叫，也可單獨跑）：

```bash
bash ~/.agents/skills/gitlab-delivery-loop/scripts/install-codex-merge-rule.sh \
  --host gitlab.com --project GROUP/SUBGROUP/PROJECT \
  --rules-dir ~/.codex/rules
```

裝完**必須完整重啟 Codex** 才會載入。

### Codex 有三個互不相干的子閘

```text
Codex 一次 merge 要同時通過：
  network profile（打不打得出去） × PreToolUse hook（送不送得出命令） × execpolicy（離不離得開 sandbox）
```

這是 GitHub 側 2026-08-07 漏報事故的教訓，**原樣適用於 GitLab**：preflight 第一版只驗
network 與 execpolicy，兩者 ALLOW 後就印綠燈——但 `~/.codex/hooks/auto-approve.sh` 仍會擋。
**驗證器少驗一個平面，就把「還會被擋」報成「可以了」。**
回歸守衛＝`tests/merge-gate/verify.sh` 第 4b 案。

### config 是分層的，只讀最近那份會報假紅

專案 `.codex/config.toml` 若只為 MCP server 存在、沒提 permissions，按官方分層序它會**繼承**
user 層 profile。驗證器只讀「往上找到的第一份」等於把繼承當成缺席，會報假紅。
修法＝照官方分層解析並印出實際讀了哪幾份（`A over B`）。
回歸守衛＝`tests/merge-gate/verify.sh` 第 4c 案。

### 檔名不是契約，規則內容才是

`codex execpolicy check` 的 `--rules` 是**可重複**參數，Codex 讀的是整個 rules 目錄。
從專案路徑推檔名，會讓一條手寫的、檔名不合慣例的有效規則在 probe 眼裡等於不存在
（本機就有一個：`ix-agy-merge.rules`）。所以 probe **掃 `~/.codex/rules/*.rules` 全部丟給
`--rules`**，讓 execpolicy 自己判。

**三者是同一個病**：假綠＝少驗一個平面；假紅其一＝少讀一個層級；假紅其二＝把自己的命名慣例
當成對方的載入契約。都不是「規則寫錯」，而是**驗證器對真實解析規則建模不足**。
每加一個 host 面向要問的是**「它真正的解析規則是什麼」**，不是「我知道的那份檔在哪」。

### prefix rule 擋不住尾隨旗標（GitLab 版的症狀是 `--auto-merge`）

GitHub 版實測發現 prefix rule 擋不住 `--admin`，因為它出現在 PR 編號之後、位置浮動。
**GitLab 有同類缺口，症狀不同**：`glab mr merge` 的 `--auto-merge` 預設為 true
（官方 help：「When a pipeline is running, auto-merge is enabled by default」），
落地時若沒顯式關掉，命令會**回傳成功但什麼都沒合**。

它同樣在 prefix contract 之外，所以三道實際防線是：

1. `merge_command()` 永遠產生 `--auto-merge=false --yes`，且沒有任何旗標可以要求它不產生；
2. `tests/merge-gate/verify.sh` 第 6 案直接斷言產出的 argv 含該旗標（變異測試證明拔掉會紅）；
3. 安裝器的煙測用 **land 的真實 argv 形狀**，不是 `... 1 --merge` 這種較短的方便形式——
   GitHub 側的教訓正是「用短形狀驗過的規則，對真正會跑的那條 argv 什麼都沒說」。

教訓：窄規則的「窄」要用負控量，不能看它 allow 了正控就宣稱窄。

## 3. GitLab 層

### 官方語意

- [`glab mr merge`](https://gitlab.com/gitlab-org/cli)：`--sha` =「Merge only if the HEAD of the
  source branch matches this SHA. Use to ensure that only reviewed commits are merged」；
  `--auto-merge` 預設 true（有 pipeline 時）；`-R` 接受 `OWNER/REPO`、`GROUP/NAMESPACE/REPO`
  或完整 URL；`--yes` 跳過確認。
- MR 的可合併性是**單一枚舉** `detailed_merge_status`（取代舊的粗粒度 `merge_status`）。
  只有 `mergeable` 可落地。

### 為什麼人閘用 label 而不是 approval

GitLab 的 required approvals 在**免費方案的公開專案上受限**，且單人帳號下作者無法核可自己；
要用 approval 當人閘就得引入第二個身分（bot／service account），那是額外基建。

再加上一個 GitLab 特有的硬事實：**group 專案的 `owner` 欄位是 `null`**
（`GET /projects/:id` 對 `gitlab-org/cli` 實測）。GitHub 版「label actor == repo owner」
的判準在 GitLab 上會比對到 null——不是假紅就是假綠。

所以人閘落在 **`merge-admit` label ＋ membership access level**：

- 由專案 Owner 在 GitLab UI 施加（手機可操作，可批次），是 server 端的
  `resource_label_events`，帶 actor、action 與時間戳，事後可稽核；
- `gitlab_merge_gate.py` 要求該 actor 的 **`access_level >= 50`（Owner）**，
  查詢用 `members/all?query=<username>` 收斂成單一請求（group 專案可能有數千繼承成員）；
- 個人 namespace 另給出口：`namespace.kind == "user"` 且 `full_path == actor` 直接成立，
  因為個人專案擁有者不一定出現在 members 清單；
- **labelled_at ≥ head commit 的 committed_date**，貼完標籤又推新 commit 會自動失效（`admit-stale`）；
- 實際 merge 一律帶 `--sha <被 admit 的 SHA>`，HEAD 漂移即失敗。

門檻取 Owner(50) 而非 Maintainer(40) 是刻意的：**Maintainer 本來就能 merge**，
拿它當人閘等於讓能 merge 的人核可自己能 merge，閘就不存在了。

這幾條合起來，讓「人 admit」是一個**有物理載體、可否證、且與 agent 執行分離**的事實。
它不宣稱能防住一個蓄意偽造的代理（有 shell 就有 token），
它防的是「代理自作主張 merge」與「admit 後內容悄悄改變」。

### `detailed_merge_status` 的三種讀法不可混淆

| 類別 | 值 | 應該怎麼讀 |
|---|---|---|
| 可落地 | `mergeable` | 綠 |
| **尚未算完** | `unchecked` / `checking` / `preparing` | **retry，不是拒絕**——當成拒絕會讓人去修一個不存在的問題 |
| 政策選擇 | `ci_still_running` / `ci_must_pass` | 需 `--allow-unstable` 才放行 |
| 真拒絕 | `conflict` / `draft_status` / `need_rebase` / `not_approved` / `discussions_not_resolved` / `blocked_status` | 各自印確切修法 |

回歸守衛＝`tests/merge-gate/verify.sh` 第 3b 案。

## 4. 全域 vs per-project（新專案要做什麼）

把每一塊放在它能放的最高層，per-project 只留真正無法全域的兩件：

| 元件 | 位置 | 範圍 |
|---|---|---|
| canonical skill | `~/.agents/skills-shared/skills/gitlab-delivery-loop/` | **全域**，兩個 user 層 surface symlink 過來 |
| Claude Code PreToolUse 黑名單 | `~/.claude/hooks/auto-approve.sh` | **全域**，目前對 glab 全放行（見 §1） |
| Codex PreToolUse 黑名單 | `~/.codex/hooks/auto-approve.sh` | **全域**（與上一列是同一行規則的鏡像） |
| Codex sandbox（network） | `~/.codex/config.toml` 的 `default_permissions` ＋ profile | **全域**；個別 repo 要不同就用自己的 `.codex/config.toml` 覆蓋 |
| `merge-admit` label | GitLab project | **per-project**（server 端物件，無法全域） |
| execpolicy 窄規則 | `~/.codex/rules/gitlab-merge-<host>-<slug>.rules` | **per-project**（prefix rule 必須寫死 `-R https://host/path`） |
| Codex project trust | `~/.codex/config.toml` 的 `[projects."<path>"]` | **per-path** |

所以新專案只需要一句（`--project` 省略時從 cwd 的 glab remote 推，連 host 一起推）：

```bash
python3 ~/.agents/skills/gitlab-delivery-loop/scripts/gitlab_merge_gate.py bootstrap
```

冪等：label 與 rule 已存在就印 `OK` 不重建，最後接一次 preflight 把四層現況印出來。
它**只做那兩件 per-project 的事**——全域那四列不歸它管，改動全域＝治理事件，由人執行。

## 5. 缺席與拒絕必須長得不一樣

`preflight` 的退出碼刻意三分：

| exit | 意義 |
|---|---|
| 0 | 至少一張 MR 可落地，且四層皆放行 |
| 1 | 有一層**拒絕**（stderr 指名是哪一層、哪張 MR、確切修法） |
| 3 | **沒有任何 MR 被 admit**——缺席，不是拒絕 |

把 3 併進 1 會讓「還沒人核可」在自動化裡讀起來像「被擋住了」，於是有人去改權限修一個
不存在的權限問題。由 `tests/merge-gate/verify.sh` 第 3 案守著。

同一原則在本 skill 還有三個落點，都是「缺席自己有出口」：

- `remote-head-unverifiable`（本地無此 commit）≠ `export-tree-drift`（樹不同）；
- `first_pass_rate: null` ＋ 明確原因欄位 ≠ `first_pass_rate: 0`；
- `unchecked`（還沒算完）≠ `conflict`（真的不能合）。
