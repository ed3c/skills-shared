# github-vs-gitlab.md — 兩個 forge 不混淆的契約

這個 skill 是 `github-delivery-loop` 的**姊妹**，不是它的多後端版本。
兩者共用**設計**（四層原生看板、零網路 receipt 閘、四層 merge 授權堆疊、缺席≠拒絕），
但**不共用任何一行程式碼、任何一個 schema 名、任何一個 registry 檔**。

## 0. 為什麼不做成 `--host gitlab`

一支腳本加旗標是比較短的 diff，但它把「打到哪個 forge」變成**執行期參數**——
旗標打錯、registry 抄錯、環境變數殘留，任何一個都會讓 GitLab 的 receipt 拿去驗 GitHub 的專案，
而且**驗得過**（結構長得幾乎一樣）。分成兩支之後，錯配在**載入的第一刻**就撞牆：
schema 名不同、欄位名不同、URL 形狀不同，三道都對不上。

代價是重複：metrics 推導、atomic write、L2 host probe 三段邏輯兩邊各一份。
這是**刻意付的**——它們會各自演化（下面 §2 已經有五處分岔），而共用一份的話，
修 GitHub 的一個 bug 會靜默改變 GitLab 的行為。

## 1. 機械閘（不是散文提醒）

「不混淆」不能靠文件寫「請注意」。四道閘都在程式碼裡，且都有負控測試
（`tests/cross-forge/verify.sh`）：

| 閘 | 位置 | 拿 GitHub 東西餵進來會怎樣 |
|---|---|---|
| schema 名 | `gitlab-delivery-registry/v1` 等全部 `gitlab-*` | `github-delivery-registry/v1` → 拒絕，並**指名去用 github-delivery-loop** |
| 身份欄位 | `gitlab_host` / `gitlab_project` / `gitlab_project_id` | 出現 `github_repo` → 拒絕。**不是忽略未知欄位**——未知欄位通常無害，這一個代表走錯 skill |
| URL 正則 | `https://<host>/<path>/-/(issues\|work_items\|merge_requests\|boards)/N` | 任何含 `github.com` 的 URL → 拒絕並標 `cross-forge URL` |
| snapshot | 頂層 `"forge": "gitlab"` | GitHub snapshot replay → 拒絕並指名另一支 skill |

execpolicy 規則檔名也分開命名空間：`gitlab-merge-<host>-<slug>.rules`，
永不寫成 `github-merge-*`。否則一條過期的 GitHub 規則會被讀成「GitLab merge 已有覆蓋」。

## 2. 實測出來的平台差異（照抄 GitHub 版就會錯的地方）

以下每一列都是 2026-08-07 對 `gitlab.com` 唯讀 API 實跑得到的，不是從記憶或文件推的。

### 2.1 專案路徑有兩段以上，不是 `OWNER/REPO`

GitLab 專案住在巢狀 group 底下（`group/subgroup/project`）。GitHub 版的
`[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+` 只認一條斜線，會**拒絕合法的 GitLab 專案**。
本 skill 的 `PROJECT_RE` 要求兩段以上。

### 2.2 group 專案的 `owner` 是 `null`

`GET /projects/:id` 對 `gitlab-org/cli` 回 `"owner": null`——`owner` 只在**個人 namespace**
才有值。GitHub 版的人閘是「label 的 actor == `repo.owner.login`」，
直接照搬到 GitLab 會**永遠比對到 null**，於是所有 admit 都被拒（假紅），
或更糟：若寫成 `!= owner` 才拒，則變成永遠放行（假綠）。

本 skill 改成**從 membership 讀權限等級**：admit actor 必須在該專案有
`access_level >= 50`（Owner）。查詢用 `members/all?query=<username>` 收斂成單一請求，
不對動輒數千繼承成員的 group 分頁掃描。

個人 namespace 另給一條出口：`namespace.kind == "user"` 且 `namespace.full_path == actor`
時直接成立——個人專案的擁有者不一定出現在 members 清單裡。
（`tests/merge-gate/fixtures/personal` 守著這條。）

門檻選 Owner(50) 而不是 Maintainer(40) 是刻意的：Maintainer **本來就能 merge**，
用它當人閘等於「能 merge 的人核可自己能 merge」，閘就不存在了。

### 2.3 GitLab 沒有 root tree sha

GitHub 的 export-tree binding 靠 `GET /repos/.../commits/:sha` 回傳的 `commit.tree.sha`。
GitLab **兩條路都沒有**：

- REST `GET /projects/:id/repository/commits/:sha` 的欄位裡沒有 tree（實跑列過 keys）；
- GraphQL `Tree` 型別沒有 `sha` 欄位（實跑回 `Field 'sha' doesn't exist on type 'Tree'`）。

所以綁定改成**本地解析**：export clone 就是我們推上去的那份，它必然含有 GitLab 回報的 head
commit，`git rev-parse <head>^{tree}` 即得。兩種缺席各有出口：

| 情況 | blocker |
|---|---|
| 本地樹 ≠ 驗過的樹 | `export-tree-drift` |
| 本地根本沒有那個 commit（別人推過） | `remote-head-unverifiable` |

第二條比 GitHub 版更嚴：GitHub 版只會比出 tree 不同，本版會直說「這棵樹我無從證明」。

### 2.4 issue 的 `web_url` 可能是 `/-/work_items/N`

實測 `gitlab-org/cli` 的 issue 回 `https://gitlab.com/gitlab-org/cli/-/work_items/8487`。
只認 `/-/issues/N` 的驗證器會**拒絕真實的 GitLab URL**。本 skill 產出時一律寫 canonical
`/-/issues/N`，驗證時兩種都收。

### 2.5 `glab mr merge` 預設會開 auto-merge

`--auto-merge` 的預設是 `true`，且「When a pipeline is running, auto-merge is enabled by default」。
意思是：有 pipeline 在跑時，`glab mr merge` **回傳成功，但什麼都沒合**——
正是這個 skill 存在要擋的「產物缺席卻顯示成功」。

所以 `merge_command()` 永遠帶 `--auto-merge=false --yes`，並由測試守著。
它**不能**靠 execpolicy 守：`--auto-merge` 出現在 MR 編號之後、位置浮動，
prefix contract 表達不了——這與 GitHub 版 `--admin` 守不住是**同一類缺口**
（尾隨旗標在前綴規則之外），只是換了個症狀。

### 2.6 其他不對稱

| 概念 | GitHub | GitLab | 影響 |
|---|---|---|---|
| 工作單編號 | `number` | `iid`（專案內）／`id`（全站） | 用錯就跨專案抓到別人的東西 |
| PR | `pull` / `pr_urls` | `merge_request` / `mr_urls` | 名詞不混用，receipt 欄位也不同名 |
| 狀態字面 | `OPEN` / `CLOSED` | `opened` / `closed` | 照抄大寫比較會**永遠不匹配**且靜默 |
| 可合併性 | `mergeable` + `mergeStateStatus` | `detailed_merge_status` 單一枚舉 | 只有 `mergeable` 可落地 |
| 可見度 | PUBLIC / PRIVATE | public / **internal** / private | `internal` 無 GitHub 對應物，單獨給 blocker，不與 private 併攏 |
| license | `spdx_id == "MIT"` | `license.key == "mit"`，且需 `?license=true` | 忘了帶參數會讀成「沒授權」的假 blocker |
| label 事件 | `issues/:n/events` | `resource_label_events`（action add/remove） | 找 `labeled`/`unlabeled` 會抓不到任何東西 |
| 重開事件 | 同上 events | `resource_state_events` | 分在另一個端點 |
| review | reviews 有 `submitted_at` ＋ `CHANGES_REQUESTED` | approvals 無時間戳、無 changes-requested | first-pass rate **沒有等價物** → 明確缺席，見下 |
| 看板 | Projects v2（跨 repo） | Issue Board（專案／group 內） | 投影語意相同，載體不同 |

### 2.7 first-pass rate 在 GitLab 沒有等價物

GitHub 版用 review 事件的 `submitted_at` ＋ `APPROVED`／`CHANGES_REQUESTED` 算首過率。
GitLab 的 approvals 是**當下狀態清單、沒有時間戳**（實跑 `/approvals` 的 keys 確認），
而且**根本沒有 changes-requested 這個狀態**。

可以從 system notes 的文字（"approved this merge request"）反推，但那是對本地化字串做
pattern matching——把 `[推論]` 級的東西冒充成事件真相。所以本 skill 選擇：
`first_pass_rate: null` ＋ `first_pass_rate_absent: "<原因>"`。
**缺席有明確出口，不補零**——補零會讓「量不到」讀起來像「首過率是 0」。

## 3. 兩個 skill 何時該互相回饋

共用的是**設計**，所以 know-why 層級的發現要雙向 fold：

- 「同一個 host 的閘可能不只一個平面」（Codex hook 漏報）→ 兩邊 L2 都要有；
- 「缺席與拒絕必須長得不一樣」（exit 3）→ 兩邊都有；
- 「窄規則的窄要用負控量」→ 兩邊都有，但**症狀不同**（`--admin` vs `--auto-merge`）。

反過來，**平台事實不互抄**：§2 每一列都只屬於 GitLab，寫進 GitHub 那份就是污染。
判斷準則：講「閘怎麼設計」的 fold 過去，講「這個 forge 的 API 長怎樣」的留在原地。
