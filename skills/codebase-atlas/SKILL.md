---
name: codebase-atlas
description: Turn the current repository into a self-contained, interactive isometric architecture atlas in a monochrome drafting-paper style. Use for “make a codebase atlas”, “turn this repo into a visual architecture map”, “isometric codebase map”, or when updating an existing atlas. Do not use for a small one-off mechanism diagram, a Mermaid request, or a product UI mockup.
version: 2.0.0
---

# Codebase Atlas — Evidence-Driven System Prompt

## 0. Runtime defaults

Use these defaults unless the user gives explicit replacements:

```yaml
TASK_MODE: CREATE_OR_UPDATE
REPO_ROOT: current workspace repository root
OUTPUT_LANGUAGE: language used by the user
OUTPUT_HTML: artifacts/codebase-atlas.html
EVIDENCE_DIR: artifacts/codebase-atlas-evidence
TEMPLATE_HTML: references/atlas-template.html
REFERENCE_VIEWPORT: 2048x1090
PRIMARY_TEST_VIEWPORT: 1800x1000
NARROW_TEST_VIEWPORT: 760x980
MIN_MAJOR_STRUCTURES: 15
MAX_MAJOR_STRUCTURES: 35
TRACE_STEPS_MIN: 10
TRACE_STEPS_MAX: 14
SHARE_SAFETY: STRICT
FLOW_DEFAULT: PAUSED
MAX_REPAIR_PASSES: 8
```

Use the current repository automatically. Do not ask the user to choose files when the repository root, build manifests, and source tree can resolve the task.

## 1. Mission

Convert the repository into one stable, single-file HTML architecture atlas that looks and behaves like an isometric technical drawing on aged drafting paper:

- a full-width metadata and control bar;
- a grouped repository-structure rail on the left;
- a large pannable and zoomable isometric city in the center;
- hatched blocks whose geometry is driven by measured repository facts;
- solid and dashed data routes with moving payload dots;
- external-system labels with dashed leaders;
- a two-tab inspector on the right;
- hover explanations, pinned selection, go-inside drill-downs, and a canonical step-by-step trace;
- no runtime dependency, network request, or invented repository count.

The atlas is a repository explanation and evidence surface, not a decorative diagram.

## 2. Definition of done

Do not declare completion until every hard gate below passes:

1. `OUTPUT_HTML` is one self-contained HTML document with inline CSS, inline JavaScript, inline SVG, and no external dependency.
2. Every displayed count and repository claim is measured from the scanned repository or explicitly shown as `not measured`; no number is guessed.
3. The page renders all variable-element classes listed in Section 7.
4. The default, selected, hover, inside, trace, how-built, flow, zoom, pan, reset, and narrow-view states execute without console errors.
5. Headless screenshots exist for the required states and have no severe clipping, collision, or orphaned structure.
6. Grid footprints are disjoint at the data-model level.
7. The share-safety scan passes.
8. `coverage-report.json` says `PASS`, and every Boolean coverage key is `true`.

A visually similar screenshot without working state transitions is a failure. A working diagram with invented counts is also a failure.

## 3. Source-of-truth inventory

Before writing the atlas, perform a thorough repository scan. Use code search, manifests, source files, tests, deployment definitions, documentation, generated route tables, and runtime receipts when available.

Produce an internal inventory with:

- 15–35 major subsystems;
- short display name and stable ID;
- directory and key files;
- one or two plain-English sentences for a non-expert;
- measured LOC and file count where feasible;
- code-level role versus deployed service classification;
- inbound and outbound dependencies;
- what data or control signal moves on every directed dependency;
- storage surfaces, queues, databases, caches, generated artifacts, model providers, SaaS boundaries, and user-facing surfaces;
- one canonical end-to-end request or job trace;
- headline repository statistics;
- test count, routes, feature count, packages, services, and deployed units only when they can be measured reliably.

Correct any assumed subsystem list after the scan. Do not treat a module named `worker`, `service`, `agent`, or `engine` as a deployed service unless deployment evidence supports that classification.

When a value cannot be measured:

- use `null` internally;
- render `not measured` or omit the statistic;
- record the missing evidence in the coverage report;
- never infer a precise number from prose.

## 4. Single data source

All visible and interactive content must be generated from one embedded data object. Do not hard-code a sidebar row, title, count, route, tooltip, inspector paragraph, trace step, or external label outside this object.

Use this logical contract. Additional evidence fields are allowed, but do not remove the required fields.

```ts
type AtlasData = {
  meta: Array<{ id: string; label: string; value: string; evidence?: string[] }>;
  actions: Array<{ id: "flow" | "trace" | "reset" | string; label: string; activeLabel?: string }>;
  groups: Array<{ id: string; name: string; rowIds: string[] }>;
  structures: Array<{
    id: string; code: string; name: string; group: string; paths: string[]; keyFiles?: string[];
    loc: number | null; files: number | null;
    classification: "deployed-service" | "code-role" | "storage" | "external-adapter" | "generated-output";
    gx: number; gy: number; w: number; d: number; h: number; slab?: boolean; layers?: number; nested?: boolean;
    what: string; how: string; talks: string[];
    conditions?: Array<{ state: "pass" | "warn" | "fail"; name: string; detail: string }>;
    children?: Array<{
      id: string; code: string; name: string; gx: number; gy: number; w: number; d: number; h: number;
      what: string; how: string;
      conditions?: Array<{ state: "pass" | "warn" | "fail"; name: string; detail: string }>;
    }>;
  }>;
  edges: Array<{
    id: string; f: string; t: string; pay: string; flow?: boolean; dashed?: boolean; via?: Array<[number, number]>;
  }>;
  externals: Array<{ id: string; label: string; gx: number; gy: number; to: string; pay: string }>;
  trace: Array<{ structureId: string; sentence: string; edgeId?: string }>;
  overview: { eyebrow: string; title: string; subtitle: string; what: AtlasSection[]; how: AtlasSection[] };
};

type AtlasSection = {
  label: string;
  paragraphs?: string[];
  conditions?: Array<{ state: "pass" | "warn" | "fail"; name: string; detail: string }>;
};
```

Keep evidence paths in the data or a sibling inventory JSON, but do not expose private absolute filesystem paths in the rendered page.

## 5. Fixed visual grammar

The content is variable. The following visual grammar is invariant.

### 5.1 Geometry

At a `2048x1090` viewport, use these principal boundaries:

- top bar: `52px` high;
- left rail: `206px` wide;
- right inspector: approximately `441px` wide;
- center stage: the remaining width;
- one-pixel dark rules between all principal regions.

Use responsive CSS equivalent to:

```css
--topbar: 52px;
--rail: clamp(178px, 10.06vw, 206px);
--inspector: clamp(372px, 21.53vw, 441px);
```

The body must fill the viewport and must not scroll horizontally. The rail and inspector may scroll vertically. The center stage must clip its SVG scene.

### 5.2 Color and type

Use this palette unless the user explicitly requests a different one:

```css
--paper: #cdc499;
--paper-2: #d8cfaa;
--paper-3: #c5bc91;
--ink: #1b1506;
--muted: #756e4f;
--grid: rgba(27, 21, 6, 0.105);
--rule: rgba(27, 21, 6, 0.78);
```

Use a system monospace stack. Do not fetch fonts. Use small uppercase labels with wide tracking, rectangular controls and tabs, no rounded cards, no glossy gradient, and no rainbow category palette.

### 5.3 Isometric projection

Use a deterministic projection equivalent to:

```js
x = originX + (gx - gy) * 35;
y = originY + (gx + gy) * 19 - z * 18;
```

Render faint isometric grid lines, a light roof face, two differently angled hatched side faces, thin dark outlines, centered short structure code on the roof, selected/trace-target roofs, slabs, and visible strata when `layers > 1`.

Draw edges before blocks. Sort blocks by `gx + gy` for painter order. Do not use arbitrary z-index fixes.

## 6. Layout rules for repository data

Cluster by functional zone: user/client surfaces upper area; API/orchestration nearby; ingestion left; agent/model-call roles right; core domain center; compute below core; storage lower row; CI/release/verification in a corner; externals beyond the main cluster.

Largest measured subsystem must be among tallest or broadest structures. Storage is flat. Small adapters are short. No top-level grid footprints may overlap.

## 7. Variable-element coverage registry

The atlas must cover all variable classes visible or implied by the reference UI: metadata/revision, headline stats, runtime status, flow state, trace action, reset, left groups, rail row code/name/count, nested rows, selection synchronization, isometric grid, variable position/footprint/height, slabs, stacked structures, hatching, roof codes, solid/dashed/waypoint edges, animated payload dots, externals, tooltips, overview/selected/route inspector contexts, WHAT IT DOES/HOW IT'S BUILT tabs, status/condition rows, go-inside children/back-out, canonical trace banner and active target, pan/zoom/wheel/keyboard/focus/reduced-motion, URL-hash debug state, narrow layout, offline/CSP execution, and share-safety.

Maintain an internal coverage ledger with: `id`, `element`, `source`, `states`, `trigger`, `render_function`, `verification_screenshot`, and `pass`.

## 8. Interaction state machine

Required synchronized states:

- overview;
- hover structure;
- pinned structure selection;
- route/payload hover;
- WHAT IT DOES / HOW IT'S BUILT;
- flow running / paused;
- trace step 1, middle, final;
- inside/drill-down and come-back-out;
- zoom in/out;
- pan;
- reset.

Selection must stay synchronized across rail, map block, inspector, and trace where applicable.

Expose deterministic hash/debug states such as `#selected=<id>`, `#inside=<id>`, `#trace=<n>`, `#paused=1`, `#tab=how`, and equivalent zoom states. Expose a small `window.__ATLAS_DEBUG__` surface sufficient for headless assertions.

## 9. Screenshot-conformance loop

Do not validate only the default view. Capture a state matrix including at least:

- default overview;
- selected structure;
- supporting-system selection;
- HOW IT'S BUILT;
- flow running and paused;
- trace step 1, a middle step, final step;
- one inside view when children exist;
- zoomed in/out;
- reset;
- hover structure;
- hover edge/payload where supported;
- narrow viewport.

For each pass: render, inspect, classify discrepancy, make minimum repair, rerender. Repair priority: page geometry → column proportions → projection → block placement/dimensions → grouping → edges → inspector → typography/spacing → animation → interaction polish.

Never change repository facts for visual similarity.

## 10. Runtime verification

Run deterministic validation first, then Playwright/headless browser screenshots at `1800x1000`, `2048x1090`, and `760x980` where relevant. Verify no console/page errors, no external subresource requests, no severe clipping/collisions, correct selection/trace/inside/hash states, disjoint footprints, pause/resume, reset, zoom, and offline execution.

Write `coverage-report.json` with PASS/FAIL per gate. Do not claim PASS from prose alone.

## 11. Share-safety

Assume the atlas may be posted publicly. Preserve module names, measured LOC, generic stack and architectural roles; scrub operationally sensitive cloud/resource names, project/account IDs, queue/topic identifiers, endpoint paths, credential locations, mount paths, key prefixes/formats, secret names, internal emails/usernames, and private infrastructure URLs.

Search final HTML for known prefixes plus `@`, `secret`, `token`, `key`, `/api/`, `/internal/`, `/mnt/`, `/Users/`, `http://`, and `https://`. Review every match. Record the result in the evidence directory.

## 12. Update mode

When updating an existing atlas: re-scan changed areas and downstream dependencies, preserve stable structure IDs/layout when architecture is unchanged, refresh affected counts/descriptions/edges/children/trace/stats, then rerun the full verification and safety workflow. Keep the artifact filename stable.

## 13. Exit condition

Complete only when both hold:

```text
ARCHITECTURE_TRUTH = PASS
VISUAL_STATE_COVERAGE = PASS
```

Static resemblance alone is insufficient; runtime evidence is mandatory.
