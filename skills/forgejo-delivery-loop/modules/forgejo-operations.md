# Module: forgejo-operations — 驅動本機 Forgejo 的操作層

> 屬 [`forgejo-delivery-loop`](../SKILL.md)。SKILL.md 管「追蹤什麼」（四層儀表板／registry／
> 收據閘／goal 迴圈）；本檔管「怎麼安全地動它」——登入、唯讀預檢、typed request、idempotency
> marker、fail-closed、降級恢復。
>
> 2026-08-07 由獨立 skill `forgejo-loop-ops` 併入（人裁）。兩者本來就是同一條迴圈的兩層：
> 追蹤面沒有操作層就只能靠人點 UI，操作層沒有追蹤面就不知道該動哪一條線。分成兩個名字，
> 只是讓「先跑哪一支」變成每次都要重新想的問題。

這是大小迴圈到本機 Forgejo 的操作層，不是另一個 Git writer。
先執行確定性 router，再依 route 只載入需要的 operator。

```bash
bun run <本skill>/scripts/route.ts --input <route-input.json>
```

## 不變量

1. 只允許 `http://localhost:3000` 與 `http://127.0.0.1:3000`。
   GitHub、GitLab、外部 Forgejo、webhook、mirror 與 remote runner 不適用。
2. 需要瀏覽器狀態時只用使用者現有 Chrome 與 `chrome:control-chrome`。
   禁止開測試瀏覽器、無痕視窗或新的登入 profile。
3. 登入頁確實出現時，先查現有 Chrome 是否已有 session。
   若仍未登入，才可用 `git credential fill` 取得 `localhost:3000` 憑證並直接填入表單。
   憑證只留在記憶體；禁止回顯、寫檔、寫 receipt、貼進 issue 或 commit。
   若 helper 缺憑證，停止登入操作並由 host operator 執行
   `<runtime-env-root>/runtime-env local-env migrate-forgejo-keychain`。該 broker 擁有
   dotenv → macOS Keychain 的唯一遷移責任；本 skill 禁止 source、解析或複製 `.env`。
4. Forgejo 是工作狀態與下一步投影，不是真相來源。
   Git commit、source lineage、typed receipt 與 schema readback 才是證據 SSOT。
5. 大迴圈只排程、限流與投影。每個外部 mutation 必須下沉成一個小迴圈。
   小迴圈只處理一個 terminal slice，並以 idempotency marker 回讀。
6. repo 內容、branch、remote、push 與 commit 只交給輸出 repo 的
   `repo-terminal-operator`。本 Skill 不切主工作樹 branch、不改 `origin`、不 force push、
   不使用 `--allow-unrelated-histories`，也不提供任何 skip-gate 入口。
7. `automatic_execution:false`、缺 admission、缺 repo identity、缺 marker search 或 auth 失敗時，
   mutation 必須 fail closed。HTTP 成功但 response body／readback 不符也算失敗。
8. 私人 Gmail／Gemini／DR／GCR 原文不得進 Forgejo；issue 只放 paraphrase、acceptance criteria、
   artifact path、claim ID 與 hash-bound lineage。

## Stateful workflow

```mermaid
flowchart LR
  M[M0 Match<br/>平台·大小迴圈·操作] --> G[G0 Generate<br/>唯讀預檢·typed request]
  G -->|需要 repo 寫入| R[repo-local operator<br/>CQ + production-use]
  G -->|需要既有登入狀態| C[既有 Chrome<br/>登入·搜尋·操作]
  G -->|大迴圈| Q[bounded queue<br/>投影成單一小迴圈]
  R --> V[V0 Validate<br/>marker·API/UI readback·receipt]
  C --> V
  Q --> M
  V -->|PASS| N[next-mode prompt]
  V -->|FAIL| D[degraded/outbox<br/>禁止 merge·release·admit]
```

### M0 — Match

建立 `forgejo-loop-route-input@v1`：

- `platform`：只有 `local-forgejo` 會觸發。
- `loop_size`：`large` 只編排；`small` 才可執行一個外部 mutation。
- `operation`：`status | login | repository-bootstrap | issue | pull-request | merge | git-write | recover`。
- `auth_state`：`authenticated | login-required | not-selected`。
- `request_state`：`absent | projected | admitted`。
- `repo_local_operator_ready`：repo-local CQ／production-use 與 branch handoff 是否已就緒。

執行 router 並採用輸出的唯一 `actor`、`mode`、`mutation_allowed` 與 `next_prompt`。
不得在模型內另寫一套平行路由規則。

### G0 — Generate and preflight

1. 唯讀確認 Forgejo version、目前 auth、精確 repository full name、Git remote 與 branch。
   repository 不存在時不得把 issue 404 當暫時錯誤重試；先投影一個獨立的
   `repository-bootstrap` 小迴圈，建立後回讀 owner／name／visibility，再交 repo-local operator 配 remote。
2. issue 終態操作先產生 `forgejo-terminal-issue-state-request@v2`，再執行：
   `python3 <本skill>/scripts/issue_state.py validate --request <request.json>` 與
   `validate-source-live`。
   它只接受 loopback Forgejo、明確 user admission、完整 GitHub source closure lineage，且
   authenticated GitHub read 必須證明 issue closed、PR merged、merge SHA 與 `Closes #N` 關係；
   expected/desired 必須確實形成狀態轉移。缺任一欄位或語義不符就停止。
3. mutation 前以 `capture-pre-live` 從 authenticated Forgejo API 讀回 expected state，並在 issue
   body 搜尋完整 source URL idempotency marker。
   找到便回用既有 issue，不得建立第二張。
4. 若 route 指向 `repo-terminal-operator`，只交付 typed terminal packet；
   operator 完成 focused CQ／production-use 與分子 commit 後再回本流程。
5. 若 route 指向 Chrome，先讀並使用 `chrome:control-chrome`；
   操作現有 tab，逐步觀察頁面，不以預期 UI 冒充實際結果。

### V0 — Validate and advance

每次操作完成都重新讀取目標物，至少核對 repository、issue／PR number、marker、head／merge SHA
與 HTTP/UI 狀態。issue 終態以 `forgejo-issue-state-observation@v1` 保存 mutation 前的 authenticated
API observation，再執行：`python3 <本skill>/scripts/issue_state.py verify-live --request
<request.json> --pre-observation <pre-observation.json>`。此命令自行重新讀取 Forgejo 後態；呼叫者
不能傳入自填 post observation，且必須從 authenticated timeline 找到 pre-read 後五分鐘內唯一的
close event。任何不一致回 `failed`，保留原始錯誤因果與下一個修復 prompt。

- 小迴圈 PASS：回傳單一 terminal receipt、Forgejo URL／number 與下一個合法 mode。
- 大迴圈 PASS：只更新 queue projection；一次最多十個 open gaps、每個 repo 最多一個
  `in-progress` terminal slice。
- merge、release、admission 永遠需要各自的 typed readback 與人閘；issue 關閉不能代理 admission。

## 降級與恢復

Forgejo 不健康時只在使用者已授權服務恢復的範圍內做最多三次有界重啟。
每次都重新跑 version／auth／repository canary。三次仍失敗就把操作寫入 append-only outbox，
保留 idempotency key 與 payload hash；本機實作可繼續，但 merge、release、admit 一律禁止。
恢復後按 key 重播；payload 不同則建立 decision issue，不做 last-write-wins。

## 驗證

改動本 Skill、router 或 cases 後執行：

```bash
bun run <本skill>/scripts/route.ts --selftest
bun test tests/forgejo/forgejo-delivery-route.test.ts
bash <本skill>/tests/issue-state/verify.sh
```

完整契約與舊經驗取捨見 [references/contracts.md](references/contracts.md)。
