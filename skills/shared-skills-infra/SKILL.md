---
name: shared-skills-infra
description: |
  管理跨 repo 共用的基礎設施 skills：一個名稱要嘛是共用基礎設施（只有一份，住在
  ~/.agents/skills-shared，經 user 層 symlink 讓所有專案看到），要嘛是該 repo 真正差異化的
  自有 skill——不能兩者皆是。repo 自留同名副本會無聲影蓋共用版（兩個 host 的 project skill
  都優先於 user skill），這是同一個修法在五個 repo 被重覆發現的機制。
  觸發詞：共用 skill、skills 基礎設施、skill 漂移、同名影蓋、新 repo 接上共用 skills、
  shared-skills-infra。
  NOT for：某個共用 skill 自己的程序（去那個 skill）；判該不該新建 skill（write-a-skill）。
---

# shared-skills-infra — 共用基礎設施 skills 的治理

## 一條規則

**共用 ≠ 差異化。** 一個 skill 名稱只能是二選一：

| | 住哪 | 誰改 |
|---|---|---|
| **共用基礎設施** | `~/.agents/skills-shared/skills/<name>/`（本 repo，有 git 歷史） | 任一 repo 的執行經驗都回饋到這一份，全體立即受益 |
| **repo 自有** | `<repo>/.agents/skills/<name>/` | 只有該 repo；差異化屬於它自己的大迴圈 |

登記在 [`registry.json`](../../registry.json)（只存**裁決**，不存掃描結果——凍結的 hash 遲早跟現實
不一致）。沒登記的同名多份＝待人裁，不是失敗。

## 為什麼影蓋是無聲的

兩個 host 的 project-level skill 都優先於 user-level。所以某個 repo 在
`.claude/skills/<共用名>/` 放自己的版本時，**不會有任何錯誤**——它只是安靜地取代共用版，
於是那個 repo 的經驗再也回不到共用面，而共用面的修正也到不了它。
五個 repo 現況實測：同名多份 26 個，其中 24 個內容分岔、只有 2 個相同。

## 與絕對路徑解耦

版控的 `registry.json` **只存裁決，不存任何機器路徑**；路徑全在 `sites.local.json`
（gitignored）或旗標。所以這個 checkout 放在哪個目錄都能用，clone 到別台機器也一樣。

| 事實 | 住哪 | 進 git？ |
|---|---|---|
| 誰是共用、誰是 repo 自有、為什麼 | `registry.json` | ✅ |
| user 層兩個 surface 在哪、要治理哪些專案、哪些專案的 Claude 側要轉發樁 | `sites.local.json` | ❌ |
| canonical 在哪 | 由 `__file__` 推導 | — |

## 指令

```bash
INFRA=~/.agents/skills/shared-skills-infra/scripts/shared_skills.py
python3 $INFRA install --project <repo> [--project …] [--claude-forwarder <repo-name>]
python3 $INFRA check     # T0：已登記的裁決有沒有被違反（零網路）
python3 $INFRA report    # 決策佇列：同名多份、尚未裁決、以及延後裁決的清單＋內容 hash
python3 $INFRA link <name>
python3 $INFRA adopt <name> --from <path> --why "…" [--defer <repo>] [--dry-run]
python3 $INFRA sync --requirements <consumer>/.agents/shared-skills.requirements.json \
  --target-root <consumer> [--apply|--check]
```

`check` exit 0 乾淨｜1 有裁決被違反；`report` exit 3 有待裁項（**待裁不是失敗**）。
正控＝`tests/verify.sh`（全合成世界，不碰這台機器真實 skill 樹，零網路）。

`sync` 只接受乾淨的 canonical commit，輸出 requirements-filtered immutable binding；
完整欄位與 rollback 契約見 [modular consumer contract](../../docs/modular-consumer-contract.md)。

### 內容 ownership 與 body-neutrality

`evals/body-neutrality.json` v2 將受管 Markdown 明分四類：

| 類別 | owner／判準 |
|---|---|
| `portable_body` | shared Skill 的通用程序；預設類別，接受 body-neutrality ratchet |
| `repo_binding_source` | consumer-specific 投影真源；由其 projection manifest、byte equality、budget 與 UNREGISTERED 控制治理 |
| `generated_projection` | consumer 端生成物；由 projection readback 治理，本 repo 目前不保存此類輸出 |
| `archive_evidence` | 歷史／證據；不冒充現行程序，由其 receipt／fixture owner 治理 |

未分類檔案一律落入 `portable_body`，不是默認豁免。非 body root 必須精確列入 manifest；整支 Skill
不能被排除。執行入口為 `scripts/check_body_neutrality.py --selftest` 與 repo root 相容轉發器
`scripts/check_body_neutrality.py`。

### `scripts/check_index.py` — 索引對它宣稱的那棵樹，兩個方向都要驗

一份索引會**單向失效**：死連結點下去才知道，**漏列的檔案永遠沒人會知道**——
短的清單與完整的清單長得一模一樣。散文裡的數字更沒有變紅的辦法：本 repo 的 README
曾寫「共用 17 個」而 registry 是 22，沒人打錯字，只是抄了沒量。

```bash
CHK=~/.agents/skills/shared-skills-infra/scripts/check_index.py
python3 $CHK --selftest                                   # 先證它會紅
python3 $CHK <doc> [--root <dir>] [--covers <dir> …]      # exit 0 乾淨｜1 索引與樹不符
```

`--covers` 逐目錄要求「每個檔案都在文件裡被指名」（散文提到也算，不必是連結）；
文件不必索引自己。三支 delivery-loop 用它守自己的 SKILL.md，各自
`tests/index/verify.sh`；首次真跑就在三支裡各抓到一支從沒被提過的 sync 類腳本。

`check`同時掃全 repo 的 `tests/**/verify.sh` 與 `tests/run-all.sh`，抓「物理上不可能失敗」
的死斷言（`! cmd` 在語句位置、`test A && test B`、`|| true` 吞掉斷言、狀態被丟棄的 `grep`）。
每個閘只有一份 verify.sh 當正對照，死斷言＝沒人守的閘卻掛著綠燈。單獨跑：

```bash
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/check_dead_assertions.py
# exit 0 乾淨｜1 有死斷言（指名檔案行號＋正確寫法）｜3 一個測試檔都沒掃到（缺席不算通過）
```

`if`／`while`／`until` **條件位置**的 `!` 是合法且有效的，一律豁免——沒有這條豁免，
linter 自己就是噪音源而被關掉，比沒有它更糟。

### `scripts/check_skill_bootstrap.py` — 消費端 Agent 動手前，憑什麼說 Skill 已就位

上面的 `check` 管的是**這台機器上的 canonical 樹**；這一支管的是**消費 repo 的 Agent 在改動之前
可以宣稱什麼**。System Prompt 給不了檔案系統或行程權限，所以一句「load 這些 Skill」證明不了
讀到哪個 commit 的哪些 bytes、走哪個 host surface、環境有沒有真的備妥。這支驗
`skill-resolution-receipt/v1`（schema 在 `references/skill-resolution-receipt.schema.json`）：

```bash
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/check_skill_bootstrap.py RECEIPT.json
# exit 0 可執行｜2 收據違反 bootstrap 不變量｜64 缺席／不可讀／schema 不合｜70 缺 jsonschema
```

四條刀口：

- **access mode 要該 runtime 真的觀測得到**。connector 讀得到 exact commit 的 bytes，就只證明
  bytes——證明不了本機安裝、worktree、可執行環境；它宣稱 `TASK_EXECUTION_ADMITTED` 直接紅。
  `ABSENT` 不是 PASS，`UNKNOWN` runtime fail closed。
- **最小觸發閉集**。每個 selected Skill 宣告的相依必須也在集合裡，否則閉集是開的；
  `selection_reason` 的 enum 裡**沒有** registry-wide 這個選項——把整個 registry 當被動上下文
  載入，正是這張收據要拒絕的行為。
- **影蓋掃描要 CLEAN 才准執行**。兩個 host 都優先吃 project-local 副本，所以同名被影蓋＝
  canonical body 根本沒跑，而這件事從結果看不出來。
- **secret 只留名字**。schema 沒有存 value 的欄位且 `additionalProperties: false`，所以帶了值的
  收據是 schema 不合而不是「不建議」；setup entrypoint 是 dotted ID，pattern 上就拼不出
  shell 命令列。

正對照涵蓋四種該被admit的形狀（本機執行、connector 只推理、Actions pinned bundle、
誠實記錄被擋的 lane），負對照 25 個。`tests/skill-bootstrap/verify.py`。

### `scripts/check_skill_requirements.py` — 同一份契約的兩半：需求與綁定

收據記的是**觀測**；這兩份記的是**宣告**。`skill-runtime-requirements/v1` 是某個 Skill
抽象地需要什麼（能力、可執行檔與版本、網路政策、檔案系統與隔離、secret 的**名字**、
固定 entrypoint ID、以及「沒有真實 substrate 就 NOT_EXERCISED 的宣稱」）；
`consumer-skill-binding/v1` 是某個消費 repo 把這些抽象解析到確切 commit 與 host surface
（即 `.skill-bindings/skills-shared.json`）。

```bash
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/check_skill_requirements.py DOC.json
# 文件自己的 schema 欄位決定用哪份 schema；exit 0｜2 宣告了自己撐不起的東西｜64 不合｜70 缺 jsonschema
```

刀口分兩類。**可攜性**打在型別上：canonical commit 必須是 40-hex（`main` 這種會動的 ref
拼不出來，否則綁定等於沒綁），surface 與 writable 路徑必須是 repo 相對且不含 `..`，
executable 只能是工具名不能是絕對路徑，url 不接受 `file://`——這些一旦寫進去，
binding 就只在某一台機器成立。**過度宣稱**打在語意上：空的 ALLOWLIST 是掛著寬鬆標籤的
NONE；要 secret 或要 UNRESTRICTED 網路，就必須同時宣告哪些事沒有真實 substrate 就是
NOT_EXERCISED——否則 fixture 全綠會被讀成完整支援。

access mode 矩陣**與 bootstrap checker 共用同一份**（直接 import，不複製）：binding 允許
一個該 runtime 根本觀測不到的 mode，跟收據宣稱它是同一個錯誤，只是提早發生在設定裡。

正對照四個（含「離線 Skill 可以什麼都不宣告為未證」與「binding 可以沒有 runtime_env」——
邊界是有條件的，不是普世的），負對照 23 個。`tests/skill-bootstrap/verify_requirements.py`。

### Repository Control Plane profile — 新 repo 只掛薄 binding

當新 repo 要同時使用 Git Town、dual forge、Spatial Loop、Shadow Architect 與 Agentic Tech Lead 時，
不要把五支 Skill body 或安裝腳本複製進 consumer。使用
[`references/repository-control-plane.default.json`](references/repository-control-plane.default.json)
固定六段 controller chain，並用
[`references/repository-control-plane-profile.schema.json`](references/repository-control-plane-profile.schema.json)
封住 scope、authority、projection 與 evidence state。Consumer binding、offline issue snapshot 與 monitor plan
另由 `references/repository-control-plane-consumer-binding.schema.json`、
`references/github-open-issues-snapshot.schema.json`、
`references/repository-control-plane-monitor-plan.schema.json` 驗證，schema 名稱不再只是未落地的字串。

```bash
RCP=~/.agents/skills-shared/skills/shared-skills-infra/scripts/repository_control_plane.py
python3 "$RCP" profile-check
python3 "$RCP" attach --target-root <repo> \
  --consumer-repository-id <owner/repo> \
  --runtime-env-commit <exact-commit> --apply
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/shared_skills.py sync \
  --requirements <repo>/.agents/shared-skills.requirements.json \
  --target-root <repo> --apply
python3 "$RCP" verify --target-root <repo>
python3 "$RCP" monitor-plan --target-root <repo> --issues <offline-snapshot.json>
```

`repository_control_plane.py` 只是 CLI router；契約、consumer projection 與 monitor 分別由
`scripts/repository_control_plane_profile.py`、
`scripts/repository_control_plane_consumer.py`、
`scripts/repository_control_plane_monitor.py` 擁有，避免形成另一個不可替換的單體 bootstrap。

`attach` 只產生 `.agents/shared-skills.requirements.json` 與
`.agents/repository-control-plane.json`；immutable Skill binding 仍由現有 `shared_skills.py sync`
產生。`verify` 會拒絕 project-local body copy、mutable runtime ref、closure drift 與未生成的 binding；
缺席回報 `NOT_EXERCISED`／exit 3，不冒充 PASS。`monitor-plan` 只把 host 提供的 GitHub issue
snapshot 正規化成 controller plan，不輪詢網路、不執行 issue、不 merge。

完整 ownership、一次安裝、遷移與 rollback 見
[Repository Control Plane](../../docs/repository-control-plane.md)。正控與 planted mutations 在
`tests/repository-control-plane/test_repository_control_plane.py`；CI 只證明 deterministic contract，
不證明 Git Town、Forgejo、Worktree、Stack 或 dual-forge live execution。Host-scoped Git Town
installer 與 doctor 由 `runtime-env#36` 擁有，不得回流成 consumer-local 安裝器。

## clone 下來怎麼接線

```bash
git clone <private-repo> ~/.agents/skills-shared
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/shared_skills.py \
  install --project ~/proj-a --project ~/proj-b --claude-forwarder proj-b
```

`install` 做三件事：把路徑寫進 `sites.local.json`、把每個共用 skill 連上 user 層兩個 surface
與各專案、最後跑一次 `check`。**冪等**，換機器或搬動 checkout 後重跑即復原
（symlink 存的是路徑，搬完舊連結會先以 `WRONG-TARGET` 報錯而不是靜默指錯地方）。

新專案只要 `install --project <新 repo>`。共用 skills 其實在 user 層就已對所有專案可見；
專案層那份 symlink 是給**該 repo 自己的閘與文件用路徑引用**的，不是給發現用的。

### 兩種專案側形態（用參數選，不自動猜）

| 形態 | 產生什麼 | 給誰 |
|---|---|---|
| 預設 | `<repo>/.claude/skills/<name>` symlink | 大多數 repo |
| `--claude-forwarder <repo>` | 帶 `disable-model-invocation` 與 `$ARGUMENTS` 的轉發樁 | 家規要求樁內容的 repo（實例：ix-agy 的 `check_skill_forwarders.py`） |

專案側一律用**絕對路徑**指向 canonical：相對的 `.claude → ../../.agents` 一跳，
在 fork 過的 repo 會解析到它自己的本地副本而不是 canonical——連結會靜默指錯東西。

## 延後裁決（`deferred_in`）

收編某個 skill 時，若某些 repo 的版本**不在這次裁決範圍內**，用 `--defer <repo>`：
它們的副本原地保留、登記進 `deferred_in`，`check` 不當違規、`report` 持續列為待辦。
掃掉它們＝替人裁決；不記錄＝讓閘對一個沒人回答的問題長紅。兩者都不誠實。

## 這個閘刻意不進 CI

它的判準橫跨五個 repo 的絕對路徑與 user 層目錄，**在 CI 容器裡物理上不可重現**。
硬接進 pre-commit 只會製造一個永遠紅或永遠被跳過的假閘。它是本機治理閘，手動或
session 起手跑；要進 CI 得先設計成密封的（例如各 repo 只驗自己那一側）。
