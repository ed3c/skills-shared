# commit 角色（本機 Forgejo）——身分設定與執行職責

「commit 角色」＝**這條交付線上，每個 commit 對外掛誰的名字，以及誰在什麼時機被允許 commit**。
兩件事寫在同一份檔案裡，因為它們同一時刻決定：身分設錯，commit 就算流程全對也會失去歸屬；
職責設錯，身分再對也只是把錯的東西掛上正確的名字。

本檔是這個 skill 對 commit 角色的**完整設定**，不與 `delivery-mechanism.md`／`forgejo-operations.md`
分割：那兩份管四層追蹤面與 mutation 安全，本檔管身分與提交紀律。

---

## §1 這台機器上的既存事實（2026-08-07 實測，非推論）

| 事實 | 值 | 怎麼再驗一次 |
|---|---|---|
| 全域 author/committer | `ed3c <mcnum01@gmail.com>` | `git config --global user.name; git config --global user.email` |
| Forgejo 實例 | `http://localhost:3000`，版本 `9.0.3+gitea-1.22.0` | `curl -s http://localhost:3000/api/v1/version` |
| Forgejo 帳號 | login `neon`，id `1`，`is_admin: false` | `curl -s http://localhost:3000/api/v1/users/neon` |
| 帳號 email | `neon@noreply.localhost` | 同上（`email` 欄位；此端點免認證） |
| push 通道 | HTTP（remote 為 `http://localhost:3000/neon/<repo>.git`） | `git -C <repo> remote -v` |
| 憑證 | localhost URL 級 helper chain 為空 reset ＋ `osxkeychain`；不再以 `~/.git-credentials` 保存該密碼 | `git config --global --get-all credential.http://localhost:3000.helper`；值只應依序為空與 `osxkeychain` |
| 簽章 | 未啟用（無 `commit.gpgsign`、無 `user.signingkey`） | `git config --global --get-regexp 'gpgsign\|signingkey'`（無輸出＝未啟用） |

**`neon@noreply.localhost` 不是隨便取的**：Forgejo 的 `NO_REPLY_ADDRESS` 預設 `noreply.localhost`，
帳號的私密 commit 位址即 `<username>@<NO_REPLY_ADDRESS>`。它就是本實例上**唯一會被連回 `neon` 帳號**
的位址（除非另有已驗證的次要 email——那需要登入後查 `/api/v1/user/emails`，本檔未查證，
**「未查證」不等於「不存在」**）。

**歷史缺陷已收斂，但不可把它改寫成從未發生**：localhost 密碼曾由全域
`credential.helper=store` 明文落在 `~/.git-credentials`。現在由 runtime-env 的
`forgejo-local-password` 模組與 `local-env migrate-forgejo-keychain` broker 負責一次性遷移：先在
Keychain store/get，比對 URL 級 helper，刪除並回讀確認明文 entry，最後才清空 private dotenv 的
`FORGEJO_PASSWORD`。本 skill 的正常路徑只呼叫 `git credential fill`；它不讀 dotenv 或 Keychain
資料庫，也不把秘密寫入 log、receipt 或 commit。

---

## §2 身分怎麼設（三層，就近覆蓋）

生效順序由弱到強，**後者覆蓋前者**：

1. **全域** `~/.gitconfig`：`ed3c <mcnum01@gmail.com>`。任何沒特別設定的 repo 都用這個值——
   對本機 Forgejo 而言**這是錯的預設**（見 §3）。
2. **per-repo**：`git -C <repo> config user.email neon@noreply.localhost`。
   Forgejo 線一律靠這層把身分扳回來。
3. **單次環境變數**：`GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_EMAIL`。只給腳本與測試 fixture 用，
   不要當長期設定——它不留在 repo 裡，下一個 session 看不到，會靜默漂回全域值。

**唯一權威的「現在會用什麼身分」查法**（含環境變數覆蓋，`git config` 查不到這層）：

```bash
git -C <repo> var GIT_AUTHOR_IDENT
```

**worktree 繼承 repo 設定**，隔離工作面不必重設；反過來說 repo 那層設錯，每個 worktree 都跟著錯。

**絕不用 `git config --global` 在 host 之間切換身分**：全域是所有 repo 共享的，切過去就忘了切回來，
下一條線靜默用錯身分——§6 三件事故都是這個機制。

---

## §3 本機 Forgejo 線的人類預設身分

人直接操作時一律使用 `neon <neon@noreply.localhost>`，有兩個獨立理由：

1. **歸屬**：Forgejo 用 author email 比對帳號。用 gmail commit，UI 上就是一個沒有頭像、
   點不進去的陌生人，issue／PR 的 `@` 關聯也對不上。
2. **隱私**：本機 repo 有可能被匯出、被 mirror、被打包成交付物。真實信箱一旦寫進 git object，
   刪 commit 也還在。noreply 位址從源頭就沒這個問題。

```bash
git -C <repo> config user.name  neon
git -C <repo> config user.email neon@noreply.localhost
```

**反向鐵律**：`neon@noreply.localhost` **只屬於這台機器的 Forgejo**。它出現在 GitHub／GitLab 的
remote 上就是身分錯置——那邊的帳號永遠比對不到它，commit 直接失去歸屬。

若目標 repo 有 `evals/commit-roles.json`，自動化 commit 另受該可執行契約約束：machine role
必須使用 `<role>@<host>.invalid`，且 `Driven-By`／`Driven-On` 必須與 author 相符。這不是第二個
Forgejo 帳號，也不產生 reviewer independence；它只防止把機器工作錯算成人的 contribution。

---

## §4 agent 的署名（driver、carrier 與 forge actor 分開）

- 人直接提交：使用 §3 的人類身分，`Driven-By: human`，並記錄實際 carrier。
- agent 直接提交：使用 repo 的 machine-role vocabulary，例如
  `agent-macro <agent-macro@codex-app.invalid>`，並連續寫入相符的 `Driven-By`／`Driven-On`
  trailers。不可把 agent commit 偽標為 `human`。
- forge 產生的 merge/squash commit：由可驗證的 forge committer address 分類；不要偽造 forge 身分。
- `Co-Authored-By` 只補充模型參與。例如 Claude Code 可再附：

  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  ```

  Codex 有它自己的 trailer 慣例，依該 host 的規則走，**不要互相投射**。
  Forgejo 對 `Co-Authored-By:` 的 UI 呈現未實測——要它變成 UI 上的共同作者請先在本實例試一次，
  別假設與 GitHub 相同。
- trailer 是**紀錄**不是**授權**：是否可自動 merge 由目標 repo 的 admission policy 決定，
  不能從 author 身分推論。

---

## §5 第二身分：這個實例上等於沒有

本實例是**單人本機部署**（`neon` 是唯一活躍帳號，且 `is_admin: false`）。因此：

- 「讓另一個身分開 PR、由本人 review」在這裡沒有現實基礎；machine-role identity 只是 provenance，
  不是第二個帳號。
- 需要人閘時仍須由真人 admit；允許自動 merge 時也必須由專屬 delivery gate 授權，不能靠改 email
  冒充第二位 reviewer。
- 任意捏一個 `user.email` **不會**在 Forgejo 眼中變成第二個人；只有 repo vocabulary 允許且 trailers
  相符的 `.invalid` 身分才是可接受的 machine provenance。

---

## §6 已發生的身分事故（同型錯誤要一次掃完，不要逐個踩）

| repo | 觀測 | 機制 |
|---|---|---|
| `<consumer-repo-a>`（Forgejo 線） | log 同時有全域真實信箱身分與 `Fixture User <fixture@example.invalid>` | repo 層沒設 `user.email`，直接吃全域身分；另有一顆佔位身分。**這些 commit 在 Forgejo UI 上不連回本機帳號**（除非真實信箱已登記為次要 email，未查證），且把真實信箱寫進了 repo |
| `<consumer-repo-b>`（Forgejo 線） | 全部 `neon <neon@noreply.localhost>` | **這是正確樣板**。要抄就抄這個 |
| `<owner>/<github-control-repo>`（GitHub 線，對照組） | 最近 6 個 commit 全是 `Loop Test <loop-test@example.invalid>` | 小迴圈為了測試在 repo 層設了 fixture 身分，之後真的推上去。`.invalid` 是保留 TLD，永遠比對不到任何帳號，且**無法事後修正而不 rewrite history** |

**開工前的一次性檢查**（零網路，任何 CWD）：

```bash
git -C <repo> var GIT_AUTHOR_IDENT
```

Forgejo 線上輸出不是 `neon <neon@noreply.localhost>` → **停下先修設定**，不要先 commit 再說。
已推上去的舊 commit 屬於歷史事實，rewrite 是人的決定，不由 agent 代辦。

---

## §7 commit 這個動作的職責（何時、多大、寫什麼）

1. **時機**：跟著 `/tdd` 的節奏——每個「能編譯、能過測試」的最小狀態就是一個 commit。
   不累積成一顆大 commit，也不為了湊數把不能跑的中間態 commit 進去。
2. **粒度**：一個 commit 一件事。PR 的 commit 鏈本身就是四層儀表板第 3 層的可審敘事；
   鏈斷了 reviewer 只能整包看 diff。
3. **訊息**：解釋**為什麼**，不是複述 diff 做了什麼（diff 自己會說）。PR body 用 `Closes #N`，
   merge 後 milestone 進度自動推進。
4. **收手前自審 diff**：`git diff --staged` 看過再 commit。
5. **硬禁止**（違反其一即停下回報，不得換寫法繞過）：
   - `--no-verify` 繞 pre-commit hook —— hook 擋住就修那個問題（本 repo 的
     `check_credential_hygiene.py` 就掛在這裡，它正是防止憑證被 commit 進去的那一道）。
   - 在**主 working tree** 切分支（`git checkout` / `git switch`）—— 共享 tree 會讓其他 session 的
     HEAD 漂移、commit 落錯分支。隔離一律走 worktree 或乾淨分支。
   - commit 不能編譯的程式碼。
   - 使用 vocabulary 未登記，或與 trailers 不一致的 machine 身分（§4）。
   - 任意改 remote、force push。
6. **與 delivery 收據的接合**：物化 repo 的那一刻同步寫 `delivery.json`；commit 前跑
   `check_delivery_receipt.py`（零網路 T0 閘）。**身分對、收據缺席一樣是 FATAL**，兩件事各管各的。

---

## §8 硬閘（本檔範圍內）

- 人直接提交時，`git var GIT_AUTHOR_IDENT` 不是 `neon <neon@noreply.localhost>` → 不得 commit。
- agent 直接提交時，author 不是 vocabulary 允許的 `<role>@<host>.invalid`，或與 trailers 不一致 → 不得 commit。
- 真實信箱（`mcnum01@gmail.com`）出現在 Forgejo 線的新 commit → 視為設定錯誤，不是風格差異。
- `neon@noreply.localhost` 出現在 GitHub／GitLab 線 → 身分錯置，回去用對應的那一支 skill。
- 人類預設身分只靠環境變數、沒寫進 repo config → 視為未設定；machine-role endpoint 則必須逐次
  顯式注入並由 commit-role gate 回讀，不能污染 repo 的人類預設。
- 憑證（`~/.git-credentials` 的內容、token、cookie）以任何形式進入 commit、log 或工具輸出 → FATAL。
- 「未查證」與「已否定」在輸出裡必須長得不一樣（如 §1 的次要 email）。
