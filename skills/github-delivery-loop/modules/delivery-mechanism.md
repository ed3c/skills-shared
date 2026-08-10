# Delivery mechanism

## 邊界與資料流

```text
small loop ──materializes──> artifact_path
     │                            │
     └──writes receipt────────────┘
                                  ↓
registry ───────────────> zero-network check
                                  ↓
GitHub sync ────────────> publication attestation + metrics
```

小迴圈擁有實作與驗證；delivery engine 擁有 GitHub 同步與量測。receipt 是唯一交界，避免
delivery 流程侵入各 loop 的 prompt SSOT。

## Registry v1

`.github-delivery/registry.json`：

```json
{
  "schema": "github-delivery-registry/v1",
  "repo_root": "..",
  "lines": [{
    "id": "portable-loop",
    "github_repo": "owner/repository",
    "artifact_path": "loop_wiki/portable-loop",
    "receipt_path": ".github-delivery/receipts/portable-loop.json",
    "publication_path": ".github-delivery/publications/portable-loop.json"
  }]
}
```

所有路徑相對 `repo_root`；不可用絕對路徑或 `..` 逃逸。registry 必須至少有一條 line，空表
不代表成功。每條 line 另釘 `github_repository_id`（GitHub GraphQL node ID）；owner/repo 可以因
transfer 改名，node ID 才是身份。sync 接受同 node 的 canonical URL 更新，拒絕「同名但不同 node」。

## Receipt v1

receipt 必須含 schema、line、github_repo、prd_issue_url、issue_urls、pr_urls、project_url、
40 字元 source_commit 與 ISO-8601 synced_at。URL 必須是該 repository 的真實 GitHub issue／PR
形狀；`"u"` 之類 placeholder 會被拒絕。

## Publication attestation v1

publication attestation 把遠端 clean tree 釘回本地證據：remote URL、visibility、遠端 commit、
export source commit、export tree sha、file count、是否擁有 parentless history root、license SPDX、
public readiness、blockers 與最後查驗時間。`check` 只驗本地 attestation 的形狀與 line identity；
產生或更新它的 GitHub 查證是網路 sync 的責任，不可把本地 shape check 冒充遠端即時查證。

### Export tree binding

「push 前驗證通過」若沒有把驗過的東西釘回推上去的東西，就是不可否證的宣稱：file count 相同、
history root 為真的樹，內容仍可以完全不同。所以 `verify` 回傳它驗過那棵樹的 Git tree id，
`sync` 以 `--export-tree-sha` 收下，並與遠端 default branch head 的 tree sha 比對：

```text
public_export.py verify ──> tree_sha ──┐
                                       ├─ 相等？──> 否 ──> blocker: export-tree-drift
GitHub head commit ────────> tree_sha ─┘
```

tree id 由 blob 內容與檔案 mode 共同決定，所以位元組漂移與 executable bit 漂移都會改變它；
比對只用 sync 既有的 head commit 查詢，不下載任何遠端 blob。`verify` 同時比對 staged mode 與
commit 內 mode，讓 mode 漂移在能被 attest 之前就失敗。

## Merge authority stack

Merge 不是單一「有／無權限」位元，而是由多層獨立閘串接；任一層拒絕就不得宣稱已放行：

```text
L1 authority (human admit OR explicit personal-owner policy)
        ↓
Codex execpolicy prefix rule
        ↓
active repository / platform PreToolUse hooks
        ↓
GitHub authentication + branch / repository rules
        ↓
merge API
```

1. **Authority gate**：預設是 owner 對指定 PR 的 fresh label；只有使用者明確 opt-in 時，才可改成
   personal-owner policy。後者以 authenticated viewer 與 repository owner 的 immutable user ID 每次重驗，
   讓同一人擁有的未來 repo 自動納入、collaborator／organization repo 排除。永久 command allow 本身
   兩種模式下都不構成 landing decision。
2. **Codex execpolicy**：user-level `prefix_rule` 只決定某個 argv prefix 能否離開 sandbox 執行。
   human-admit 規則釘到 `gh pr merge --repo OWNER/REPOSITORY`；owner-auto 規則釘到 canonical
   `merge_gate.py land --repo` wrapper，絕不放行 generic `gh api graphql`。參數順序是 prefix contract
   的一部分。寫入 active `rules/` 後必須重啟 Codex，並用
   `codex execpolicy check` 驗證結果。
3. **PreToolUse hooks**：hook 與 execpolicy 是不同 policy plane。即使 execpolicy 顯示 `allow`，hook
   仍可拒絕相同 shell command，甚至拒絕 connector merge tool。最嚴格決策勝出；不得用換 API、
   command obfuscation 或停用 hook 逃逸，應回報命中的 policy 與所需 owner 變更。
4. **GitHub gate**：最後仍受 token/repository 權限、branch protection、required checks、HEAD 漂移
   與 mergeability 約束。merge 前釘 expected HEAD；每次 base 更新後重新查下一張 PR。

安裝窄規則的可重播入口：

```bash
bash <repo>/.agents/skills/github-delivery-loop/scripts/install-codex-merge-rule.sh \
  --repo OWNER/REPOSITORY \
  --rules-dir /Users/neon/.codex/rules
```

安裝器會備份同名規則、原子替換、跑 `codex execpolicy check`，並明示它不能覆蓋 hook、runtime
identity gate 或 GitHub gate。這個邊界來自實測：user rule 已成功載入後，active PreToolUse blacklist 仍先於 shell 與
GitHub connector merge 執行，證明兩層不可混稱。

Codex rules 的檔案位置、restart requirement、prefix token matching 與「最嚴格決策勝出」語義，
以官方 [Rules](https://learn.chatgpt.com/docs/agent-configuration/rules.md) 為準；本 skill 只保存
delivery 邊界與可重播安裝器，不複製整份產品手冊。

## 速度 SSOT

速度由 GitHub 事件時間戳即時計算，不把衍生數字寫回 registry：

- lead time：issue 建立 → merge
- queue time：issue 建立 → 首次實作事件
- cycle time：首次實作事件 → merge
- review time：PR ready-for-review → merge
- blocked time：blocked 區間總和
- WIP、throughput、first-pass rate、reopen rate、redaction leakage rate

這些是流程健康度，不是個人生產力排名。Project 是投影，issue/PR event 才是事件真相。

## Sync 與 dashboard

`sync --github` 透過已登入的 `gh` 讀 repository、issues、issue events、pulls、reviews 與 Project，
先在記憶體完成 identity/schema/時間順序驗證，再一起替換 receipt、publication attestation、metrics
JSON 與 Markdown dashboard。`--snapshot` 使用同一條推導路徑離線重播，避免測試與歷史審計依賴網路。

- 只有帶 `Closes/Fixes/Resolves #N` 且 merged 的 PR 才算 accepted slice。
- closed issue 沒有 merge evidence 會列為 `closed_without_merge`，不灌進 throughput。
- `Part of #N` 只建立 started/queue 關係，不宣稱 accepted。
- blocked time 由 blocked label 的 labeled→unlabeled/closed/snapshot 區間派生。
- 樣本不存在時 p50/p85 與 first-pass 必須是 `null`，不可補零。

## 四層原生儀表板（為什麼不自建進度工具）

進度不自建工具，疊四層 GitHub 原生機制，由下而上，每層只做一件事：

| 層 | 載體 | 職責 |
|---|---|---|
| 1 規格根 | **PRD issue** | Problem／Solution／User Stories／Implementation & Testing Decisions／Out-of-scope，決策完整；任何 slice 的「為什麼」都能在這一頁找到，不需口傳背景 |
| 2 工作單 | **slice issues** | 每張帶 `## Parent` 回鏈 PRD＋acceptance criteria checkbox（GitHub 原生渲染成進度條）＋`Blocked by` 依賴序；依賴是文字契約＋人讀，不裝依賴外掛 |
| 3 交付載體 | **PR** | 分子 commit 鏈保留每步意圖；body `Closes #N` 使 merge 瞬間自動關工作單 |
| 4 橫向視圖 | **Projects 看板** | issue 開/關經內建 workflow 自動投影成卡片泳道，可跨 repo 同板 |

新開一條線按 1→2→4 鋪（PRD → slices → 掛板），實作期只產生第 3 層。

為什麼是「疊四層原生」而不是自建儀表板：每層的狀態轉移都由 GitHub 原生事件驅動
（merge→close→board），零自建代碼＝零維護面＝零「儀表板本身漂移」的新病種。
看板永遠是投影，不是第二份真相——手動拖卡只改視圖，真相仍在 issue 狀態。
receipt 記的正是這四層的 URL，把本地物化的產物釘到四層儀表板上；零網路的 `check`
只驗 receipt 的形狀與 identity，**不**在 commit 時打網路查四層活狀態。

## 三種提示的放置鐵律

小迴圈 exchange packet 既有三個欄位，分界不是風格而是治理：

- **固定提示**（規範，改動＝治理事件）→ `modules/development-standards.md` 等規範模組。
  它的每一行都經過人 admit，下游（test-before-code 閘、archetype 判定）直接消費。
- **自動提示**（迭代上下文，機器生成）→ packet 的 `iteration_auto_context` 與
  `_engine-run/loop-auto-prompt.*`。
- **湧現提示**（執行中冒出的未裁決新知）→ packet 的 `emergent_prompt_context` ＋ issue 內文；
  **禁寫入規範模組**。直接寫進規範模組等於讓未裁決內容穿上規範外衣——這正是
  「禁把 candidate 升格為 proof」要擋的路徑。湧現知識先落 packet／issue（可追溯、帶時間點
  與證據），沉澱後由 fold-in 判 durable home；真值得成為規範，才由人 admit 升格。
