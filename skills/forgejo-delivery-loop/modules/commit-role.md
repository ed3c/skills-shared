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
| 憑證 | `credential.helper=store`，`~/.git-credentials` 內有 `localhost%3a3000` 一筆 | `git config --global credential.helper` |
| 簽章 | 未啟用（無 `commit.gpgsign`、無 `user.signingkey`） | `git config --global --get-regexp 'gpgsign\|signingkey'`（無輸出＝未啟用） |

**`neon@noreply.localhost` 不是隨便取的**：Forgejo 的 `NO_REPLY_ADDRESS` 預設 `noreply.localhost`，
帳號的私密 commit 位址即 `<username>@<NO_REPLY_ADDRESS>`。它就是本實例上**唯一會被連回 `neon` 帳號**
的位址（除非另有已驗證的次要 email——那需要登入後查 `/api/v1/user/emails`，本檔未查證，
**「未查證」不等於「不存在」**）。

**憑證落盤這件事要講清楚，不要靠沉默掩蓋**：`credential.helper=store` 表示 `localhost:3000` 的憑證
**已經以明文存在 `~/.git-credentials`**。skill 的「秘密只留記憶體」不變量約束的是**本 skill 的行為**
（不輸出、不新增落盤、不寫進 log 或 commit），它並沒有、也無法撤銷這個既存的存量。要收斂的話是
把 helper 換成 `osxkeychain` 並清掉那一行——那是人的決定，不由 agent 代辦。

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

## §3 本機 Forgejo 線用哪個 email

**一律 `neon <neon@noreply.localhost>`**，兩個獨立理由：

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

---

## §4 agent 的署名（commit 由誰按下，與 commit 出自誰的手）

- **author／committer 永遠是人**（上面設定的身分）。agent 不冒用第二個 git 身分去 commit——
  一旦 agent 有自己的 author 身分，`git log` 就無法回答「這行程式碼是誰負責的」。
- **agent 的參與寫在 trailer**，Claude Code 在 commit message 末尾附：

  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  ```

  Codex 有它自己的 trailer 慣例，依該 host 的規則走，**不要互相投射**。
  Forgejo 對 `Co-Authored-By:` 的 UI 呈現未實測——要它變成 UI 上的共同作者請先在本實例試一次，
  別假設與 GitHub 相同。
- trailer 是**紀錄**不是**授權**：掛了 agent 名字不代表這個 commit 通過任何閘，
  merge 仍然只由人 admit。

---

## §5 第二身分：這個實例上等於沒有

本實例是**單人本機部署**（`neon` 是唯一活躍帳號，且 `is_admin: false`）。因此：

- 「讓另一個身分開 PR、由本人 review」在這裡沒有現實基礎——不必為此替 agent 造 git 身分。
- **人閘就是人閘**：merge 永遠由人在 UI 上按（SKILL.md 的執行循環）。agent 推進到 PR 開好、
  findings 齊備為止。
- agent 自己捏一個 `user.email` **不會**在 Forgejo 眼中變成第二個人——它比對的是帳號上的 email，
  比對不到就只是一串沒有歸屬的文字。

---

## §6 已發生的身分事故（同型錯誤要一次掃完，不要逐個踩）

| repo | 觀測 | 機制 |
|---|---|---|
| `bettor-arena`（Forgejo 線） | log 同時有 `ed3c <mcnum01@gmail.com>` 與 `t <t@t.t>` | repo 層沒設 `user.email`，直接吃全域 gmail；另有一顆佔位身分。**這些 commit 在 Forgejo UI 上不連回 `neon`**（除非 gmail 已登記為次要 email，未查證），且把真實信箱寫進了 repo |
| `ts-skill-bettor`（Forgejo 線） | 全部 `neon <neon@noreply.localhost>` | **這是正確樣板**。要抄就抄這個 |
| `ed3c/skill-bettor`（GitHub 線，對照組） | 最近 6 個 commit 全是 `Loop Test <loop-test@example.invalid>` | 小迴圈為了測試在 repo 層設了 fixture 身分，之後真的推上去。`.invalid` 是保留 TLD，永遠比對不到任何帳號，且**無法事後修正而不 rewrite history** |

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
   - 用 agent 自造的 git 身分 commit（§4）。
   - 任意改 remote、force push。
6. **與 delivery 收據的接合**：物化 repo 的那一刻同步寫 `delivery.json`；commit 前跑
   `check_delivery_receipt.py`（零網路 T0 閘）。**身分對、收據缺席一樣是 FATAL**，兩件事各管各的。

---

## §8 硬閘（本檔範圍內）

- Forgejo 線上 `git var GIT_AUTHOR_IDENT` 不是 `neon <neon@noreply.localhost>` → 不得 commit。
- 真實信箱（`mcnum01@gmail.com`）出現在 Forgejo 線的新 commit → 視為設定錯誤，不是風格差異。
- `neon@noreply.localhost` 出現在 GitHub／GitLab 線 → 身分錯置，回去用對應的那一支 skill。
- 身分靠環境變數臨時撐著、沒寫進 repo config → 視為未設定（下個 session 會漂回全域）。
- agent 以自己的 author 身分 commit → 失敗，不是可接受的替代方案。
- 憑證（`~/.git-credentials` 的內容、token、cookie）以任何形式進入 commit、log 或工具輸出 → FATAL。
- 「未查證」與「已否定」在輸出裡必須長得不一樣（如 §1 的次要 email）。
