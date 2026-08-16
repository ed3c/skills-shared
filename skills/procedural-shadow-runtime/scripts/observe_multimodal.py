#!/usr/bin/env python3
"""Emit and gate multimodal EvidenceEvents from browser and device-like surfaces.

Exit codes:
  0   every emitted assertion is admissible and the lane closed
  2   an assertion was refused, or a live observation contradicted its claim
  64  the surface, the driver, or the fixture is absent

#218 Lane B. The rule the gate exists to enforce is one line long:

    a screenshot may corroborate a state claim; it may never carry one alone.

`tests/fixtures/multimodal/` holds the reason. Two pages render the same pixels.
One says `data-state="REFUNDED"` and logs a settled dispute; the other says
`data-state="PENDING"` and logs a failed settlement behind an identical green
badge. A visual diff clears both. Anything that treats the image as the evidence
admits the second page as a completed refund.

So an `EvidenceEvent` whose only artifact is an image is refused for any
`STATE_TRANSITION` or `SAFETY` claim, and the browser adapter proves the refusal
against a live render rather than a fixture of a render.

Lanes are reported separately and neither implies the other:

    BROWSER   live headless Chromium via Playwright
    DEVICE    contract implemented; no authorised simulator, so NOT_EXERCISED
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SKILL = Path(__file__).resolve().parents[1]
FIXTURES = SKILL / "tests" / "fixtures" / "multimodal"

INVALID = 64
REFUSED = 2

# A claim of this weight cannot rest on pixels. Weaker kinds may.
HARD_CLAIM_KINDS = {"STATE_TRANSITION", "SAFETY"}
IMAGE_KINDS = {"SCREENSHOT", "VIDEO", "VISUAL_DIFF"}
STRUCTURED_KINDS = {"DOM_ASSERTION", "ACCESSIBILITY_TREE", "CONSOLE", "NETWORK",
                    "PROCESS_STATE", "STRUCTURED_LOG"}
LANE_STATES = {"OBSERVED", "NOT_OBSERVED", "NOT_EXERCISED", "BLOCKED"}


class Refused(Exception):
    pass


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest_json(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def portable_url(url: str) -> str:
    """A file:// URL of a fixture is one machine's path.

    The observation is about which page was rendered, not about where that
    developer keeps their checkout, and a receipt carrying the second is
    replayable nowhere else.
    """
    marker = "/skills/procedural-shadow-runtime/"
    index = url.find(marker)
    return f"<REPO>{url[index:]}" if index != -1 else url


def admit_assertion(assertion: dict[str, Any], artifacts: dict[str, dict[str, Any]]) -> None:
    """Refuse anything that cannot be replayed or that leans on an image alone."""
    for key in ("assertion_id", "claim_kind", "subject", "observed_at"):
        if not assertion.get(key):
            raise Refused(f"{assertion.get('assertion_id', '<unnamed>')}: {key} missing")
    if assertion["claim_kind"] not in HARD_CLAIM_KINDS | {"PRESENCE", "DIAGNOSTIC"}:
        raise Refused(f"{assertion['assertion_id']}: unknown claim_kind {assertion['claim_kind']!r}")

    referenced = assertion.get("artifact_ids") or []
    if not referenced:
        raise Refused(f"{assertion['assertion_id']}: no artifact bound")
    kinds = set()
    for artifact_id in referenced:
        artifact = artifacts.get(artifact_id)
        if artifact is None:
            raise Refused(f"{assertion['assertion_id']}: artifact {artifact_id!r} not in the bundle")
        if not artifact.get("sha256"):
            raise Refused(f"{assertion['assertion_id']}: artifact {artifact_id!r} is not content-addressed")
        kinds.add(artifact["kind"])

    if assertion["claim_kind"] in HARD_CLAIM_KINDS and not (kinds & STRUCTURED_KINDS):
        raise Refused(
            f"{assertion['assertion_id']}: a {assertion['claim_kind']} claim backed only by "
            f"{sorted(kinds)} -- an image cannot carry a state claim"
        )


def build_bundle(lane: str, surface: dict[str, Any], subject: dict[str, Any],
                 artifacts: dict[str, dict[str, Any]], assertions: list[dict[str, Any]],
                 lane_state: str, interaction_trace: list[dict[str, Any]]) -> dict[str, Any]:
    if lane_state not in LANE_STATES:
        raise Refused(f"unknown lane state {lane_state!r}")
    return {
        "schema": "multimodal-evidence-bundle/v1",
        "lane": lane,
        "lane_state": lane_state,
        "surface": surface,
        "subject": subject,
        "artifacts": artifacts,
        "assertions": assertions,
        "interaction_trace": interaction_trace,
        "authority": {
            "observer_read_only": True,
            "capability_widening": "DENY",
            "private_data_egress": "DENY",
            "raw_private_reasoning": "DENY",
        },
        "bundle_digest": digest_json({"artifacts": artifacts, "assertions": assertions}),
    }


BROWSER_SCRIPT = r"""
import json, sys, pathlib
from playwright.sync_api import sync_playwright

target, out_dir = sys.argv[1], pathlib.Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
console, requests = [], []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 720, "height": 400})
    page.on("console", lambda m: console.append({"type": m.type, "text": m.text}))
    page.on("request", lambda r: requests.append({"method": r.method, "resource_type": r.resource_type}))
    response = page.goto(target, wait_until="load")
    shot = out_dir / (pathlib.Path(target).stem + ".png")
    page.screenshot(path=str(shot))
    state = {
        "url": page.url,
        "title": page.title(),
        "status": response.status if response else None,
        "status_state": page.get_attribute("#status", "data-state"),
        "status_text": page.inner_text("#status"),
        "amount_usd": page.get_attribute("#amount", "data-usd"),
        "accessibility": page.locator("body").aria_snapshot(),
        "console": console,
        "network": {"request_count": len(requests)},
        "screenshot_path": str(shot),
    }
    browser.close()
print(json.dumps(state))
"""


def observe_browser(page_path: Path, out_dir: Path, timeout: int) -> dict[str, Any]:
    if not page_path.is_file():
        raise SystemExit(INVALID)
    driver = out_dir / "_playwright_driver.py"
    out_dir.mkdir(parents=True, exist_ok=True)
    driver.write_text(BROWSER_SCRIPT, encoding="utf-8")
    process = subprocess.run(
        [sys.executable, str(driver), page_path.resolve().as_uri(), str(out_dir)],
        capture_output=True, text=True, check=False, timeout=timeout,
    )
    if process.returncode != 0:
        print(f"OBSERVE-INVALID playwright: {process.stderr.strip()[-300:]}", file=sys.stderr)
        raise SystemExit(INVALID)
    return json.loads(process.stdout)


def browser_bundle(state: dict[str, Any], expected_state: str, subject: dict[str, Any],
                   version: str) -> dict[str, Any]:
    shot = Path(state["screenshot_path"])
    image_digest = sha256_bytes(shot.read_bytes())
    dom = {"status_state": state["status_state"], "status_text": state["status_text"],
           "amount_usd": state["amount_usd"]}
    errors = [entry for entry in state["console"] if entry["type"] == "error"]

    artifacts = {
        "screenshot": {"kind": "SCREENSHOT", "sha256": image_digest, "path": shot.name,
                       "bytes": shot.stat().st_size},
        "dom": {"kind": "DOM_ASSERTION", "sha256": digest_json(dom), "value": dom},
        "a11y": {"kind": "ACCESSIBILITY_TREE", "sha256": digest_json(state["accessibility"])},
        "console": {"kind": "CONSOLE", "sha256": digest_json(state["console"]),
                    "error_count": len(errors)},
        "network": {"kind": "NETWORK", "sha256": digest_json(state["network"]),
                    "value": state["network"]},
    }
    url = portable_url(state["url"])
    observed_at = f"navigation:{url}"
    assertions = [
        {
            "assertion_id": "settled-state-matches-declared-transition",
            "claim_kind": "STATE_TRANSITION",
            "subject": subject["page"],
            "observed_at": observed_at,
            # Structured state first, image second. The order is not cosmetic:
            # the screenshot is corroboration for a claim the DOM already
            # decided, and swapping them is the defect this lane exists to stop.
            "artifact_ids": ["dom", "screenshot"],
            "expected": expected_state,
            "actual": state["status_state"],
            "result": "PASS" if state["status_state"] == expected_state else "FAIL",
        },
        {
            "assertion_id": "page-reported-no-runtime-error",
            "claim_kind": "DIAGNOSTIC",
            "subject": subject["page"],
            "observed_at": observed_at,
            "artifact_ids": ["console"],
            "expected": 0,
            "actual": len(errors),
            "result": "PASS" if not errors else "FAIL",
        },
        {
            "assertion_id": "rendered-badge-is-visible",
            "claim_kind": "PRESENCE",
            "subject": subject["page"],
            "observed_at": observed_at,
            "artifact_ids": ["screenshot", "a11y"],
            "expected": "Order refunded",
            "actual": state["status_text"],
            "result": "PASS" if state["status_text"] == "Order refunded" else "FAIL",
        },
    ]
    for assertion in assertions:
        admit_assertion(assertion, artifacts)
    return build_bundle(
        "BROWSER",
        {"driver": "playwright-chromium", "driver_version": version, "headless": True,
         "viewport": "720x400", "url": url},
        subject, artifacts, assertions, "OBSERVED",
        [{"step": 0, "action": "navigate", "target": url},
         {"step": 1, "action": "screenshot", "target": shot.name}],
    )


def device_bundle() -> dict[str, Any]:
    """The contract exists; no authorised simulator does. Reported, not simulated."""
    return build_bundle(
        "DEVICE",
        {"driver": "simctl", "driver_version": None, "headless": None, "viewport": None},
        {"page": None, "repository": "ed3c/skills-shared",
         "note": "no booted simulator and no device authorisation for this repository"},
        {}, [], "NOT_EXERCISED", [],
    )


def playwright_version() -> str:
    result = subprocess.run([sys.executable, "-c", "import playwright; print(playwright.__version__)"],
                            capture_output=True, text=True, check=False)
    return result.stdout.strip() or "unknown"


def selftest() -> int:
    """Every admission rule, offline. No browser, no network."""
    artifacts = {
        "shot": {"kind": "SCREENSHOT", "sha256": "a" * 64},
        "dom": {"kind": "DOM_ASSERTION", "sha256": "b" * 64},
        "unaddressed": {"kind": "DOM_ASSERTION"},
    }
    base = {"assertion_id": "x", "claim_kind": "STATE_TRANSITION", "subject": "p",
            "observed_at": "navigation:file:///x"}

    admit_assertion({**base, "artifact_ids": ["dom", "shot"]}, artifacts)
    admit_assertion({**base, "claim_kind": "PRESENCE", "artifact_ids": ["shot"]}, artifacts)

    refusals = [
        ("image-only-state-claim", {**base, "artifact_ids": ["shot"]}),
        ("image-only-safety-claim", {**base, "claim_kind": "SAFETY", "artifact_ids": ["shot"]}),
        ("no-artifact", {**base, "artifact_ids": []}),
        ("unknown-artifact", {**base, "artifact_ids": ["ghost"]}),
        ("unaddressed-artifact", {**base, "artifact_ids": ["unaddressed"]}),
        ("no-subject", {**base, "subject": "", "artifact_ids": ["dom"]}),
        ("no-timestamp", {**base, "observed_at": "", "artifact_ids": ["dom"]}),
        ("unknown-claim-kind", {**base, "claim_kind": "VIBES", "artifact_ids": ["dom"]}),
    ]
    for name, assertion in refusals:
        try:
            admit_assertion(assertion, artifacts)
        except Refused:
            continue
        print(f"SELFTEST RED: control {name!r} was admitted", file=sys.stderr)
        return 1

    try:
        build_bundle("BROWSER", {}, {}, {}, [], "PROBABLY_FINE", [])
    except Refused:
        pass
    else:
        print("SELFTEST RED: an invented lane state was accepted", file=sys.stderr)
        return 1

    for state in sorted(LANE_STATES):
        build_bundle("BROWSER", {}, {}, {}, [], state, [])

    leaky = "file:///Users/someone/checkout/skills/procedural-shadow-runtime/tests/x.html"
    if "/Users/someone" in portable_url(leaky):
        print(f"SELFTEST RED: a machine path survived URL redaction: {portable_url(leaky)}",
              file=sys.stderr)
        return 1
    if portable_url("https://example.invalid/page") != "https://example.invalid/page":
        print("SELFTEST RED: a remote URL was rewritten by the path redactor", file=sys.stderr)
        return 1

    if not FIXTURES.joinpath("truthful.html").is_file() or not FIXTURES.joinpath("lookalike.html").is_file():
        print("SELFTEST RED: the look-alike fixture pair is missing", file=sys.stderr)
        return 1

    print(
        f"SELFTEST GREEN: structured+image state claims admitted; {len(refusals)} controls refused "
        "including image-only state and safety claims, unbound and uncontent-addressed artifacts, "
        "and missing subject/timestamp; invented lane states refused; fixture pair present"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--observe-browser", type=Path, metavar="PAGE",
                        help="local HTML page to render and observe")
    parser.add_argument("--expect-state", default="REFUNDED")
    parser.add_argument("--device-lane", action="store_true",
                        help="emit the device lane bundle in its real state")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--artifact-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    if args.selftest:
        return selftest()
    if not args.output:
        print("OBSERVE-INVALID: --output is required unless --selftest", file=sys.stderr)
        return INVALID

    if args.device_lane:
        bundle = device_bundle()
    elif args.observe_browser:
        if not args.artifact_dir:
            print("OBSERVE-INVALID: --artifact-dir is required with --observe-browser",
                  file=sys.stderr)
            return INVALID
        state = observe_browser(args.observe_browser, args.artifact_dir, args.timeout)
        subject = {"page": args.observe_browser.name, "repository": "ed3c/skills-shared"}
        try:
            bundle = browser_bundle(state, args.expect_state, subject, playwright_version())
        except Refused as exc:
            print(f"OBSERVE-REFUSED {exc}", file=sys.stderr)
            return REFUSED
    else:
        print("OBSERVE-INVALID: one of --observe-browser or --device-lane is required",
              file=sys.stderr)
        return INVALID

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    failed = [item["assertion_id"] for item in bundle["assertions"] if item["result"] == "FAIL"]
    print(f"OBSERVE {bundle['lane']} state={bundle['lane_state']} "
          f"assertions={len(bundle['assertions'])} failed={failed} "
          f"digest={bundle['bundle_digest'][:12]}")
    return REFUSED if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
