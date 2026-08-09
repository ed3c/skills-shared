#!/usr/bin/env python3
"""First-class Code Graph config, validation, archive, and HTML projection."""

from __future__ import annotations

import html
import json
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any


@dataclass(frozen=True)
class CodeGraphAsset:
    """Validated graph and its deterministic delivery metadata."""

    path: Path
    archive_name: str
    report_path: Path | None
    report_archive_name: str
    label: str
    graph: dict[str, Any]
    source_bytes: bytes
    report: dict[str, Any]
    report_bytes: bytes

    def archive_members(self) -> list[tuple[str, bytes]]:
        return [
            (self.archive_name, self.source_bytes),
            (self.report_archive_name, self.report_bytes),
        ]


def safe_archive_name(value: str) -> str:
    """Reject absolute/traversing ZIP member names before any output is written."""
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts or value.endswith("/"):
        raise ValueError(f"unsafe code_graph archive path: {value}")
    return value


def _ids(items: list[dict[str, Any]], kind: str, errors: list[str]) -> set[str]:
    values = [item.get("id") for item in items]
    missing = [index for index, value in enumerate(values) if not isinstance(value, str) or not value]
    if missing:
        errors.append(f"{kind} missing id at indexes: {missing}")
    known = {value for value in values if isinstance(value, str) and value}
    if len(known) != len(values) - len(missing):
        duplicates = sorted({value for value in known if values.count(value) > 1})
        errors.append(f"duplicate {kind} ids: {duplicates}")
    return known


def _string_list(
    item: dict[str, Any], key: str, owner: str, errors: list[str]
) -> list[str]:
    """Read a schema string array without letting malformed JSON raise TypeError."""
    value = item.get(key, [])
    if not isinstance(value, list) or any(not isinstance(entry, str) for entry in value):
        errors.append(f"{owner} {key} must be an array of strings")
        return []
    return value


def validate_code_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Validate the stable v1 node/edge/evidence seam, not producer internals."""
    errors: list[str] = []
    if not isinstance(graph, dict):
        raise ValueError("code graph root must be a JSON object")
    if not isinstance(graph.get("schema_version"), str):
        errors.append("schema_version must be a string")
    if not isinstance(graph.get("title"), str) or not graph.get("title"):
        errors.append("title must be a non-empty string")

    typed_lists: dict[str, list[dict[str, Any]]] = {}
    for key in ("nodes", "edges", "evidence"):
        value = graph.get(key)
        if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
            errors.append(f"{key} must be an array of objects")
            typed_lists[key] = []
        else:
            typed_lists[key] = value
    nodes = typed_lists["nodes"]
    edges = typed_lists["edges"]
    evidence = typed_lists["evidence"]
    invariants = graph.get("invariants", [])
    if not isinstance(invariants, list) or any(not isinstance(item, dict) for item in invariants):
        errors.append("invariants must be an array of objects when present")
        invariants = []

    node_ids = _ids(nodes, "node", errors)
    nodes_by_id = {node.get("id"): node for node in nodes if node.get("id")}
    _ids(edges, "edge", errors)
    evidence_ids = _ids(evidence, "evidence", errors)
    _ids(invariants, "invariant", errors)
    if not nodes:
        errors.append("nodes must not be empty")

    node_evidence: dict[str, list[str]] = {}
    for node in nodes:
        node_id = node.get("id", "<missing>")
        if not isinstance(node.get("label"), str) or not node.get("label"):
            errors.append(f"node label missing: {node_id}")
        referenced = _string_list(node, "evidence_ids", "node", errors)
        if isinstance(node_id, str):
            node_evidence[node_id] = referenced
        _string_list(node, "reach", "node", errors)
        missing = sorted(set(referenced) - evidence_ids)
        if missing:
            errors.append(f"node evidence missing: {node_id} -> {missing}")
        location = node.get("location")
        if location is not None:
            if not isinstance(location, dict):
                errors.append(f"node location must be object or null: {node_id}")
            else:
                required = {"repo", "sha", "path", "start_line", "end_line"}
                absent = sorted(required - set(location))
                if absent:
                    errors.append(f"source location incomplete: {node_id} -> {absent}")

    edge_reaches: list[list[str]] = []
    for edge in edges:
        edge_id = edge.get("id", "<missing>")
        source = edge.get("source")
        target = edge.get("target")
        if source not in node_ids or target not in node_ids:
            errors.append(f"edge source/target missing: {edge_id} -> {source} / {target}")
        referenced = _string_list(edge, "evidence_ids", "edge", errors)
        edge_reach = _string_list(edge, "reach", "edge", errors)
        target_node = nodes_by_id.get(target, {})
        structural_invariant_edge = (
            edge.get("kind") == "AFFECTS_INVARIANT"
            and target_node.get("kind") == "business_invariant"
            and bool(node_evidence.get(str(source)))
        )
        if edge.get("critical") and not referenced and not structural_invariant_edge:
            errors.append(f"critical edge has no evidence: {edge_id}")
        missing = sorted(set(referenced) - evidence_ids)
        if missing:
            errors.append(f"edge evidence missing: {edge_id} -> {missing}")
        edge_reaches.append(edge_reach)

    reach_counts: dict[str, int] = {}
    for edge_reach in edge_reaches:
        for reach in edge_reach:
            key = str(reach)
            reach_counts[key] = reach_counts.get(key, 0) + 1
    sessions_present = "agent_sessions" in graph
    synthetic = bool((graph.get("scope") or {}).get("synthetic"))
    if not sessions_present:
        agent_scope = "UNKNOWN"
    elif synthetic:
        agent_scope = "SYNTHETIC_ONLY"
    else:
        agent_scope = "OBSERVED"
    deployment = str((graph.get("deployment") or {}).get("status", "UNKNOWN"))
    return {
        "ok": not errors,
        "schema_version": graph.get("schema_version"),
        "counts": {
            "nodes": len(nodes),
            "edges": len(edges),
            "critical_edges": sum(bool(edge.get("critical")) for edge in edges),
            "evidence": len(evidence),
            "invariants": len(invariants),
        },
        "reach_edge_counts": dict(sorted(reach_counts.items())),
        "agent_scope": agent_scope,
        "deployment": deployment,
        "errors": errors,
    }


def load_code_graph(config_path: Path, config: dict[str, Any]) -> CodeGraphAsset | None:
    """Load the optional native `code_graph` config and fail closed on defects."""
    item = config.get("code_graph")
    if item is None:
        return None
    if not isinstance(item, dict) or not item.get("path"):
        raise ValueError("code_graph must be an object containing path")
    graph_path = (config_path.parent / str(item["path"])).resolve()
    if not graph_path.is_file() or graph_path.suffix.lower() != ".json":
        raise ValueError(f"Code Graph source missing or invalid: {graph_path}")
    source_bytes = graph_path.read_bytes()
    graph = json.loads(source_bytes.decode("utf-8"))
    report = validate_code_graph(graph)
    if not report["ok"]:
        raise ValueError("code graph validation failed: " + "; ".join(report["errors"]))
    report_bytes = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    archive_name = safe_archive_name(
        str(item.get("as", f"code-graph/{graph_path.name}"))
    )
    report_archive_name = safe_archive_name(
        str(
            item.get(
                "verification_as",
                f"code-graph/{graph_path.stem}.verification.json",
            )
        )
    )
    if archive_name == report_archive_name:
        raise ValueError("code_graph source and verification archive paths collide")
    report_path = None
    if item.get("verification_report"):
        report_path = (config_path.parent / str(item["verification_report"])).resolve()
    return CodeGraphAsset(
        path=graph_path,
        archive_name=archive_name,
        report_path=report_path,
        report_archive_name=report_archive_name,
        label=str(item.get("label", "Code Graph")),
        graph=graph,
        source_bytes=source_bytes,
        report=report,
        report_bytes=report_bytes,
    )


def code_graph_css() -> str:
    """Namespaced, responsive styles for the optional graph decision surface."""
    return r"""
#view-codegraph{max-width:none;padding:22px 0 48px}.ctg-active main{max-width:1680px}
.ctg-status{display:grid;grid-template-columns:repeat(auto-fit,minmax(245px,1fr));gap:9px;margin:12px 0}
.ctg-card{background:#fff;border:1px solid #d8e0ea;border-radius:13px;padding:14px;box-shadow:0 3px 12px #10253f10;min-width:0}
.ctg-card h3{margin:0 0 6px;font-size:16px}.ctg-card p{margin:0;color:#445c75;font-size:13px;overflow-wrap:anywhere}
.ctg-card.warning{border-top:4px solid #b3382c}.ctg-card.info{border-top:4px solid #1d6fa8}.ctg-card.decision{border-top:4px solid #5f3dc4}
.ctg-controls{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:12px 0;padding:11px;background:#edf3f9;border:1px solid #d8e0ea;border-radius:12px}
.ctg-controls input,.ctg-controls select{border:1px solid #b9c8d8;border-radius:8px;padding:9px 11px;background:#fff;min-width:min(230px,100%);max-width:100%}
.ctg-controls button{border:1px solid #8fa6bf;border-radius:8px;background:#fff;color:#18304d;padding:8px 12px;font-weight:700;cursor:pointer}
.ctg-controls button.active{background:#18304d;color:#fff}.ctg-controls button:focus-visible,.ctg-tree button:focus-visible,.ctg-close:focus-visible{outline:3px solid #4da3e0;outline-offset:2px}.ctg-legend{font-size:12px;color:#607086;flex-basis:100%}
.ctg-workspace{display:grid;grid-template-columns:minmax(220px,280px) minmax(0,1fr);gap:10px;align-items:stretch;min-width:0}
.ctg-panel{background:#fff;border:1px solid #d8e0ea;border-radius:11px;min-width:0;overflow:hidden}
.ctg-panel-head{background:#eaf2fa;border-bottom:1px solid #d8e0ea;padding:10px 12px;font-weight:800;color:#18304d;display:flex;gap:8px;justify-content:space-between;align-items:center;flex-wrap:wrap}
.ctg-panel-body{padding:11px;max-height:min(72vh,820px);overflow:auto;overscroll-behavior:contain}.ctg-tree details{margin:5px 0}.ctg-tree summary{cursor:pointer}
.ctg-tree summary,.ctg-tree button{max-width:100%;overflow-wrap:anywhere;word-break:break-word}
.ctg-tree button{border:0;background:transparent;color:#1d6fa8;text-align:left;padding:4px 0;cursor:pointer;font:inherit}
#ctg-wrap{height:min(72vh,820px);min-height:560px;overflow:auto;overscroll-behavior:contain;background:linear-gradient(#fff,#fbfdff);max-width:100%}#ctg-svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;display:block}
.ctg-node{cursor:pointer}.ctg-node rect{fill:#fff;stroke:#9fb6cf;stroke-width:1.5;rx:9}.ctg-node.critical rect{stroke:#b45309;stroke-width:2.5}
.ctg-node.gap rect{stroke:#b3382c;stroke-width:2.8;fill:#fff5f4}.ctg-node.selected rect{stroke:#1d6fa8;stroke-width:4}
.ctg-node.agent-dim{opacity:.28}.ctg-node.agent-hit rect{stroke:#5f3dc4;stroke-width:4}
.ctg-node text{pointer-events:none}.ctg-node-label{font-weight:800;font-size:12px;fill:#18212f}.ctg-node-kind{font-size:9px;fill:#607086}
.ctg-edge{fill:none;stroke:#b45309;stroke-width:1.8;stroke-dasharray:7 5;cursor:pointer}.ctg-edge.sandbox{stroke:#1d6fa8;stroke-width:2.5;stroke-dasharray:none}.ctg-edge.prod{stroke:#1a7a4a;stroke-width:4;stroke-dasharray:none}.ctg-edge.gap{stroke:#b3382c;stroke-width:3;stroke-dasharray:4 4}.ctg-edge.selected{stroke:#0b1c31;stroke-width:5}
.ctg-edge-label{font-size:8px;fill:#607086;cursor:pointer}.ctg-pill{display:inline-block;border-radius:999px;padding:2px 7px;margin:1px 3px 1px 0;background:#eaf0f7;color:#33465c;font-size:10px;font-weight:800}.ctg-pill.static{background:#fff7ed;color:#8a4307}.ctg-pill.sandbox{background:#e8f2fa;color:#155b8b}.ctg-pill.prod{background:#f2fbf6;color:#11643b}.ctg-pill.unknown,.ctg-pill.refuted{background:#fff5f4;color:#8c2c23}.ctg-pill.settled{background:#f2fbf6;color:#11643b}
#ctg-review-dialog{width:min(1120px,calc(100vw - 32px));max-width:none;max-height:calc(100dvh - 32px);padding:0;border:1px solid #b9c8d8;border-radius:16px;background:#f4f7fb;color:#18212f;box-shadow:0 28px 90px #07142580;overflow:hidden}
#ctg-review-dialog::backdrop{background:#071425b8;backdrop-filter:blur(2px)}.ctg-dialog-open{overflow:hidden}
.ctg-review-shell{display:grid;grid-template-rows:auto auto minmax(0,1fr);max-height:calc(100dvh - 34px)}
.ctg-review-head{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:18px 22px;background:#10253f;color:#fff;border-bottom:1px solid #29445f}
.ctg-review-head h2{margin:0;border:0;padding:0;font-size:clamp(20px,3vw,30px)}.ctg-review-head p{margin:4px 0 0;color:#bdd0e2;font-size:13px}.ctg-close{flex:0 0 auto;background:#fff;color:#18304d;border:0;border-radius:999px;padding:8px 12px;font-size:14px}
.ctg-review-path{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 22px;background:#e8f0f8;border-bottom:1px solid #c8d7e6;color:#18304d}.ctg-review-path[hidden]{display:none}.ctg-review-path p{margin:0;font-size:13px;font-weight:800}.ctg-review-path div{display:flex;gap:7px;flex:0 0 auto}.ctg-review-path button{border:1px solid #8fa6bf;border-radius:8px;background:#fff;color:#18304d;padding:7px 10px;font-weight:800;cursor:pointer}
.ctg-review-body{overflow:auto;overscroll-behavior:contain;padding:20px 22px 28px}.ctg-review-grid{display:grid;grid-template-columns:minmax(0,1.15fr) minmax(300px,.85fr);gap:14px;align-items:start}
.ctg-review-section{background:#fff;border:1px solid #d8e0ea;border-radius:12px;padding:14px;min-width:0;margin-bottom:12px}.ctg-review-section h3{margin:0 0 9px;font-size:15px}.ctg-review-section p{margin:6px 0}.ctg-review-section ul{margin:6px 0;padding-left:20px}
.ctg-review-section pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0b1420;color:#eaf2fa;padding:13px;border-radius:8px;font-size:12px;line-height:1.55;max-height:46vh;overflow:auto}.ctg-evidence{border-left:3px solid #8fa6bf;padding:8px 9px;margin:8px 0;background:#f7fafd;font-size:12px}.ctg-source{overflow-wrap:anywhere;font-size:11px;color:#445c75}.ctg-related{display:flex;gap:6px;flex-wrap:wrap}.ctg-related button{background:#eef6fb;color:#155b8b;border:1px solid #bdd4e6;padding:6px 9px;font-size:12px}.ctg-timeline{border-left:3px solid #9fb6cf;padding-left:12px;margin:8px 0}.ctg-empty{color:#607086;font-style:italic}.ctg-kicker{text-transform:uppercase;letter-spacing:.08em;font-size:11px;color:#607086;font-weight:800}
@media(max-width:1050px){.ctg-workspace{grid-template-columns:1fr}.ctg-tree.ctg-panel-body{max-height:240px}#ctg-wrap{height:66vh;min-height:520px}.ctg-review-grid{grid-template-columns:1fr}}
@media(max-width:640px){#view-codegraph{padding:14px 0 32px}.ctg-controls input,.ctg-controls select{min-width:100%;width:100%}.ctg-status{grid-template-columns:1fr}#ctg-wrap{height:62vh;min-height:460px}#ctg-review-dialog{width:100%;height:100dvh;max-height:none;margin:0;border:0;border-radius:0}.ctg-review-shell{height:100dvh;max-height:none}.ctg-review-head{padding:14px 16px}.ctg-review-path{padding:9px 14px;align-items:flex-start;flex-direction:column}.ctg-review-body{padding:14px 14px 24px}}

/* Private Code Truth Graph v1.1 reference grammar.  Reach is encoded by line
   shape/weight; invariant state is encoded by colour.  Navigation stays grey. */
.ctg-controls{display:flex;gap:8px;margin:10px 0;padding:0;background:transparent;border:0;border-radius:0}
.ctg-controls input{min-width:260px;padding:9px 11px;border:1px solid var(--line);border-radius:8px}
.ctg-controls select,.ctg-controls button{padding:8px 11px;border:1px solid #b8c7d5;border-radius:8px;background:#fff;color:#245579;font-weight:750}
.ctg-controls button.active{background:#173f63;color:#fff}.ctg-legend{flex-basis:auto;align-self:center;color:var(--muted)}
.ctg-workspace{display:grid;grid-template-columns:250px minmax(500px,1fr) 340px;gap:12px;align-items:start;min-width:0}
.ctg-panel{background:#fff;border:1px solid var(--line);border-radius:13px;min-height:640px;overflow:hidden}
.ctg-panel-head{padding:11px 13px;background:#edf3f8;border-bottom:1px solid var(--line);color:var(--ink);font-weight:800}
.ctg-panel-body{padding:12px;max-height:76vh;overflow:auto}.ctg-tree{color:var(--muted)}
#ctg-wrap{height:auto;min-height:640px;max-height:76vh;overflow:auto;background:#fbfdff}
.ctg-node rect{fill:#fff;stroke:#95a8ba;stroke-width:1.5;rx:10}.ctg-node.critical rect{stroke:#b45309;stroke-width:3}
.ctg-node.blind rect{fill:#eef1f5;stroke:#a0a8b2}.ctg-node.selected rect{stroke:#176da5;stroke-width:4}
.ctg-node.reach-2{filter:drop-shadow(0 0 3px #176da570)}.ctg-node.reach-3{filter:drop-shadow(0 0 5px #18794e80)}
.ctg-node-label{font-size:12px;font-weight:750;fill:#1f2d3d}.ctg-node-kind{font-size:9px;fill:#627086;font-weight:850}
.ctg-edge{fill:none;stroke:#7d8ca0;stroke-width:2;cursor:pointer}.ctg-edge.static{stroke-dasharray:8 6}.ctg-edge.sandbox{stroke-width:3;stroke-dasharray:none}.ctg-edge.prod{stroke-width:5;stroke-dasharray:none}
.ctg-edge.unknown{stroke:#ad5c00}.ctg-edge.survived{stroke:#18794e}.ctg-edge.refuted,.ctg-edge.gap{stroke:#b1362e}
.ctg-edge.selected{stroke:#152033;stroke-width:6}.ctg-edge-label{font-size:9px;fill:#627086;font-weight:750}
#ctg-inline-detail{font-size:12px}.ctg-inline-title{margin:0 0 4px;font-size:16px}.ctg-inline-subtitle{margin:0 0 10px;color:var(--muted)}
#ctg-inline-detail .ctg-review-grid{display:block}#ctg-inline-detail .ctg-review-section{padding:10px;margin-bottom:8px;border-radius:8px;box-shadow:none}
#ctg-inline-detail .ctg-review-section pre{max-height:230px;font-size:10px}#ctg-inline-detail .ctg-open-review{width:100%;margin:0 0 10px;background:#173f63;color:#fff}
.ctg-history-panel{margin-top:12px;background:#fff;border:1px solid var(--line);border-radius:13px;overflow:hidden}.ctg-history-controls{display:flex;gap:12px;align-items:center;padding:11px 13px;background:#edf3f8;border-bottom:1px solid var(--line)}
.ctg-history-controls label{font-weight:800}.ctg-history-controls input{flex:1}.ctg-history-list{display:flex;gap:8px;overflow:auto;padding:12px}.ctg-history-event{flex:0 0 260px;border:1px solid #e8edf2;border-left:4px solid #ad5c00;border-radius:8px;padding:9px;background:#fff}.ctg-history-event.refuted{border-left-color:#b1362e}.ctg-history-event.settled{border-left-color:#18794e}.ctg-history-event b{display:block}.ctg-history-event p{margin:4px 0;color:var(--muted)}
@media(max-width:1100px){.ctg-workspace{grid-template-columns:1fr}.ctg-panel{min-height:0}.ctg-tree.ctg-panel-body{max-height:240px}#ctg-wrap{min-height:560px;max-height:70vh}#ctg-inline-detail{max-height:none}}
@media(max-width:650px){.ctg-controls input,.ctg-controls select,.ctg-controls button{min-width:100%;width:100%}.ctg-history-controls{align-items:stretch;flex-direction:column}#ctg-wrap{min-height:460px}}
""".strip()


def render_code_graph_section(asset: CodeGraphAsset, hidden: bool = True) -> str:
    """Render the static shell; graph content is an escaped inline JSON payload."""
    graph = asset.graph
    title = html.escape(str(graph.get("title", asset.label)))
    scope = graph.get("scope") or {}
    boundary = html.escape(str(scope.get("business_boundary", "未提供 business boundary")))
    return f"""
<div class="view" id="view-codegraph"{' hidden' if hidden else ''}>
  <section aria-labelledby="ctg-title">
    <h2 id="ctg-title">{title}</h2>
    <p>{boundary}</p>
    <p class="doc-meta">每個 node／edge 可回到 source location 與 evidence。這是 review index；Markdown 仍是裁決 SSOT。</p>
    <div class="ctg-status" id="ctg-status"></div>
    <div class="ctg-controls">
      <input id="ctg-search" type="search" placeholder="symbol / payload / endpoint / file…" aria-label="搜尋 Code Graph">
      <button type="button" id="ctg-agent-overlay">Agent overlay</button>
      <button type="button" id="ctg-critical" class="active">Critical slice only</button>
      <select id="ctg-lane" aria-label="過濾 graph lane"><option value="">全部 lanes</option></select>
      <select id="ctg-comparison" aria-label="過濾雙向機制差距"><option value="">全部比較狀態</option></select>
      <select id="ctg-agent" aria-label="Agent scope overlay"><option value="">全部 agent sessions</option></select>
      <select id="ctg-path" aria-label="選擇 guided review path" hidden><option value="">Guided review path</option></select>
      <button type="button" id="ctg-path-prev" hidden>← 上一節點</button>
      <button type="button" id="ctg-path-next" hidden>下一節點 →</button>
      <button type="button" id="ctg-reset">重設檢視</button>
      <span class="ctg-legend">線型：虛線 STATIC · 實線 SANDBOX · 粗實線 PROD；顏色：橙 UNKNOWN · 綠 survived · 紅 refuted</span>
    </div>
    <div class="ctg-workspace">
      <div class="ctg-panel"><div class="ctg-panel-head">Directory &amp; symbol tree <span class="small">navigation only</span></div><div class="ctg-panel-body ctg-tree" id="ctg-tree"></div></div>
      <div class="ctg-panel"><div class="ctg-panel-head"><span>Reach-aware graph</span><span id="ctg-count"></span></div><div id="ctg-wrap"><svg id="ctg-svg" aria-label="Code Graph"></svg></div></div>
      <div class="ctg-panel"><div class="ctg-panel-head">Node / edge evidence</div><div class="ctg-panel-body" id="ctg-inline-detail"><p class="ctg-empty">Select a node or edge. Navigation visibility is not verification.</p></div></div>
    </div>
    <section class="ctg-history-panel" aria-labelledby="ctg-history-title">
      <div class="ctg-history-controls"><label id="ctg-history-title" for="ctg-time">Refutation history</label><input id="ctg-time" type="range" min="0" value="0" step="1"><span id="ctg-time-label">CURRENT</span></div>
      <div class="ctg-history-list" id="ctg-history"></div>
    </section>
  </section>
  <dialog id="ctg-review-dialog" aria-labelledby="ctg-review-title">
    <div class="ctg-review-shell">
      <div class="ctg-review-head"><div><p class="ctg-kicker">Code Review</p><h2 id="ctg-review-title">Node／edge review</h2><p id="ctg-review-subtitle">觀察、推論、抵達與反證分開呈現</p></div><button class="ctg-close" type="button" id="ctg-review-close" aria-label="關閉 Code Review 視窗">關閉 ✕</button></div>
      <div class="ctg-review-path" id="ctg-review-path" hidden><p id="ctg-review-path-status">Guided review path</p><div><button type="button" id="ctg-review-path-prev">← 上一節點</button><button type="button" id="ctg-review-path-next">下一節點 →</button></div></div>
      <div class="ctg-review-body" id="ctg-detail"><p>選取節點或邊。</p></div>
    </div>
  </dialog>
</div>
""".strip()


def code_graph_script(asset: CodeGraphAsset) -> str:
    """Return a self-contained generic v1 graph renderer."""
    payload = json.dumps(
        asset.graph, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).replace("</", "<\\/")
    template = r"""<script id="ctg-data" type="application/json">__GRAPH_JSON__</script>
<script>
(()=>{
const G=JSON.parse(document.getElementById('ctg-data').textContent);
const N=Object.fromEntries(G.nodes.map(n=>[n.id,n])),E=Object.fromEntries(G.evidence.map(e=>[e.id,e]));
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const laneOf=n=>String(n.lane??(n.metadata||{}).lane??((n.metadata||{}).visual_stage!==undefined?'Stage '+(n.metadata||{}).visual_stage:n.kind??'Other'));
const reaches=x=>(x||[]).map(r=>`<span class="ctg-pill ${esc(String(r).toLowerCase())}">${esc(r)}</span>`).join('');
const history=Array.isArray(G.invariant_events)?G.invariant_events:[];let timeIndex=history.length;
const reachClass=e=>(e.reach||[]).includes('PROD')?'prod':(e.reach||[]).includes('SANDBOX')?'sandbox':'static';
function edgeStateAt(e){let state=String((e.metadata||{}).invariant_state||e.status||'UNKNOWN');history.slice(0,timeIndex).forEach(event=>{const delta=event.graph_delta||{};if((delta.invalidated_edges||[]).includes(e.id))state='REFUTED';if((delta.added_edges||[]).includes(e.id))state=String(event.next_state||event.state||'SURVIVED')});return state}
const stateClass=e=>{const state=edgeStateAt(e);if(String(e.kind||'').match(/MISSING|VIOLAT|REFUT/i)||/REFUT|FAIL|INVALID/i.test(state))return 'refuted';if(/SETTLED|SURVIV|PASS/i.test(state))return 'survived';return 'unknown'};
const edgeClass=e=>`${reachClass(e)} ${stateClass(e)}`;
function autoLayout(){
 const indeg=Object.fromEntries(G.nodes.map(n=>[n.id,0])),out={};
 G.edges.forEach(e=>{if(e.source in indeg&&e.target in indeg){indeg[e.target]++;(out[e.source]??=[]).push(e.target)}});
 const depth=Object.fromEntries(G.nodes.map(n=>[n.id,0]));let q=Object.keys(indeg).filter(id=>indeg[id]===0).sort();
 while(q.length){const id=q.shift();(out[id]||[]).sort().forEach(t=>{depth[t]=Math.max(depth[t],depth[id]+1);indeg[t]--;if(indeg[t]===0){q.push(t);q.sort()}})}
 const supplied=G.view?.positions||{};if(G.nodes.every(n=>supplied[n.id]))return {positions:supplied,width:G.view.width||2480,height:G.view.height||1540};
 const groups={};G.nodes.slice().sort((a,b)=>a.id.localeCompare(b.id)).forEach(n=>{const stage=Number.isFinite(Number((n.metadata||{}).visual_stage))?Number((n.metadata||{}).visual_stage):depth[n.id];(groups[stage]??=[]).push(n)});
 const positions={};let maxRows=0;Object.entries(groups).forEach(([stage,nodes])=>{maxRows=Math.max(maxRows,nodes.length);nodes.forEach((n,i)=>positions[n.id]={x:40+Number(stage)*225,y:45+i*92})});
 return {positions,width:Math.max(1280,(Math.max(0,...Object.keys(groups).map(Number))+1)*225+260),height:Math.max(720,maxRows*92+120)};
}
const V=autoLayout();let critical=true,query='',lane='',comparison='',agentSession='',pathIndex=-1,currentReviewNodeId='';
const sessions=Array.isArray(G.agent_sessions)?G.agent_sessions:[];
const paths=Array.isArray(G.review_paths)?G.review_paths:[];
const comparisonOf=n=>String((n.metadata||{}).comparison_status||'');
function visibleNodes(){const criticalIds=new Set(G.edges.filter(e=>e.critical).flatMap(e=>[e.source,e.target]));let xs=G.nodes.filter(n=>(!critical||n.critical||criticalIds.has(n.id))&&(!lane||laneOf(n)===lane)&&(!comparison||comparisonOf(n)===comparison));if(query)xs=xs.filter(n=>JSON.stringify(n).toLowerCase().includes(query));return xs}
function agentTouched(){const s=sessions.find(x=>String(x.id||x.session_id)===agentSession);return new Set(s?.touched_node_ids||[])}
function render(){const ns=visibleNodes(),ids=new Set(ns.map(n=>n.id)),es=G.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&(!lane||e.lane===lane||laneOf(N[e.source])===lane));const touched=agentTouched();
 const svg=document.getElementById('ctg-svg');svg.setAttribute('width',V.width);svg.setAttribute('height',V.height);svg.innerHTML='<defs><marker id="ctg-arrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#718196"/></marker></defs>';
 es.forEach(e=>{const a=V.positions[e.source],b=V.positions[e.target];if(!a||!b)return;const x1=a.x+190,y1=a.y+34,x2=b.x,y2=b.y+34,m=(x1+x2)/2;const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',`M${x1},${y1} C${m},${y1} ${m},${y2} ${x2},${y2}`);p.setAttribute('class',`ctg-edge ${edgeClass(e)}`);p.setAttribute('marker-end','url(#ctg-arrow)');p.dataset.id=e.id;p.onclick=()=>showEdge(e);svg.appendChild(p);const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',m);t.setAttribute('y',(y1+y2)/2-5);t.setAttribute('class','ctg-edge-label');t.textContent=e.kind;t.onclick=()=>showEdge(e);svg.appendChild(t)});
 ns.forEach(n=>{const p=V.positions[n.id];if(!p)return;const g=document.createElementNS('http://www.w3.org/2000/svg','g');const agentClass=agentSession?(touched.has(n.id)?'agent-hit':'agent-dim blind'):'';const reachCount=new Set(n.reach||[]).size;g.setAttribute('class',`ctg-node ${n.critical?'critical':''} ${String(n.kind).match(/gap|missing/i)?'gap':''} reach-${reachCount} ${agentClass}`);g.setAttribute('transform',`translate(${p.x},${p.y})`);g.dataset.id=n.id;g.setAttribute('role','button');g.setAttribute('tabindex','0');const r=document.createElementNS('http://www.w3.org/2000/svg','rect');r.setAttribute('width',190);r.setAttribute('height',68);g.appendChild(r);const l=document.createElementNS('http://www.w3.org/2000/svg','text');l.setAttribute('x',9);l.setAttribute('y',23);l.setAttribute('class','ctg-node-label');l.textContent=n.label.length>27?n.label.slice(0,26)+'…':n.label;g.appendChild(l);const k=document.createElementNS('http://www.w3.org/2000/svg','text');k.setAttribute('x',9);k.setAttribute('y',45);k.setAttribute('class','ctg-node-kind');k.textContent=`${laneOf(n)} · ${n.kind} · ${(n.reach||[]).join('/')}`;g.appendChild(k);g.onclick=()=>showNode(n);g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();showNode(n)}};svg.appendChild(g)});document.getElementById('ctg-count').textContent=`${ns.length} nodes · ${es.length} edges`;renderTree(ns)}
function evidence(ids){const body=(ids||[]).map(id=>E[id]).filter(Boolean).map(e=>`<div class="ctg-evidence">${reaches([e.reach])}<b>${esc(e.method)}</b> · ${esc(e.status)}<div>${esc(e.summary)}</div><div class="ctg-source">${esc(e.source)} · ${esc(e.authority)} / ${esc(e.environment_class)}</div>${e.details?`<details><summary>evidence details</summary><pre><code>${esc(typeof e.details==='string'?e.details:JSON.stringify(e.details,null,2))}</code></pre></details>`:''}</div>`).join('');return body||'<p class="ctg-empty">未掛 evidence；不得自行補成已驗證。</p>'}
function snippet(n){const m=n.metadata||{};return m.snippet??m.expression??m.description??m.value??'No snippet'}
const asList=x=>Array.isArray(x)?x:(x?[x]:[]);
function reviewList(title,items){const xs=asList(items);return `<section class="ctg-review-section"><h3>${esc(title)}</h3>${xs.length?`<ul>${xs.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:'<p class="ctg-empty">未提供；保持 UNKNOWN。</p>'}</section>`}
function related(id){const rows=[];G.edges.forEach(e=>{if(e.source===id)rows.push({kind:e.kind,id:e.target,dir:'→'});if(e.target===id)rows.push({kind:e.kind,id:e.source,dir:'←'})});return rows.length?`<div class="ctg-related">${rows.map(r=>`<button type="button" data-node="${esc(r.id)}">${r.dir} ${esc(r.kind)} · ${esc(N[r.id]?.label||r.id)}</button>`).join('')}</div>`:'<p class="ctg-empty">沒有相鄰節點。</p>'}
function timelineFor(n){const inv=n.kind==='business_invariant'?n.id.replace(/^invariant:/,''):((n.metadata||{}).invariant_id||'');const rows=(G.invariant_events||[]).filter(x=>x.invariant_id===inv||x.node_id===n.id);return rows.length?rows.map(x=>`<div class="ctg-timeline">${reaches([x.reach])}<b>${esc(x.at||'')}</b> · ${esc(x.state||'UNKNOWN')}<div>${esc(x.basis||'')}</div>${x.note?`<div class="ctg-source">${esc(x.note)}</div>`:''}</div>`).join(''):'<p class="ctg-empty">沒有此節點的推翻時間線；不可推定從未被推翻。</p>'}
function wireRelated(root){root.querySelectorAll('[data-node]').forEach(b=>b.onclick=()=>showNode(N[b.dataset.node]))}
function openReview(title,subtitle,body){document.getElementById('ctg-review-title').textContent=title;document.getElementById('ctg-review-subtitle').textContent=subtitle;const detail=document.getElementById('ctg-detail');detail.innerHTML=body;wireRelated(detail);syncReviewPath();const d=document.getElementById('ctg-review-dialog');document.body.classList.add('ctg-dialog-open');if(!d.open)d.showModal();document.getElementById('ctg-review-close').focus()}
function showInline(title,subtitle,body){const detail=document.getElementById('ctg-inline-detail');detail.innerHTML=`<h3 class="ctg-inline-title">${esc(title)}</h3><p class="ctg-inline-subtitle">${esc(subtitle)}</p><button type="button" class="ctg-open-review">Open full Code Review</button>${body}`;wireRelated(detail);detail.querySelector('.ctg-open-review').onclick=()=>openReview(title,subtitle,body)}
function closeReview(){const d=document.getElementById('ctg-review-dialog');if(d.open)d.close();document.body.classList.remove('ctg-dialog-open')}
function showNode(n,modal=false){if(!n)return;currentReviewNodeId=n.id;document.querySelectorAll('.ctg-node').forEach(x=>x.classList.toggle('selected',x.dataset.id===n.id));const l=n.location||{},m=n.metadata||{},r=m.review||{},a=m.reach_assessment||{};const source=l.repo?`${esc(l.repo)}@${esc(l.sha)}:${esc(l.path)}:${esc(l.start_line)}-${esc(l.end_line)}`:'virtual／negative node';const counterpart=r.counterpart&&N[r.counterpart]?`<button type="button" data-node="${esc(r.counterpart)}">開啟 counterpart：${esc(N[r.counterpart].label)}</button>`:'';const body=`<div class="ctg-review-grid"><div><section class="ctg-review-section"><span class="ctg-kicker">${esc(comparisonOf(n)||'UNCLASSIFIED')}</span><h3>${esc(r.summary||'尚未提供 structured review summary')}</h3>${reaches(n.reach)}${n.critical?'<span class="ctg-pill">CRITICAL</span>':''}<p><b>Kind:</b> ${esc(n.kind)}<br><b>ID:</b> <code>${esc(n.id)}</code></p><div class="ctg-source">${source}</div>${counterpart}</section><section class="ctg-review-section"><h3>程式碼節錄</h3><pre><code>${esc(snippet(n))}</code></pre><p class="ctg-source">節錄是導航，不是完整原文；裁決以 checked SHA source 與 evidence 為準。</p></section><section class="ctg-review-section"><h3>Evidence by reach</h3>${evidence(n.evidence_ids)}</section></div><div><section class="ctg-review-section"><h3>觀察（source says）</h3><p>${esc(r.observation||'未提供；只可讀取 source location 與 snippet。')}</p></section><section class="ctg-review-section"><h3>推論（review inference）</h3><p>${esc(r.inference||'未提供；不得從可見 source 自動提升成 runtime 結論。')}</p></section>${reviewList('能證明',r.proves)}${reviewList('不能證明',r.does_not_prove)}${reviewList('風險／反證條件',r.risks)}<section class="ctg-review-section"><h3>抵達狀態</h3><p><b>${esc(a.state||'UNKNOWN')}</b> · settled=${a.settled===true?'true':'false'} · independent reaches: ${esc(asList(a.independent_reaches).join(', ')||'UNKNOWN')}</p><p><b>下一個獨立抵達：</b>${esc(a.next_reach||'未指定')}</p></section><section class="ctg-review-section"><h3>Recommendation</h3><p>${esc(r.recommendation||'未提供。')}</p></section><section class="ctg-review-section"><h3>Invariant timeline</h3>${timelineFor(n)}</section><section class="ctg-review-section"><h3>相鄰 Code Graph nodes</h3>${related(n.id)}</section></div></div>`;const subtitle=`${n.kind} · ${comparisonOf(n)||'comparison unclassified'}`;showInline(n.label,subtitle,body);if(modal)openReview(n.label,subtitle,body)}
function showEdge(e,modal=false){currentReviewNodeId='';document.querySelectorAll('.ctg-edge').forEach(x=>x.classList.toggle('selected',x.dataset.id===e.id));const inherited=!e.evidence_ids?.length&&e.kind==='AFFECTS_INVARIANT';const evidenceIds=inherited?(N[e.source]?.evidence_ids||[]):e.evidence_ids;const r=(e.metadata||{}).review||{};const body=`<div class="ctg-review-grid"><div><section class="ctg-review-section"><h3>${esc(e.kind)}</h3>${reaches(e.reach)}${e.critical?'<span class="ctg-pill">CRITICAL EDGE</span>':''}<p><b>From:</b> <button type="button" data-node="${esc(e.source)}">${esc(N[e.source]?.label||e.source)}</button><br><b>To:</b> <button type="button" data-node="${esc(e.target)}">${esc(N[e.target]?.label||e.target)}</button><br><b>ID:</b> <code>${esc(e.id)}</code></p>${inherited?'<p class="ctg-source">Structural invariant edge；evidence inherited from source node.</p>':''}</section><section class="ctg-review-section"><h3>Evidence by reach</h3>${evidence(evidenceIds)}</section></div><div><section class="ctg-review-section"><h3>觀察（source says）</h3><p>${esc(r.observation||`Graph records ${e.source} ${e.kind} ${e.target}.`)}</p></section><section class="ctg-review-section"><h3>推論（review inference）</h3><p>${esc(r.inference||'Edge reach belongs to this relation; endpoint reach must not be inherited.')}</p></section>${reviewList('能證明',r.proves)}${reviewList('不能證明',r.does_not_prove)}${reviewList('風險／反證條件',r.risks)}<section class="ctg-review-section"><h3>Recommendation</h3><p>${esc(r.recommendation||'挑戰只有 STATIC 且指進 critical node 的邊。')}</p></section></div></div>`;const title=e.kind,subtitle=`${N[e.source]?.label||e.source} → ${N[e.target]?.label||e.target}`;showInline(title,subtitle,body);if(modal)openReview(title,subtitle,body)}
function renderTree(ns){const groups={};ns.forEach(n=>{const p=n.location?.path||`[${laneOf(n)} virtual]`;(groups[p]??=[]).push(n)});document.getElementById('ctg-tree').innerHTML=Object.entries(groups).sort().map(([p,xs])=>`<details><summary><b>${esc(p)}</b> <span class="small">${xs.length}</span></summary>${xs.map(n=>`<div><button data-id="${esc(n.id)}">${esc(n.label)}${n.location?':'+n.location.start_line:''}</button></div>`).join('')}</details>`).join('');document.querySelectorAll('#ctg-tree button').forEach(b=>b.onclick=()=>showNode(N[b.dataset.id]))}
function status(){const cards=[];(G.invariants||[]).forEach(i=>cards.push(`<div class="ctg-card ${String(i.current_status||i.settlement?.status).match(/REFUT|FAIL/i)?'warning':'info'}"><h3>${esc(i.id)} · ${esc(i.current_status||i.settlement?.status||'UNKNOWN')}</h3><p>${esc(i.reason||i.statement)}</p></div>`));(G.diagnostics||[]).slice(0,3).forEach(d=>cards.push(`<div class="ctg-card ${d.severity==='warning'?'warning':'info'}"><h3>${esc(d.code||'Diagnostic')}</h3><p>${esc(d.summary)}</p></div>`));(G.decision_queue||[]).forEach(d=>cards.push(`<div class="ctg-card decision"><h3>Decision Queue · ${esc(d.id)} · ${esc(d.status||'OPEN')}</h3><p>${esc(d.question)}<br><b>Owner:</b> ${esc(d.owner||'UNASSIGNED')} · <b>Default:</b> ${esc(d.default||'UNKNOWN')}</p></div>`));const synthetic=!!G.scope?.synthetic,agentState=!('agent_sessions' in G)?'UNKNOWN':synthetic?'SYNTHETIC_ONLY':'OBSERVED';cards.push(`<div class="ctg-card"><h3>Agent scope · ${agentState}</h3><p>${sessions.length} session receipts；未提供不可改寫成 0%。</p></div>`);cards.push(`<div class="ctg-card"><h3>Deployment · ${esc(G.deployment?.status||'UNKNOWN')}</h3><p>沒有 deployment receipt 不得宣稱 Deployed。</p></div>`);document.getElementById('ctg-status').innerHTML=cards.join('')}
function renderHistory(){const slider=document.getElementById('ctg-time'),label=document.getElementById('ctg-time-label'),list=document.getElementById('ctg-history');slider.max=String(history.length);slider.value=String(timeIndex);label.textContent=timeIndex===history.length?'CURRENT':`T${timeIndex}`;const visible=history.slice(0,timeIndex);list.innerHTML=visible.length?visible.map(event=>{const state=String(event.next_state||event.state||'UNKNOWN'),cls=/REFUT|FAIL/i.test(state)?'refuted':/SETTLED/i.test(state)?'settled':'';return `<article class="ctg-history-event ${cls}"><b>${esc(event.at||'')} · ${esc(event.invariant_id||event.node_id||'')}</b><p>${esc(event.prior_state||'UNKNOWN')} → ${esc(state)}</p>${reaches([event.reach])}<p>${esc(event.basis||'')}</p>${event.note?`<p>${esc(event.note)}</p>`:''}</article>`}).join(''):'<p class="ctg-empty">T0：尚未套用任何推翻事件；這不是「從未被推翻」。</p>'}
const lanes=[...new Set(G.nodes.map(laneOf))].sort();document.getElementById('ctg-lane').insertAdjacentHTML('beforeend',lanes.map(x=>`<option>${esc(x)}</option>`).join(''));const comparisons=[...new Set(G.nodes.map(comparisonOf).filter(Boolean))].sort();document.getElementById('ctg-comparison').insertAdjacentHTML('beforeend',comparisons.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join(''));const agentSelect=document.getElementById('ctg-agent');if(!sessions.length)agentSelect.hidden=true;else agentSelect.insertAdjacentHTML('beforeend',sessions.map(s=>{const id=String(s.id||s.session_id);return `<option value="${esc(id)}">${esc(s.agent||id)}</option>`}).join(''));
const pathSelect=document.getElementById('ctg-path'),pathPrev=document.getElementById('ctg-path-prev'),pathNext=document.getElementById('ctg-path-next'),reviewPath=document.getElementById('ctg-review-path'),reviewPathStatus=document.getElementById('ctg-review-path-status'),reviewPathPrev=document.getElementById('ctg-review-path-prev'),reviewPathNext=document.getElementById('ctg-review-path-next');if(paths.length){pathSelect.hidden=false;pathPrev.hidden=false;pathNext.hidden=false;pathSelect.insertAdjacentHTML('beforeend',paths.map(p=>`<option value="${esc(p.id)}">${esc(p.label||p.id)}</option>`).join(''))}function activePath(){return paths.find(p=>String(p.id)===pathSelect.value)}function syncReviewPath(){const p=activePath(),index=p?.node_ids?.indexOf(currentReviewNodeId)??-1;reviewPath.hidden=!p||index<0;if(reviewPath.hidden)return;pathIndex=index;reviewPathStatus.textContent=`${p.label||p.id} · ${index+1}/${p.node_ids.length}`;reviewPathPrev.disabled=p.node_ids.length<2;reviewPathNext.disabled=p.node_ids.length<2}function stepPath(delta){const p=activePath();if(!p?.node_ids?.length)return;pathIndex=(pathIndex+delta+p.node_ids.length)%p.node_ids.length;showNode(N[p.node_ids[pathIndex]],true)}pathSelect.onchange=()=>{pathIndex=-1;if(activePath())stepPath(1)};pathPrev.onclick=()=>stepPath(-1);pathNext.onclick=()=>stepPath(1);reviewPathPrev.onclick=()=>stepPath(-1);reviewPathNext.onclick=()=>stepPath(1);
const agentOverlay=document.getElementById('ctg-agent-overlay');if(!sessions.length)agentOverlay.disabled=true;agentOverlay.onclick=()=>{agentSession=agentSession?'':String(sessions[0]?.id||sessions[0]?.session_id||'');agentSelect.value=agentSession;agentOverlay.classList.toggle('active',!!agentSession);render()};document.getElementById('ctg-time').oninput=e=>{timeIndex=Number(e.target.value);renderHistory();render()};document.getElementById('ctg-search').oninput=e=>{query=e.target.value.trim().toLowerCase();render()};document.getElementById('ctg-lane').onchange=e=>{lane=e.target.value;render()};document.getElementById('ctg-comparison').onchange=e=>{comparison=e.target.value;render()};agentSelect.onchange=e=>{agentSession=e.target.value;agentOverlay.classList.toggle('active',!!agentSession);render()};document.getElementById('ctg-critical').onclick=e=>{critical=!critical;e.currentTarget.classList.toggle('active',critical);render()};document.getElementById('ctg-reset').onclick=()=>{critical=true;query=lane=comparison=agentSession='';timeIndex=history.length;document.getElementById('ctg-search').value='';document.getElementById('ctg-lane').value='';document.getElementById('ctg-comparison').value='';agentSelect.value='';agentOverlay.classList.remove('active');document.getElementById('ctg-critical').classList.add('active');renderHistory();render()};document.getElementById('ctg-review-close').onclick=closeReview;document.getElementById('ctg-review-dialog').onclick=e=>{if(e.target===e.currentTarget)closeReview()};document.getElementById('ctg-review-dialog').addEventListener('close',()=>document.body.classList.remove('ctg-dialog-open'));status();renderHistory();render();
})();
</script>"""
    return template.replace("__GRAPH_JSON__", payload)
