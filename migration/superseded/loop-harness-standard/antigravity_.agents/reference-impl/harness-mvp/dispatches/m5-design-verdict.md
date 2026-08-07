# M5 設計分判官裁決 — harness-mvp

> Fresh zero-context Opus (T1)。無本大迴圈 drafting 史。只讀封裝包 5 件 + src/*.py + tests/test_sc*.py。
> 判準：done 格＝(a) 錨真偽 + (b) 覆蓋真偽（測試真驗到 element 核心行為）；cut 格＝DC 理由是真裁剪還是遮羞布。
> 抽核深度：22/22 格錨逐格對讀 SYNTHESIS §1/§2/§4/§6/§7/§7.1 原文（**遠超 8 格下限**）；16 done 格全部讀對應 test 檔 + src 核覆蓋；34 passed 親跑複核（下附）。

## 親跑複核
`python3 -m pytest tests/ -q` → **34 passed in 0.27s**（判官本機真跑，非採信 PLAN 自陳）。

## 逐格表（22 格，一格未跳）

| 行 | element 摘要 | done/cut | 錨核對 | 覆蓋核對 | verdict |
|---|---|---|---|---|---|
| R1 (L7) | L0 薄核心 while-loop 只管工具態/重試/事件流，不內建 Plan/子代理 | done SC2 | 真（§1 L0:37 逐字；§6:282） | 實（test_sc2 純度斷言無 plan/planner/subagent/orchestrate + 重試/事件流測試） | **PASS** |
| R2 (L8) | L0 收 dispatch 封包+L2 指標，發事件流+執行結果，每步交還確定性碼 | done SC1,SC2 | 真（§1 L0:38-40） | 實（run_loop 簽名收 task_packet+ledger；loop.py:67-73 每步交 l3/l4 閘） | **PASS** |
| R3 (L9) | L2 append-only JSONL + DAG parentId + 大物件 URI/hash 指針 | done SC3 | 真（§1 L2:56-69；§6:292-305） | 實（envelope._validate_snapshot >512B 強制指針；test_sc3 五 case 含 append-only 增長/lineage/大物件拒收） | **PASS** |
| R4 (L10) | 統一信封九欄 id/parentId/loop_layer/task_ref/event/exec/handoff/budget/freshness | done SC1,SC3 | 真（§6:292-303 JSON 塊逐欄） | 實（REQUIRED_FIELDS＝該九欄；test_sc3 斷言排序九欄；test_sc1 拒 schema drift） | **PASS** |
| R5 (L11) | exec 獨立 result_snapshot 欄不超載 error_snapshot | done SC3 | 真（§6:299；§7 UK3:323） | 實（EXEC_FIELDS 含 result_snapshot；test_sc3 兩欄各自 round-trip；sig 用 result_snapshot 非 error） | **PASS** |
| R6 (L12) | 每筆整行含 \n 單次 write，禁分段寫 | done SC7 | 真（§7.1 UK6:335 鐵律逐字） | 實（test_sc7 spy os.write：3 筆各 1 call 各 1 \n；無 partial-write 公開面；長行單 write） | **PASS** |
| R7 (L13) | Resume 純讀 JSONL 重建 iteration/tokens/dup streak/parentId，無隱藏記憶體態 | done SC4 | 真（§7 UK4:325） | 實（ledger.rebuild_l3_state 純讀磁碟；test_sc4 五 case 含 budget 不重置/跨 cutoff dup kill/lineage 重建） | **PASS** |
| R8 (L14) | 非零 exit_code 無 handoff 自動 L3/L4 阻斷不靜默續行 | done SC1,SC8 | 真（§1 L2:64；§6:305） | 實（gates._deterministic_failure；test_sc1/test_sc8 硬斷 exit30；test_sc2 重試耗盡阻斷） | **PASS** |
| R9 (L15) | L3 硬限起於可配置 max_iterations/maxMessages/maxAttempts，須真迭代校準非證定常數 | done SC6 | 真（§6:284-287；§6:309） | 實（核心原則）；**maxMessages 無獨立旋鈕**——見 OF-1 | **PASS**（OF-1） |
| R10 (L16) | L3 dup 預設 sig_with_result（含 tool+args+result hash），非無結果簽名 | done SC5 | 真（§7 UK1:319） | 實（sig_with_result 用 command+event_args+result_snapshot 且唯一預設；test_sc5 結果遞變/重試不同結果零誤殺＝證含 result hash） | **PASS** |
| R11 (L17) | L3 per-signature 早殺：任一簽名達門檻即停，含交錯 | done SC5 | 真（§7 UK1:319；§7.1 UK5:333） | 實（_duplicate_hit per-sig count；test_sc5 連續/交錯 A,B,C,A 各準時殺） | **PASS** |
| R12 (L18) | 滑動視窗 W≥交錯元數 N；保守 max_tools 或 8+ | done SC5 | 真（§7.1 UK5:333） | 實（L3Config.__post_init__ 強制 window≥interleaving；default 8；正向交錯偵測有測）；**W<N 拒絕守衛無專測**——見 OF-2 | **PASS**（OF-2） |
| R13 (L19) | L3 預算 ladder 可配置、真 stop 閘輸入，非寫死抄廠商數 | done SC6 | 真（§6:288-309；§7 UK2:321） | 實（max_tokens/max_usd 皆 config，None 預設；test_sc6/test_sc1 budget 咬）；soft-tier ladder 已 defer(G-04)——見 OF-3 | **PASS**（OF-3） |
| R14 (L20) | 多閘同咬事後優先序 budget>dup>max_iterations；max_iter 留 pre-flight 兜底 | done SC6 | 真（§7 UK2:321 逐字） | 實（l3_after_record 檢查序 budget→dup→max；test_sc6 三閘全咬 budget 勝 exit20 + pre-flight 兜底 + dup 單獨） | **PASS** |
| R15 (L21) | L4 確定性證據(exit/lint/type)硬斷；LLM judge 僅警告；畢業/merge 人 admit | done SC8 | 真（§1 L4:83-94；§6:290） | 實（l4_after_record 確定性硬斷/proxy warning-only；test_sc8 四 case 含硬斷優先/warning 留痕不斷） | **PASS** |
| R16 (L22) | L4 G-E 零共享上下文/異質 Validator/80-20 隱蔽測試 | **cut DC-5** | 真（§1 L4:87-93；§6:290；NOTE §5#4 D1 半反證已透明載明） | n-a（可編碼半面＝SC8 承載） | **PASS**（見 DC-5 裁定） |
| R17 (L23) | 控制流歸 L0/L3/L4 確定性碼；LLM 只在 L1 路由+L0 工具選擇出結構化選擇 | done SC2 | 真（§6:282 逐字） | 實（迴圈控制全 Python，executor 注入＝唯一 LLM 縫；test_sc2 純度斷言無 LLM 控制符號） | **PASS** |
| R18 (L24) | context 水位等數值閾值保持可配置；無單一 cluster 數被當定案（證據矛盾） | done SC6(config) + **cut DC-6** | 真（§4:233-236；§6:287-309） | 實（config 半面：L3Config 全閾值可配置無寫死定常數）；ctx-water＝DC-6（見裁定） | **PASS**（見 DC-6 裁定） |
| R19 (L25) | DC L1 網關不自建，外採 LiteLLM/Bifrost 延後 | **cut DC-1** | 真（§2:146-148；§6:280 明示外採） | n-a | **PASS** |
| R20 (L26) | DC L6 沙盒不自建，外採 E2B/gVisor/Tetragon 延後 | **cut DC-2** | 真（§2:163-166；§6:280 明示外採） | n-a | **PASS** |
| R21 (L27) | DC L5 併發鎖不自建，grite/Switchman 延後（現無並發 writer） | **cut DC-3** | 真（§2:155-156；§2:175 G 裁決；§6:280；§7.1 UK6:335） | n-a | **PASS**（最強支撐） |
| R22 (L28) | DC L7 fold-in/系統迴圈不自建，復用 antigravity fold-in（人 admit） | **cut DC-4** | 真（§1 L7:118-123；§6:280 明示復用） | n-a | **PASS** |

## Designed-cut 嚴審（DC-5 / DC-6 為被裁架構原則，理由須嚴格）

**DC-5（G-E 零共享上下文）＝真裁剪，成立。**
MVP 無多代理 generator/evaluator runtime（L1/L5 均已 DC，executor＝注入式 callable）→ runtime 內無「兩代理零共享上下文」可編碼的對象。可編碼半面（評審用確定性證據硬斷、LLM judge 僅警告不自動 admit）**已由 SC8 真實現且四 case 測到**。不可編碼半面（異質 LLM 廠商 Validator、80/20 隱蔽測試）在無 LLM 執行層的 MVP 無承載面，屬使用流程紀律（本小迴圈自身 codex driver × Opus judge 即實踐）。理由誠實——甚至主動援引 §5 #4 D1 半反證（Factory validators 實讀 trajectory，「零共享」是本 MVP 比業界更嚴的設計選擇非已證慣例），答案卡格內 Opus 核註亦已透明標示。**非遮羞布。**

**DC-6（context 水位閾值）＝真裁剪，成立。**
context 水位是 compaction 觸發參數，量測前提＝存在可量的 LLM context 窗；本 MVP 無 LLM 執行層（executor 注入）→ 無 context 消耗可量 → 無可寫的水位參數。可配置原則半面已由 L3Config（budget/iterations/dup 全可配置、零寫死定常數）在 SC6 體現。§4 脆弱點二本身即判「四報告四數字矛盾、不可寫死、須真模型迭代校準」——**寫死任一數字才是錯**，延後到 L1 接入後校準是 SYNTHESIS 明示的正解（§6:287）。理由與 SSOT 同向。**非遮羞布。**

其餘四 cut（DC-1/2/3/4）：§6:280 逐條明示「外採/復用」而非自建，DC-3 更疊 §2:175 G 併發鎖裁決（現架構無並發 writer、無聊替代 flock/lockfile 語意唯一相符）與 §7.1 UK6（單機多進程單 write 零撕裂、最小三角無需檔案鎖）雙重加持。全部成立。

## MISS 清單
**（空）— 零 MISS。**

## Open findings（整體 PASS，仍列供編排者裁量；編排者可據此裁 FAIL）
- **OF-1（R9 / 極輕微）**：cell 具名三限 max_iterations/maxMessages/maxAttempts，impl 有 max_iterations（L3Config）+ maxAttempts（loop._resolve_max_attempts），**無獨立 maxMessages 旋鈕**。但 `_apply_record_state` 每筆 record（含重試 record）皆 `iterations += 1`，故 max_iterations 實質已兼任 message 計數＝maxMessages 折入 max_iterations，非缺功能。cell 核心（可配置、可校準、非證定常數）真成立。近乎無實害。
- **OF-2（R12 / 輕微）**：W≥N 由 `L3Config.__post_init__` fail-fast 守衛（window<interleaving 拋 ValueError），**但無專測構造非法 config 斷言該 raise**；UK5 的 W<N 漏殺失效邊界亦無回歸測。正向交錯偵測（W≥N）有測。守衛可讀碼驗（gates.py:26-27），核心行為成立。建議補一條 `pytest.raises(ValueError)` 守衛測 + 一條 W<N 漏殺對照測。
- **OF-3（R13 / 輕微）**：預算實作為單一硬門檻（≥max_tokens/max_usd 即斷），SYNTHESIS §6:288 的 75/90/100 多層 soft/hard ladder 中的 soft-warn 層未建（已由 §7.1 DEFER-TO-M **G-04 明示 defer**、§7 註 soft_warn/degrade「只留痕不改控制流」）。cell 核心（可配置、真 stop 閘輸入、非寫死廠商數）成立；soft-tier 屬已登記延後項，非本格漏做。

## 最終
**設計分 PASS（零 MISS）。**
22/22 格錨全真、16 done 格覆蓋全實、6 cut 格理由全成立（含 DC-5/DC-6 兩被裁架構原則嚴審通過）。3 條 open finding 皆輕微、均不掏空對應格核心行為。

## 帳尾
本 verdict 是**給人的證據，非放行令**。設計分綠 ≠ 畢業；impl 分（verify.sh LIVE exit 0）與 LAND-DECISION 人 admit 兩門另計。編排者可依上列 open finding 逕裁 FAIL，本判官不代行放行。
