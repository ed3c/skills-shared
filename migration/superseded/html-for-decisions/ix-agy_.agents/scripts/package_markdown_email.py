#!/usr/bin/env python3
"""Render Markdown SSOTs into self-contained HTML, ZIP, and email-ready EML."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path
from typing import Any

from check_redaction import scan as redaction_scan

# Box-drawing, arrow, and gate glyphs used by the plan documents' ASCII diagrams.
# A fenced block carrying enough of these is a diagram, not a shell transcript.
DIAGRAM_MARKS = "│─┼┌┐└┘├┤┬┴▼▲►◄→←↑↓◇★⚠✓✗═╪╬╫"
# A block tagged with a programming language is code even when its comments carry
# arrows; diagrams are written as ```text or with no tag at all.
CODE_LANGS = frozenset(
    {
        "bash", "sh", "shell", "zsh", "console",
        "swift", "js", "javascript", "ts", "typescript", "json", "jsonc",
        "python", "py", "sql", "go", "kotlin", "java", "objc", "c", "cpp",
        "yaml", "yml", "toml", "xml", "html", "css", "diff", "mermaid",
    }
)


# An identifier a document family uses to name a fact, a rule, or a decision.
# Deliberately permissive in shape but filtered against the collected definitions,
# so `UTF-8` and `RFC-822` never become links just because they look like IDs.
# 兩種形狀：代號（NEG-101、INV-OOBE-011）與步驟（Commit 11）。
# 步驟也要能點——一份計畫最常被交叉引用的就是「第幾步」，
# 而讀者在別節看到「Commit 11」時最想知道的正是它到底要做什麼。
SYMBOL = re.compile(r"\b(?:[A-Z]{1,6}-)+\d{1,4}\b|\bCommit\s+\d{1,3}\b")


def symbol_id(name: str) -> str:
    """Anchor-safe id for a symbol（`Commit 11` 含空白，不能直接當 id）。"""
    return re.sub(r"\s+", "-", name.strip())


@dataclass(frozen=True)
class Symbol:
    """Where an identifier is defined, so every mention can point at it."""

    name: str
    doc_index: int
    doc_label: str
    gloss: str
    rank: int = 0


# 定義的「份量」。一個代號可能在好幾處出現在定義位置，但只有一處是原始來源：
#   標題   一整節在講它 —— 這是來源
#   條列   一條完整敘述 —— 帳本的主要形式，也是來源
#   表格列 只是摘要或索引 —— 指到這裡等於把讀者送到目錄而不是內文
# 索引跳轉的目的就是「找到原始來源」，所以份量高的一律勝出，與文件順序無關。
RANK_HEADING, RANK_BULLET, RANK_ROW = 0, 1, 2
# 範圍標題（`Commit 1〜10`、`AK-01 到 AK-05`）講的是一群，不是定義其中任何一個。
RANGE_AFTER = re.compile(r"^\s*[〜～~\-–—到至]")


def symbol_definitions(text: str) -> list[tuple[str, str, int]]:
    """Return (id, gloss, rank) for identifiers this document defines."""
    found: list[tuple[str, str, int]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.count("|") >= 2:
            cells = [c.strip().strip("*` ") for c in stripped.strip("|").split("|")]
            if not cells or is_table_separator(line):
                continue
            names = SYMBOL.findall(cells[0])
            # 只認「首欄幾乎只有代號」的列，避免把敘述句裡的代號當成定義
            if names and len(cells[0]) <= len(names[0]) + 24:
                gloss = cells[1] if len(cells) > 1 else ""
                for name in names:
                    found.append((name, gloss[:120], RANK_ROW))
        elif re.match(r"^[-*+]\s+\*{0,2}[A-Z]{1,6}-", stripped):
            # 條列定義：`- **INV-101 [A]** …` 是不變量帳本的主要寫法，
            # 也是這個文件族最大量的定義來源。同樣只認開頭那一個代號。
            item = re.sub(r"^[-*+]\s+", "", stripped).lstrip("* ")
            names = SYMBOL.findall(item[:40])
            if names and item.startswith(names[0]) and not RANGE_AFTER.match(
                item[len(names[0]):]
            ):
                gloss = re.sub(r"^\S+\s*(?:\[[A-Z]\])?\s*\*{0,2}", "", item)
                found.append((names[0], gloss[:120], RANK_BULLET))
        elif stripped.startswith("#"):
            # 標題只定義「開頭那一個」代號。`### E-8 / INV-101（…）` 定義的是 E-8；
            # INV-101 只是被提及，它真正的定義在別處。把兩者混為一談會讓索引
            # 把讀者送到錯的地方，比沒有索引更糟。
            title = stripped.lstrip("# ").strip()
            names = SYMBOL.findall(title)
            if names and title.startswith(names[0]) and not RANGE_AFTER.match(
                title[len(names[0]):]
            ):
                found.append((names[0], title[:120], RANK_HEADING))
    return found


def collect_symbols(documents: list[SourceDocument]) -> dict[str, Symbol]:
    """Build the family-wide symbol table, preferring the ORIGINAL source.

    Not first-wins: a summary row in an early document must not beat the section
    that actually defines the thing in a later one. Jumping from an index is only
    useful if it lands on the source, not on another index.
    """
    best: dict[str, tuple[int, Symbol]] = {}
    for index, document in enumerate(documents, start=1):
        for name, gloss, rank in symbol_definitions(document.text):
            current = best.get(name)
            if current is None or rank < current[0]:
                best[name] = (rank, Symbol(name, index, document.label, gloss, rank))
    return {name: sym for name, (_, sym) in best.items()}


def linkify_symbols(escaped: str, symbols: dict[str, Symbol]) -> str:
    """Turn every mention of a known identifier into a link to its definition."""
    if not symbols:
        return escaped

    def repl(match: re.Match[str]) -> str:
        name = match.group(0)
        target = symbols.get(name)
        if target is None:
            return name
        return (
            f'<a class="sym" href="#sym-{html.escape(symbol_id(name))}" '
            f'title="{html.escape(target.doc_label)}：{html.escape(target.gloss)}">'
            f"{name}</a>"
        )

    return SYMBOL.sub(repl, escaped)


def is_diagram(lines: list[str], lang: str = "") -> bool:
    """Return true when a fenced block is an ASCII diagram rather than code.

    Dense box drawing always qualifies; a sparser block still counts when it
    spans several lines, which is how the shorter call-site chains are drawn.
    """
    if lang.lower() in CODE_LANGS or len(lines) < 2:
        return False
    text = "\n".join(lines)
    marks = sum(text.count(mark) for mark in DIAGRAM_MARKS)
    return marks >= 8 or (marks >= 4 and len(lines) >= 3)


@dataclass(frozen=True)
class SourceDocument:
    """A source Markdown document declared by bundle config."""

    path: Path
    display_path: str
    label: str
    role: str
    archive_name: str
    text: str
    digest: str


@dataclass(frozen=True)
class Figure:
    """A diagram extracted from a source document, addressable on the page."""

    anchor: str
    number: int
    caption: str
    width: int
    height: int




def sha256_bytes(data: bytes) -> str:
    """Return a lowercase SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def validate_date(value: str) -> str:
    """Validate an externally supplied snapshot date."""
    datetime.strptime(value, "%Y-%m-%d")
    return value


def safe_basename(value: str) -> str:
    """Validate a portable output basename."""
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,79}", value):
        raise ValueError("basename must match [a-z0-9][a-z0-9._-]{0,79}")
    return value


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split a leading YAML frontmatter block without interpreting it."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index]), "\n".join(lines[index + 1 :])
    return None, text


def inline_markup(value: str, symbols: dict[str, Symbol] | None = None) -> str:
    """Render a conservative Markdown inline subset without external requests.

    When a symbol table is supplied, every mention of a known identifier becomes
    a link to where that identifier is defined — including mentions inside code
    spans, which is where most of them live.
    """
    symbols = symbols or {}
    placeholders: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        body = linkify_symbols(html.escape(match.group(1), quote=False), symbols)
        placeholders.append(f"<code>{body}</code>")
        return f"\x00CODE{len(placeholders) - 1}\x00"

    protected = re.sub(r"`([^`]+)`", stash_code, value)
    escaped = html.escape(protected, quote=False)

    def render_link(match: re.Match[str]) -> str:
        label = match.group(1)
        target = html.unescape(match.group(2))
        if target.startswith(("http://", "https://")):
            return f'<span class="external-link">{label} ({html.escape(target)})</span>'
        return f'<span class="local-ref">{label} ({html.escape(target)})</span>'

    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", render_link, escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"_([^_]+)_", r"<em>\1</em>", escaped)
    escaped = linkify_symbols(escaped, symbols)
    for index, code in enumerate(placeholders):
        escaped = escaped.replace(f"\x00CODE{index}\x00", code)
    return escaped


def is_table_separator(line: str) -> bool:
    """Return true for a GitHub-style Markdown table separator row."""
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def table_cells(line: str) -> list[str]:
    """Split a Markdown table row."""
    content = line.strip().strip("|")
    cells: list[str] = []
    current: list[str] = []
    in_code = False
    escaped = False
    for character in content:
        if escaped:
            current.append(character)
            escaped = False
            continue
        if character == "\\":
            current.append(character)
            escaped = True
            continue
        if character == "`":
            in_code = not in_code
            current.append(character)
            continue
        if character == "|" and not in_code:
            cells.append("".join(current).strip())
            current.clear()
            continue
        current.append(character)
    cells.append("".join(current).strip())
    return cells


def render_figure(anchor: str, number: int, caption: str, code_lines: list[str]) -> str:
    """Render a diagram as a captioned, individually scalable figure."""
    width = max((len(line) for line in code_lines), default=0)
    body = html.escape(chr(10).join(code_lines))
    return (
        f'<figure class="diagram" id="{anchor}">'
        f'<figcaption><span class="fig-no">圖 {number}</span>'
        f"<span class=\"fig-cap\">{html.escape(caption)}</span>"
        f'<span class="fig-dim">{width}×{len(code_lines)}</span>'
        '<button type="button" class="fig-fit" onclick="fitFigure(this)">'
        "縮放以完整顯示</button></figcaption>"
        f"<pre><code>{body}</code></pre></figure>"
    )


def markdown_to_html(text: str, fig_prefix: str = "fig", symbols: dict[str, Symbol] | None = None,
    symbols_anchored: set[str] | None = None, doc_index: int = 0) -> tuple[str, list[Figure]]:
    """Render the Markdown subset used by ix-agy plan documents.

    Returns the HTML and every diagram found, so the page can index them.
    """
    frontmatter, body = split_frontmatter(text)
    lines = body.splitlines()
    output: list[str] = []
    figures: list[Figure] = []
    last_heading = ""
    anchored: set[str] = symbols_anchored if symbols_anchored is not None else set()

    def owns(name: str, rank: int) -> bool:
        """True when THIS site is the chosen definition for that symbol.

        Without this, a summary row and the real section would both emit
        `id="sym-X"`; the browser takes whichever comes first in the document,
        which is exactly the wrong one.
        """
        sym = (symbols or {}).get(name)
        if not (sym and sym.doc_index == doc_index and sym.rank == rank):
            return False
        # 同一份文件裡同階的定義可能不只一處（例如兩張表都以 G-04 開頭）。
        # 只認第一處，否則會產生重複 id，而瀏覽器只會跳到其中一個。
        return name not in anchored
    if frontmatter:
        output.append(
            '<details class="frontmatter"><summary>文件 metadata</summary><pre>'
            f"{html.escape(frontmatter)}</pre></details>"
        )

    index = 0
    in_code = False
    code_lang = ""
    code_lines: list[str] = []
    list_kind: str | None = None
    paragraph: list[str] = []

    def close_paragraph() -> None:
        if paragraph:
            output.append(f"<p>{inline_markup(' '.join(paragraph), symbols)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal list_kind
        if list_kind:
            output.append(f"</{list_kind}>")
            list_kind = None

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if in_code:
            if stripped.startswith("```"):
                if is_diagram(code_lines, code_lang):
                    number = len(figures) + 1
                    anchor = f"{fig_prefix}-{number:02d}"
                    caption = last_heading or "資料流圖"
                    output.append(render_figure(anchor, number, caption, code_lines))
                    figures.append(
                        Figure(
                            anchor=anchor,
                            number=number,
                            caption=caption,
                            width=max((len(item) for item in code_lines), default=0),
                            height=len(code_lines),
                        )
                    )
                else:
                    css_class = (
                        f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                    )
                    output.append(
                        f"<pre><code{css_class}>"
                        f"{html.escape(chr(10).join(code_lines))}</code></pre>"
                    )
                in_code = False
                code_lines.clear()
            else:
                code_lines.append(line)
            index += 1
            continue

        if stripped.startswith("```"):
            close_paragraph()
            close_list()
            in_code = True
            code_lang = stripped[3:].strip()
            index += 1
            continue

        if not stripped:
            close_paragraph()
            close_list()
            index += 1
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            close_paragraph()
            close_list()
            level = len(heading.group(1))
            last_heading = heading.group(2)
            # 標題也是定義點（例如「### E-5 / NEG-106」），錨點要掛在這裡，
            # 否則內文指向該代號的連結會全部落空。
            anchor = ""
            if symbols:
                named = [n for n in SYMBOL.findall(last_heading) if n in symbols]
                if named and owns(named[0], RANK_HEADING):
                    anchor = f' id="sym-{html.escape(symbol_id(named[0]))}"'
                    anchored.add(named[0])
            output.append(
                f"<h{level}{anchor}>{inline_markup(heading.group(2), symbols)}</h{level}>"
            )
            index += 1
            continue

        if stripped == "---":
            close_paragraph()
            close_list()
            output.append("<hr>")
            index += 1
            continue

        if (
            stripped.startswith("|")
            and index + 1 < len(lines)
            and is_table_separator(lines[index + 1])
        ):
            close_paragraph()
            close_list()
            headers = table_cells(line)
            output.append("<div class=\"table-wrap\"><table><thead><tr>")
            output.extend(f"<th>{inline_markup(cell, symbols)}</th>" for cell in headers)
            output.append("</tr></thead><tbody>")
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = table_cells(lines[index])
                output.append("<tr>")
                for position, cell in enumerate(cells):
                    anchor = ""
                    if position == 0 and symbols:
                        # 首欄的代號就是定義點；把 id 掛在這裡，
                        # 所有提及處的連結才有地方可去。
                        defined = [
                            name
                            for name in SYMBOL.findall(cell.strip("*` "))
                            if name in symbols
                        ]
                        if (defined and len(cell.strip("*` ")) <= len(defined[0]) + 24
                                and owns(defined[0], RANK_ROW)):
                            anchor = f' id="sym-{html.escape(symbol_id(defined[0]))}"'
                            anchored.add(defined[0])
                    output.append(f"<td{anchor}>{inline_markup(cell, symbols)}</td>")
                output.append("</tr>")
                index += 1
            output.append("</tbody></table></div>")
            continue

        quote = re.match(r"^>\s?(.*)$", stripped)
        if quote:
            close_paragraph()
            close_list()
            quote_lines = [quote.group(1)]
            index += 1
            while index < len(lines):
                next_quote = re.match(r"^>\s?(.*)$", lines[index].strip())
                if not next_quote:
                    break
                quote_lines.append(next_quote.group(1))
                index += 1
            output.append(f"<blockquote>{inline_markup(' '.join(quote_lines), symbols)}</blockquote>")
            continue

        unordered = re.match(r"^[-*+]\s+(.+)$", stripped)
        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if unordered or ordered:
            close_paragraph()
            wanted = "ul" if unordered else "ol"
            if list_kind != wanted:
                close_list()
                list_kind = wanted
                output.append(f"<{wanted}>")
            item = unordered.group(1) if unordered else ordered.group(1)
            # 條列也是定義點：`- **NEG-101 [A]** …` 是不變量帳本的實際寫法。
            anchor = ""
            if symbols:
                head = item[:40]
                named = [n for n in SYMBOL.findall(head) if n in symbols]
                if named and head.lstrip("* ").startswith(named[0]) and owns(named[0], RANK_BULLET):
                    anchor = f' id="sym-{html.escape(symbol_id(named[0]))}"'
                    anchored.add(named[0])
            output.append(f"<li{anchor}>{inline_markup(item, symbols)}</li>")
            index += 1
            continue

        paragraph.append(stripped)
        index += 1

    close_paragraph()
    close_list()
    if in_code:
        output.append(f"<pre><code>{html.escape(chr(10).join(code_lines))}</code></pre>")
    return "\n".join(output), figures


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and validate the bundle configuration."""
    config = json.loads(config_path.read_text(encoding="utf-8"))
    required = ["title", "snapshot", "basename", "output_dir", "documents", "quiz"]
    missing = [key for key in required if key not in config]
    if missing:
        raise ValueError(f"config missing keys: {', '.join(missing)}")
    validate_date(str(config["snapshot"]))
    safe_basename(str(config["basename"]))
    if not config["documents"]:
        raise ValueError("documents must not be empty")
    if not config["quiz"]:
        raise ValueError("quiz must not be empty")
    return config


def load_documents(config_path: Path, config: dict[str, Any]) -> list[SourceDocument]:
    """Load explicitly declared Markdown documents."""
    documents: list[SourceDocument] = []
    used_names: set[str] = set()
    for index, item in enumerate(config["documents"], start=1):
        source_path = (config_path.parent / item["path"]).resolve()
        if not source_path.is_file() or source_path.suffix.lower() != ".md":
            raise ValueError(f"Markdown source missing or invalid: {source_path}")
        archive_name = f"{index:02d}-{source_path.name}"
        if archive_name in used_names:
            raise ValueError(f"duplicate archive name: {archive_name}")
        used_names.add(archive_name)
        data = source_path.read_bytes()
        documents.append(
            SourceDocument(
                path=source_path,
                display_path=str(item["path"]),
                label=str(item.get("label", source_path.name)),
                role=str(item.get("role", "source")),
                archive_name=archive_name,
                text=data.decode("utf-8"),
                digest=sha256_bytes(data),
            )
        )
    return documents


def render_quiz(quiz: list[dict[str, Any]], symbols: dict[str, Symbol] | None = None) -> str:
    """Render the quiz, and the per-question teaching shown after a wrong answer.

    A quiz that only says "wrong" teaches nothing — the reader is left where they
    started. Each question therefore carries the reasoning, the identifiers the
    answer rests on (rendered as links into the documents), and the few lines of
    real code the claim comes from, so being wrong is where the learning happens.
    """
    symbols = symbols or {}
    blocks: list[str] = []
    answers: dict[str, int] = {}
    for index, item in enumerate(quiz, start=1):
        name = f"q{index}"
        answer = int(item["answer"])
        options = list(item["options"])
        if answer < 0 or answer >= len(options):
            raise ValueError(f"quiz answer out of range for {name}")
        answers[name] = answer
        blocks.append(
            f'<fieldset id="qf{index}"><legend>{index}. '
            f'{inline_markup(str(item["question"]), symbols)}</legend>'
        )
        for option_index, option in enumerate(options):
            blocks.append(
                '<label class="quiz-option">'
                f'<input type="radio" name="{name}" value="{option_index}"> '
                f"{inline_markup(str(option), symbols)}</label>"
            )
        # 解答面板：答錯才展開。正確選項、理由、代號連結、實碼各一段。
        parts = [
            f'<div class="qa" id="qa{index}" hidden>',
            f'<p class="qa-ans"><b>正確答案：</b>{inline_markup(str(options[answer]), symbols)}</p>',
        ]
        if item.get("why"):
            parts.append(f'<p class="qa-why">{inline_markup(str(item["why"]), symbols)}</p>')
        refs = item.get("refs") or []
        if refs:
            chips = "".join(
                f'<a class="sym" href="#sym-{html.escape(symbol_id(str(r)))}">{html.escape(str(r))}</a>'
                if str(r) in symbols
                else f'<span class="qa-ref-plain">{html.escape(str(r))}</span>'
                for r in refs
            )
            parts.append(f'<p class="qa-refs"><b>知識引用：</b>{chips}</p>')
        code = item.get("code")
        if code:
            body = html.escape("\n".join(code.get("lines", [])))
            label = html.escape(str(code.get("label", "")))
            parts.append(
                f'<div class="qa-code"><div class="qa-code-h">末端實作 · {label}</div>'
                f"<pre><code>{body}</code></pre></div>"
            )
        parts.append("</div>")
        blocks.append("".join(parts))
        blocks.append("</fieldset>")
    answer_json = json.dumps(answers, ensure_ascii=False, separators=(",", ":"))
    blocks.append(
        '<p><button type="button" onclick="grade()">檢查答案</button> '
        '<button type="button" class="ghost" onclick="resetQuiz()">重做</button></p>'
    )
    blocks.append(
        '<p id="quiz-result" aria-live="polite">全對才代表理解就緒；approve 仍由人。</p>'
    )
    blocks.append(
        "<script>"
        f"const ANSWERS={answer_json};"
        "function grade(){let ok=true,right=0,total=0,first=null;"
        "for(const [name,answer] of Object.entries(ANSWERS)){total++;"
        "const n=name.slice(1);const fs=document.getElementById('qf'+n);"
        "const qa=document.getElementById('qa'+n);"
        "const picked=document.querySelector('input[name=\"'+name+'\"]:checked');"
        "const good=picked&&Number(picked.value)===answer;"
        "fs.classList.toggle('wrong',!good);fs.classList.toggle('right',!!good);"
        "qa.hidden=!!good;"
        "if(good){right++;}else{ok=false;if(!first)first=fs;}}"
        "document.getElementById('quiz-result').textContent=ok?"
        "('全對 '+right+'/'+total+'：理解就緒，但仍需人類裁決。'):"
        "('答對 '+right+'/'+total+'——答錯的題目已展開正確答案、知識引用與末端實碼。');"
        "if(first){first.scrollIntoView({block:'center'});}}"
        "function resetQuiz(){document.querySelectorAll('#quiz input[type=radio]')"
        ".forEach(i=>i.checked=false);"
        "document.querySelectorAll('#quiz fieldset').forEach(f=>"
        "f.classList.remove('wrong','right'));"
        "document.querySelectorAll('#quiz .qa').forEach(d=>d.hidden=true);"
        "document.getElementById('quiz-result').textContent="
        "'全對才代表理解就緒；approve 仍由人。';}"
        "</script>"
    )
    return "\n".join(blocks)


def page_css() -> str:
    """Return inline CSS shared by the full report."""
    return """
:root{--ink:#18212f;--muted:#607086;--paper:#f4f7fb;--card:#fff;--line:#d8e0ea;
--blue:#1d6fa8;--green:#1a7a4a;--amber:#b45309;--red:#b3382c}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);
font:15px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI","Noto Sans CJK TC",sans-serif}
header{padding:42px max(24px,calc((100vw - 1120px)/2));background:#10253f;color:#fff}
header h1{margin:.2em 0;font-size:clamp(28px,4vw,46px)}header p{max-width:900px}
main{max-width:1120px;margin:auto;padding:28px 24px 80px}.notice{border-left:5px solid var(--amber);
background:#fff7ed;padding:14px 18px;margin:18px 0}.grid{display:grid;
grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}.card,.document{background:var(--card);
border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 5px 22px #18304d0d}
.card strong{display:block;color:var(--blue)}nav a{display:block;color:var(--blue);text-decoration:none;
padding:6px 0}.document{margin-top:24px}.doc-meta{color:var(--muted);font-size:13px;overflow-wrap:anywhere}
h1,h2,h3,h4{line-height:1.25;scroll-margin-top:12px}h2{border-bottom:2px solid var(--line);
padding-bottom:8px}code{background:#edf1f6;padding:.12em .35em;border-radius:5px}pre{overflow:auto;
background:#111a28;color:#e9f0fa;padding:16px;border-radius:10px}pre code{background:transparent;padding:0}
.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;margin:14px 0}th,td{border:1px solid
var(--line);padding:8px 10px;vertical-align:top}th{background:#eaf0f7;text-align:left}blockquote{margin:14px 0;
padding:10px 16px;border-left:4px solid var(--blue);background:#eef6fb}.external-link,.local-ref{color:#445c75}
fieldset{border:1px solid var(--line);border-radius:10px;margin:12px 0;padding:14px}.quiz-option{display:block;
padding:5px}button{background:var(--green);color:#fff;border:0;border-radius:8px;padding:10px 16px;
font-weight:700;cursor:pointer}button.ghost{background:transparent;color:var(--blue);
border:1px solid var(--line)}.frontmatter{margin:10px 0;color:var(--muted)}footer{margin-top:32px;color:var(--muted)}
figure.diagram{margin:18px 0;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#111a28}
figure.diagram figcaption{display:flex;gap:10px;align-items:center;flex-wrap:wrap;padding:9px 14px;
background:#0b1420;color:#cfe0f2;font-size:13px;border-bottom:1px solid #1e2c3f}
figure.diagram pre{margin:0;border-radius:0;font:13px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace;
white-space:pre}figure.diagram.fitted pre{overflow:visible}
.fig-no{background:var(--blue);color:#fff;border-radius:999px;padding:2px 9px;font-weight:700;
white-space:nowrap}.fig-cap{flex:1;min-width:140px}.fig-dim{color:#8fa6bf;font-size:12px;
font-variant-numeric:tabular-nums;white-space:nowrap}
.fig-fit{background:#1d6fa8;font-size:12px;padding:5px 10px;font-weight:600}
.legend{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0}.legend-item{background:#eef3f9;
border:1px solid var(--line);border-radius:999px;padding:4px 11px;font-size:13px}
.legend-item b{margin-right:6px;color:var(--red)}
.atlas{columns:3 280px;column-gap:16px;margin-top:12px}
.atlas-group{break-inside:avoid;-webkit-column-break-inside:avoid;margin:0 0 16px}
.atlas-group h3{margin:0 0 8px;font-size:14px;display:flex;justify-content:space-between;gap:8px;
border-bottom:1px solid var(--line);padding-bottom:6px}
/* 懸浮元件一律以「分頁列底緣」為基準，由 --floattop 動態給值。
   在標題區時 --floattop 會是標題＋分頁列的高度，元件不會壓到深色標題；
   捲過標題後分頁列黏在頂端，--floattop 縮成分頁列高度，元件跟著上移。 */
:root{--floattop:300px}
#navpad{position:fixed;top:calc(var(--floattop) + 10px);left:max(12px,calc((100vw - 1180px)/2 - 128px));
z-index:60;display:flex;gap:6px;transition:top .12s ease-out}
#navpad button{background:#12294f;color:#dce9f7;border:1px solid #2b4a72;border-radius:999px;
padding:8px 14px;font-size:13.5px;font-weight:600;cursor:pointer;box-shadow:0 6px 18px #0b1c3140}
#navpad button:hover{background:#1d3d5e}
#navpad button[disabled]{opacity:.35;cursor:default}
@media(max-width:1420px){#navpad{left:12px}}
.bk-n{margin-left:5px;color:#8fb6dd;font-size:11.5px}
aside.toc{position:fixed;top:calc(var(--floattop) + 10px);
right:max(12px,calc((100vw - 1180px)/2 - 210px));width:210px;
max-height:calc(100vh - var(--floattop) - 28px);overflow:auto;z-index:15;background:var(--card);
transition:top .12s ease-out,max-height .12s ease-out;
border:1px solid var(--line);border-radius:12px;padding:12px 10px;box-shadow:0 6px 22px #18304d12}
aside.toc h4{margin:0 0 8px;font-size:12px;color:var(--muted);letter-spacing:.04em}
@media(max-height:520px){aside.toc{display:none}}
aside.toc a{display:block;color:#44607d;text-decoration:none;font-size:12.5px;line-height:1.35;
padding:5px 8px;border-left:2px solid transparent;border-radius:0 6px 6px 0}
aside.toc a:hover{background:#f1f6fb}
aside.toc a.lv3{padding-left:18px;color:#6a8099;font-size:12px}
aside.toc a.here{background:#e8f2fa;border-left-color:var(--blue);color:var(--ink);font-weight:600}
@media(max-width:1500px){aside.toc{display:none}}
fieldset.right{border-color:var(--green);background:#f2fbf6}
fieldset.wrong{border-color:var(--red);background:#fff5f4}
.qa{margin-top:12px;border-top:1px dashed var(--line);padding-top:12px}
.qa-ans{margin:0 0 6px}.qa-why{margin:0 0 8px;color:#33465c}
.qa-refs{margin:0 0 8px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
.qa-ref-plain{color:var(--muted);font-size:13px}
.qa-code{border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-top:8px}
.qa-code-h{background:#eef3f9;color:#44607d;font-size:12px;padding:5px 10px}
.qa-code pre{margin:0;border-radius:0;font-size:12.5px}
nav.tabs{position:sticky;top:0;z-index:20;display:flex;gap:4px;flex-wrap:wrap;
background:#0b1c31;padding:0 max(24px,calc((100vw - 1120px)/2))}
.tab{background:transparent;color:#9fb6cf;border:0;border-bottom:3px solid transparent;
border-radius:0;padding:13px 18px;font-weight:600;font-size:15px}
.tab[aria-selected="true"]{color:#fff;border-bottom-color:#4da3e0;background:#12294510}
.tab-n{background:#1d3d5e;color:#cfe0f2;border-radius:999px;padding:1px 8px;font-size:12px;margin-left:6px}
.docpicks{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:8px;margin-top:10px}
.docpick{display:flex;flex-direction:column;align-items:flex-start;gap:2px;text-align:left;
background:#f7fafd;color:var(--ink);border:1px solid var(--line);border-radius:10px;
padding:10px 12px;font-weight:500;font-size:14px}
.docpick[aria-selected="true"]{background:#e8f2fa;border-color:var(--blue);
box-shadow:inset 3px 0 0 var(--blue)}
.dp-no{color:var(--blue);font-weight:700;font-size:12px}
.dp-role{color:var(--muted);font-size:12px;font-weight:400}
#doc-filter{width:100%;max-width:420px;padding:9px 12px;border:1px solid var(--line);
border-radius:8px;font-size:14px}
a.sym{color:var(--blue);text-decoration:none;border-bottom:1px dotted var(--blue);
white-space:nowrap;cursor:help}a.sym:hover{background:#e8f2fa}
code a.sym{border-bottom-color:#8fa6bf}
.sym-family{margin:10px 0;border:1px solid var(--line);border-radius:10px;padding:10px 14px;background:#fbfdff}
.sym-family summary{cursor:pointer;font-size:14px}
.sym-doc a{color:var(--muted);text-decoration:none;font-size:12px}
#sym-filter{width:100%;max-width:420px;padding:9px 12px;border:1px solid var(--line);
border-radius:8px;font-size:14px}
tr.flash td,td.flash,li.flash,h2.flash,h3.flash,h4.flash{background:#fff3bf;
box-shadow:inset 3px 0 0 #e0a800;transition:background .2s}
.fig-links{display:flex;flex-direction:column;gap:5px}a.fig-link{display:flex;gap:8px;align-items:center;
text-decoration:none;color:var(--ink);background:#f7fafd;border:1px solid var(--line);border-radius:8px;
padding:6px 9px;font-size:13px}a.fig-link:hover{background:#eaf2fa}
@media print{body{background:#fff}.card,.document{box-shadow:none}header{background:#fff;color:#000;padding:20px 0}
.fig-fit,.legend{display:none}figure.diagram pre{white-space:pre-wrap}}
""".strip()


FIGURE_LEGEND = (
    ("◇", "判斷閘門"),
    ("★", "真正阻止覆蓋的關鍵閘門"),
    ("⚠", "覆蓋風險點"),
    ("✓", "保住原 Account Key"),
    ("✗", "缺席／不成立"),
)


SYMBOL_FAMILIES = (
    ("INV", "確認存在的事實（正向不變量）"),
    ("NEG", "確認**不存在**的防護（負向不變量）"),
    ("IMPL", "跨服務的隱含依賴"),
    ("E", "末端實作證據（含實碼區塊）"),
    ("AK", "測試矩陣案例"),
    ("G", "直接邊防護規則"),
    ("S", "sample 專屬防護規則"),
    ("P", "修補提案（未套用）"),
    ("KC", "文件連續性規則"),
)


def render_symbol_index(symbols: dict[str, Symbol], anchored: set[str] | None = None) -> str:
    """Render a clickable index of every identifier the family defines.

    Why a page needs this: the documents cross-reference each other with short
    codes. Without an index the reader must remember which document defines
    which code — exactly the memory dependency the family is trying to remove.
    Every code in the body links here, and every entry here links back to its
    definition, so the reader can traverse in both directions.
    """
    if not symbols:
        return ""

    def family_of(name: str) -> str:
        return name.split("-")[0]

    grouped: dict[str, list[Symbol]] = {}
    for symbol in symbols.values():
        grouped.setdefault(family_of(symbol.name), []).append(symbol)

    def sort_key(symbol: Symbol) -> tuple:
        digits = re.findall(r"\d+", symbol.name)
        return (len(symbol.name.split("-")), [int(d) for d in digits])

    blocks: list[str] = []
    known = {prefix for prefix, _ in SYMBOL_FAMILIES}
    ordered = list(SYMBOL_FAMILIES) + [
        (prefix, "") for prefix in sorted(grouped) if prefix not in known
    ]
    for prefix, description in ordered:
        items = grouped.get(prefix)
        if not items:
            continue
        cells = []
        for s in sorted(items, key=sort_key):
            escaped = html.escape(s.name)
            sid = html.escape(symbol_id(s.name))
            if anchored is not None and s.name not in anchored:
                # 內文沒有定義錨點 → 這一列就是它的落點。
                first = f'<td id="sym-{sid}"><b>{escaped}</b></td>'
            else:
                first = f'<td><a class="sym" href="#sym-{sid}">{escaped}</a></td>'
            cells.append(
                f"<tr>{first}<td>{inline_markup(s.gloss)}</td>"
                f'<td class="sym-doc"><a href="#doc-{s.doc_index:02d}">'
                f"{s.doc_index:02d}. {html.escape(s.doc_label)}</a></td></tr>"
            )
        rows = "".join(cells)
        blocks.append(
            f'<details class="sym-family" open><summary><b>{html.escape(prefix)}-</b>'
            f"　{inline_markup(description)}　<span class=\"fig-dim\">{len(items)} 個</span></summary>"
            '<div class="table-wrap"><table><thead><tr><th>代號</th><th>它是什麼</th>'
            f"<th>定義在</th></tr></thead><tbody>{rows}</tbody></table></div></details>"
        )

    return (
        f'<section class="card" id="symbol-index"><h2>符號索引 — {len(symbols)} 個代號</h2>'
        "<p><strong>你不需要記得任何一個代號。</strong>本文件族用短代號互相引用，"
        "而內文裡每個代號都是連結——點下去會跳到它的定義；這裡的每一列也會連回定義所在的文件。"
        "兩個方向都能走，所以讀到一半遇到不認得的代號，隨時可以查了再回來。</p>"
        "<p class=\"doc-meta\">滑鼠停在內文的代號上會顯示它是什麼，不必離開當下段落。</p>"
        '<p><input type="search" id="sym-filter" placeholder="輸入代號或關鍵字過濾…" '
        'oninput="filterSymbols(this.value)" aria-label="過濾符號索引"></p>'
        f'<div id="sym-groups">{"".join(blocks)}</div></section>'
    )


def render_atlas(figure_index: list[tuple[SourceDocument, int, list[Figure]]]) -> str:
    """Render a diagram atlas so every data-flow view is reachable in one hop."""
    total = sum(len(figures) for _, _, figures in figure_index)
    legend = "".join(
        f'<span class="legend-item"><b>{mark}</b>{html.escape(meaning)}</span>'
        for mark, meaning in FIGURE_LEGEND
    )
    groups: list[str] = []
    for document, index, figures in figure_index:
        links = "".join(
            f'<a class="fig-link" href="#{figure.anchor}">'
            f'<span class="fig-no">圖 {figure.number}</span>'
            f"<span class=\"fig-cap\">{html.escape(figure.caption)}</span>"
            f'<span class="fig-dim">{figure.width}×{figure.height}</span></a>'
            for figure in figures
        )
        groups.append(
            f'<div class="atlas-group"><h3>{index:02d}. {html.escape(document.label)}'
            f'<span class="fig-dim">{len(figures)} 張</span></h3>'
            f'<div class="fig-links">{links}</div></div>'
        )
    return (
        f'<section class="card" id="atlas"><h2>圖錄 — {total} 張資料流圖</h2>'
        "<p>每份來源文件至少一張；寬圖可用各圖右上角的「縮放以完整顯示」一鍵縮到不必橫捲。</p>"
        f'<div class="legend">{legend}</div>'
        '<p><button type="button" onclick="fitAll()">全部縮放以完整顯示</button> '
        '<button type="button" class="ghost" onclick="resetAll()">還原原始大小</button></p>'
        f'<div class="atlas">{"".join(groups)}</div></section>'
    )


def view_script() -> str:
    """Tabs, plus the deep-link handling that keeps every anchor working.

    Tabs are the only way a nine-document bundle stays navigable, but they break
    anchors by default: the target sits in a hidden panel, so the browser scrolls
    nowhere. Every jump therefore goes through `goAnchor`, which reveals the
    containing view AND the containing document before scrolling.
    """
    return (
        "<script>"
        "function switchView(id){pushTrail();showView(id);}"
        "function showView(id,push){document.querySelectorAll('.view').forEach(v=>{"
        "v.hidden=(v.id!==id);});"
        "document.querySelectorAll('.tab').forEach(b=>{"
        "b.setAttribute('aria-selected',String(b.dataset.view===id));});"
        "if(push!==false){history.replaceState(null,'','#'+id);}"
        "window.scrollTo({top:0});buildToc();}"
        "function showDoc(n){document.querySelectorAll('article.document').forEach(a=>{"
        "a.hidden=(a.id!=='doc-'+n);});"
        "document.querySelectorAll('.docpick').forEach(b=>{"
        "b.setAttribute('aria-selected',String(b.dataset.doc===n));});buildToc();}"
        # 右側章節索引：從「目前顯示的那份文件」現場建，並用捲動位置標出讀到哪。
        # 文件是切換式的，所以 TOC 不能靜態產生一份。
        "let TOCSPY=null;"
        "function buildToc(){const aside=document.getElementById('toc');if(!aside)return;"
        "const art=[...document.querySelectorAll('article.document')].find(a=>!a.hidden);"
        "const view=[...document.querySelectorAll('.view')].find(v=>!v.hidden);"
        "const scope=(view&&view.id==='view-docs')?art:view;"
        "if(!scope){aside.hidden=true;return;}"
        "const heads=[...scope.querySelectorAll('h2,h3')];"
        "if(heads.length<3){aside.hidden=true;return;}"
        "aside.hidden=false;"
        "let html='<h4>本頁章節</h4>';"
        "heads.forEach((h,i)=>{if(!h.id)h.id='sec-'+(scope.id||'v')+'-'+i;"
        "const t=h.textContent.trim().slice(0,42);"
        "html+='<a href=\"#'+h.id+'\" class=\"'+(h.tagName==='H3'?'lv3':'')+'\">'+"
        "t.replace(/</g,'&lt;')+'</a>';});"
        "aside.innerHTML=html;"
        "if(TOCSPY)TOCSPY.disconnect();"
        "TOCSPY=new IntersectionObserver(es=>{es.forEach(e=>{if(!e.isIntersecting)return;"
        "aside.querySelectorAll('a').forEach(a=>a.classList.remove('here'));"
        "const link=aside.querySelector('a[href=\"#'+e.target.id+'\"]');"
        "if(link){link.classList.add('here');"
        "const r=link.getBoundingClientRect(),ar=aside.getBoundingClientRect();"
        "if(r.top<ar.top||r.bottom>ar.bottom)link.scrollIntoView({block:'nearest'});}});},"
        "{rootMargin:'-80px 0px -70% 0px'});"
        "heads.forEach(h=>TOCSPY.observe(h));}"
        # 每次跳轉前先記下「現在在哪」：哪個分頁、哪份文件、捲到哪。
        # 沒有這個堆疊，讀者點了代號去查定義之後就回不到原本讀到的那一行，
        # 而「查了再回來」正是這個索引存在的理由。
        "const TRAIL=[],AHEAD=[];"
        "function here(){const v=[...document.querySelectorAll('.view')]"
        ".find(x=>!x.hidden);const d=[...document.querySelectorAll('article.document')]"
        ".find(x=>!x.hidden);"
        "return{view:v?v.id:'view-overview',doc:d?d.id.slice(4):'01',y:window.scrollY};}"
        "function restore(p){showView(p.view,false);showDoc(p.doc);"
        "requestAnimationFrame(()=>window.scrollTo({top:p.y}));}"
        # 新的跳轉會清掉「下一步」——就像瀏覽器：往回走之後又轉向，
        # 原本的前路就不再存在，留著只會把人帶到無關的地方。
        "function pushTrail(){TRAIL.push(here());if(TRAIL.length>50)TRAIL.shift();"
        "AHEAD.length=0;renderNav();}"
        "function renderNav(){const pad=document.getElementById('navpad');if(!pad)return;"
        "const b=document.getElementById('backbtn'),f=document.getElementById('fwdbtn');"
        "pad.hidden=(TRAIL.length===0&&AHEAD.length===0);"
        "b.disabled=TRAIL.length===0;f.disabled=AHEAD.length===0;"
        "b.querySelector('.bk-n').textContent=TRAIL.length>1?String(TRAIL.length):'';"
        "f.querySelector('.fw-n').textContent=AHEAD.length>1?String(AHEAD.length):'';}"
        "function goBack(){const p=TRAIL.pop();if(!p)return;"
        "AHEAD.push(here());renderNav();restore(p);}"
        "function goForward(){const p=AHEAD.pop();if(!p)return;"
        "TRAIL.push(here());renderNav();restore(p);}"
        # 懸浮元件的基準線：分頁列底緣。捲動與改變視窗大小時都要重算，
        # 否則捲到頂端時按鈕與章節索引會壓在深色標題上。
        "function syncFloat(){const t=document.querySelector('nav.tabs');if(!t)return;"
        "const b=Math.max(0,t.getBoundingClientRect().bottom);"
        "document.documentElement.style.setProperty('--floattop',b+'px');}"
        # highlight 不設定時器：留著直到讀者點別處。
        # 索引跳轉的目的是找到來源，而找到之後多半要讀幾秒——
        # 1.6 秒就自己消失會逼人重點一次。
        "function clearMark(){document.querySelectorAll('.flash')"
        ".forEach(n=>n.classList.remove('flash'));}"
        "function mark(el){clearMark();(el.closest('tr')||el).classList.add('flash');}"
        "function goAnchor(id,remember){const el=document.getElementById(id);"
        "if(!el)return false;"
        # 已經站在原始來源上就不要跳：只標示。跳到自己身上會白白吃掉一格返回歷史，
        # 而讀者按返回時會發現「回到原地」——那是壞掉的體驗。
        # 注意：隱藏面板裡的元素 rect 全是 0，會讓「在畫面內」誤判成 true。
        # 必須先確認它真的有版面（offsetParent／非零高度），再看位置。
        "const laidOut=!!(el.offsetParent||el.getClientRects().length);"
        "const r=el.getBoundingClientRect();"
        "const tabsBottom=(document.querySelector('nav.tabs')||{getBoundingClientRect:"
        "()=>({bottom:0})}).getBoundingClientRect().bottom;"
        "const inView=laidOut&&r.height>0&&r.top>=tabsBottom"
        "&&r.bottom<=window.innerHeight;"
        "if(inView){mark(el);return true;}"
        "if(remember!==false)pushTrail();"
        "const art=el.closest('article.document');"
        "if(art){showView('view-docs',false);showDoc(art.id.slice(4));}"
        "else{const v=el.closest('.view');if(v){showView(v.id,false);}}"
        "requestAnimationFrame(()=>{el.scrollIntoView({block:'center'});mark(el);});"
        "return true;}"
        "document.addEventListener('click',e=>{const a=e.target.closest('a[href^=\"#\"]');"
        "if(!a){clearMark();return;}"
        "const id=a.getAttribute('href').slice(1);if(!id)return;"
        # 連結就在自己的定義處（索引列的自我連結）→ 原地標示即可。
        "const el=document.getElementById(id);"
        "if(el&&(el===a||el.contains(a))){e.preventDefault();mark(el);return;}"
        "if(el&&goAnchor(id)){e.preventDefault();"
        "history.replaceState(null,'','#'+id);}});"
        "window.addEventListener('hashchange',()=>{const id=location.hash.slice(1);"
        "if(!id)return;if(id.startsWith('view-')){showView(id,false);}else{goAnchor(id);}});"
        "window.addEventListener('load',()=>{showDoc('01');renderNav();syncFloat();"
        "const id=location.hash.slice(1);"
        "if(id&&id.startsWith('view-')){showView(id,false);}"
        "else if(id&&document.getElementById(id)){goAnchor(id,false);}"
        "else{showView('view-overview',false);}});"
        "window.addEventListener('scroll',syncFloat,{passive:true});"
        "window.addEventListener('resize',syncFloat);"
        "document.addEventListener('keydown',e=>{"
        "if(e.altKey&&e.key==='ArrowLeft'){e.preventDefault();goBack();}"
        "if(e.altKey&&e.key==='ArrowRight'){e.preventDefault();goForward();}});"
        "</script>"
    )


def figure_script() -> str:
    """Return the inline script that fits wide ASCII diagrams to their column."""
    return (
        "<script>"
        "function fitOne(fig){const pre=fig.querySelector('pre');"
        "if(!fig.dataset.baseSize){fig.dataset.baseSize="
        "String(parseFloat(getComputedStyle(pre).fontSize));}"
        "const base=parseFloat(fig.dataset.baseSize);"
        "pre.style.fontSize=base+'px';"
        "const over=pre.scrollWidth/pre.clientWidth;"
        "if(over>1.001){pre.style.fontSize=Math.max(6,base/over)+'px';}"
        "fig.classList.add('fitted');}"
        "function resetOne(fig){const pre=fig.querySelector('pre');"
        "if(fig.dataset.baseSize){pre.style.fontSize=fig.dataset.baseSize+'px';}"
        "fig.classList.remove('fitted');}"
        "function fitFigure(btn){const fig=btn.closest('figure');"
        "if(fig.classList.contains('fitted')){resetOne(fig);btn.textContent='縮放以完整顯示';}"
        "else{fitOne(fig);btn.textContent='還原原始大小';}}"
        "function fitAll(){document.querySelectorAll('figure.diagram').forEach(fig=>{"
        "fitOne(fig);const b=fig.querySelector('.fig-fit');if(b){b.textContent='還原原始大小';}});}"
        "function resetAll(){document.querySelectorAll('figure.diagram').forEach(fig=>{"
        "resetOne(fig);const b=fig.querySelector('.fig-fit');if(b){b.textContent='縮放以完整顯示';}});}"
        "function filterDocs(q){const n=(q||'').trim().toLowerCase();"
        "if(!n){document.querySelectorAll('.docpick').forEach(b=>b.hidden=false);return;}"
        "document.querySelectorAll('.docpick').forEach(b=>{"
        "b.hidden=!b.textContent.toLowerCase().includes(n);});}"
        "function filterSymbols(q){const n=(q||'').trim().toLowerCase();"
        "document.querySelectorAll('#sym-groups tbody tr').forEach(tr=>{"
        "tr.style.display=(!n||tr.textContent.toLowerCase().includes(n))?'':'none';});"
        "document.querySelectorAll('#sym-groups details').forEach(d=>{"
        "const any=[...d.querySelectorAll('tbody tr')].some(tr=>tr.style.display!=='none');"
        "d.style.display=any?'':'none';if(n)d.open=true;});}"
        # 從內文點代號跳到索引時把該列高亮，否則長表格裡找不到落點。
        "window.addEventListener('hashchange',flashTarget);"
        "window.addEventListener('load',flashTarget);"
        "function flashTarget(){const id=location.hash.slice(1);if(!id)return;"
        "const el=document.getElementById(id);if(!el)return;mark(el);}"
        "</script>"
    )


def render_full_html(config: dict[str, Any], documents: list[SourceDocument]) -> str:
    """Render a self-contained full report containing every source document."""
    title = html.escape(str(config["title"]))
    snapshot = html.escape(str(config["snapshot"]))
    decision = html.escape(str(config.get("decision", "未提供裁決摘要")))
    summaries = "".join(f"<li>{html.escape(str(item))}</li>" for item in config.get("summary", []))
    nav = "".join(
        f'<a href="#doc-{index:02d}">{index:02d}. {html.escape(doc.label)}</a>'
        for index, doc in enumerate(documents, start=1)
    )
    docpick = "".join(
        f'<button type="button" class="docpick" role="tab" data-doc="{index:02d}" '
        f'aria-selected="false" onclick="showDoc(\'{index:02d}\')">'
        f'<span class="dp-no">{index:02d}</span>{html.escape(doc.label)}'
        f'<span class="dp-role">{html.escape(doc.role)}</span></button>'
        for index, doc in enumerate(documents, start=1)
    )
    symbols = collect_symbols(documents)
    # 記錄哪些代號在內文真的拿到了錨點。沒拿到的，錨點改掛在索引列上——
    # 保證每個連結都有落點，因為懸空連結比純文字更糟：讀者點了沒反應就不再信任其餘的。
    anchored: set[str] = set()
    document_html: list[str] = []
    figure_index: list[tuple[SourceDocument, int, list[Figure]]] = []
    undiagrammed: list[str] = []
    for index, document in enumerate(documents, start=1):
        rendered, figures = markdown_to_html(
            document.text, fig_prefix=f"fig{index:02d}", symbols=symbols,
            symbols_anchored=anchored, doc_index=index,
        )
        if not figures:
            undiagrammed.append(document.display_path)
        figure_index.append((document, index, figures))
        document_html.append(
            f'<article class="document" id="doc-{index:02d}" hidden>'
            f"<h2>{index:02d}. {html.escape(document.label)}</h2>"
            f'<p class="doc-meta">角色：{html.escape(document.role)} · '
            f"來源：{html.escape(document.display_path)} · SHA-256 {document.digest} · "
            f"資料流圖 {len(figures)} 張</p>"
            f"{rendered}</article>"
        )
    if undiagrammed:
        raise ValueError(
            "every source document must carry at least one data-flow diagram; "
            f"missing in: {', '.join(undiagrammed)}"
        )
    quiz_html = render_quiz(config["quiz"], symbols)
    atlas_html = render_atlas(figure_index)
    # 必須在文件全部渲染完之後才建索引——`anchored` 這時才知道哪些代號
    # 在內文拿到了落點，剩下的才由索引列自己當落點。
    symbol_html = render_symbol_index(symbols, anchored)
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1"><title>{title}</title><style>{page_css()}</style></head>
<body><header><p>OOBE／REOOBE evidence package</p><h1>{title}</h1>
<p>本頁為投影非 SSOT · 快照 {snapshot} · 完整來源與 checksum 隨 ZIP 交付</p></header>
<div id="navpad" hidden>
<button type="button" id="backbtn" onclick="goBack()"
title="回到跳轉前的位置（Alt+←）">← 上一步<span class="bk-n"></span></button>
<button type="button" id="fwdbtn" onclick="goForward()"
title="回到剛才返回前的位置（Alt+→）">下一步 →<span class="fw-n"></span></button>
</div>
<aside class="toc" id="toc" hidden aria-label="本頁章節"></aside>
<nav class="tabs" role="tablist">
<button type="button" class="tab" role="tab" data-view="view-overview" aria-selected="true"
onclick="switchView('view-overview')">概覽</button>
<button type="button" class="tab" role="tab" data-view="view-docs" aria-selected="false"
onclick="switchView('view-docs')">文件 <span class="tab-n">{len(documents)}</span></button>
<button type="button" class="tab" role="tab" data-view="view-atlas" aria-selected="false"
onclick="switchView('view-atlas')">圖錄</button>
<button type="button" class="tab" role="tab" data-view="view-symbols" aria-selected="false"
onclick="switchView('view-symbols')">符號索引</button>
<button type="button" class="tab" role="tab" data-view="view-quiz" aria-selected="false"
onclick="switchView('view-quiz')">理解 quiz <span class="tab-n">{len(config["quiz"])}</span></button>
</nav>
<main>
<div class="view" id="view-overview">
<section class="notice"><strong>已記錄裁決</strong><br>{decision}</section>
<section class="grid"><div class="card"><strong>Release-reachable</strong>checked SHA 正常入口可達</div>
<div class="card"><strong>Deployed</strong>沒有 receipt 一律 UNKNOWN</div>
<div class="card"><strong>Source count</strong>{len(documents)} 份 Markdown</div></section>
<section class="card"><h2>結論摘要</h2><ul>{summaries}</ul></section>
<section class="card"><h2>全部相關文件</h2>
<p class="doc-meta">點任一份會切到「文件」分頁並開啟該份。</p><nav>{nav}</nav></section>
</div>
<div class="view" id="view-docs" hidden>
<section class="card"><h2>選一份文件</h2>
<p class="doc-meta">一次顯示一份，避免九份串成一條長捲軸。內文的代號連結會自動切到對應文件。</p>
<p><input type="search" id="doc-filter" placeholder="過濾文件名稱或角色…"
oninput="filterDocs(this.value)" aria-label="過濾文件"></p>
<div class="docpicks" role="tablist">{docpick}</div></section>
{''.join(document_html)}
</div>
<div class="view" id="view-atlas" hidden>{atlas_html}</div>
<div class="view" id="view-symbols" hidden>{symbol_html}</div>
<div class="view" id="view-quiz" hidden>
<section class="document" id="quiz"><h2>理解 quiz</h2>{quiz_html}</section>
</div>
<footer>重生來源：bundle config + Markdown SSOT。本頁為投影非 SSOT；裁決變更先回寫 Markdown。</footer>
</main>{view_script()}{figure_script()}</body></html>"""


def render_email_html(config: dict[str, Any], documents: list[SourceDocument]) -> str:
    """Render a compact email body that avoids large-message clipping."""
    rows = "".join(
        "<tr>"
        f"<td style='padding:6px;border:1px solid #d8e0ea'>{html.escape(doc.label)}</td>"
        f"<td style='padding:6px;border:1px solid #d8e0ea'>{html.escape(doc.role)}</td>"
        "</tr>"
        for doc in documents
    )
    summaries = "".join(f"<li>{html.escape(str(item))}</li>" for item in config.get("summary", []))
    return f"""<!doctype html><html lang="zh-Hant"><body style="font-family:-apple-system,Segoe UI,sans-serif;
color:#18212f;line-height:1.55"><h1>{html.escape(str(config['title']))}</h1>
<p><strong>快照 {html.escape(str(config['snapshot']))}</strong></p>
<p style="padding:12px;background:#fff7ed;border-left:4px solid #b45309">
{html.escape(str(config.get('decision', '未提供裁決摘要')))}</p><ul>{summaries}</ul>
<p><strong>完整內容：</strong>請開啟隨信 HTML；原始 Markdown 與 checksum 在 ZIP。</p>
<table style="border-collapse:collapse"><tr><th style="padding:6px;border:1px solid #d8e0ea">文件</th>
<th style="padding:6px;border:1px solid #d8e0ea">角色</th></tr>{rows}</table>
<p>本郵件本文是精簡投影非 SSOT；完整依據以附件 Markdown 為準。</p></body></html>"""


def zip_info(name: str, snapshot: str) -> zipfile.ZipInfo:
    """Create deterministic ZIP member metadata from snapshot date."""
    parsed = datetime.strptime(snapshot, "%Y-%m-%d")
    year = max(parsed.year, 1980)
    info = zipfile.ZipInfo(name, (year, parsed.month, parsed.day, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    return info


def load_extras(config_path: Path, config: dict[str, Any]) -> list[tuple[str, bytes]]:
    """Files the documents tell the reader to run, so the archive can carry them.

    Without this the package ships instructions like "execute
    guards/check_account_key_guards.py" to someone who does not have that file —
    the reader can read the claim but cannot re-derive it, which is the whole
    point of anchoring facts to source in the first place.
    """
    extras: list[tuple[str, bytes]] = []
    for item in config.get("extras", []):
        source = (config_path.parent / item["path"]).resolve()
        if not source.is_file():
            raise ValueError(f"extras 指定的檔案不存在：{source}")
        extras.append((str(item.get("as", item["path"])), source.read_bytes()))
    return extras


def build_zip(
    zip_path: Path,
    html_name: str,
    html_bytes: bytes,
    config_path: Path,
    documents: list[SourceDocument],
    snapshot: str,
    extras: list[tuple[str, bytes]] | None = None,
) -> str:
    """Build the portable archive and return its internal checksum manifest."""
    members: list[tuple[str, bytes]] = [(html_name, html_bytes)]
    members.append(("bundle-config.json", config_path.read_bytes()))
    for document in documents:
        members.append((f"sources/{document.archive_name}", document.text.encode("utf-8")))
    members.extend(extras or [])
    manifest = "".join(f"{sha256_bytes(data)}  {name}\n" for name, data in members)
    members.append(("MANIFEST.sha256", manifest.encode("utf-8")))
    with zipfile.ZipFile(zip_path, "w") as archive:
        for name, data in members:
            archive.writestr(zip_info(name, snapshot), data)
    return manifest


def build_eml(
    eml_path: Path,
    config: dict[str, Any],
    email_html: str,
    full_html_name: str,
    full_html: bytes,
    zip_path: Path,
) -> None:
    """Build an importable MIME email with compact body and full attachments."""
    snapshot = str(config["snapshot"])
    basename = safe_basename(str(config["basename"]))
    message = EmailMessage()
    message["Subject"] = str(config.get("subject", config["title"]))
    message["From"] = str(config.get("from", "OOBE Audit <noreply@example.invalid>"))
    message["To"] = str(config.get("to", "Recipient <recipient@example.invalid>"))
    # Derived from the snapshot, never from wall-clock time: a missing Date is
    # rejected by some MTAs, but a `now()` Date would make every rebuild differ
    # and defeat the manifest's job of proving HTML/ZIP tracked the Markdown SSOT.
    stamp = datetime.strptime(snapshot, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    message["Date"] = format_datetime(stamp)
    message["Message-ID"] = f"<{basename}.{snapshot}@bundle.invalid>"
    plain_lines = [str(config["title"]), f"快照 {config['snapshot']}", "", str(config.get("decision", ""))]
    plain_lines.extend(f"- {item}" for item in config.get("summary", []))
    plain_lines.append("\n完整 HTML 與 Markdown ZIP 已附上。")
    message.set_content("\n".join(plain_lines))
    message.add_alternative(email_html, subtype="html")
    message.add_attachment(
        full_html,
        maintype="text",
        subtype="html",
        filename=full_html_name,
    )
    message.add_attachment(
        zip_path.read_bytes(),
        maintype="application",
        subtype="zip",
        filename=zip_path.name,
    )
    # EmailMessage picks random MIME boundaries, which would make every rebuild
    # differ even when nothing changed — the same failure mode the snapshot date
    # avoids. Derive them instead, so the manifest only moves when content moves.
    for part_index, part in enumerate(
        (item for item in message.walk() if item.is_multipart())
    ):
        part.set_boundary(f"=_{basename}_{snapshot}_{part_index}_=")
    eml_path.write_bytes(message.as_bytes())


def generate(config_path: Path) -> list[Path]:
    """Generate HTML, ZIP, EML, and an outer checksum manifest."""
    config_path = config_path.resolve()
    config = load_config(config_path)
    documents = load_documents(config_path, config)
    # Cheap pre-flight before anything is written: the redaction gate exists, so
    # run it on every declared source instead of hoping someone remembers to.
    leaks = redaction_scan([document.path for document in documents] + [config_path])
    if leaks:
        raise ValueError("redaction gate failed: " + "; ".join(leaks))
    output_dir = (config_path.parent / str(config["output_dir"])).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    basename = safe_basename(str(config["basename"]))
    html_path = output_dir / f"{basename}.html"
    zip_path = output_dir / f"{basename}.zip"
    eml_path = output_dir / f"{basename}.eml"
    manifest_path = output_dir / f"{basename}.MANIFEST.sha256"

    full_html = render_full_html(config, documents).encode("utf-8")
    html_path.write_bytes(full_html)
    internal_manifest = build_zip(
        zip_path,
        html_path.name,
        full_html,
        config_path,
        documents,
        str(config["snapshot"]),
        load_extras(config_path, config),
    )
    build_eml(
        eml_path,
        config,
        render_email_html(config, documents),
        html_path.name,
        full_html,
        zip_path,
    )
    outer_entries = [html_path, zip_path, eml_path]
    outer_manifest = "".join(
        f"{sha256_bytes(path.read_bytes())}  {path.name}\n" for path in outer_entries
    )
    manifest_path.write_text(
        "# distributable files\n" + outer_manifest + "\n# ZIP internal manifest\n" + internal_manifest,
        encoding="utf-8",
    )
    return [html_path, zip_path, eml_path, manifest_path]


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    try:
        outputs = generate(args.config)
    except (OSError, UnicodeError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
