# Specs-as-Code 提示詞 v1（ready to paste）

> 屬 [`repo-agent-native`](../SKILL.md)。這是 `/specs-as-code` command 的 payload。方法論全文 → [`codebase-mastery-methodology.md`](codebase-mastery-methodology.md)。
> **這是 northstar `repo-agent-native/modules/specs-as-code-prompt.md` 的 antigravity retarget**——提示詞本體(tool-agnostic agent 指令)一對一映；北極星專屬的 worked-example 路徑(sandcastle `.knowledge_base/`)拿掉、留 lineage 註。
> **用途**：給 agent 一個提示詞，對一個 repo 產出「完全掌握」型 `.knowledge_base/`(3 檔)。
> **v1 改進來源**：northstar sandcastle 全源 run 的 `00-validation-scorecard.md` 實證——v0 naive 三檔模板(security 只問 SQLi/XSS/N+1)會漏 7 條 answer-key fact。v1 把 8 條 implicit-design probe 烤進每個 file spec、令 security 隨 repo 本質自適應、加平台條件審計與自評迭代步驟。
> **保留 v0 強項**：3 檔 `.knowledge_base`、`[[Obsidian]]` 連結、Mermaid、`⚠ 需人工二次確認` 旗標。

---

## ✂️ COPY-PASTE BLOCK（提示詞本體 v1）

```
你是一位頂尖系統架構師 + 安全專家。任務：對目標 repo 建立「完全掌握」型知識庫，產出 .knowledge_base/ 三檔。
你的事實必須可被任何人逐字複驗——不是「讀起來像懂」，而是真的掌握了設計合約。

═══ 鐵律 0：SOURCE = SSOT，先 clone 先讀源碼（功能漏斗 Tier 0 起，禁跳層）═══
1. 確認 canonical repo：對齊 npm `repository` 欄 / package.json / README 連結，別讀 fork/鏡像/過時 tag。
   記下版本錨點（如 package.json 的 version）。
2. clone 到本地（如 <OUT>/src/<name>；全歷史，never --depth 1）。後續每一條事實都附 source_ref = 檔案路徑 + 行號
   （file:line），指向這份 clone。
3. Tier 0 起：package.json（stack/entry/deps 性質）→ entry barrel（index/bin）→ 核心 façade → seam →
   provider。先把骨架讀出來，才用語義檢索（grepai / ripgrep）。
4. 任何「無法附 file:line」的事實（外部生態 / 上游 wire protocol / 雲端 SDK 假定）一律標
   「⚠ 需人工二次確認」。這是誠實邊界，不是失敗。禁把 README / 行銷宣稱當已驗證事實。

═══ 鐵律 1：IMPLICIT-DESIGN PROBE（每一檔都必須跑這 8 條探針）═══
不要只列 API 表面與漏洞清單。對每個模組主動問下列 8 條，並「把 README/我給你的 brief 的任何假設當作
待證命題，回源碼逐 file:line 證偽」——若源碼推翻了假設，明確寫「⚠ 與 brief/README 相反」並給 file:line：
  P1 SEAM 接縫        ：可抽換擴展點在哪？dispatch on 什麼（tag/name/型別）？加後端要不要碰 core？
  P2 DETERMINISM 邊界 ：每個 gate/判定是 exit-code/字串掃描（確定性）還是 LLM-judge/heuristic？
                        畫出「確定性 vs agent/heuristic-judged」的線。誤把確定性編排器讀成 agentic = 重大錯誤。
  P3 PLATFORM 條件碼  ：grep platform/win32/darwin/process.platform。哪些行為依平台分叉？
                        某個 no-op 是 bug 還是「正確地什麼都不做」？追「真正幹活的那步在 host 還是容器/平台內」。
  P4 BOUNDED LOOP     ：迴圈上限/終止信號/timeout 的【預設值】各是多少？是引擎內建結構還是呼叫端組合？
  P5 TRUST 邊界       ：哪些輸入不可信？信任邊界劃在哪（容器/進程/host）？哪個開關會讓它整條塌陷？
  P6 ERGONOMICS       ：有沒有「方便但危險」的語法糖/DX 合約？它同時是攻擊面嗎？防禦擋得住偽造嗎？
  P7 TYPED ERRORS     ：錯誤是 typed 還是裸 throw？error channel 怎麼設計？失敗時丟不丟副作用/上下文？
  P8 FRAMEWORK IDIOM  ：整棧建在哪個框架慣用法上（DI/Layer/Actor/...）？load-bearing 還是裝飾？用硬數據釘住
                        （如 grep 某 idiom 排 test 剛好 N 個）。

═══ 鐵律 2：security 隨 repo 本質自適應（先判型，再選攻擊面）═══
先用源碼判定 repo 本質，把結論寫在 security 檔開頭（load-bearing）：
  - 是 web/DB app（有 HTTP handler / SQL / ORM / 前端 render）？→ 才套 SQLi / XSS / CSRF / authz / N+1 / 記憶體洩漏 /
    re-render 瓶頸。
  - 是 sandbox/runtime/編排層（跑 untrusted 或 agent-generated code）？→ 真攻擊面 = 容器逃逸粒度、untrusted-code
    執行、mount/secret 跨界、shared-FS 信任邊界、把隔離整個拿掉的降級開關。【禁】硬塞 SQLi/XSS/N+1。
  - 是 library / SDK / CLI？→ 攻擊面 = 不可信輸入解析、命令注入、路徑穿越、依賴供應鏈、敏感預設值。
  - 其他（資料管線 / 編譯器 / infra）→ 推導其真實不可信輸入與信任邊界，別套錯清單。
若硬把 web 漏洞清單貼到非 web repo，就是問錯了問題——明確說明本 repo 真正的攻擊面為何。

═══ 鐵律 3：DETERMINISM-vs-HEURISTIC call-out（明確一張表）═══
在 data-flow 檔列一張表：每個「判定點 / gate」一行，標機制、是否確定性、file:line。
唯一允許的 heuristic（如 time-based timeout）也要單獨點名並說明它不評斷品質。

═══ 鐵律 4：PLATFORM-CONDITIONAL 審計步驟 ═══
grep 全 repo 的平台分叉，列一張表：file:line / guard 條件 / non-matching 平台行為 / 風險。
特別追：merge/commit/IO 這類「真正落地」的步驟究竟跑在 host 還是平台內；某平台的 no-op 是否其實正確。

═══ 鐵律 5：寫檔用 Write 工具 / heredoc 腳本（禁 echo/cat 拼檔）═══
不要用 echo / cat >> 逐行拼檔（脆、會被 shell 轉義咬、無原子性）。用 Write 工具直接寫整檔，或寫一個
heredoc 腳本一次性產出。檔案要可被 Obsidian 開：模組名用 [[雙鏈]]，圖用 ```mermaid```。

═══ 產出：.knowledge_base/ 三檔（每檔都跑完上面 8 條 probe）═══
[[architecture_map.md]]
  - business purpose + full tech stack（附 file:line）+ framework idiom（P8，硬數據釘住）。
  - C4-ish Mermaid 架構圖：標出 seam（P1）與依賴方向；粗線=核心接縫、虛線=旁路。
  - 目錄/核心模組責任 + 依賴方向（[[雙鏈]]）；第三方依賴 5–10 個 + 角色 + 性質（peer/optional/devDep）。
  - typed-error 家族（P7）。⚠ 外部/上游不可附 line 者標待確認。

[[data_flow_and_api.md]]
  - 載重糾正區（先讀）：若源碼與 brief/README 相反，開頭就講清。
  - 單次主流程 Mermaid sequence diagram：把 entry→façade→loop→seam→provider→落地 串成一條合約。
  - DETERMINISM-vs-HEURISTIC 表（鐵律 3）。
  - public API 輸入選項表（含【預設值】，P4 bounded-loop）；驗證閘；結構化返回型別。
  - 平台條件式表（鐵律 4）。

[[security_and_bottlenecks.md]]
  - 開頭一行 repo 本質判定（鐵律 2，load-bearing）+ 一句話威脅模型 + 不可信輸入是什麼。
  - 真實攻擊面（依本質選清單，非預設 web 清單）：trust 邊界（P5）、ergonomic 攻擊面（P6，含偽造防禦評估）、
    secrets/env 跨界、降級開關。每條附 file:line 與風險定性。
  - 真實瓶頸（同樣依本質：web 才 N+1/re-render；runtime 則資源耗盡/無界成長/並行 fan-out 無上限等）。
  - refactor/加固建議：對 load-bearing 但脆弱的設計（如「呼叫站點完整性」）給可行動結論。
  - 凡推測或無法源碼證實者標 ⚠ 需人工二次確認。

═══ 鐵律 6：自評 + 迭代（evaluator-first，收尾必做）═══
產出三檔後，以 fresh eye 重讀自己寫的 KB，回答並寫成一個 self-review 區塊：
  (a) 列出我【漏掉】的隱含設計：8 條 probe 裡哪條沒在某模組跑到？
  (b) 我有沒有把任何 README/brief 宣稱當事實而沒回源碼證偽？逐條補驗或標待確認。
  (c) 若有既有吸收 / 答案鑰匙（answer-key），逐條判 yes/partial/no，證據必須來自 KB 自身的 file:line；
      load-bearing 條目回 clone 源碼逐字複驗（KB 說對 ≠ 自洽）。
然後【修訂】三檔補上漏掉的隱含設計，直到：8 條 probe 對每個核心模組都跑過 + 每條 load-bearing 事實
都有 file:line 且回源碼複驗屬實。把 coverage 與 MISSES 寫進 self-review。

═══ 鐵律 7：behavioral/runtime claim 只能真跑定案（RIP 封頂）═══
任何「某操作在某平台是否可用 / 是否真隔離 / perf 數字」的行為 claim，禁只憑源碼讀或窄 probe 斷定
（會 over-reach）。跑一次完整 RIP（目標 repo 自己的 run/test 端到端路徑）定案；未 RIP 者最高標 Evidence B「未 RIP」。
```

---

## v0 → v1：改了什麼且為什麼（northstar sandcastle scorecard 實證，摘要）
v1 相對 naive 三檔模板(v0)的加固，各對映它修的 answer-key miss：
- **鐵律 0**(clone-first ＋ file:line) → 全部事實的可複驗基礎；README 宣稱 vs 源碼觀測只有源碼 SSOT 才分得開。
- **鐵律 2**(security 隨本質自適應) → sandbox/runtime repo 的真攻擊面(隔離粒度／shared-FS／inline-shell／secrets)，禁硬塞 web 清單。
- **鐵律 1 P2 ＋ 鐵律 3**(determinism-vs-heuristic 表) → 防把確定性編排器誤讀成 agentic 自評。
- **鐵律 1 P3 ＋ 鐵律 4**(平台條件碼) → host-side merge-back／platform no-op 這種「naive 模板絕無可能觸及」的最高價值點。
- **鐵律 1 P4**(bounded-loop 預設值) → loop-agnostic 泛用迴圈 vs 呼叫端組合。
- **鐵律 1 P1**(seam dispatch on tag/name/型別)、**P6**(ergonomic 偽造防禦)、**P7+P8**(typed-error channel ＋ framework idiom 硬數據)。
- **鐵律 6**(fresh-eye self-review ＋ answer-key 計分) → 把「8 probe 是否真跑過每個模組」變成可量測收尾閘。
- **鐵律 7**(RIP 封頂) → behavioral claim 完整真跑定案(cc-20260624 sandcastle merge-back 雙重 should-catch 教訓)。
- 保留 v0 強項：3 檔結構、`[[Obsidian]]`、Mermaid、`⚠ 需人工二次確認`——原樣保留，v1 只 harden。

## 一句話
v1 ＝ v0 的三檔／Obsidian／Mermaid／⚠ 旗標**全留**，再把「先 clone 源碼當 SSOT ＋ 8 條 implicit-design probe ＋ repo 本質自適應 security ＋ determinism／平台審計 ＋ evaluator-first 自評迭代 ＋ RIP 封頂」烤進每個 file spec。
