#!/usr/bin/env python3
"""Privacy class to execution lane routing.

Two states that look alike and are not: a provider being *healthy* and a
provider being *permitted*. A reachable endpoint says nothing about whether
this document may be sent to it, and an approved endpoint that is down is not a
reason to fall back to a lane the document was never admitted to. So health and
admission are tracked separately and neither substitutes for the other.

Exits: 0 routed, 2 refused, 64 usage.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

PRIVACY_CLASSES = ("PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED")
LANES = ("LOCAL_ONLY", "PRIVATE_ENDPOINT", "EXTERNAL_APPROVED")

# The maximum lane a class may ever reach. A class may always be processed more
# privately than required; it may never be processed less privately.
CEILING = {
    "PUBLIC": "EXTERNAL_APPROVED",
    "INTERNAL": "PRIVATE_ENDPOINT",
    "CONFIDENTIAL": "EXTERNAL_APPROVED",  # only with an exact human approval
    "RESTRICTED": "LOCAL_ONLY",
}
LANE_RANK = {lane: index for index, lane in enumerate(LANES)}


class Refused(Exception):
    pass


def check_route(request: dict[str, Any]) -> None:
    privacy = request.get("privacy_class")
    if privacy not in PRIVACY_CLASSES:
        raise Refused(f"unknown privacy_class {privacy!r}")
    lane = request.get("execution_lane")
    if lane not in LANES:
        raise Refused(f"unknown execution_lane {lane!r}")

    if LANE_RANK[lane] > LANE_RANK[CEILING[privacy]]:
        raise Refused(
            f"{privacy} may not reach {lane}; its ceiling is {CEILING[privacy]}"
        )

    if privacy == "RESTRICTED":
        if lane != "LOCAL_ONLY":
            raise Refused("RESTRICTED always routes LOCAL_ONLY")
        if request.get("network_enabled") is not False:
            raise Refused("RESTRICTED requires network_enabled false")

    if lane == "LOCAL_ONLY" and request.get("network_enabled") is True:
        raise Refused("LOCAL_ONLY with network_enabled true is not a local lane")

    if privacy == "CONFIDENTIAL" and lane == "EXTERNAL_APPROVED":
        approval = request.get("human_approval")
        if not approval:
            raise Refused(
                "CONFIDENTIAL external processing requires an exact human "
                "approval receipt and none is present"
            )
        for field in ("approver_identity", "approver_kind", "subject_digest",
                      "approval_receipt_digest"):
            if not approval.get(field):
                raise Refused(f"human_approval.{field} is absent")
        if approval["approver_kind"] != "HUMAN":
            raise Refused(
                f"approval was created by {approval['approver_kind']}; an agent "
                f"cannot approve its own external processing"
            )
        if approval["subject_digest"] != request.get("subject_digest"):
            raise Refused(
                "approval names a different subject than the document being sent"
            )

    provider = request.get("provider")
    if lane in ("PRIVATE_ENDPOINT", "EXTERNAL_APPROVED"):
        if not provider:
            raise Refused(f"{lane} requires a declared provider")
        # Health and admission are separate states. Either one being absent
        # blocks, and neither one being present substitutes for the other.
        if provider.get("privacy_admission") != "ADMITTED":
            raise Refused(
                f"provider {provider.get('id')!r} is not admitted for this lane; "
                f"reachability is not permission"
            )
        health = provider.get("health")
        if health != "HEALTHY":
            raise Refused(
                f"provider {provider.get('id')!r} health is {health!r}; an "
                f"admitted provider that is not healthy blocks rather than "
                f"falling back to a lane this document was not admitted to"
            )

    # A durable receipt must not carry operational identity.
    receipt = request.get("durable_receipt_fields") or []
    forbidden_markers = ("token", "secret", "password", "session", "cookie",
                         "api_key", "apikey", "/users/", "/home/", "c:\\")
    for field in receipt:
        lowered = str(field).lower()
        for marker in forbidden_markers:
            if marker in lowered:
                raise Refused(
                    f"durable receipt field {field!r} looks like a secret, "
                    f"session, or machine path; those never reach a durable receipt"
                )

    # An absent selection is not a permitted one.
    if request.get("fallback_used") and not request.get("fallback_declared"):
        raise Refused(
            "a fallback was used without being declared; an evidence downgrade "
            "must be explicit"
        )


def _canonical() -> dict[str, Any]:
    return {
        "privacy_class": "INTERNAL",
        "execution_lane": "PRIVATE_ENDPOINT",
        "network_enabled": True,
        "subject_digest": "sha256:" + "a" * 64,
        "provider": {
            "id": "fixture-private-endpoint",
            "privacy_admission": "ADMITTED",
            "health": "HEALTHY",
        },
        "human_approval": None,
        "durable_receipt_fields": ["subject_digest", "lane", "provider_id"],
        "fallback_used": False,
        "fallback_declared": False,
    }


def _selftest() -> int:
    import copy

    survived: list[str] = []

    try:
        check_route(_canonical())
    except Refused as error:
        print(f"SELFTEST RED: canonical route refused: {error}", file=sys.stderr)
        return 2

    # Every class must be routable at its own ceiling, or the table is unusable.
    for privacy in PRIVACY_CLASSES:
        body = copy.deepcopy(_canonical())
        body["privacy_class"] = privacy
        body["execution_lane"] = CEILING[privacy]
        if privacy == "RESTRICTED":
            body["network_enabled"] = False
        if CEILING[privacy] == "LOCAL_ONLY":
            body["network_enabled"] = False
            body["provider"] = None
        if privacy == "CONFIDENTIAL":
            body["human_approval"] = {
                "approver_identity": "ed3c",
                "approver_kind": "HUMAN",
                "subject_digest": body["subject_digest"],
                "approval_receipt_digest": "sha256:" + "b" * 64,
            }
        try:
            check_route(body)
        except Refused as error:
            print(f"SELFTEST RED: {privacy} at its own ceiling refused: {error}",
                  file=sys.stderr)
            return 2

    mutations: list[tuple[str, Any]] = [
        ("RESTRICTED routed off-box", lambda b: (
            b.__setitem__("privacy_class", "RESTRICTED"),
            b.__setitem__("execution_lane", "PRIVATE_ENDPOINT"))),
        ("RESTRICTED with network enabled", lambda b: (
            b.__setitem__("privacy_class", "RESTRICTED"),
            b.__setitem__("execution_lane", "LOCAL_ONLY"),
            b.__setitem__("network_enabled", True))),
        ("INTERNAL sent to an external lane", lambda b: (
            b.__setitem__("execution_lane", "EXTERNAL_APPROVED"))),
        ("CONFIDENTIAL external with no approval", lambda b: (
            b.__setitem__("privacy_class", "CONFIDENTIAL"),
            b.__setitem__("execution_lane", "EXTERNAL_APPROVED"))),
        ("CONFIDENTIAL external approved by an agent", lambda b: (
            b.__setitem__("privacy_class", "CONFIDENTIAL"),
            b.__setitem__("execution_lane", "EXTERNAL_APPROVED"),
            b.__setitem__("human_approval", {
                "approver_identity": "router-bot", "approver_kind": "AGENT",
                "subject_digest": b["subject_digest"],
                "approval_receipt_digest": "sha256:" + "b" * 64}))),
        ("approval for a different document", lambda b: (
            b.__setitem__("privacy_class", "CONFIDENTIAL"),
            b.__setitem__("execution_lane", "EXTERNAL_APPROVED"),
            b.__setitem__("human_approval", {
                "approver_identity": "ed3c", "approver_kind": "HUMAN",
                "subject_digest": "sha256:" + "9" * 64,
                "approval_receipt_digest": "sha256:" + "b" * 64}))),
        ("LOCAL_ONLY lane with network enabled", lambda b: (
            b.__setitem__("execution_lane", "LOCAL_ONLY"),
            b.__setitem__("network_enabled", True))),
        ("provider healthy but not admitted", lambda b: (
            b["provider"].__setitem__("privacy_admission", "PENDING"))),
        ("provider admitted but unhealthy", lambda b: (
            b["provider"].__setitem__("health", "DEGRADED"))),
        ("external lane with no provider", lambda b: (
            b.__setitem__("provider", None))),
        ("session identity in the durable receipt", lambda b: (
            b["durable_receipt_fields"].append("session_id"))),
        ("machine path in the durable receipt", lambda b: (
            b["durable_receipt_fields"].append("/Users/neon/docs/manual.xml"))),
        ("api key in the durable receipt", lambda b: (
            b["durable_receipt_fields"].append("provider_api_key"))),
        ("undeclared fallback", lambda b: (
            b.__setitem__("fallback_used", True))),
        ("unknown privacy class", lambda b: (
            b.__setitem__("privacy_class", "SECRETISH"))),
        ("unknown lane", lambda b: (
            b.__setitem__("execution_lane", "WHEREVER"))),
    ]
    for name, apply in mutations:
        body = copy.deepcopy(_canonical())
        apply(body)
        try:
            check_route(body)
        except Refused:
            continue
        survived.append(name)

    if survived:
        for name in survived:
            print(f"SELFTEST RED: mutation survived: {name}", file=sys.stderr)
        return 2

    print(
        f"SELFTEST GREEN: every class routable at its ceiling; "
        f"{len(mutations)} mutations refused"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--request", type=Path)
    args = parser.parse_args()

    if args.selftest:
        return _selftest()
    if args.request is None:
        parser.error("--request or --selftest is required")

    try:
        body = json.loads(args.request.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"FATAL: {error}", file=sys.stderr)
        return 64

    try:
        check_route(body)
    except Refused as error:
        print(f"PRIVACY ROUTING RED: {error}", file=sys.stderr)
        return 2

    print(f"PRIVACY ROUTING GREEN: {body['privacy_class']} -> {body['execution_lane']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
