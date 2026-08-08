#!/usr/bin/env bash
set -euo pipefail

test_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
renderer="$test_dir/../../scripts/package_markdown_email.py"
html_checker="$test_dir/../../scripts/check_decision_html.py"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cp -R "$test_dir/fixtures/good" "$tmp_dir/case"
python3 "$renderer" "$tmp_dir/case/config.json"

html="$tmp_dir/case/output/test-bundle.html"
archive="$tmp_dir/case/output/test-bundle.zip"
email="$tmp_dir/case/output/test-bundle.eml"
manifest="$tmp_dir/case/output/test-bundle.MANIFEST.sha256"

python3 "$html_checker" "$html"
python3 - "$archive" "$email" "$manifest" <<'PY'
import re
from email import policy
from email.parser import BytesParser
from pathlib import Path
import sys
import zipfile

archive_path, email_path, manifest_path = map(Path, sys.argv[1:])
with zipfile.ZipFile(archive_path) as bundle:
    names = set(bundle.namelist())
required = {
    "test-bundle.html",
    "bundle-config.json",
    "sources/01-a.md",
    "sources/02-b.md",
    "sources/03-c.md",
    "sources/04-d.md",
    # extras：文件叫人執行的工具必須隨包附上，否則讀者能讀到主張卻無法重新推導。
    "tools/tool.py",
    "code-graph/graph.json",
    "code-graph/graph.verification.json",
    "MANIFEST.sha256",
}
assert required <= names, sorted(required - names)
message = BytesParser(policy=policy.default).parsebytes(email_path.read_bytes())
types = [part.get_content_type() for part in message.walk()]
assert "text/plain" in types
assert types.count("text/html") >= 2
assert "application/zip" in types
assert "test-bundle.html" in manifest_path.read_text(encoding="utf-8")
assert "Date" in message and "Message-ID" in message, "missing Date/Message-ID"
assert message["Date"].startswith("Thu, 06 Aug 2026"), message["Date"]
rendered = Path(sys.argv[3]).parent.joinpath("test-bundle.html").read_text(encoding="utf-8")
assert "<code>&lt;T&gt;</code>" in rendered
assert "<code>A | B</code>" in rendered
assert "&amp;lt;T&amp;gt;" not in rendered
assert rendered.count('<figure class="diagram"') == 4, "every source must yield a diagram"
assert 'id="atlas"' in rendered and "圖錄" in rendered
assert 'id="fig01-01"' in rendered and 'href="#fig01-01"' in rendered
assert "function fitFigure" in rendered

# ── 原生 Code Graph：config → 可操作分頁 → graph/report 自動入包 ─────────
assert 'data-view="view-codegraph"' in rendered
assert 'id="view-codegraph"' in rendered
assert 'id="ctg-data" type="application/json"' in rendered
assert "Fixture Code Review Graph" in rendered
assert "Critical only" in rendered and "Directory &amp; symbol tree" in rendered
assert "src/client.py" in rendered, "source anchor must be reviewable in-page"
report_path = manifest_path.parent / "test-bundle.graph-verification.json"
report = __import__("json").loads(report_path.read_text(encoding="utf-8"))
assert report["ok"] is True, report
assert report["counts"] == {
    "critical_edges": 3,
    "edges": 3,
    "evidence": 2,
    "invariants": 1,
    "nodes": 4,
}, report

# ── 分頁：九份文件不能串成一條長捲軸 ────────────────────────────────────
assert 'id="view-docs"' in rendered and 'class="tab"' in rendered
assert rendered.count('class="docpick"') == 4, "每份文件都要有挑選鈕"
assert 'article class="document" id="doc-01" hidden' in rendered, "文件預設收起"

# ── 遍歷：符號索引 ＋ 上一步／下一步 ＋ 章節索引 ────────────────────────
assert 'id="symbol-index"' in rendered and "function filterSymbols" in rendered
assert 'id="backbtn"' in rendered and 'id="fwdbtn"' in rendered
assert "function goForward" in rendered and "function goBack" in rendered
assert 'aside class="toc"' in rendered and "IntersectionObserver" in rendered
# 懸浮元件必須以分頁列底緣為基準，否則捲到頂端會壓在標題上
assert "--floattop" in rendered and "function syncFloat" in rendered
# 已在畫面內只標示不跳；隱藏面板的元素 rect 全是 0，必須先確認有版面
assert "const laidOut=" in rendered, "in-view 判斷必須先檢查元素真的有版面"
assert "function clearMark" in rendered, "highlight 要能被點別處清除"

no_js = re.sub(r"<script.*?</script>", "", rendered, flags=re.S)
ids = re.findall(r'id="(sym-[A-Za-z][A-Za-z0-9-]*)"', no_js)
assert len(ids) == len(set(ids)), f"重複錨點 id：{[i for i in set(ids) if ids.count(i) > 1]}"
links = set(re.findall(r'href="#(sym-[A-Za-z][A-Za-z0-9-]*)"', no_js))
assert not (links - set(ids)), f"懸空連結：{sorted(links - set(ids))}"

# ── 跳轉要落在原始來源，不是另一個索引 ──────────────────────────────────
# c.md 用摘要表列出 Commit 1；d.md 用標題真正定義它。錨點必須在 d.md（doc-04）。
pos = rendered.index('id="sym-Commit-1"')
owner = re.findall(r'id="doc-(\d+)"', rendered[:pos])[-1]
assert owner == "04", f"Commit 1 應落在原始定義 doc-04，實得 doc-{owner}"
# 範圍標題（`Commit 1〜2`）不得被當成定義
seg = rendered[pos:pos + 400]
assert "〜" not in seg.split("</h")[0], "錨點落在範圍標題上"
PY

# Graph validation is a public CLI boundary: dangling endpoints and evidence-less
# critical edges must fail before a distributable is written.
bad_out="$(python3 "$renderer" "$tmp_dir/case/bad-config.json" 2>&1 || true)"
if ! grep -q "node evidence_ids must be an array" <<<"$bad_out"; then
  echo "malformed evidence_ids did not produce a diagnostic validation error: $bad_out" >&2
  exit 1
fi
if ! grep -q "edge source/target missing" <<<"$bad_out"; then
  echo "dangling graph edge was not rejected: $bad_out" >&2
  exit 1
fi
if ! grep -q "critical edge has no evidence" <<<"$bad_out"; then
  echo "evidence-less critical edge was not rejected: $bad_out" >&2
  exit 1
fi
if [ -e "$tmp_dir/case/bad-output/bad-graph-bundle.html" ]; then
  echo "rejected graph must not leave partial output behind" >&2
  exit 1
fi

if python3 "$renderer" "$test_dir/fixtures/hollow/config.json"; then
  echo "hollow fixture unexpectedly passed" >&2
  exit 1
fi

# Byte-reproducibility: a rebuild from unchanged sources must produce identical
# bytes, otherwise the manifest cannot tell "projection tracked the Markdown" from
# "renderer emitted noise". Covers the snapshot-derived Date and MIME boundaries.
before="$(cd "$tmp_dir/case/output" && shasum -a 256 test-bundle.* | sort)"
python3 "$renderer" "$tmp_dir/case/config.json" >/dev/null
after="$(cd "$tmp_dir/case/output" && shasum -a 256 test-bundle.* | sort)"
if [ "$before" != "$after" ]; then
  echo "rebuild from unchanged sources was not byte-identical" >&2
  diff <(echo "$before") <(echo "$after") >&2 || true
  exit 1
fi

# Content change must move the hashes, otherwise the receipt proves nothing.
printf '\n\n新增一行讓內容改變。\n' >>"$tmp_dir/case/a.md"
python3 "$renderer" "$tmp_dir/case/config.json" >/dev/null
changed="$(cd "$tmp_dir/case/output" && shasum -a 256 test-bundle.* | sort)"
if [ "$after" = "$changed" ]; then
  echo "source change did not move the output hashes" >&2
  exit 1
fi

# Isolating negative control for the diagram rule: a well-formed bundle whose only
# defect is a source document without a data-flow diagram must be rejected.
no_diagram_out="$(python3 "$renderer" "$test_dir/fixtures/no-diagram/config.json" 2>&1 || true)"
if ! grep -q "at least one data-flow diagram" <<<"$no_diagram_out"; then
  echo "diagram-less source was not rejected: $no_diagram_out" >&2
  exit 1
fi
if [ -e "$test_dir/fixtures/no-diagram/output/no-diagram.html" ]; then
  echo "rejected bundle must not leave partial output behind" >&2
  exit 1
fi
