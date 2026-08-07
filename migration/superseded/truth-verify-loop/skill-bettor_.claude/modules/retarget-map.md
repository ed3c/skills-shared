# Module: truth-verify-loop — antigravity → skill-bettor retarget 帳(2026-07-17)

> 屬 [`truth-verify-loop`](../SKILL.md)。port 觸發=計劃包 `docs/plans/2026-07-17-agent-native-sdlc-panorama/`
> Q7 人裁「現在就 port」。上游原檔=`/Users/neon/antigravity/.agents/skills/truth-verify-loop/`
> (SKILL.md 67 行+modules/measurement-methodology.md 42 行,port 當日 wc 實測)。

## 搬了什麼(方法論層,跨 repo 可轉移)

| 機制 | 上游形態 | 本地形態 |
|---|---|---|
| 階段拓撲(抽取→worker→聚合→判官→bounce→計分→落帳) | 組件卡逐階段表(帶上游檔案路徑) | SKILL.md「階段拓撲」一段壓縮+指針(不抄合約內容) |
| 不可簡化不變量 7 條 | 引用上游基座(AGENTS.md Resolved/KB 鐵律 7/hypotheses.md) | retarget:③⑤合併措辭、⑥「不 ingest KB」→「不入 families/」(本 repo 無 KB,隔離語意等價)、⑦保留 agy 紀律並對齊本 repo §5 |
| 判官紀律(fresh/下限 Opus/永不 agy) | 上游不變量 4 | 原樣保留+擴「永不 codex」(本 repo §5 硬約束① 2026-07-17 擴充版) |
| Gotchas(WebFetch 二手/U+2019/壞包) | 上游 Gotchas | 保留前二;「harness 壞包→AGENTS.md Resolved」指針**去除**(本 repo 無該帳本),壞包成本語意併入不變量 5 |

## 不搬什麼(+why,誠實帳)

| 上游物 | 為何不搬 |
|---|---|
| `truth-verify/t0/` 工具鏈+`contracts/` 實體 | 未原樣搬。skill-bettor 後來在獨立 Git root `loop_wiki/tv-dual-loop-context/` 建出本地實作並真跑;本地程式與 receipts 現為執行證據 SSOT,上游只留歷史 know-why。新題目不得重新引入上游 runtime dependency。 |
| `fixtures/_sealed/`+六 run 實測數字(E 主成分/tier 三明治) | 那是 antigravity 自己迴圈的考卷與證成軌跡,不是本 repo 證據(同 judge-loop-chooser port 先例:「不搬 truth-verify 實測錨」) |
| `hypotheses.md`/`loop-ledger.md` 內容 | 帳本=per-repo 產物;本地帳本在首次實例化時于沙盒內新開 |
| AGENTS.md「Resolved」處置協議指針 | skill-bettor 無集中式 Resolved 帳本(fold-in 明文);等價紀律走沙盒 `anti/`+PLAN.md |
| U0 誕生路徑指針(unknown-discovery-composer 全程編排史) | 上游的誕生史;本地 lineage=Q7 人裁,已記於 SKILL.md frontmatter |

## 本地新增(上游沒有)

- **已真跑本地實例**:`loop_wiki/tv-dual-loop-context/` 具備 Gemini/Codex findings workers、blind
  aggregation、fresh tools-disabled judge、pure scorer、ledger amendment 與 hash-bound Human LAND。
  已完成/未完成矩陣見 `modules/local-instance.md`。
- **codex=第四家族 worker 選項**(TYPE_C 跨家族聚合多一路;§5 2026-07-17 codex 檔位收編後才可能)。
- **額度 fallback 紀律指針**(§5 fallback 鏈+禁 silent fallback——上游無此軸)。
- **「模型自報不可信,判 model 看 session log」Gotcha**(2026-07-17 codex proof run 實測課)。
- **persona 注入 Gotcha**(ponytail SubagentStart;上游 host 無此插件生態)。

## 已知風險(port 時點誠實記)

- 上游路徑指針仍可能漂移,但只影響歷史 know-why;任何本地驗證或新題目流程依賴上游路徑都應
  fail closed 並移除該 dependency,不可回退成跨 repo runtime。
- 本地實例只證 dual-loop context 題目與已 LAND 的 context-engine tree;不可把這段證成外推到
  product seed、任意 technical design、跨 Domain composition 或使用者服務足夠性。
- Skill 不複製 receipts,因此能力狀態以 `modules/local-instance.md` 指到的實際 gate 重播為準;
  文件敘述與 exit code 衝突時一律信物理 gate。
