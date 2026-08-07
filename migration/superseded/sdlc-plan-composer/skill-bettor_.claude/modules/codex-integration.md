# Module: sdlc-plan-composer — S4 Codex（OpenAI）子代理整合

> **2026-07-27 current override**：下方 Claude plugin／`codex:codex-rescue`／`CLAUDE_PLUGIN_ROOT` 內容只作
> 歷史 proof，不是 production carrier。現行 interface 是
> `execute(slice_ref, base_sha, isolation=native_worktree) -> SliceReceipt`：當前 Codex 主 session 擁有
> dependency DAG 與串行 integration queue；execution session 必在工作起點進原生 worktree，記
> session/worktree/base/head/dirty/writer-set/artifact-root/commands/exits/diff/model/tool-policy/cleanup receipt。
> 原生隔離不可證時停止 write delegation；主 tree 禁切 branch，也禁止共享 tree 並發。Codex App 由
> **Worktree** 或 **Hand off → Worktree** 建立 managed worktree。Codex CLI 沒有 worktree 建立命令；CLI
> fallback 只能在工作起點由人或明確獲授權的 orchestration 用標準 `git worktree add --detach` 建立，
> 再以 `codex -C <worktree>` 啟動。不可把自製目錄或未核驗 JSON 冒充 worktree。
> 結果分 `executed`／`validated`／`integrated`／`full_verified`，completion message 不得冒充任一後態。

### Worktree receipt（官方 surface 對齊）

官方 Codex 文件把 managed worktree 定位在 ChatGPT desktop app；App 預設從所選 branch 的 HEAD 建立
detached worktree，並可用 `.worktreeinclude` 複製必要的 ignored 檔。CLI 的 `-C/--cd` 只選既有工作
目錄，不會建立 worktree。因此 CLI execution 的可重跑流程是：

```sh
git worktree add --detach <worktree-path> <base-sha>
git -C <worktree-path> rev-parse --show-toplevel --is-inside-work-tree HEAD
codex -C <worktree-path> doctor --json
python3 <worktree-path>/scripts/native_worktree_receipt.py \
  <worktree-path>/<plan-dir> --node <node-id> --output <receipt.json>
```

CLI **不能把已在執行的同一 session 原地改綁到另一個 workspace root**。`/fork` 與穩定子命令
`codex fork` 分叉的是 transcript/thread，不是 Git checkout；單獨執行 `/fork` 不會建立或切換
worktree。建立並驗收 worktree 後，依是否需要舊對話選一條新 session 入口：

```sh
# 全新 transcript
codex -C <worktree-path>

# 保留來源 transcript，但產生新的 thread id；<session-id> 先由來源 TUI 的 /status 取得
codex fork <session-id> -C <worktree-path>
```

多 session 並行時禁以 `codex fork --last` 當可稽核派工入口，因為「最近一次」可能不是欲分叉的
session。`/fork`／`codex fork` 也不得拿來滿足 fresh zero-context judge：fork 會保留作者 transcript，
只適合需要延續上下文的 execution session。若只在舊 session 逐條用 `git -C <worktree-path>`，其啟動時
workspace、sandbox writable roots 與 `AGENTS.md` 載入鏈仍未重綁，也不算已切換 execution session。

最後一步要求 `.git` 是 linked-worktree 指標檔、Git dir 與 common dir 不同，且 doctor 的
`repo detected=true`、`cwd`、`repo root` 都精確指向該 worktree；receipt 綁 plan digest、node、HEAD
與上述路徑。`scripts/execute_sdlc_plan.py` 會對 live checkout 重驗，故主 tree 產生的假 receipt 無法解鎖。

surface 邊界：Codex App 有 managed worktree、Handoff 與 `.worktreeinclude`；Codex IDE 只有目前介面
確實列出時才使用 `/worktree`；CLI 有 `/fork`／`codex fork` 與 `-C`，但沒有 `codex worktree`、
`--worktree` 或 `-w`。

官方來源：[Worktrees](https://learn.chatgpt.com/docs/environments/git-worktrees)、
[Codex CLI command options](https://learn.chatgpt.com/docs/developer-commands?surface=cli)、
[Codex IDE extension slash commands](https://learn.chatgpt.com/docs/developer-commands?surface=ide)。

> 屬 [`sdlc-plan-composer`](../SKILL.md) S4。**範疇提醒**：本檔只補「S4 需要 OpenAI GPT 家族子代理時
> 怎麼做」這一塊新知識，**不**重新評估/重寫 S4 目前對三個 backend（Claude 原生 `Agent`/`Workflow`
> 工具＋codex＋agy）的分工判斷——`superpowers:*` 理論性路由已於 2026-07-17 拿掉（2026-07-11 核實未
> 啟用，2026-07-17 定案改指原生工具），見 SKILL.md 該行的 ⚠️ blockquote 與 `modules/retarget-map.md`。
> 本段 current override 以 2026-07-27 官方 Worktrees／CLI／IDE 文件與本機 `codex --help`、
> `codex fork --help` 驗收為準；下方 antigravity/plugin 內容只保留 2026-07-17 的歷史 proof，不能反向
> 覆蓋 current override。

## 官方 plugin：優先於任何手刻 Codex CLI 呼叫

`codex@openai-codex` plugin（v1.0.6，`~/.claude/plugins/cache/openai-codex/`，scope=user，
`/codex:setup` 本機驗證就緒：`codex-cli 0.144.5`、ChatGPT login active、`reviewGateEnabled: false`）。
其 `codex-cli-runtime` skill 明文：「Prefer the helper over hand-rolled...direct Codex CLI strings」
——不要自己刻 `codex exec` 呼叫，官方維護的 `codex-companion.mjs` runtime 才是正確入口（它管
auth/job tracking/background/resume，自己刻會重造一套會漂移的替代品）。

**主要機制**：`Agent({subagent_type: "codex:codex-rescue"})`（或 `/codex:rescue` slash 命令）——唯一
入口，內部只做一次 `Bash` 呼叫 `node "${CLAUDE_PLUGIN_ROOT}/scripts/codex-companion.mjs" task ...`，
原樣回傳 stdout，不加工、不改寫。

派工時的具體規則：

- **model/effort 只在明確要求時才設**：官方預設不填（「Leave unset unless the user explicitly
  requests one」）；S4 分治委派本身就是明確要求的來源，需要哪個 tier 就直接在轉發給
  `codex:codex-rescue` 的請求文字裡指定 `--model <值>`/`--effort <值>`（接受值：`none`/`minimal`/
  `low`/`medium`/`high`/`xhigh`；`spark` 會被映射成 `gpt-5.3-codex-spark`）。
- **write-capable 是預設**：除非明確要求唯讀/只要 review/diagnosis/research。
- **背景執行**：任務開放式/預期跑很久 → 請求帶 `--background`；小而明確 → 預設 foreground（或帶
  `--wait`）。
- **接續同一條 thread**：`--resume`（內部映射 `task --resume-last`）；全新一輪用 `--fresh`。
- **結果處理鐵律**（官方 `codex-result-handling` skill）：Codex 回傳的是原始輸出，failed/incomplete
  的 run **不可被接手改成自己的實作嘗試**；沒有 findings 就明講沒有；review 類輸出**絕不自動套用修正**
  ——一定先問人要不要修，動一個檔都不行。

## 其他官方能力（附註，未接線進本 skill 或 `judge-loop-chooser`）

`/codex:review`（defect-focused）與 `/codex:adversarial-review`（approach/design-challenge-focused）
是純只讀 code review，跟本地 `code-review` skill 角色不重疊，是額外的跨模型家族（GPT vs Claude）獨立
觀點，需要時可直接呼叫。**刻意不接進 `judge-loop-chooser`**——該 skill 明文「代碼產物→直接
code-review，無 code-branch」是刻意設計邊界，不為塞新功能破壞它。skill-bettor 沒有
`repo-fullstack-debugger` 這類 skill（antigravity 特有），故 `codex:codex-rescue` 與既有診斷 skill 的
邊界說明本檔略過，誠實記為不適用，非遺漏。

**完整命令面**（2026-07-17 補盤，`commands/` 實有 8 檔；先前本檔只記 3 個是盤點缺口非刻意）：
- `/codex:status`／`/codex:result`／`/codex:cancel`——**背景心流的收割介面**：review／adversarial-review
  ／task 帶 `--background` 跑後，用 status 查進度、result 收成果、cancel 中止。與 tracer 紀律相容：
  收割仍以實際輸出為準，遇 runtime 層回報異常時 fallback=session log 直讀（2026-07-17 實測過一次：
  子代理回「已轉背景」即停＝exit-0 假成功形態，最後由 rollout jsonl 收割）。
- `/codex:transfer`（`--source <claude-jsonl>`）——把當前 Claude session 轉成可 `codex resume
  <session-id>` 的 Codex thread，**「離線交接」的官方正版**。社群流傳的「`codex exec --brief
  <brief.md>`／fable-codex-brief 規範」**不存在**（`codex exec --help` 零命中 `--brief`，2026-07-17
  直測）——別照抄；離線交接兩條正路：①本 repo 計劃包 `NN-slice` 執行契約段本身就是 brief
  （意圖／patch-spec／驗證段），餵 `codex:rescue`；②官方 `/codex:transfer`。
- `/codex:setup`——就緒檢查（本檔開頭已用）。

## 與小迴圈八大基座的接線（2026-07-17 同批新增）

本檔是**大迴圈**（S4 分治委派）層級的 codex 整合知識；**小迴圈**（`loop_wiki/*` 八大基座）層級的
codex driver 接線在 `loop-harness-standard`（`.claude/skills/loop-harness-standard/modules/
harness-spec.md` §3 第 4 項＋新增 ❻❼❽ 方法論），已把 `codex` 接進 `loop_wiki/engine.sh`（第三個
合法 `--driver`）與 `loop_wiki/_template`／`_template_dr`（未來新 op 的起點模板）。兩層不重複——
本檔管「S4 怎麼呼叫 codex」，harness-spec.md 管「小迴圈 run.sh 怎麼呼叫 codex」，呼叫機制相同（同一支
官方 `codex-companion.mjs`），只是誰在呼叫不同。**proof run 已補**（2026-07-17 同日稍後）：經 `codex:codex-rescue` 真跑 gpt-5.4-mini@medium 最小唯讀 tracer，24.8s 返回；A 級錨=`~/.codex/sessions/2026/07/17/rollout-*019f6f4c*.jsonl` 內 `"model":"gpt-5.4-mini"`,`"effort":"medium"`。**教訓**：模型輸出自報 model 名不可信（該次自稱 gpt-5），判實跑 model 一律看 session log。（antigravity 側更早已在 `loop_wiki/codex_demo`/`design_governance` 真跑驗證；小迴圈側 `--driver codex` 完整 op 真跑仍未發生。）

## Sources（2026-07-17，會過期）

- antigravity 同日等價模組：`/Users/neon/antigravity/.agents/skills/sdlc-plan-composer/modules/
  multi-model-subagent-dispatch.md`（Backend 2 段，本檔內容的直接來源）。
- 官方 plugin 原檔（本機讀取直測）：`~/.claude/plugins/cache/openai-codex/codex/1.0.6/`
  `skills/codex-cli-runtime/SKILL.md`、`agents/codex-rescue.md`、`skills/codex-result-handling/SKILL.md`、
  `commands/{rescue,review,adversarial-review,status,result,cancel,transfer,setup}.md`（8 檔全清單，
  2026-07-17 補盤直測）。
- `/codex:setup --json` 本機直測輸出（2026-07-17）；`codex exec --help` 直測（無 `--brief`，同日）。
