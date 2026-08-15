---
name: gitlab-delivery-loop
description: |
  把大小迴圈的本地產物綁到 GitLab PRD issue、slice issues、MR 與 issue board，並以零網路
  delivery receipt 閘阻止「產物缺席卻顯示成功」；merge 由四層授權堆疊守門，開工前以
  gitlab_merge_gate.py preflight 用每個 host 自己的閘真跑一次，把「哪一層會拒絕」從執行期
  提前到開工前。適用於 GitLab／glab 的交付追蹤、迭代速度量測、worktree 切線、小迴圈
  handoff，以及「merge 權限被擋／換個 host 又被擋」的診斷與根治。
  觸發詞：GitLab 看板進度、glab、merge request、MR 交付、delivery 收據、issue 驅動實作、
  merge 被擋、preflight、merge-admit、gitlab-delivery-loop。
  這是 github-delivery-loop 的姊妹 skill，**兩者不可混用**：GitHub 的 registry／receipt／
  snapshot 餵進來會被拒絕並指回另一支。不負責取代 TDD、code review 或人類 merge/public gate。
---

# GitLab Delivery Loop

這個 skill 只擁有「本地產物 ↔ GitLab 追蹤面」的交付邊界。小迴圈仍擁有自己的 prompt、
判官與收斂條件；兩者透過 receipt 協作，不複製任何小迴圈 prompt。

完整 schema、狀態流與速度定義見 [modules/delivery-mechanism.md](modules/delivery-mechanism.md)。
各 host 的權限真相、確切修法與官方出處見 [modules/host-permissions.md](modules/host-permissions.md)。
**與 GitHub 版的分界與五處實測平台差異見 [modules/github-vs-gitlab.md](modules/github-vs-gitlab.md)——
動手前先讀它**，照抄 GitHub 版的假設會靜默失敗。

## 與 github-delivery-loop 不混用

同一套設計，兩份實作，**零共用程式碼**。錯配在載入的第一刻就撞牆，不是執行到一半才發現：

| | GitHub | GitLab |
|---|---|---|
| schema | `github-delivery-*` | `gitlab-delivery-*` |
| 身份 | `github_repo` ＋ node ID | `gitlab_host` ＋ `gitlab_project` ＋數字 `gitlab_project_id` |
| registry | `.github-delivery/registry.json` | `.gitlab-delivery/registry.json` |
| CLI | `gh` | `glab` |
| 交付載體 | PR / `pr_urls` | MR / `mr_urls` |
| execpolicy 規則 | `github-merge-*.rules` | `gitlab-merge-*.rules` |

把 GitHub 的 registry、receipt 或 snapshot 餵進本 skill → 拒絕，並指名去用
`github-delivery-loop`。負控由 `tests/cross-forge/verify.sh` 守著。

## 可攜性（canonical 單一家）

canonical 住 `~/.agents/skills-shared/skills/gitlab-delivery-loop/`，經 `~/.agents/skills/`
與 `~/.claude/skills/` 兩個 user 層 surface 的 symlink 讓所有專案看到，沒有第二份可漂移的副本。
接線與同名影蓋的治理歸 `shared-skills-infra`，本 skill 不自帶連結工具。

所有腳本以絕對路徑＋顯式 `--registry`／`--project` 呼叫，**任何 CWD、任何 repo 都能跑**；
整個目錄 `cp -r` 到別台機器即完整（scripts＋tests＋fixtures 自含，只用 Python stdlib、`glab` 與 `git`）。
自測零網路：`bash ~/.agents/skills/gitlab-delivery-loop/tests/run-all.sh`。

## 操作順序

1. 先建立 PRD issue，再拆成可獨立驗收的 slice issues。
2. 將每條線登記在 `.gitlab-delivery/registry.json`；`artifact_path` 是小迴圈的物化產物，
   `receipt_path` 是它交給 delivery engine 的物理收據。`gitlab_project_id` 釘數字 id，
   不是路徑——路徑會因 transfer 改變。
3. 從任何 CWD 執行：
   `python3 ~/.agents/skills/gitlab-delivery-loop/scripts/gitlab_delivery.py check --registry <repo>/.gitlab-delivery/registry.json`。
4. 需要 GitLab 活狀態與速度快照時執行 `sync --gitlab`，明確提供 line、metrics、dashboard、
   40 字元 export source commit、`export_tree_sha`，以及推上去的那份 clone（`--export-repo`）；
   測試與重播改用 `--snapshot <json>`，不得在測試中打網路。
5. 每張 issue 在隔離 worktree 走 TDD → review → MR，MR description 使用 `Closes #N`。
6. Merge 走下節的 admit → preflight → land；漂移或新發現另開 issue，不塞進正在進行的 slice。

## 新專案套用（一句，冪等）

全域的部分（skill 本體、兩個 host 的 PreToolUse 黑名單、Codex sandbox profile）一次設好就
對所有專案生效；真正 per-project 的只有 `merge-admit` label 與 execpolicy 窄規則。在新專案裡跑：

```bash
python3 ~/.agents/skills/gitlab-delivery-loop/scripts/gitlab_merge_gate.py bootstrap
```

`--project` 省略時從 cwd 的 glab remote 推（連 host 一起推，所以自架實例也對）。
已存在就印 `OK` 不重建，最後接一次 preflight 印出四層現況。
全域／per-project 的完整分界表 → [modules/host-permissions.md §4](modules/host-permissions.md)。

## Merge authority（人 admit → agent 執行）

merge 不是一個「有／無權限」位元，是四層獨立閘：L1 人 admit、L2 host shell policy、
L3 GitLab、L4 merge 本身。任一層拒絕就不得宣稱已放行。堆疊語意見
[delivery-mechanism.md § Merge authority stack](modules/delivery-mechanism.md#merge-authority-stack)。

**L2 在單一 host 內可能不只一個平面**：Claude Code 是 PreToolUse hook；Codex 是
PreToolUse hook × sandbox network profile × execpolicy，三者互不相干，任一擋住就是擋住。
preflight 三個都驗——少驗一個平面就會把「還會被擋」報成綠燈。

1. **人 admit**：專案 Owner 在 GitLab 對可落地的 MR 貼 `merge-admit` label（UI／手機，可批次）。
   這是唯一構成 landing decision 的事實；永久 command allow 不是。
   GitLab 的 group 專案**沒有單一 `owner` 欄位**（實測為 `null`），所以判準是
   **access_level ≥ 50（Owner）**，或個人 namespace 的擁有者本人。

2. **preflight**（開工前就跑，不要等到 MR 開好）——它把合成的 PreToolUse payload 餵進實際設定的
   hook、呼叫 `codex execpolicy check`、讀 `.codex/config.toml` 的 network 授權，**真跑每個 host
   自己的閘，不推論**；非 active host 只報告不阻擋：

   ```bash
   python3 ~/.agents/skills/gitlab-delivery-loop/scripts/gitlab_merge_gate.py \
     preflight --project GROUP/SUBGROUP/PROJECT [--host gitlab.example.com]
   ```

   `exit 0` 可落地｜`1` 有一層拒絕（stderr 指名層、MR 與確切修法）｜`3` 沒有任何 MR 被 admit
   （**缺席，不是拒絕**——別去修一個不存在的權限問題）。

3. **land**：綠了才落地。每張 MR 落地前重取快照，並帶 `--sha` 釘住被 admit 的 commit；
   base 隨每次 merge 移動後自動重算下一張。

   ```bash
   python3 ~/.agents/skills/gitlab-delivery-loop/scripts/gitlab_merge_gate.py \
     land --project GROUP/SUBGROUP/PROJECT [--dry-run]
   ```

4. 任一層拒絕 → **停下並回報命中的 policy 與 owner 需要的變更**；禁止改用混淆命令、換 API
   或停用 hook 繞過。安裝 Codex 窄規則用 `scripts/install-codex-merge-rule.sh`。

## Worktree surface 不可混用

- Codex App：在起點建立 Worktree chat，或使用正式 Hand off → Worktree。
- Codex IDE：只有介面實際提供時才用 `/worktree`。
- Codex CLI：先由人或獲授權 orchestration 執行標準 `git worktree add`，再以
  `codex -C <existing-worktree-path>` 啟動；不存在 `EnterWorktree`、`codex worktree` 或 `codex -w`。
- Claude Code：只使用當前 carrier 真正提供的 worktree 能力；沒有隔離欄位就 fail closed。

## 硬閘

- artifact 不存在是 `UNMATERIALIZED` 失敗，不是 SKIP。
- receipt/publication attestation 缺席、身份漂移、假 URL 或短 SHA 都失敗。
- **任何 GitHub 形狀的 state（schema、`github_repo` 欄位、`github.com` URL、GitHub snapshot）
  一律拒絕並指回 `github-delivery-loop`**——未知欄位通常無害，這一個代表走錯 forge。
- publication attestation 必須把 `export_tree_sha` 釘回遠端 head 的樹。GitLab 不提供
  root tree sha（REST／GraphQL 皆無，實測），所以由 export clone 本地解析；
  解不出來是 `remote-head-unverifiable`，與 `export-tree-drift` 是**兩個不同的 blocker**。
- 本地 `check` 與 `preflight --snapshot` 零網路；GitLab 活狀態由 `sync --gitlab` 與
  `preflight`（無 `--snapshot`）負責，兩種證據不得混稱。
- project identity 釘數字 `gitlab_project_id` ＋ `gitlab_host`；路徑只作可轉移別名。
- `merge-admit` 只有 **Owner 施加、且晚於 head commit** 才算數；貼完標籤又推新 commit
  自動失效（`admit-stale`）。merge 一律帶 `--sha`，HEAD 漂移即失敗。
- merge 一律帶 `--auto-merge=false`。`glab mr merge` 在有 pipeline 時**預設開 auto-merge**，
  那會回報成功但什麼都沒合——這正是本 skill 要擋的病。此旗標位置浮動，
  **execpolicy 前綴規則守不住它**，只能由 `merge_command()` ＋測試守。
- `internal` visibility 沒有 GitHub 對應物，單獨給 blocker，不與 private 併攏。
- first-pass rate 在 GitLab 沒有等價物 → 恆 `null` ＋ 明確原因欄位，**不補零**。
- Codex user rule 只處理 sandbox execpolicy，不能覆蓋 PreToolUse hook、GitLab 保護分支規則
  或人類 gate；若下游層拒絕，必須停下報告衝突。
- 不以 LOC、commit 數或個人排名衡量速度。

## 索引紀律（本檔對自己的樹的宣稱）

索引**單向失效**：死連結點下去才知道，漏列的檔案永遠沒人會知道——短的清單與完整的清單長得一模一樣。
本檔漏掉的是 [`scripts/gitlab_sync.py`](scripts/gitlab_sync.py)（GitLab snapshot 攝取、label/state
event 推導的 flow metrics 與 board 解析），而三支 delivery-loop 各藏著一支從沒被自己 SKILL.md 提過的
sync 類腳本，是同型缺陷三處齊發。

規則靠 [`tests/index/verify.sh`](tests/index/verify.sh) 執行，而不靠人記得。

