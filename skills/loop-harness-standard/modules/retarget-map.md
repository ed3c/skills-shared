# Module: loop-harness-standard — 上游 → 宿主 retarget 映射 + 誠實帳本

> 屬 [`loop-harness-standard`](../SKILL.md)。本檔＝移植的命門與誠實帳本:哪些機制一對一映到宿主、
> 哪些因為架構前提不同被拿掉/降級、為何不是簡化。
>
> **詞彙**:**上游**＝這份 skill 被移植出來的那個 repo;**宿主**＝正在訂閱這份共用 body 的 repo。
> 具體是哪個上游、哪個宿主、哪一天、釘在哪個 commit,屬 binding,寫在該 repo 的
> `.skill-bindings/loop-harness-standard/retarget-map.md`;本檔只留任何 repo 都適用的映射判準。

---

## 1. 為何多數內容不能逐字複製——上游版摻了大量它自己的歷史證成紀錄

上游版 `harness-spec.md` 與 `evals-design-method.md` 裡,相當比例是
**上游自己迴圈跑出來的證成紀錄**:具體 commit hash、具體踩坑案例編號、決策編號帳本、
某個 pilot 的逐輪判官 finding。這些是上游自己的軌跡,不是可搬的方法論——
逐字複製會:①違反這份標準自己教的紀律(≤300 行反膨脹);② 跟宿主已有的架構文件
(通常已用它自己的 families/evals/holdout 詞彙萃取過一次同一套方法論)重複又打架。

**移植只萃取可轉移的方法論**(8 基座卡精神、Verify 三層、evals 設計三段法、cache 不變量、驗證器
隔離原則),不搬歷史證成紀錄——宿主未來自己累積的軌跡,記在它各家族的 `changelog/`,不是繼承
上游的。

## 2. 逐機制 retarget 映射表

| 上游機制 | 宿主對應物 | 為何這樣映 / 拿掉了什麼 |
|---|---|---|
| 2×2 host×driver 平行設定矩陣(兩個 host 各維護一棵設定樹) | **不搬平行設定樹；改為 macro carrier × small driver 的觀測矩陣** | 宿主的 macro session 可由任一支援的 carrier 承載，small driver 另選 `claude -p`/`agy`/`codex`。兩軸用同一組 B1-B8 owner 與 receipt 觀測，不各建 settings/skills 治理副本；驗證隔離看 author×judge 家族，不看 host 名稱。 |
| `.agents/*`(settings.json EAGER／hooks.json／skills.json／agents/verifier.md)agy 側平行目錄 | **拿掉獨立 host config 目錄,授權走 `run.sh` CLI 旗標;保留 sandbox-local domain endpoint 能力** | 宿主的 op 沙盒通常沒有雙 host 平行 config 維護的需求;agy/codex driver 啟用時才落 `AGENTS.md` entry。若 entry contract 與 `CLAUDE.md` 真同構,可採一實體＋symlink;若需 codex/agy 權限、findings-only、`ROUTES.md` 等 host-specific 邊界,採薄 wrapper 指回 `CLAUDE.md`。但小迴圈可有 `.agents/agents/*` 和 `.agents/skills/*` 作 domain/task route endpoint;它們不是 `settings.json`/`hooks.json`/`skills.json` 這類 host config。 |
| 決策編號帳本(D1-D12 這類) | **不搬** | 那是上游團隊自己的決策沿革記錄,宿主沒有對應歷史,硬搬＝引用不存在的脈絡。 |
| 具體 commit 錨、編號踩坑案例史、pilot 逐輪 finding | **不搬,改用「本地 worked instance 指針」句式** | 這些是上游自己迴圈的證成軌跡。宿主對應的是它自己第一個有成長曲線的家族 evals 目錄——指到那裡,不複製上游的案例。 |
| `PLAN.md`/`PROMPT.md`/`CLAUDE.md` 命名與職責 | **原樣映**(命名本來就相同) | 上游 Claude 側早已用這套短名(非 agy 側 `IMPLEMENTATION_PLAN.md`/`AGENTS.md`),宿主 `_template/` 照此建;移植只是把規範文件補上。 |
| 8 基座組件卡 | **改寫詞彙**(scripts/tests fixtures → family evals/runner.py;.claude/agents/verifier.md → fresh subagent inline 描述) | 精神一對一映,措辭改用宿主架構文件已經用過的詞彙,避免同一概念兩套講法。 |
| Verify 三層 | **原樣映**(T0/行為/畢業判官三層概念完全通用) | 這是全篇少數與 host/driver 矩陣無關、純屬「怎麼分層驗證」的方法論,無需改。 |
| evals 設計三段法(維度×槓桿/runnable-rubric/planted-defect) | **原樣映,worked instance 換成本地家族** | 方法論通用;上游那種 `COMPLETENESS_RUBRIC`@`data.js` 專屬錨,換成宿主自己的家族 evals 目錄。 |
| cache 五不變量 | **原樣映**(Claude Code cache 機制與 host repo 無關) | 這條本來就是 Claude Code 平台事實,不因單/雙 host 而變。 |

## 3. 拿掉的東西不是「簡化」,而是「不引入不存在的架構前提」

- **能一對一映的映**:8 基座卡精神、Verify 三層、驗證器/執行者隔離原則、cache 不變量、evals 設計法、
  防退化鐵律裡與 host 無關的條款。
- **架構前提不同、真改造**:拿掉 2×2 平行 host config 與隔離翻面表；保留 carrier×driver 的觀測維度，
  並由 `data/dual-loop-eight-base.json` 綁共同介面。agy 側獨立 `.agents/*` config 仍不搬。
- **歷史紀錄、故意不搬**:編號決策帳本、commit 錨、編號案例史——那是上游自己的
  軌跡,宿主累積自己的在 `families/*/changelog/`。

## 4. 判別「retarget 成立」的鐵錨

- 本地活基座真存在:`loop_wiki/_template/`、`loop_wiki/engine.sh`(disk 已驗證)。
- 本地 worked instance 真存在:宿主第一個有成長曲線原點的家族 `evals/` 目錄。
- `loop_demo/{agy,claude_agy}` 本地目錄範例:見 loop-harness-standard SKILL.md 移植同批工作,
  若尚未落地以該任務狀態為準,不得假設已存在。

若有人往本 skill 塞回編號決策碼、上游具體 commit 錨，或為每個 carrier 重建一套平行治理
目錄，就是把不適用的架構前提搬回來——擋下。新增 carrier 應擴 adapter 與 receipt，不複製 B1-B8 SSOT。

---

## Sources / Lineage
- 上游源:上游 repo 內的 `.agents/skills/loop-harness-standard/`(SKILL.md +
  `modules/{harness-spec,evals-design-method}.md`);它在哪台機器、哪個 checkout、釘哪個 commit,
  屬 binding,記在宿主的 `.skill-bindings/loop-harness-standard/`。
- 宿主既有同構:宿主自己的架構文件(同一套方法論的 tight/at-a-glance 版,本 skill 是其
  深度展開版,兩者不重複——架構文件給常駐脈絡,本 skill 給 on-demand 深度 know-why)。

---

> 以下三節是**一次真實 retarget 的逐項落位紀錄**,留在共用 body 當範例,示範「上游條目 → 本地落位」
> 該長什麼樣;宿主自己那一次的實際條目寫進 `.skill-bindings/loop-harness-standard/retarget-map.md`。

## 增補範例 ①:oracle-aware 完成契約遷入(composer-integration Slice A)

- 上游 `harness-spec.md §5.1`(上游 2026-07-19 命名)→ 本地 **§4.5**(緊接 §4 Verify
  三層——本地章節結構不同,照本地落位,不抄上游編號)。
- **拿掉**:上游 checkpoint 記錄格式範本對上游 `dr-to-mvp/SKILL.md` 的行號指針(本地
  等價=`dr-to-mvp` dual-score 設計分∧實作分段,採用不重造,不釘上游行號);上游
  cache oracle 句(本地 §5 已有);上游證成史/設計理由(只留唯讀指針到上游計劃檔,不搬)。
- **新增於本地而上游無**:誠實正名條款成文(「零飄逸只在 dense 成立」——HANDOFF §2 正名,防產品側
  過度承諾);B-1 斷言表 schema 定義權落 §4.5(上游定義權在其計劃檔,本地無該檔,升格進 spec)。
- 三態 grounding 不遷:本地 SSOT 已在 `judge-loop-chooser/modules/grounding-and-independence.md`,
  §4.5 只指針。

## 增補範例 ②:execution-feedback 遷入(composer-integration Slice B)

- module+4 checker+fixtures+verify.sh 自上游
  `.agents/skills/loop-harness-standard/{modules/execution-feedback.md,scripts/execution-feedback/}`
  遷入;**checker/fixtures 逐位元組帶入不改邏輯**(diff -rq 已證同構;no-smuggled-plan-delta 含
  上游 branch-1 剝標籤修)。module 內文 retarget:
- **改指本地**:`harness-spec §5.1`→`§4.5`(×2);上游「§9❶ 人閘」→宿主架構文件的人閘節;B-1 schema
  定義權「上游計劃檔」→本地 §4.5;軌跡實名 `driver.iterN.json`(上游)→`driver.iterN.out`
  (本地 engine.sh dispatch 落檔 `driver.iterN.out` 實名,執行時 grep 驗真);「codex exec 主+`< /dev/null` 鐵律」→本地唯一入口
  codex-companion+「寫≠真跑」補真跑(宿主架構文件 codex 列)。
- **拿掉**:上游記憶引用(`anti-inflation-is-discriminator`/`agy-quota-silent-noop`——後者
  實質改指宿主架構文件 agy 列同義警告);編號式「引擎家族」代碼;定位段對上游「三類編排
  skill」節的指針(本地無此節,留實質句)。
- **新增於本地而上游無**:判官禁 ponytail hook 注入條款(本地已知 SubagentStart fail-open 注入
  風險);variant 目錄收攏形態「由 engine_nv wrapper(Slice C)定」的顯式留白。
- 上游計劃檔以唯讀指針保留於 module 頭注,證成史不搬。

## 增補範例 ③:更正(composer-integration Slice E,seam 審計追加)

- 範例 ① 節「拿掉 checkpoint 範本對 dr-to-mvp 行號指針」實際效果=**整條指針被拿掉,seam 第三環斷**
  (上游定案鏈:sdlc Output Contract→完成契約 §→dr-to-mvp dual-score;上游對應 slice 的驗收=dr-to-mvp
  零改動,方向=單向採用)。Slice E 已補回**本地**指針:§4.5 sparse 條→`dr-to-mvp` dual-score 段,
  LIVE 錨=宿主自己已畢業的那個家族。「不釘上游行號」的原意保留,錨改本地活實作。
