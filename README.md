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

## 開始

```bash
INFRA=~/.agents/skills/shared-skills-infra/scripts/shared_skills.py
python3 $INFRA check     # 已登記的裁決有沒有被違反
python3 $INFRA report    # 同名多份、尚未裁決的決策佇列
bash ~/.agents/skills-shared/skills/shared-skills-infra/tests/verify.sh   # 自測，零網路
```

## 現況與待辦

首批共用＝`github-delivery-loop`（2026-08-07 admit）。五個 repo 普查出 **26 個同名多份、
其中 24 個內容分岔**——那是待人裁的佇列，不是失敗；`report` 隨時重算，本 repo 不凍結掃描結果。

沒有 remote。要跨機器同步或走 PR review，加一個 remote 即可，屆時它自己就能吃
`github-delivery-loop` 的那套 admit → preflight → land。
