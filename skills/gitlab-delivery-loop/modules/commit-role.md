# commit 角色（GitLab）——身分設定與執行職責

「commit 角色」＝**這條交付線上，每個 commit 對外掛誰的名字，以及誰在什麼時機被允許 commit**。
兩件事寫在同一份檔案裡，因為它們同一時刻決定：身分設錯，commit 就算流程全對也會失去歸屬；
職責設錯，身分再對也只是把錯的東西掛上正確的名字。

本檔是這個 skill 對 commit 角色的**完整設定**，不與 `delivery-mechanism.md`／`host-permissions.md`
分割：那兩份管 receipt 與 merge 授權，本檔管身分與提交紀律。

---

## §1 這台機器上的既存事實（2026-08-07 實測，非推論）

| 事實 | 值 | 怎麼再驗一次 |
|---|---|---|
| 全域 author/committer | `ed3c <mcnum01@gmail.com>` | `git config --global user.name; git config --global user.email` |
| GitLab 帳號 | username `ed3c`，immutable id `5792129` | `glab api user`（欄位 `id` / `username`） |
| 帳號的 commit email | `mcnum01@gmail.com`（`public_email` 為空） | `glab api user` 的 `commit_email` 欄位 |
| push 通道 | SSH（`glab auth status` 報 `Git operations … use ssh protocol`），API 走 HTTPS | `glab auth status` |
| token | 存在 OS keyring，不在 repo 也不在 shell 歷史 | `glab auth status` |
| 簽章 | 未啟用（無 `commit.gpgsign`、無 `user.signingkey`） | `git config --global --get-regexp 'gpgsign\|signingkey'`（無輸出＝未啟用） |

**GitLab 的歸屬規則與 GitHub 不同**：GitLab 用 commit 的 author email 去比對「帳號上已驗證的
任一 email」，比對到就把 commit 連回該帳號。所以權威來源就是 `glab api user` 的 `commit_email`——
**它現在回什麼，帳號就認什麼**，不需要（也不該）從別處推論。

---

## §2 身分怎麼設（三層，就近覆蓋）

生效順序由弱到強，**後者覆蓋前者**：

1. **全域** `~/.gitconfig`：`ed3c <mcnum01@gmail.com>`。任何沒特別設定的 repo 都用這個值。
2. **per-repo**：`git -C <repo> config user.email <addr>`。切 host、切公開／私有線一律用這層。
3. **單次環境變數**：`GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_EMAIL`。只給腳本與測試 fixture 用，
   不要當長期設定——它不留在 repo 裡，下一個 session 看不到，會靜默漂回全域值。

**唯一權威的「現在會用什麼身分」查法**（含環境變數覆蓋，`git config` 查不到這層）：

```bash
git -C <repo> var GIT_AUTHOR_IDENT
```

**worktree 繼承 repo 設定**，隔離工作面不必重設；反過來說 repo 那層設錯，每個 worktree 都跟著錯。

**絕不用 `git config --global` 在 host 之間切換身分**：全域是所有 repo 共享的，切過去就忘了切回來，
下一條線靜默用錯身分——§6 兩件事故都是這個機制。

---

## §3 公開線用哪個 email（這是隱私決定，不是風格）

commit 的 author email 會**永久寫進公開 repo 的 git object**，刪 commit 也還在 fork 與快取裡。

- **對外公開的 project** → 改用 GitLab 的私密位址（形態 `<id>-<username>@users.noreply.gitlab.com`，
  本帳號即 `5792129-ed3c@…`）。**設定完以 `glab api user` 的 `commit_email` 回值為準**——
  在 GitLab profile 把 commit email 切成私密後，那個欄位就會回傳它；欄位還回 gmail 就是還沒切成功，
  別憑格式字串自我說服。
- **私有 project** → 用哪個都可以，但**同一條線內不要混**：混用會讓 `git log --author` 與 blame
  統計裂成兩個人。
- 決定完就寫進該 repo 的 `git config user.email`，別靠記憶每次手動帶。

```bash
git -C <repo> config user.name  ed3c
git -C <repo> config user.email 5792129-ed3c@users.noreply.gitlab.com   # 先用 glab api user 確認
```

---

## §4 agent 的署名（commit 由誰按下，與 commit 出自誰的手）

- **author／committer 永遠是人**（上面設定的身分）。agent 不冒用第二個 git 身分去 commit——
  一旦 agent 有自己的 author 身分，`git log` 就無法回答「這行程式碼是誰負責的」。
- **agent 的參與寫在 trailer**，Claude Code 在 commit message 末尾附：

  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  ```

  Codex 有它自己的 trailer 慣例，依該 host 的規則走，**不要互相投射**。
  注意 GitLab 對 `Co-Authored-By:` 的呈現不保證與 GitHub 一致——trailer 對 GitLab 而言主要是
  **訊息內的紀錄**，要它變成 UI 上的共同作者請先實測，別假設。
- trailer 是**紀錄**不是**授權**：掛了 agent 名字不代表這個 commit 通過了任何閘，
  merge 授權仍然只由 §5 的四層決定。

---

## §5 第二身分：什麼時候真的需要，什麼時候不需要

GitLab 的硬規則是**作者不能 approve 自己的 MR**；而個人 namespace 的 project 連 required
approvals 都不完整（見 [host-permissions.md](host-permissions.md)）。所以「用 approval 當人閘」
在單人帳號下要嘛做不到、要嘛得引入第二個身分（bot／service account）——那是額外基建。

- **不需要**為了「有人 review」而替 agent 開第二個 git 身分。
- **需要**第二身分的唯一情境是：這條線改用 required approvals 當人閘。那時第二身分是**帳號層**的，
  仍然不是 agent 自己捏一個 `user.email` 就算數——捏出來的 email 只是沒歸屬的字串，
  GitLab 不會把它當成另一個人（它比對的是帳號上已驗證的 email，§1）。
- `glab mr merge` **沒有 `--admin`**：GitLab 端不存在「以管理員身分無視所有要求」的旗標，
  所以也沒有靠身分升級繞過閘的路。

---

## §6 已發生的身分事故（同型錯誤要一次掃完，不要逐個踩）

事故發生在鄰近的 host，但機制與 GitLab 完全相同（都是 repo 層 `user.email` 被設成佔位字串後推上真 remote）：

| 事故 | 觀測 | 機制 |
|---|---|---|
| 測試身分落到真 remote | `ed3c/skill-bettor` 最近 6 個 commit 全是 `Loop Test <loop-test@example.invalid>` | 小迴圈為了測試在 repo 層設了 fixture 身分，之後真的推上去。`.invalid` 是保留 TLD，永遠比對不到任何帳號——這些 commit 沒有作者，且**無法事後修正而不 rewrite history** |
| 佔位身分混進真線 | `bettor-arena` 的 log 同時有 `ed3c <mcnum01@gmail.com>` 與 `t <t@t.t>` | 同上，只是佔位字串不同 |
| 跨 host 位址錯置 | `ts-skill-bettor` 用 `neon@noreply.localhost` | 那是本機 Forgejo 的 noreply 位址；**推到 GitLab 會完全失去歸屬**，因為它不在 GitLab 帳號的已驗證清單上 |

**開工前的一次性檢查**（零網路，任何 CWD）：

```bash
git -C <repo> var GIT_AUTHOR_IDENT
```

輸出若含 `example.invalid`、`@t.t`、`localhost`、或任何不在 GitLab 帳號驗證清單上的位址 →
**停下先修設定**，不要先 commit 再說。已推上去的舊 commit 屬於歷史事實，rewrite 是人的決定，
不由 agent 代辦。

---

## §7 commit 這個動作的職責（何時、多大、寫什麼）

1. **時機**：跟著 `/tdd` 的節奏——每個「能編譯、能過測試」的最小狀態就是一個 commit。
   不累積成一顆大 commit，也不為了湊數把不能跑的中間態 commit 進去。
2. **粒度**：一個 commit 一件事。MR 的 commit 鏈本身就是 review 的敘事；鏈斷了 reviewer 只能整包看 diff。
3. **訊息**：解釋**為什麼**，不是複述 diff 做了什麼（diff 自己會說）。MR body 用 `Closes #N` 綁回工作單。
4. **收手前自審 diff**：`git diff --staged` 看過再 commit。
5. **硬禁止**（違反其一即停下回報，不得換寫法繞過）：
   - `--no-verify` 繞 pre-commit hook —— hook 擋住就修那個問題。
   - 在**主 working tree** 切分支（`git checkout` / `git switch`）—— 共享 tree 會讓其他 session 的
     HEAD 漂移、commit 落錯分支。隔離一律走 worktree（surface 規則見 SKILL.md）。
   - commit 不能編譯的程式碼。
   - 用 agent 自造的 git 身分 commit（§4）。
6. **與 merge 閘的接合**：commit 與 push 是本 skill 可以自主做的；**merge 不是**。
   push 完到 MR 開好、findings 齊備為止，接手的是 admit → preflight → land。

---

## §8 硬閘（本檔範圍內）

- `git var GIT_AUTHOR_IDENT` 的 email 不在 GitLab 帳號的已驗證清單上 → 不得 commit。
- 公開線上出現真實信箱、或私密位址與帳號 id 不符（不是 `5792129-ed3c@…`）→ 視為設定錯誤。
- 私密位址「已設定」的判準是 `glab api user` 的 `commit_email` 回傳它，不是字串長得像。
- 身分靠環境變數臨時撐著、沒寫進 repo config → 視為未設定（下個 session 會漂回全域）。
- agent 以自己的 author 身分 commit → 失敗，不是可接受的替代方案。
- GitHub 的位址（`…@users.noreply.github.com`）出現在 GitLab 線上 → 與本 skill 的 cross-forge 拒絕
  同一個理由：**兩支 skill 的身分不可混用**，回去用對應的那一支。
