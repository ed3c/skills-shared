import pytest

from src.envelope import EnvelopeError, make_envelope
from src.ledger import Ledger


def _record(
    record_id: str,
    *,
    parent_id: str | None = None,
    result_snapshot: object = "ok",
    error_snapshot: object = None,
) -> dict[str, object]:
    return make_envelope(
        id=record_id,
        parentId=parent_id,
        loop_layer="L2",
        task_ref={"packet_id": "SC3", "priority": "high", "passes": True},
        event={"kind": "ledger_append", "tool": "pytest", "args": {"case": record_id}},
        exec={
            "command": "pytest -q",
            "exit_code": 0,
            "result_snapshot": result_snapshot,
            "error_snapshot": error_snapshot,
        },
        handoff={
            "verified_hypotheses": ["sc3"],
            "ruled_out": [],
            "current_diff": "src+tests",
            "next_action": "handled",
        },
        budget={"tokens_used": 7, "usd": 0.02},
        freshness={"git_commit_sha": "abc123", "fact_stale": False},
    )


def test_sc3_nine_field_round_trip_preserves_pointer_snapshots(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    record = _record(
        "root",
        result_snapshot={"uri": "file:///tmp/result.json", "sha256": "deadbeef", "preview": "trimmed"},
        error_snapshot={"hash": "beadfeed", "preview": "stderr tail"},
    )

    ledger.append(record)

    records = ledger.read_all()
    assert list(records[0]) == [
        "budget",
        "event",
        "exec",
        "freshness",
        "handoff",
        "id",
        "loop_layer",
        "parentId",
        "task_ref",
    ]
    assert records[0]["exec"]["result_snapshot"]["uri"] == "file:///tmp/result.json"
    assert records[0]["exec"]["error_snapshot"]["hash"] == "beadfeed"


def test_sc3_parent_id_lineage_can_be_reloaded(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    root = _record("root")
    child = _record("child", parent_id="root")
    leaf = _record("leaf", parent_id="child")

    ledger.append(root)
    ledger.append(child)
    ledger.append(leaf)

    lineage = ledger.read_lineage("leaf")

    assert [record["id"] for record in lineage] == ["root", "child", "leaf"]
    assert [record["parentId"] for record in lineage] == [None, "root", "child"]


def test_sc3_append_only_keeps_prior_records(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    first = _record("first")
    second = _record("second", parent_id="first")

    ledger.append(first)
    size_after_first = (tmp_path / "ledger.jsonl").stat().st_size
    ledger.append(second)

    records = ledger.read_all()
    assert len(records) == 2
    assert [record["id"] for record in records] == ["first", "second"]
    assert (tmp_path / "ledger.jsonl").stat().st_size > size_after_first


def test_sc3_missing_required_field_fails_fast_on_append(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    record = _record("broken")
    del record["freshness"]

    with pytest.raises(EnvelopeError):
        ledger.append(record)


def test_sc3_large_inline_snapshot_is_rejected_without_pointer(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")

    with pytest.raises(EnvelopeError):
        record = _record("too-big", result_snapshot={"payload": "x" * 600})
        ledger.append(record)
