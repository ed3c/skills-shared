# Module: 授權 / 專利 合規查證軸（開源可商用零 copyleft + 科技巨頭 permissive 選）

> 屬 [`external-verify`](../SKILL.md)。當研究/DR 推薦一個技術堆疊（tool/lib/**model**）而下游要**商用且不強制開源**時，用官方 primary source（LICENSE 檔/HF model card/repo）查授權與專利鐵錨，不靠記憶。
> **反-husk 錨**：判定寫進 owner 的 LICENSES/NOTICE **真檔**（如 cutplan `prototype/llm-timeline-editing/cutplan/LICENSES.md`，本方法論的 LIVE 實例）。
> **LIVE（cc-20260711）**：cutplan 全 arc 授權合規三輪──移 LGPL(GES) → otiotool(ASWF/Apache-2.0) permissive 閉 G5-B1 → FFmpeg/codec 專利姿態。

## 為何要這一軸（授權/專利 ≠ 功能對）
研究/DR 常推薦「開源可用」的堆疊，但**開源 ≠ 可商用、開源授權 ≠ 免專利、code 授權 ≠ model 授權**。把「開源」當「隨便商用零義務」= 隱形法規炸彈。這一軸把每個推薦元素約分到 primary-source 授權鐵錨。

## 查證程序（疊在 external-verify 6 步上）
1. **code 授權**：拉 repo `LICENSE`/manifest → 分類 **permissive（MIT/BSD/Apache/CC-BY-attribution）vs copyleft（GPL/LGPL/AGPL/MPL/EUPL）**。copyleft＝強制開源條款（LGPL 弱 copyleft：動態連結/subprocess 可商用但仍有義務）。
2. **🔴 model 授權分開查（code≠model）**：ML 模型的 **model card 條款**與其 code 授權**不同**且常 gated/custom。實測（HF primary，2026-07）：`pyannote-audio` **code=MIT**，但 diarization **model**：`speaker-diarization-community-1`=**CC-BY-4.0**（可商用 ✅、非 share-alike ✅、但**署名 attribution + HF gated**、且 CC-BY 是**內容授權非 OSI code license**）；`3.1`=MIT。→ **「開源可商用零 copyleft」對模型必看 model card，別假設同 code 授權**。
3. **專利軸（與授權獨立）**：codec/演算法專利與開源授權是**兩條法律軸**。H.264/H.265/AAC 由 Via LA（原 MPEG-LA）管，開源實作不免專利費（有門檻、**encode 風險 ≫ decode**）。查「產品是否 encode 專利格式」。
4. **附義務**：permissive 也可能有義務（CC-BY 要 attribution、LGPL 要允許替換動態庫+提供改動源）──列進 NOTICE。
5. **判定寫真檔**：結論落 owner 的 `LICENSES.md`/NOTICE（非只對話）。

## 通用結論模式（cutplan 實證）
- **subprocess 外部 binary（如使用者自己的 ffmpeg）≠ bundle/link → 該 binary 的 LGPL/GPL/專利義務對本產品 N/A**；bundle（如 PyPI wheel 內含預編譯 ffmpeg）才需自負。
- **產品類型決定專利暴露**：**剪輯決定/中介文件工具（產 OTIO/FCPXML/EDL/xges，不 encode）→ 編碼專利在下游 render 的 NLE，不在本產品**。
- **需要「真開源 permissive 引擎」時的科技巨頭選＝OpenTimelineIO / ASWF（Linux Foundation：Pixar/Disney/Netflix + 巨頭群，Apache-2.0）**──`otiotool`（隨 opentimelineio 內建、零新依賴）做 headless 真 import 驗證；真 NLE app（DaVinci Resolve 18 免費版）原生 import `.otio`。**誠實但書**：所有開源 *NLE 引擎* 皆 copyleft（GES/MLT=LGPL、Kdenlive/Shotcut/Blender=GPL）、非 copyleft 皆專有──「零 copyleft 又要真編輯器引擎 ingest」不存在。
- **防禦手段（給要 encode 的下游）**：OS-native codec（責任轉 OS/晶片商）· AV1/VP9+Opus 免版稅（AOMedia）· Cisco OpenH264（Cisco 代付 H.264）；測試 fixture 用 FFV1（免專利無損）。
- **Path B 誠實**：授權/專利門檻具體數字會隨時變動→標為方法論陳述（"historically"），非鐵錨 claim；真鐵錨＝拉到的 LICENSE/model-card 逐字 + grep（如「tests/src 零 libx264」）。

## 下游 owner 引用
- gcr [downstream-landing.md](../../gemini-conversation-research/modules/downstream-landing.md) D2 等價物矩陣：每元素加 license 欄（code/model/copyleft/commercial/patent），指針本軸。
- dr-research-loop 的 DR tech-stack 推薦同樣過本軸（指針，不重造）。
