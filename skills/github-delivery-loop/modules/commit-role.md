# commit 角色（GitHub）——身分設定與執行職責

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
| GitHub 帳號 | login `ed3c`，immutable id `30064024` | `gh api user --jq '{login,id}'` |
| GitHub 私密位址 | `30064024+ed3c@users.noreply.github.com` | 即 `<id>+<login>@users.noreply.github.com`；GitHub 設定頁的 Emails 區塊顯示同一串 |
| push 通道 | SSH（`gh auth status` 報 `Git operations protocol: ssh`） | `gh auth status` |
| token scopes | `admin:public_key, gist, project, read:org, repo, workflow`——**沒有 `user`** | `gh auth status` |
| 簽章 | 未啟用（無 `commit.gpgsign`、無 `user.signingkey`） | `git config --global --get-regexp 'gpgsign\|signingkey'`（無輸出＝未啟用） |

**`user` scope 缺席的直接後果**：`gh api user/emails` 回 404，所以**無法用 API 查「這個 email 有沒有
在帳號上驗證過」**。要確認歸屬，只能推一個 commit 後看網頁上的 author 有沒有連到頭像，或先
`gh auth refresh -h github.com -s user`。這是缺席，不是否定——別把「查不到」講成「沒驗證」。

---

## §2 身分怎麼設（三層，就近覆蓋）

生效順序由弱到強，**後者覆蓋前者**：

1. **全域** `~/.gitconfig`：`ed3c <mcnum01@gmail.com>`。這是任何沒特別設定的 repo 會用的值。
2. **per-repo**：`git -C <repo> config user.email <addr>`。切 host、切公開／私有線一律用這層。
3. **單次環境變數**：`GIT_AUTHOR_EMAIL` / `GIT_COMMITTER_EMAIL`。只給腳本與測試 fixture 用，
   不要拿來當長期設定——它不留在 repo 裡，下一個 session 看不到，會靜默漂回全域值。

**唯一權威的「現在會用什麼身分」查法**（含環境變數覆蓋，`git config` 查不到這層）：

```bash
git -C <repo> var GIT_AUTHOR_IDENT
```

**worktree 繼承 repo 設定**，所以在 `git worktree add` 出來的隔離工作面上不需要重設；
反過來說，repo 那層設錯，每個 worktree 都跟著錯。

**絕不用 `git config --global` 在 host 之間切換身分**：全域是所有 repo 共享的，切過去就忘了切回來，
下一條線靜默用錯身分——下面 §6 兩件事故都是這個機制。

---

## §3 公開線用哪個 email（這是隱私決定，不是風格）

commit 的 author email 會**永久寫進公開 repo 的 git object**，刪 commit 也還在 fork 與快取裡。

- **對外公開的 repo**（如 `ed3c/ix-agy` 這條開源線）→ 用 `30064024+ed3c@users.noreply.github.com`。
  GitHub 照樣把 commit 連回 `ed3c` 帳號、照樣算 contribution，但不外洩真實信箱。
- **私有／託管 repo**（如 `ed3c/ix-agy-private`）→ 用哪個都可以，但**同一條線內不要混**：
  混用會讓 `git log --author` 與 blame 統計裂成兩個人。
- 決定完就寫進該 repo 的 `git config user.email`，別靠記憶每次手動帶。

```bash
git -C <repo> config user.name  ed3c
git -C <repo> config user.email 30064024+ed3c@users.noreply.github.com
```

---

## §4 agent 的署名（commit 由誰按下，與 commit 出自誰的手）

- **author／committer 永遠是人**（上面設定的身分）。agent 不冒用第二個 git 身分去 commit——
  一旦 agent 有自己的 author 身分，`git log` 就無法回答「這行程式碼是誰負責的」。
- **agent 的參與寫在 trailer**，Claude Code 在 commit message 末尾附：

  ```
  Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
  ```

  GitHub 會解析 `Co-Authored-By:` 並在 commit 頁顯示共同作者。Codex 有它自己的 trailer 慣例，
  依該 host 的規則走，**不要互相投射**。
- trailer 是**紀錄**不是**授權**：掛了 agent 名字不代表這個 commit 通過了任何閘，
  merge 授權仍然只由 §5 的四層決定。

---

## §5 第二身分：什麼時候真的需要，什麼時候不需要

GitHub 的硬規則是**作者不能 approve 自己的 PR**。所以「用 PR review 當人閘」在單人帳號下
物理上做不到，除非引入第二個身分（GitHub App／machine account）——那是額外基建。

**本 skill 的模型不走那條路**：人閘是 repo owner 貼 `merge-admit` label（見
[host-permissions.md](host-permissions.md) 與 SKILL.md 的四層堆疊），label 由 owner 施加、
且必須晚於 head commit。因此：

- **不需要**為了「有人 review」而替 agent 開第二個 git 身分。
- **需要**第二身分的唯一情境是：這條線改用 required approvals 當人閘。那時第二身分是**帳號層**的
  （App／machine account 開 PR），仍然不是 agent 自己捏一個 `user.email` 就算數——
  捏出來的 email 只是沒歸屬的字串，GitHub 不會把它當成另一個人。

---

## §6 已發生的身分事故（同型錯誤要一次掃完，不要逐個踩）

| 事故 | 觀測 | 機制 |
|---|---|---|
| 測試身分落到真 remote | `ed3c/skill-bettor` 最近 6 個 commit 全是 `Loop Test <loop-test@example.invalid>` | 小迴圈為了測試在 repo 層設了 fixture 身分，之後真的推上 GitHub。`.invalid` 是保留 TLD，GitHub 永遠不可能把它連回任何帳號——這些 commit 沒有作者、不算 contribution，且**無法事後修正而不 rewrite history** |
| 佔位身分混進真線 | `bettor-arena` 的 log 同時有 `ed3c <mcnum01@gmail.com>` 與 `t <t@t.t>` | 同上，只是佔位字串不同 |

**開工前的一次性檢查**（零網路，任何 CWD）：

```bash
git -C <repo> var GIT_AUTHOR_IDENT
```

輸出若含 `example.invalid`、`@t.t`、`localhost`、或任何不屬於本 host 帳號的位址 → **停下先修設定**，
不要先 commit 再說。已經推上去的舊 commit 屬於歷史事實，rewrite 是人的決定，不由 agent 代辦。

---

## §7 commit 這個動作的職責（何時、多大、寫什麼）

1. **時機**：跟著 `/tdd` 的節奏——每個「能編譯、能過測試」的最小狀態就是一個 commit。
   不累積成一顆大 commit，也不為了湊數把不能跑的中間態 commit 進去。
2. **粒度**：一個 commit 一件事。PR 的 commit 鏈本身就是 review 的敘事（四層儀表板的第 3 層），
   鏈斷了 reviewer 只能整包看 diff。
3. **訊息**：解釋**為什麼**，不是複述 diff 做了什麼（diff 自己會說）。PR body 用 `Closes #N` 綁回工作單。
4. **收手前自審 diff**：`git diff --staged` 看過再 commit。
5. **硬禁止**（違反其一即停下回報，不得換寫法繞過）：
   - `--no-verify` 繞 pre-commit hook —— hook 擋住就修那個問題。
   - 在**主 working tree** 切分支（`git checkout` / `git switch`）—— 共享 tree 會讓其他 session 的
     HEAD 漂移、commit 落錯分支。隔離一律走 worktree（surface 規則見 SKILL.md）。
   - commit 不能編譯的程式碼。
   - 用 agent 自造的 git 身分 commit（§4）。
6. **與 merge 閘的接合**：commit 與 push 是本 skill 可以自主做的；**merge 不是**。
   push 完到 PR 開好、findings 齊備為止，接手的是 §5 的 admit → preflight → land。

---

## §8 硬閘（本檔範圍內）

- `git var GIT_AUTHOR_IDENT` 的 email 不屬於本 host 的帳號 → 不得 commit。
- 公開線上出現真實信箱、或私密位址與帳號 id 不符（不是 `30064024+ed3c@…`）→ 視為設定錯誤。
- 身分靠環境變數臨時撐著、沒寫進 repo config → 視為未設定（下個 session 會漂回全域）。
- agent 以自己的 author 身分 commit → 失敗，不是可接受的替代方案。
- 「查不到」與「不合格」在輸出裡必須長得不一樣（如 §1 的 `user` scope 缺席）。
