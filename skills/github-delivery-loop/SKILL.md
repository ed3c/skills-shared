---
name: github-delivery-loop
description: |
  把大小迴圈的本地產物綁到 GitHub PRD issue、slice issues、PR 與 Project，並以零網路
  delivery receipt 閘阻止「產物缺席卻顯示成功」；merge 由四層授權堆疊守門，開工前以
  merge_gate.py preflight 用每個 host 自己的閘真跑一次，把「哪一層會拒絕」從執行期提前到
  開工前；private repo 的 CI publication 另以本地驗證收據、三種 publication intent 與帳務
  circuit breaker 守門，避免每個微小 commit 都燒一個 Actions job-minute。適用於交付追蹤、
  迭代速度量測、worktree 切線、小迴圈 handoff、GitHub Actions 使用/浪費、以及
  「merge 權限被擋／換個 host 又被擋」的診斷與根治。
  觸發詞：看板進度、delivery 收據、issue 驅動實作、worktree 切線、merge 被擋、
  merge 權限、preflight、merge-admit、github-delivery-loop。
  人類 admit 是預設；也支援使用者明確配置的 personal-owner 自動放行，但不取代 TDD、code review、
  GitHub required checks 或 public gate。
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
   40 字元 export source commit，以及該 commit 的 tree sha（artifact 就是 repo 本身時即
   `git rev-parse <export-source-commit>^{tree}`）；測試與重播改用 `--snapshot <json>`，
   不得在測試中打網路。`initial-pr` 另須由 raw transport 對 exact
   `refs/heads/<branch>` 的獨立查詢證明 remote branch 不存在；「查不到 PR」不能替代這個證據。
5. 每張 issue 在隔離 worktree 走 TDD → review；**本地 commit 可以高頻，remote push 不可以**。
   private repo 先以 `scripts/ci_publish.py verify` 產生 exact-HEAD 收據，再由同一腳本的
   `publish` 子命令走唯一 GitHub 發佈路徑；PR body 使用 `Closes #N`。
6. Merge 走下節的 authority → preflight → land；漂移或新發現另開 issue，不塞進正在進行的 slice。

## Private-repo CI publication gate

完整 snapshot schema、三種合法 publication intent、帳務熔斷與 workflow 觸發建議見
[modules/ci-publication.md](modules/ci-publication.md)。零網路判定入口：

```bash
python3 ~/.claude/skills/github-delivery-loop/scripts/ci_publish_gate.py evaluate \
  --repo-root /absolute/repo \
  --snapshot /tmp/github-actions-publish.json \
  --verification /absolute/repo/.git/github-delivery/local-verification.json \
  --evidence /absolute/repo/.git/github-delivery/local-verification-evidence.json \
  --verification-contract /absolute/repo/.github-delivery/local-verification-contract.json \
  --intent initial-pr --json
```

這支 `scripts/ci_publish_gate.py` 只承認 `initial-pr`、`ready-for-review`、`batched-repair`
三種 intent，且只有 decision=`ALLOW` 才進下一層。
`checkpoint`、驗證不是 exact HEAD、需要新 head 的 intent 卻沒有新 SHA、同一 feedback 已發佈，
或 account billing no-runner circuit 未被 owner 的較新
recovery receipt 關閉，都必須停止；禁止以 rerun、no-op commit 或改 intent 拼字繞過。

`scripts/ci_publish.py` 是受管 private repo 的唯一網路發佈入口：`verify` 先跑
`.github-delivery/ci-policy.json` 指向唯一的本地驗證 contract，由 `local_verification.py` 執行固定
argv 並把 receipt/evidence 放進 git-dir；`publish` 再重驗
workflow policy、git HEAD、receipt、snapshot 與 GitHub remote identity，最後以完整 SHA refspec push。
`initial-pr` 同一 admission 會建立 draft PR；`ready-for-review` 在 head 已相同時只執行
`gh pr ready`，否則先推 final batch 再轉 ready；
`draft-first` batched repair 會 dispatch policy 指定的 workflow，`universal` batched repair 則由
snapshot 釘住的 PR head ref 之 `synchronize` 事件執行，禁止同 SHA 再 dispatch。
省略 `--execute` 必為 dry-run。

```bash
python3 ~/.claude/skills/github-delivery-loop/scripts/ci_workflow_policy.py check \
  --repo-root /absolute/repo
python3 ~/.claude/skills/github-delivery-loop/scripts/ci_publish.py verify \
  --repo-root /absolute/repo
python3 ~/.claude/skills/github-delivery-loop/scripts/ci_publish.py publish \
  --repo-root /absolute/repo --snapshot /tmp/github-actions-publish.json \
  --intent initial-pr --remote github --branch agent/feature \
  --pr-title 'Feature' --pr-body 'Closes #N' --execute
```

`scripts/ci_publish_guard.py` 是兩個 host 共用的 PreToolUse guard：只有 repo 已登記
`.github-delivery/ci-policy.json` 且目標 remote 是 GitHub 時，才阻擋原始 `git push`；同 repo 的
Forgejo remote 不受影響。以 `scripts/install-ci-publish-guard.py` 安裝，預設 dry-run、`--apply`
才原子寫入 Codex/Claude hook 設定並保留一次備份。它攔的是 Agent tool surface，不是假裝能攔人類
terminal 或第三方 bot。

evaluator 本身不執行 push，也不把本地 receipt 冒充 GitHub check。真正 merge 仍須 latest SHA 的
可信 GitHub check 與下節四層閘。

## 新專案套用（一句，冪等）

預設 human-admit 模式中，真正 per-repo 的只有 `merge-admit` label 與 execpolicy 窄規則。在新 repo 裡跑：

```bash
python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py bootstrap
```

`--repo` 省略時從 cwd 的 git remote 推。已存在就印 `OK` 不重建，最後接一次 preflight 印出四層現況。
全域／per-repo 的完整分界表 → [modules/host-permissions.md §4](modules/host-permissions.md)。

若使用者明確要求「我個人擁有的現在與未來 repo 自動放行」，一次配置 immutable GitHub User 身分：

```bash
python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py configure-owner --owner LOGIN
```

之後不用逐 PR label，也不用逐 repo bootstrap。每次 preflight／land 都即時要求：authenticated viewer、
repository owner 的 login＋numeric ID 同時等於 policy、owner type 是 `User`、且有 admin。**只是 collaborator、
organization member／owner，甚至在他人 repo 有 admin 都拒絕**。login 改名、repo redirect 或 policy 損壞也 fail closed。

## Merge authority（預設人 admit；明確 opt-in 才 owner-auto）

merge 不是一個「有／無權限」位元，是四層獨立閘：L1 authority、L2 host shell policy、
L3 GitHub、L4 merge 本身。任一層拒絕就不得宣稱已放行。堆疊語意見
[delivery-mechanism.md § Merge authority stack](modules/delivery-mechanism.md#merge-authority-stack)。

**L2 在單一 host 內可能不只一個平面**：Claude Code 是 PreToolUse hook；Codex 是
PreToolUse hook × sandbox network profile × execpolicy，三者互不相干，任一擋住就是擋住。
preflight 三個都驗——少驗一個平面就會把「還會被擋」報成綠燈（見 host-permissions.md §2 漏報事故）。

1. **L1 authority（二選一）**：預設是 repo owner 在 GitHub 對可落地 PR 貼 `merge-admit` label；
   owner-auto 只有在上述 policy 存在時啟用，用 immutable owner/viewer identity 取代逐 PR label。
   它不接受「有 admin」作為 ownership 的替代證據。
2. **preflight**（開工前就跑，不要等到 PR 開好）——它把合成的 PreToolUse payload 餵進實際設定的
   hook、呼叫 `codex execpolicy check`、讀 `.codex/config.toml` 的 network 授權，**真跑每個 host
   自己的閘，不推論**；非 active host 只報告不阻擋：

   ```bash
   python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py preflight --repo OWNER/REPO [--pr N]
   ```

   一條 delivery line 只交付一張 PR 時，`preflight` 與下方 `land` **兩邊都要帶同一個
   `--pr N`**。live 模式直接讀該 PR，snapshot 模式要求該號碼恰好出現一次；缺席、重覆或非正整數
   都 fail closed。省略 `--pr` 是刻意選擇「評估所有已授權 open PR」，不是單張交付的安全預設。

   `exit 0` 可落地｜`1` 有一層拒絕（stderr 指名層、PR 與確切修法）｜`3` 沒有任何 PR 被 admit
   （**缺席，不是拒絕**——別去修一個不存在的權限問題）｜`4` 某一層**判不出來**
   （**無能，不是拒絕**——修的是 hook 設定或這支探測器，永遠不是修權限）。

3. **land**：綠了才落地。每張 PR 落地前重取快照並釘住 HEAD；human-admit 使用
   `--match-head-commit`，owner-auto 用 GraphQL `expectedHeadOid`，語意相同。owner-auto 不覆寫
   commit email（交給 GitHub 帳號的 web Git privacy 設定），不使用 `--admin`，也忽略 `--allow-unstable` 的放寬；
   全量模式會在 base 移動後自動重算下一張；`--pr N` 模式成功合併一次就停止，不掃描其他 PR。
   跨 invocation 重跑時先查該 PR 是否已有 auto-merge request／merge queue entry，有就不重送；merge
   command exit 0 只代表 GitHub 接受請求，必須回讀同一 HEAD 的 `MERGED` 與非空 `mergedAt` 才能報
   `LANDED`。仍是 `OPEN` 或已存在 pending request 回傳 `5`，`CLOSED`、HEAD 漂移或不可判讀都 fail closed。

   ```bash
   python3 ~/.claude/skills/github-delivery-loop/scripts/merge_gate.py land --repo OWNER/REPO [--pr N] [--dry-run]
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

完整 machine-support 索引如下；入口說明分別在
[modules/README.md](modules/README.md) 與 [scripts/README.md](scripts/README.md)：

- modules： [ci-publication](modules/ci-publication.md)、
  [commit-role](modules/commit-role.md)、
  [delivery-mechanism](modules/delivery-mechanism.md)、
  [github-actions-cost-control](modules/github-actions-cost-control.md)、
  [host-permissions](modules/host-permissions.md)、
  [state-machines](modules/state-machines.md)、
  [traceability-index](modules/traceability-index.md)。
- scripts： `scripts/ci_publish.py`、`scripts/ci_publish_gate.py`、
  `scripts/ci_publish_guard.py`、`scripts/ci_workflow_policy.py`、
  `scripts/delivery_sync.py`、`scripts/delivery_sync_impl.py`、
  `scripts/github_actions_snapshot.py`、`scripts/github_delivery.py`、
  `scripts/install-ci-publish-guard.py`、`scripts/install-codex-merge-rule.sh`、
  `scripts/link-canonical.sh`、`scripts/local_verification.py`、
  `scripts/merge_gate.py`、`scripts/reference_causality.py`。

規則不靠人記得，靠 `tests/index/verify.sh`（`tests/run-all.sh` 自動探索）：它先跑 checker
自己的 `--selftest`，再驗本檔——**checker 不能證明自己會紅之前，它對本檔的綠燈不算數**。

## 硬閘

- artifact 不存在是 `UNMATERIALIZED` 失敗，不是 SKIP。
- receipt/publication attestation 缺席、身份漂移、假 URL 或短 SHA 都失敗。
- publication attestation 必須把 `export_tree_sha` 釘回遠端 head 的 tree；不相等就是
  `export-tree-drift` blocker，file count 與 orphan history 相符不足以證明推上去的就是驗過的樹。
- 本地 `check` 與 `preflight --snapshot` 零網路；GitHub 活狀態由 `sync --github` 與
  `preflight`（無 `--snapshot`）負責，兩種證據不得混稱。
- `ci_publish_gate.py evaluate` 同樣零網路；snapshot 的 GitHub/owner recovery 活證據必須由外部
  sync 或人工附上可查 URL，shape 通過不等於帳務已恢復。
- `ci_workflow_policy.py check` 是 repo 密封閘：`pull_request_mode` 缺省／`draft-first` 時 PR 只准
  `ready_for_review`；只有 repo 明確選 `universal` 才精確准
  `opened,synchronize,reopened`。`ready_for_review` 不改 head，若保留會在 universal ready 發佈時
  對同 SHA 重複執行。push 只准 default branch、必須有 manual
  dispatch/concurrency，且 action 一律釘完整 SHA；少一項就不得 enroll。
- `ci_publish_guard.py` 對解析後明確指向 GitHub 的 push fail closed，直接 argv 與可靜態解析的
  Forgejo push 仍保留。legacy hook 只給 shell 字串，並不是解析後 process event；因此帶
  `$`/backtick 展開、且仍能以 literal Git invocation 定位到 enrolled repo 的 shell 包裝一律
  fail closed。任意 shell 可計算 executable/path/remote 不在此 parser 的 sound boundary；完整
  保證必須把 guard 放在 shell evaluation 之後，接收 resolved executable/argv/cwd/env/remote。
- repository identity 釘 immutable GitHub node ID；owner/name 只作可轉移別名，redirect 不得冒充身份證據。
- human-admit 的 `merge-admit` 只有 **repo owner 施加、且晚於 head commit** 才算數；owner-auto 則每次
  重驗 immutable viewer／personal owner。兩種模式都 pin HEAD，漂移即失敗。
- Codex user rule 只處理 sandbox execpolicy，不能覆蓋 repository PreToolUse hook、GitHub branch rule
  或人類 gate；若下游層拒絕，必須停下報告衝突。
- 不以 LOC、commit 數或個人排名衡量速度。
