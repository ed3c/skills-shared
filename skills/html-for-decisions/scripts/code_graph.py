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
#view-codegraph{max-width:none;padding:22px 24px 48px}
.ctg-status{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}.ctg-status .ctg-card{flex:1;min-width:220px}
.ctg-card{background:#fff;border:1px solid #d8e0ea;border-radius:13px;padding:14px;box-shadow:0 3px 12px #10253f10}
.ctg-card h3{margin:0 0 6px;font-size:16px}.ctg-card p{margin:0;color:#445c75;font-size:13px}
.ctg-card.warning{border-top:4px solid #b3382c}.ctg-card.info{border-top:4px solid #1d6fa8}
.ctg-controls{display:flex;gap:9px;align-items:center;flex-wrap:wrap;margin:12px 0}
.ctg-controls input,.ctg-controls select{border:1px solid #b9c8d8;border-radius:8px;padding:9px 11px;background:#fff;min-width:220px}
.ctg-controls button{border:1px solid #8fa6bf;border-radius:8px;background:#fff;color:#18304d;padding:8px 12px;font-weight:700;cursor:pointer}
.ctg-controls button.active{background:#18304d;color:#fff}.ctg-legend{font-size:12px;color:#607086}
.ctg-workspace{display:grid;grid-template-columns:245px minmax(720px,1fr) 355px;gap:10px;min-height:720px}
.ctg-panel{background:#fff;border:1px solid #d8e0ea;border-radius:11px;min-width:0;overflow:hidden}
.ctg-panel-head{background:#eaf2fa;border-bottom:1px solid #d8e0ea;padding:10px 12px;font-weight:800;color:#18304d}
.ctg-panel-body{padding:11px;max-height:760px;overflow:auto}.ctg-tree details{margin:5px 0}.ctg-tree summary{cursor:pointer}
.ctg-tree summary,.ctg-tree button{max-width:100%;overflow-wrap:anywhere;word-break:break-word}
.ctg-tree button{border:0;background:transparent;color:#1d6fa8;text-align:left;padding:3px 0;cursor:pointer;font:inherit}
#ctg-wrap{height:760px;overflow:auto;background:linear-gradient(#fff,#fbfdff)}#ctg-svg{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
.ctg-node rect{fill:#fff;stroke:#9fb6cf;stroke-width:1.5;rx:9}.ctg-node.critical rect{stroke:#b45309;stroke-width:2.5}
.ctg-node.gap rect{stroke:#b3382c;stroke-width:2.8;fill:#fff5f4}.ctg-node.selected rect{stroke:#1d6fa8;stroke-width:4}
.ctg-node.agent-dim{opacity:.28}.ctg-node.agent-hit rect{stroke:#5f3dc4;stroke-width:4}
.ctg-node text{pointer-events:none}.ctg-node-label{font-weight:800;font-size:12px;fill:#18212f}.ctg-node-kind{font-size:9px;fill:#607086}
.ctg-edge{fill:none;stroke:#b45309;stroke-width:1.8;stroke-dasharray:7 5;cursor:pointer}.ctg-edge.sandbox{stroke:#1d6fa8;stroke-width:2.5;stroke-dasharray:none}.ctg-edge.prod{stroke:#1a7a4a;stroke-width:4;stroke-dasharray:none}.ctg-edge.gap{stroke:#b3382c;stroke-width:3;stroke-dasharray:4 4}.ctg-edge.selected{stroke:#0b1c31;stroke-width:5}
.ctg-edge-label{font-size:8px;fill:#607086;cursor:pointer}.ctg-pill{display:inline-block;border-radius:999px;padding:2px 7px;margin:1px 3px 1px 0;background:#eaf0f7;color:#33465c;font-size:10px;font-weight:800}.ctg-pill.static{background:#fff7ed;color:#8a4307}.ctg-pill.sandbox{background:#e8f2fa;color:#155b8b}.ctg-pill.prod{background:#f2fbf6;color:#11643b}.ctg-pill.unknown{background:#fff5f4;color:#8c2c23}
.ctg-detail pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0b1420;color:#eaf2fa;padding:11px;border-radius:8px;font-size:11px;line-height:1.5}.ctg-evidence{border-left:3px solid #8fa6bf;padding:7px 8px;margin:7px 0;background:#f7fafd;font-size:12px}.ctg-source{overflow-wrap:anywhere;font-size:11px;color:#445c75}
@media(max-width:900px){#view-codegraph{padding:68px 16px 32px}.ctg-workspace{grid-template-columns:1fr}.ctg-panel-body{max-height:420px}#ctg-wrap{height:600px}.ctg-controls input,.ctg-controls select{min-width:100%;width:100%}}
""".strip()


def render_code_graph_section(asset: CodeGraphAsset) -> str:
    """Render the static shell; graph content is an escaped inline JSON payload."""
    graph = asset.graph
    title = html.escape(str(graph.get("title", asset.label)))
    scope = graph.get("scope") or {}
    boundary = html.escape(str(scope.get("business_boundary", "未提供 business boundary")))
    return f"""
<div class="view" id="view-codegraph" hidden>
  <section aria-labelledby="ctg-title">
    <h2 id="ctg-title">{title}</h2>
    <p>{boundary}</p>
    <p class="doc-meta">每個 node／edge 可回到 source location 與 evidence。這是 review index；Markdown 仍是裁決 SSOT。</p>
    <div class="ctg-status" id="ctg-status"></div>
    <div class="ctg-controls">
      <input id="ctg-search" type="search" placeholder="symbol / payload / endpoint / file…" aria-label="搜尋 Code Graph">
      <select id="ctg-lane" aria-label="過濾 graph lane"><option value="">全部 lanes</option></select>
      <select id="ctg-agent" aria-label="Agent scope overlay"><option value="">全部 agent sessions</option></select>
      <button type="button" id="ctg-critical" class="active">Critical only</button>
      <span class="ctg-legend">虛線 STATIC · 藍線 SANDBOX · 綠粗線 PROD · 紅線 missing guard</span>
    </div>
    <div class="ctg-workspace">
      <div class="ctg-panel"><div class="ctg-panel-head">Directory &amp; symbol tree</div><div class="ctg-panel-body ctg-tree" id="ctg-tree"></div></div>
      <div class="ctg-panel"><div class="ctg-panel-head">Reach-aware graph <span id="ctg-count"></span></div><div id="ctg-wrap"><svg id="ctg-svg" aria-label="Code Graph"></svg></div></div>
      <div class="ctg-panel"><div class="ctg-panel-head">Node／edge source evidence</div><div class="ctg-panel-body ctg-detail" id="ctg-detail"><p>選取節點或邊。</p></div></div>
    </div>
  </section>
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
const edgeClass=e=>String(e.kind||'').match(/MISSING|VIOLAT|REFUT/i)?'gap':(e.reach||[]).includes('PROD')?'prod':(e.reach||[]).includes('SANDBOX')?'sandbox':'static';
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
const V=autoLayout();let critical=true,query='',lane='',agentSession='';
const sessions=Array.isArray(G.agent_sessions)?G.agent_sessions:[];
function visibleNodes(){const criticalIds=new Set(G.edges.filter(e=>e.critical).flatMap(e=>[e.source,e.target]));let xs=G.nodes.filter(n=>(!critical||n.critical||criticalIds.has(n.id))&&(!lane||laneOf(n)===lane));if(query)xs=xs.filter(n=>JSON.stringify(n).toLowerCase().includes(query));return xs}
function agentTouched(){const s=sessions.find(x=>String(x.id||x.session_id)===agentSession);return new Set(s?.touched_node_ids||[])}
function render(){const ns=visibleNodes(),ids=new Set(ns.map(n=>n.id)),es=G.edges.filter(e=>ids.has(e.source)&&ids.has(e.target)&&(!lane||e.lane===lane||laneOf(N[e.source])===lane));const touched=agentTouched();
 const svg=document.getElementById('ctg-svg');svg.setAttribute('width',V.width);svg.setAttribute('height',V.height);svg.innerHTML='<defs><marker id="ctg-arrow" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto"><path d="M0,0 L0,6 L9,3 z" fill="#718196"/></marker></defs>';
 es.forEach(e=>{const a=V.positions[e.source],b=V.positions[e.target];if(!a||!b)return;const x1=a.x+190,y1=a.y+34,x2=b.x,y2=b.y+34,m=(x1+x2)/2;const p=document.createElementNS('http://www.w3.org/2000/svg','path');p.setAttribute('d',`M${x1},${y1} C${m},${y1} ${m},${y2} ${x2},${y2}`);p.setAttribute('class',`ctg-edge ${edgeClass(e)}`);p.setAttribute('marker-end','url(#ctg-arrow)');p.dataset.id=e.id;p.onclick=()=>showEdge(e);svg.appendChild(p);const t=document.createElementNS('http://www.w3.org/2000/svg','text');t.setAttribute('x',m);t.setAttribute('y',(y1+y2)/2-5);t.setAttribute('class','ctg-edge-label');t.textContent=e.kind;t.onclick=()=>showEdge(e);svg.appendChild(t)});
 ns.forEach(n=>{const p=V.positions[n.id];if(!p)return;const g=document.createElementNS('http://www.w3.org/2000/svg','g');const agentClass=agentSession?(touched.has(n.id)?'agent-hit':'agent-dim'):'';g.setAttribute('class',`ctg-node ${n.critical?'critical':''} ${String(n.kind).match(/gap|missing/i)?'gap':''} ${agentClass}`);g.setAttribute('transform',`translate(${p.x},${p.y})`);g.dataset.id=n.id;g.setAttribute('role','button');g.setAttribute('tabindex','0');const r=document.createElementNS('http://www.w3.org/2000/svg','rect');r.setAttribute('width',190);r.setAttribute('height',68);g.appendChild(r);const l=document.createElementNS('http://www.w3.org/2000/svg','text');l.setAttribute('x',9);l.setAttribute('y',23);l.setAttribute('class','ctg-node-label');l.textContent=n.label.length>27?n.label.slice(0,26)+'…':n.label;g.appendChild(l);const k=document.createElementNS('http://www.w3.org/2000/svg','text');k.setAttribute('x',9);k.setAttribute('y',45);k.setAttribute('class','ctg-node-kind');k.textContent=`${laneOf(n)} · ${n.kind} · ${(n.reach||[]).join('/')}`;g.appendChild(k);g.onclick=()=>showNode(n);g.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();showNode(n)}};svg.appendChild(g)});document.getElementById('ctg-count').textContent=`${ns.length} nodes · ${es.length} edges`;renderTree(ns)}
function evidence(ids){return (ids||[]).map(id=>E[id]).filter(Boolean).map(e=>`<div class="ctg-evidence">${reaches([e.reach])}<b>${esc(e.method)}</b> · ${esc(e.status)}<div>${esc(e.summary)}</div><div class="ctg-source">${esc(e.source)} · ${esc(e.authority)} / ${esc(e.environment_class)}</div></div>`).join('')}
function snippet(n){const m=n.metadata||{};return m.snippet??m.expression??m.description??m.value??'No snippet'}
function showNode(n){document.querySelectorAll('.ctg-node').forEach(x=>x.classList.toggle('selected',x.dataset.id===n.id));const l=n.location||{};document.getElementById('ctg-detail').innerHTML=`<h3>${esc(n.label)}</h3>${reaches(n.reach)}${n.critical?'<span class="ctg-pill">CRITICAL</span>':''}<p><b>Kind:</b> ${esc(n.kind)}<br><b>ID:</b> <code>${esc(n.id)}</code></p><div class="ctg-source">${l.repo?`${esc(l.repo)}@${esc(l.sha)}:${esc(l.path)}:${esc(l.start_line)}-${esc(l.end_line)}`:'virtual／negative node'}</div><pre><code>${esc(snippet(n))}</code></pre><h3>Evidence</h3>${evidence(n.evidence_ids)}`}
function showEdge(e){document.querySelectorAll('.ctg-edge').forEach(x=>x.classList.toggle('selected',x.dataset.id===e.id));const inherited=!e.evidence_ids?.length&&e.kind==='AFFECTS_INVARIANT';const evidenceIds=inherited?(N[e.source]?.evidence_ids||[]):e.evidence_ids;document.getElementById('ctg-detail').innerHTML=`<h3>${esc(e.kind)}</h3>${reaches(e.reach)}${e.critical?'<span class="ctg-pill">CRITICAL EDGE</span>':''}<p><b>From:</b> ${esc(N[e.source]?.label||e.source)}<br><b>To:</b> ${esc(N[e.target]?.label||e.target)}<br><b>ID:</b> <code>${esc(e.id)}</code></p>${inherited?'<p class="ctg-source">Structural invariant edge；evidence inherited from source node.</p>':''}<h3>Evidence by reach</h3>${evidence(evidenceIds)}`}
function renderTree(ns){const groups={};ns.forEach(n=>{const p=n.location?.path||`[${laneOf(n)} virtual]`;(groups[p]??=[]).push(n)});document.getElementById('ctg-tree').innerHTML=Object.entries(groups).sort().map(([p,xs])=>`<details><summary><b>${esc(p)}</b> <span class="small">${xs.length}</span></summary>${xs.map(n=>`<div><button data-id="${esc(n.id)}">${esc(n.label)}${n.location?':'+n.location.start_line:''}</button></div>`).join('')}</details>`).join('');document.querySelectorAll('#ctg-tree button').forEach(b=>b.onclick=()=>showNode(N[b.dataset.id]))}
function status(){const cards=[];(G.invariants||[]).forEach(i=>cards.push(`<div class="ctg-card ${String(i.current_status||i.settlement?.status).match(/REFUT|FAIL/i)?'warning':'info'}"><h3>${esc(i.id)} · ${esc(i.current_status||i.settlement?.status||'UNKNOWN')}</h3><p>${esc(i.reason||i.statement)}</p></div>`));(G.diagnostics||[]).slice(0,3).forEach(d=>cards.push(`<div class="ctg-card ${d.severity==='warning'?'warning':'info'}"><h3>${esc(d.code||'Diagnostic')}</h3><p>${esc(d.summary)}</p></div>`));const synthetic=!!G.scope?.synthetic,agentState=!('agent_sessions' in G)?'UNKNOWN':synthetic?'SYNTHETIC_ONLY':'OBSERVED';cards.push(`<div class="ctg-card"><h3>Agent scope · ${agentState}</h3><p>${sessions.length} session receipts；未提供不可改寫成 0%。</p></div>`);cards.push(`<div class="ctg-card"><h3>Deployment · ${esc(G.deployment?.status||'UNKNOWN')}</h3><p>沒有 deployment receipt 不得宣稱 Deployed。</p></div>`);document.getElementById('ctg-status').innerHTML=cards.join('')}
const lanes=[...new Set(G.nodes.map(laneOf))].sort();document.getElementById('ctg-lane').insertAdjacentHTML('beforeend',lanes.map(x=>`<option>${esc(x)}</option>`).join(''));const agentSelect=document.getElementById('ctg-agent');if(!sessions.length)agentSelect.hidden=true;else agentSelect.insertAdjacentHTML('beforeend',sessions.map(s=>{const id=String(s.id||s.session_id);return `<option value="${esc(id)}">${esc(s.agent||id)}</option>`}).join(''));
document.getElementById('ctg-search').oninput=e=>{query=e.target.value.trim().toLowerCase();render()};document.getElementById('ctg-lane').onchange=e=>{lane=e.target.value;render()};agentSelect.onchange=e=>{agentSession=e.target.value;render()};document.getElementById('ctg-critical').onclick=e=>{critical=!critical;e.currentTarget.classList.toggle('active',critical);render()};status();render();
})();
</script>"""
    return template.replace("__GRAPH_JSON__", payload)
