# Delivery mechanism (GitLab)

平台差異的完整帳本在 [github-vs-gitlab.md](github-vs-gitlab.md)；本檔只寫 GitLab 這一側的
schema、狀態流與速度定義。

## 邊界與資料流

```text
small loop ──materializes──> artifact_path
     │                            │
     └──writes receipt────────────┘
                                  ↓
registry ───────────────> zero-network check
                                  ↓
GitLab sync ────────────> publication attestation + metrics
```

小迴圈擁有實作與驗證；delivery engine 擁有 GitLab 同步與量測。receipt 是唯一交界，避免
delivery 流程侵入各 loop 的 prompt SSOT。

## Registry v1

`.gitlab-delivery/registry.json`（**目錄名與 GitHub 版分開**，兩份 registry 不共用檔案）：

```json
{
  "schema": "gitlab-delivery-registry/v1",
  "repo_root": "..",
  "lines": [{
    "id": "portable-loop",
    "gitlab_host": "gitlab.com",
    "gitlab_project": "group/subgroup/project",
    "gitlab_project_id": 34675721,
    "artifact_path": "loop_wiki/portable-loop",
    "receipt_path": ".gitlab-delivery/receipts/portable-loop.json",
    "publication_path": ".gitlab-delivery/publications/portable-loop.json"
  }]
}
```

所有路徑相對 `repo_root`；不可用絕對路徑或 `..` 逃逸。registry 必須至少有一條 line，空表
不代表成功。

`gitlab_project_id` 是**數字**，是身份；`gitlab_project` 是可因 transfer／rename 改變的別名。
sync 以 id 比對，不相等即拒絕——路徑相同但 id 不同代表那是另一個專案。
`gitlab_host` 一起釘，因為同一條路徑在 gitlab.com 與自架實例上是兩個不同的東西。

## Receipt v1

必須含 schema、line、gitlab_host、gitlab_project、gitlab_project_id、prd_issue_url、
issue_urls、**mr_urls**（不是 pr_urls）、board_url、40 字元 source_commit 與 ISO-8601 synced_at。

URL 必須是該專案的真實 GitLab 形狀，含 `/-/` 分隔：

```text
https://<host>/<group>/<project>/-/issues/N        （產出用這個）
https://<host>/<group>/<project>/-/work_items/N    （API 回傳的別名，驗證時也收）
https://<host>/<group>/<project>/-/merge_requests/N
https://<host>/<group>/<project>/-/boards/N
```

`"u"` 之類 placeholder、以及任何 `github.com` URL 都會被拒。

## Publication attestation v1

把遠端 clean tree 釘回本地證據：remote URL、visibility、遠端 commit、export source commit、
export tree sha、**remote head tree sha**、file count、是否擁有 parentless history root、
license key、public readiness、blockers 與最後查驗時間。

`check` 只驗本地 attestation 的形狀與 line identity；產生它的 GitLab 查證是 sync 的責任，
不可把本地 shape check 冒充遠端即時查證。

### Export tree binding（GitLab 版必然不同）

「push 前驗證通過」若沒有把驗過的東西釘回推上去的東西，就是不可否證的宣稱。
GitHub 靠 API 回傳的 head commit tree sha 做這件事；**GitLab 不提供任何 root tree id**
（REST commit 無 tree 欄位、GraphQL `Tree` 無 `sha`，兩者皆實跑確認）。

所以綁定在本地完成——export clone 就是被推上去的那份，它必然含有 GitLab 回報的 head commit：

```text
public_export verify ──> export_tree_sha ──┐
                                           ├─ 相等？──> 否 ──> blocker: export-tree-drift
git rev-parse <remote head>^{tree} ────────┘
                     │
                     └─ 解不出來 ──> blocker: remote-head-unverifiable
```

第二條出口是重點：commit 不在本地代表**別人推過**，此時本地沒有任何東西能證明那棵樹——
這與「樹不同」是兩件事，必須長得不一樣。`--export-repo` 指定那份 clone，預設 `repo_root`。

## Merge authority stack

Merge 不是單一「有／無權限」位元，而是由多層獨立閘串接；任一層拒絕就不得宣稱已放行：

```text
human merge decision   (merge-admit label, applied by a project Owner)
        ↓
Codex execpolicy prefix rule
        ↓
active repository / platform PreToolUse hooks
        ↓
GitLab authentication + protected branch / approval rules
        ↓
merge API   (glab mr merge --sha ... --auto-merge=false)
```

1. **人類 gate**：owner 明確指定專案與 MR 才構成 merge 授權。永久 command allow 不是人類
   landing decision。GitLab 沒有單一 `owner` 欄位可比對（group 專案為 null），
   所以判準是 **access_level ≥ 50**，或個人 namespace 的擁有者本人。
2. **Codex execpolicy**：user-level `prefix_rule` 只決定某個 argv prefix 能否離開 sandbox。
   規則釘到 `glab mr merge -R https://<host>/<project>`，不可放寬成 `glab` 或 `glab mr`；
   參數順序是 prefix contract 的一部分。寫入 active `rules/` 後必須重啟 Codex。
3. **PreToolUse hooks**：hook 與 execpolicy 是不同 policy plane。即使 execpolicy 顯示 `allow`，
   hook 仍可拒絕相同 shell command。最嚴格決策勝出；不得用換 API、command obfuscation 或
   停用 hook 逃逸，應回報命中的 policy 與所需 owner 變更。
4. **GitLab gate**：仍受 token scope、protected branch、required approvals、
   `detailed_merge_status` 與 HEAD 漂移約束。merge 一律帶 `--sha`。

安裝窄規則的可重播入口：

```bash
bash ~/.agents/skills/gitlab-delivery-loop/scripts/install-codex-merge-rule.sh \
  --host gitlab.com --project GROUP/SUBGROUP/PROJECT \
  --rules-dir /Users/neon/.codex/rules
```

安裝器會備份同名規則、原子替換、用 **land 的真實 argv 形狀**跑
`codex execpolicy check`，並明示它不能覆蓋 hook 或人類 gate，也不能約束尾隨旗標。

## 速度 SSOT

速度由 GitLab 事件時間戳即時計算，不把衍生數字寫回 registry：

- lead time：issue 建立 → merge
- queue time：issue 建立 → 首次實作事件
- cycle time：首次實作事件 → merge
- review time：MR ready → merge
- blocked time：blocked 區間總和（由 `resource_label_events` 的 add→remove 派生）
- WIP、throughput、reopen rate、redaction leakage rate

**first-pass rate 在 GitLab 沒有等價物**，輸出恆為 `null` 並附 `first_pass_rate_absent` 原因。
不補零——補零會讓「量不到」讀起來像「首過率 0」。

這些是流程健康度，不是個人生產力排名。Board 是投影，issue/MR event 才是事件真相。

## Sync 與 dashboard

`sync --gitlab` 透過已登入的 `glab` 讀 project、issues、resource label/state events、
merge requests 與 board，先在記憶體完成 identity/schema/時間順序驗證，再一起替換 receipt、
publication attestation、metrics JSON 與 Markdown dashboard。
`--snapshot` 使用同一條推導路徑離線重播，避免測試與歷史審計依賴網路。

- 只有帶 GitLab closing keyword（`Closes/Fixes/Resolves/Implements #N` 及其時態變化）
  且已 merged 的 MR 才算 accepted slice。
- closed issue 沒有 merge evidence 會列為 `closed_without_merge`，不灌進 throughput。
- `Part of #N` 只建立 started/queue 關係，不宣稱 accepted。**這是本 skill 的慣例，
  不是 GitLab keyword**——GitLab 不會因為它自動關閉任何東西。
- 跨專案引用（`group/project#N`）刻意不處理：本 registry line 只對一個專案負責。
- 樣本不存在時 p50/p85 必須是 `null`，不可補零。

## 四層原生儀表板（為什麼不自建進度工具）

| 層 | 載體 | 職責 |
|---|---|---|
| 1 規格根 | **PRD issue** | Problem／Solution／User Stories／Implementation & Testing Decisions／Out-of-scope，決策完整 |
| 2 工作單 | **slice issues** | 每張帶 `## Parent` 回鏈 PRD＋acceptance criteria checkbox（GitLab 原生渲染成 task 進度）＋`Blocked by` 依賴序 |
| 3 交付載體 | **MR** | 分子 commit 鏈保留每步意圖；description 用 `Closes #N` 使 merge 瞬間自動關工作單 |
| 4 橫向視圖 | **Issue Board** | issue label／狀態經內建 workflow 自動投影成卡片泳道 |

新開一條線按 1→2→4 鋪，實作期只產生第 3 層。

為什麼是「疊四層原生」而不是自建儀表板：每層的狀態轉移都由 GitLab 原生事件驅動
（merge→close→board），零自建代碼＝零維護面＝零「儀表板本身漂移」的新病種。
看板永遠是投影，不是第二份真相。receipt 記的正是這四層的 URL；零網路的 `check`
只驗 receipt 的形狀與 identity，**不**在 commit 時打網路查四層活狀態。

GitLab 的 board 與 GitHub Projects 有一處實質差異：Projects v2 可跨 repo，
GitLab board 綁在專案或 group。要跨專案就得建 group board，那是 group 層物件，
不歸 per-project 的 `bootstrap` 管。

## 三種提示的放置鐵律

小迴圈 exchange packet 既有三個欄位，分界不是風格而是治理：

- **固定提示**（規範，改動＝治理事件）→ 規範模組。每一行都經過人 admit。
- **自動提示**（迭代上下文，機器生成）→ packet 的 `iteration_auto_context`。
- **湧現提示**（執行中冒出的未裁決新知）→ packet 的 `emergent_prompt_context` ＋ issue 內文；
  **禁寫入規範模組**。直接寫進規範模組等於讓未裁決內容穿上規範外衣。
