# skills-shared — 跨 repo 共用的基礎設施 skills

所有 Claude Code 與 Codex CLI 專案共用的 skill 本體住在這裡，**一個名稱只有一份**。
治理規則、指令與 why 全在 [`skills/shared-skills-infra/SKILL.md`](skills/shared-skills-infra/SKILL.md)；
裁決帳在 [`registry.json`](registry.json)。本檔只講拓撲與怎麼開始。

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

## clone 到任何目錄都能用

版控內容**沒有任何機器路徑**：`registry.json` 只存裁決，路徑全在 gitignored 的
`sites.local.json` 或旗標，canonical 位置由 `__file__` 推導。

```bash
git clone <this-repo> ~/.agents/skills-shared          # 目錄名隨你
python3 ~/.agents/skills-shared/skills/shared-skills-infra/scripts/shared_skills.py \
  install --project ~/proj-a --project ~/proj-b --claude-forwarder proj-b
```

`install` 寫路徑 → 連 user 層與各專案 → 跑 `check`。冪等；換機器或搬 checkout 後重跑即復原。
完整規則、旗標與兩種專案側形態 → [`skills/shared-skills-infra/SKILL.md`](skills/shared-skills-infra/SKILL.md)。

```bash
INFRA=~/.agents/skills/shared-skills-infra/scripts/shared_skills.py
python3 $INFRA check ; python3 $INFRA report
bash ~/.agents/skills-shared/skills/shared-skills-infra/tests/verify.sh   # 自測，零網路
```

## 現況與待辦

共用 17 個（2026-08-07）。五個 repo 普查出 26 個同名多份、其中 24 個內容分岔；
依「核心三repo（bettor-arena／skill-bettor／ts-skill-bettor）hash 勝出者收編」的裁決，
15 個有多數者已收編，antigravity／ix-agy 的變體以 `deferred_in` 原地保留待逐個裁決。
剩 5 個三份各不同、1 個核心只有一份、4 個只在離群 repo——`report` 隨時重算，本 repo 不凍結掃描結果。
