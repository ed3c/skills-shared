---
name: github-delivery-loop
description: |
  把大小迴圈的本地產物綁到 GitHub PRD issue、slice issues、PR 與 Project，並以零網路
  delivery receipt 閘阻止「產物缺席卻顯示成功」；merge 由四層授權堆疊守門，開工前以
  merge_gate.py preflight 用每個 host 自己的閘真跑一次，把「哪一層會拒絕」從執行期提前到
  開工前。適用於交付追蹤、迭代速度量測、worktree 切線、小迴圈 handoff、以及
  「merge 權限被擋／換個 host 又被擋」的診斷與根治。
  觸發詞：看板進度、delivery 收據、issue 驅動實作、worktree 切線、merge 被擋、
  merge 權限、preflight、merge-admit、github-delivery-loop。
  不負責取代 TDD、code review 或人類 merge/public gate。
---

# GitHub Delivery Loop

這個 skill 只擁有「本地產物 ↔ GitHub 追蹤面」的交付邊界。小迴圈仍擁有自己的 prompt、
判官與收斂條件；兩者透過 receipt 協作，不複製任何小迴圈 prompt。

完整 schema、狀態流與速度定義見 [modules/delivery-mechanism.md](modules/delivery-mechanism.md)。
各 host 的權限真相、確切修法與官方出處見 [modules/host-permissions.md](modules/host-permissions.md)。
**commit 角色（用哪個身分 commit、agent 怎麼署名、何時才准 commit）的完整設定見
[modules/commit-role.md](modules/commit-role.md)——開工前先跑它 §6 的 `git var GIT_AUTHOR_IDENT` 檢查。**

## 可攜性（canonical 單一家）

canonical 住 `~/.claude/skills/github-delivery-loop/`；各 repo 的 `.claude/skills/` 與
`.agents/skills/` 以 symlink 指過來，沒有第二份可漂移的副本。轉換用
`scripts/link-canonical.sh --target <repo>/.agents/skills/<name> [--apply]`——預設乾跑，
**副本已分岔就拒絕並印出 diff**（收斂是人的決定），舊副本是**搬到備份而非刪除**，
所以整個操作可用一次 `mv` 還原、也不需要不可逆刪除的授權。

所有腳本以絕對路徑＋顯式 `--registry`／`--repo` 呼叫，**任何 CWD、任何 repo 都能跑**；
整個目錄 `cp -r` 到別台機器即完整（scripts＋tests＋fixtures 自含，只用 Python stdlib 與 `gh`）。
自測零網路：`bash ~/.claude/skills/github-delivery-loop/tests/run-all.sh`。

## 操作順序

1. 先建立 PRD issue，再拆成可獨立驗收的 slice issues。
2. 將每條線登記在 `.github-delivery/registry.json`；`artifact_path` 是小迴圈的物化產物，
   `receipt_path` 是它交給 delivery engine 的物理收據。
3. 從任何 CWD 執行：
   `python3 ~/.claude/skills/github-delivery-loop/scripts/github_delivery.py check --registry <repo>/.github-delivery/registry.json`。
4. 需要 GitHub 活狀態與速度快照時執行 `sync --github`，明確提供 line、metrics、dashboard、
   40 字元 export source commit，以及 `public_export.py verify` 回報的 `tree_sha`；測試與重播
   改用 `--snapshot <json>`，不得在測試中打網路。
5. 每張 issue 在隔離 worktree 走 TDD → review → PR，PR body 使用 `Closes #N`。
6. Merge 走下節的 admit → preflight → land；漂移或新發現另開 issue，不塞進正在進行的 slice。

## 新專案套用（一句，冪等）

全域的部分（skill 本體、兩個 host 的 PreToolUse 黑名單、Codex sandbox profile）一次設好就
對所有專案生效；真正 per-repo 的只有 `merge-admit` label 與 execpolicy 窄規則。在新 repo 裡跑：

```bash
python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py bootstrap
```

`--repo` 省略時從 cwd 的 git remote 推。已存在就印 `OK` 不重建，最後接一次 preflight 印出四層現況。
全域／per-repo 的完整分界表 → [modules/host-permissions.md §4](modules/host-permissions.md)。

## Merge authority（人 admit → agent 執行）

merge 不是一個「有／無權限」位元，是四層獨立閘：L1 人 admit、L2 host shell policy、
L3 GitHub、L4 merge 本身。任一層拒絕就不得宣稱已放行。堆疊語意見
[delivery-mechanism.md § Merge authority stack](modules/delivery-mechanism.md#merge-authority-stack)。

**L2 在單一 host 內可能不只一個平面**：Claude Code 是 PreToolUse hook；Codex 是
PreToolUse hook × sandbox network profile × execpolicy，三者互不相干，任一擋住就是擋住。
preflight 三個都驗——少驗一個平面就會把「還會被擋」報成綠燈（見 host-permissions.md §2 漏報事故）。

1. **人 admit**：repo owner 在 GitHub 對可落地的 PR 貼 `merge-admit` label（UI／手機，可批次）。
   這是唯一構成 landing decision 的事實；永久 command allow 不是。
2. **preflight**（開工前就跑，不要等到 PR 開好）——它把合成的 PreToolUse payload 餵進實際設定的
   hook、呼叫 `codex execpolicy check`、讀 `.codex/config.toml` 的 network 授權，**真跑每個 host
   自己的閘，不推論**；非 active host 只報告不阻擋：

   ```bash
   python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py preflight --repo OWNER/REPO
   ```

   `exit 0` 可落地｜`1` 有一層拒絕（stderr 指名層、PR 與確切修法）｜`3` 沒有任何 PR 被 admit
   （**缺席，不是拒絕**——別去修一個不存在的權限問題）。

3. **land**：綠了才落地。每張 PR 落地前重取快照，並帶 `--match-head-commit` 釘住被 admit 的 SHA；
   base 隨每次 merge 移動後自動重算下一張。

   ```bash
   python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py land --repo OWNER/REPO [--dry-run]
   ```

4. 任一層拒絕 → **停下並回報命中的 policy 與 owner 需要的變更**；禁止改用混淆命令、換 API
   或停用 hook 繞過。安裝 Codex 窄規則用 `scripts/install-codex-merge-rule.sh`。

## Worktree surface 不可混用

- Codex App：在起點建立 Worktree chat，或使用正式 Hand off → Worktree。
- Codex IDE：只有介面實際提供時才用 `/worktree`。
- Codex CLI：先由人或獲授權 orchestration 執行標準 `git worktree add`，再以
  `codex -C <existing-worktree-path>` 啟動；不存在 `EnterWorktree`、`codex worktree` 或 `codex -w`。
- Claude Code：只使用當前 carrier 真正提供的 worktree 能力；沒有隔離欄位就 fail closed。

## 索引紀律（本檔對自己的樹的宣稱）

本檔列出的 `modules/`／`scripts/` 就是一份索引，而索引**單向失效**：死連結點下去才知道，
**漏列的檔案永遠沒人會知道**——短的清單與完整的清單長得一模一樣。首次真跑時，三支
delivery-loop **各藏著一支從沒被自己 SKILL.md 提過的 sync 類腳本**；本 skill 那支是
`scripts/delivery_sync.py`（GitHub snapshot 攝取、flow metrics 與決策儀表板投影）。
同型缺陷三處齊發，正是「發現一個先掃同類全部實例」的形狀。

規則不靠人記得，靠 `tests/index/verify.sh`（`tests/run-all.sh` 自動探索）：它先跑 checker
自己的 `--selftest`，再驗本檔——**checker 不能證明自己會紅之前，它對本檔的綠燈不算數**。

## 硬閘

- artifact 不存在是 `UNMATERIALIZED` 失敗，不是 SKIP。
- receipt/publication attestation 缺席、身份漂移、假 URL 或短 SHA 都失敗。
- publication attestation 必須把 `export_tree_sha` 釘回遠端 head 的 tree；不相等就是
  `export-tree-drift` blocker，file count 與 orphan history 相符不足以證明推上去的就是驗過的樹。
- 本地 `check` 與 `preflight --snapshot` 零網路；GitHub 活狀態由 `sync --github` 與
  `preflight`（無 `--snapshot`）負責，兩種證據不得混稱。
- repository identity 釘 immutable GitHub node ID；owner/name 只作可轉移別名，redirect 不得冒充身份證據。
- `merge-admit` 只有 **repo owner 施加、且晚於 head commit** 才算數；貼完標籤又推新 commit
  自動失效（`admit-stale`）。merge 一律帶 `--match-head-commit`，HEAD 漂移即失敗。
- Codex user rule 只處理 sandbox execpolicy，不能覆蓋 repository PreToolUse hook、GitHub branch rule
  或人類 gate；若下游層拒絕，必須停下報告衝突。
- 不以 LOC、commit 數或個人排名衡量速度。
