# skills-shared — 跨 repo 共用的基礎設施 skills ＋ 受管的 agent 文件

所有 Claude Code 與 Codex CLI 專案共用的 skill 本體住在這裡，**一個名稱只有一份**。
治理規則、指令與 why 全在 [`skills/shared-skills-infra/SKILL.md`](skills/shared-skills-infra/SKILL.md)；
裁決帳在 [`registry.json`](registry.json)。本檔是**索引**：說什麼住哪裡、怎麼到達、怎麼驗，不複述規則。

## 頂層

| 路徑 | 是什麼 |
|---|---|
| [`skills/`](skills/) | 22 個共用 skill 的本體（下方逐一索引） |
| [`registry.json`](registry.json) | 裁決帳：哪個名字是共用、哪個是 repo 自有、為什麼。**只存裁決，不存機器路徑、不存凍結 hash** |
| `sites.local.json` | 這台機器的路徑（gitignored）。clone 到任何目錄都能用，靠的就是路徑不進版控 |
| [`migration/`](migration/) | 2026-08-07 收編時被取代的 repo 副本（**移走不刪除**，讓遷移可對帳）＋ [`HANDOFF-2026-08-07.md`](migration/HANDOFF-2026-08-07.md) |

## 拓撲

```text
~/.agents/skills-shared/            ← 本 repo（唯一副本，有 git 歷史）
  skills/<name>/
        │
        ├─ ~/.agents/skills/<name>   → symlink（Codex user scope，canonical 側）
        │        │
        │        └─ ~/.claude/skills/<name> → ../../.agents/skills/<name>（Claude user scope）
        │
        └─ 所有專案自動看得到，包含未來新增的——不需要 per-repo 連結
```

canonical 放 `.agents/` 側有兩個理由：那是 Codex 官方的 skill 發現路徑；且這台機器 user 層
既有 42 條 symlink 就是 `.claude/ → .agents/` 這個方向，反過來做會製造第二種慣例。

**repo 層不放共用 skill。** user 層已覆蓋全部專案，repo 再放一份同名的只會無聲影蓋
（兩個 host 的 project skill 都優先於 user skill）。repo 層只放它自己真正差異化的 skill。

## Skill 索引（22 個，全部已登記）

「跑」欄標示它自帶 `scripts/` 可執行入口（8 支）。其中 4 支自帶 `--selftest`
（forgejo-delivery-loop、html-for-decisions、knowledge-continuity、loop-harness-standard），
5 支另有 `tests/`（github／gitlab-delivery-loop、html-for-decisions、knowledge-continuity、
shared-skills-infra）。**花錢前先找它自帶的便宜驗證面跑一次**——沒有 ✓ 不代表沒東西可驗，
代表要進那支 skill 自己看。

### 治理

| skill | 一句話 | 跑 |
|---|---|---|
| [shared-skills-infra](skills/shared-skills-infra/SKILL.md) | 一個名字要嘛共用要嘛 repo 自有，不能兩者皆是；`check` 就是抓「repo 副本無聲影蓋共用版」的那道 | ✓ |

### 交付追蹤（三個 host，**不可混用**）

| skill | 一句話 | 跑 |
|---|---|---|
| [forgejo-delivery-loop](skills/forgejo-delivery-loop/SKILL.md) | 本機 Forgejo：四層儀表板（PRD issue／slice／PR／milestone）＋零網路收據閘＋操作層；**也管本 repo 的 agent 文件**（見下節） | ✓ |
| [github-delivery-loop](skills/github-delivery-loop/SKILL.md) | GitHub：同型閉環＋四層 merge 授權堆疊，`merge_gate.py` 開工前 preflight | ✓ |
| [gitlab-delivery-loop](skills/gitlab-delivery-loop/SKILL.md) | GitLab／glab：MR 與 issue board 版本。**三者的 registry／receipt 互餵會被拒並指回正確那支** | ✓ |

### 迴圈工程

| skill | 一句話 | 跑 |
|---|---|---|
| [loop-harness-standard](skills/loop-harness-standard/SKILL.md) | 大小迴圈八大基座設計標準：建沙盒、選 driver、分層 verify（T0／G 閘／holdout） | ✓ |
| [loop-harness-review-handoff](skills/loop-harness-review-handoff/SKILL.md) | 把一次 harness 架構 review 交接給零上下文的 fresh-session reviewer | |
| [truth-verify-loop](skills/truth-verify-loop/SKILL.md) | 對一組 claim 跑「抽取→多 tier 驗證→跨家族聚合→fresh 判官→純腳本計分」閉環 | |
| [dr-research-loop](skills/dr-research-loop/SKILL.md) | DR proposal 迴圈 owner：一題研究跑成 proposal 並走完 T0 四閘＋人 admit | |
| [dr-to-mvp](skills/dr-to-mvp/SKILL.md) | 把研究語料冷啟動成畢業 MVP 的 stateful workflow | |

### 計劃與編排

| skill | 一句話 | 跑 |
|---|---|---|
| [sdlc-plan-composer](skills/sdlc-plan-composer/SKILL.md) | 多階段 SDLC 計劃編排：意圖對齊→不變量抽取→垂直切片→介面設計→執行者選型→驗證契約 | |
| [unknown-discovery-composer](skills/unknown-discovery-composer/SKILL.md) | 起點在迷霧時用：對 KK／KU／UK／UU 四象限逐一路由，只 surface 不執行 | |
| [autoresearch-composer](skills/autoresearch-composer/SKILL.md) | 有界 modify→verify→keep/discard 指標迭代迴圈的計劃編排（薄層 router） | |

### 驗證與判準

| skill | 一句話 | 跑 |
|---|---|---|
| [judge-loop-chooser](skills/judge-loop-chooser/SKILL.md) | 把一個可判 deliverable 路由到驗證標準、grounding 三態、獨立性 tier 與人閘 | |
| [path-b-reduction](skills/path-b-reduction/SKILL.md) | 把每個 claim 約分到確定性鐵錨（exit-code／test／selftest／已查證來源），擋認知卸載 | |
| [external-verify](skills/external-verify/SKILL.md) | 官方規範類 claim 用 primary source 查到鐵錨，不靠訓練記憶或搜尋摘要 | |

### repo 理解與診斷

| skill | 一句話 | 跑 |
|---|---|---|
| [repo-agent-native](skills/repo-agent-native/SKILL.md) | source-anchored 業務不變量抽取，每個事實帶 Evidence Level ＋ `path:line` | |
| [repo-wiki-converge](skills/repo-wiki-converge/SKILL.md) | 任意 repo → Opus 級理解 wiki，靠「Opus 判官 × Gemini 作者」judge-loop 收斂 | |
| [repo-fullstack-debugger](skills/repo-fullstack-debugger/SKILL.md) | 反覆失敗的黑盒診斷外層閉環，畢業成 tested playbook 再 fold-in | |

### 知識沉澱與產出

| skill | 一句話 | 跑 |
|---|---|---|
| [fold-in](skills/fold-in/SKILL.md) | 把一段經驗折進既有結構，而不是為每段經驗造新 skill；判 durable home | |
| [knowledge-continuity](skills/knowledge-continuity/SKILL.md) | 修補文件的知識斷點，讓讀者不必靠記憶補上文中沒給的前提 | ✓ |
| [html-for-decisions](skills/html-for-decisions/SKILL.md) | 從 Markdown SSOT 產自包含 HTML 決策面與 email bundle；Markdown 永遠是源 | ✓ |
| [gemini-conversation-research](skills/gemini-conversation-research/SKILL.md) | 把 Gemini 對話的隱性知識結構化，只把真缺口送 Deep Research | ✓ |

## 受管的 agent 文件（CLAUDE.md／AGENTS.md）

集中真源住在 **[`skills/forgejo-delivery-loop/agent-docs/`](skills/forgejo-delivery-loop/agent-docs/)**，
不是獨立 repo。各 repo 內那份是投影，方向永遠是 `agent-docs → 目標`，閘只比位元。

| 路徑 | 是什麼 |
|---|---|
| [`agent-docs/README.md`](skills/forgejo-delivery-loop/agent-docs/README.md) | 納管契約、五種輸出的意思、誰掛了 commit 閘誰沒有 |
| [`agent-docs/HOST-SURFACES.md`](skills/forgejo-delivery-loop/agent-docs/HOST-SURFACES.md) | 兩個 host 各讀哪些檔／優先序／在哪裡靜默失效（官方 URL 錨定） |
| [`agent-docs/manifest.json`](skills/forgejo-delivery-loop/agent-docs/manifest.json) | 誰被管、哪些缺席是登記過的、預算數字 |
| [`agent-docs/_template/`](skills/forgejo-delivery-loop/agent-docs/_template/) | 新專案骨架：CLAUDE.md（一行 `@AGENTS.md` import）＋ AGENTS.md（路由層） |
| `agent-docs/<repo 目錄名>/`、`agent-docs/_global/` | 各 repo 與兩個 host home 的受管檔 |

> **已知的規則張力，寫下來不掩蓋**：`registry.json` 的 `_rule` 說共用 skill 是 host 基礎設施、
> 不含 repo 專屬內容，而 `agent-docs/<repo>/` 正是 repo 專屬內容。當前是刻意的例外
> （2026-08-08 人裁「集中管理」），尚未在 `_rule` 補上對應條文。

## 指令索引

```bash
INFRA=~/.agents/skills-shared/skills/shared-skills-infra/scripts/shared_skills.py
DOCS=~/.agents/skills-shared/skills/forgejo-delivery-loop/scripts/agent_docs.py

# 共用 skill 治理
python3 $INFRA install --project ~/proj-a --project ~/proj-b   # 接上這台機器；冪等
python3 $INFRA check                                           # T0：無影蓋、無未登記
python3 $INFRA report                                          # 全表分類，待裁決佇列
bash ~/.agents/skills-shared/skills/shared-skills-infra/tests/verify.sh   # 自測，零網路

# agent 文件漂移
python3 $DOCS selftest                    # 先證閘會紅（七種植入缺陷 ＋ 乾淨對照）
python3 $DOCS check                       # 全掃
python3 $DOCS diff                        # 漂在哪
python3 $DOCS apply --to-targets          # 真源 → 各 repo（方向必須顯式）
python3 $DOCS import --key <target>       # 收編某目標的現況為真源
```

`install` 寫路徑 → 連 user 層與各專案 → 跑 `check`。換機器或搬 checkout 後重跑即復原。
版控內容**沒有任何機器路徑**：canonical 位置由 `__file__` 推導，路徑全在 gitignored 的
`sites.local.json` 或旗標。

## 現況（2026-08-08 實測，非抄錄）

`shared_skills.py check` 綠：**22 個共用 skill 全部登記且無影蓋**；`registry.json` 另記
8 個 repo 自有名稱。`agent_docs.py check` 綠：9 個受管檔位元相同。

數字別在這裡凍結——`report` 與 `check` 隨時重算，與現實不符的紀錄比沒有紀錄更糟。
2026-08-07 收編的來龍去脈（26 個同名多份、24 個內容分岔、`deferred_in` 待逐個裁決的變體）
→ [`migration/HANDOFF-2026-08-07.md`](migration/HANDOFF-2026-08-07.md) 與 `registry.json` 的逐條 `why`。
