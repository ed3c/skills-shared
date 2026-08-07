import inspect

from src.envelope import make_envelope
from src.ledger import Ledger


def _record(record_id: str, *, result_snapshot: object = "ok") -> dict[str, object]:
    return make_envelope(
        id=record_id,
        parentId=None,
        loop_layer="L2",
        task_ref={"packet_id": "SC7", "priority": "high", "passes": True},
        event={"kind": "ledger_append", "tool": "pytest", "args": {"case": record_id}},
        exec={
            "command": "pytest -q",
            "exit_code": 0,
            "result_snapshot": result_snapshot,
            "error_snapshot": None,
        },
        handoff={
            "verified_hypotheses": ["sc7"],
            "ruled_out": [],
            "current_diff": "src+tests",
            "next_action": "handled",
        },
        budget={"tokens_used": 1, "usd": 0.0},
        freshness={"git_commit_sha": "abc123", "fact_stale": False},
    )


def test_sc7_multiple_records_each_append_in_one_write_with_newline(
    tmp_path, monkeypatch
):
    calls: list[bytes] = []
    real_write = __import__("os").write

    def spy_write(fd, payload):
        calls.append(payload)
        return real_write(fd, payload)

    import src.ledger as ledger_module

    monkeypatch.setattr(ledger_module.os, "write", spy_write)
    ledger = Ledger(tmp_path / "ledger.jsonl")

    for index in range(3):
        ledger.append(_record(f"rec-{index + 1}"))

    assert len(calls) == 3
    assert all(call.endswith(b"\n") for call in calls)
    assert [call.count(b"\n") for call in calls] == [1, 1, 1]


def test_sc7_public_api_has_no_partial_write_surface():
    public_methods = sorted(
        name
        for name, member in inspect.getmembers(Ledger, predicate=inspect.isfunction)
        if not name.startswith("_")
    )

    assert public_methods == ["append", "read_all", "read_lineage", "rebuild_l3_state"]
    assert not any("write" in name for name in public_methods)
    assert inspect.signature(Ledger.append).parameters.keys() == {"self", "record"}


def test_sc7_long_record_still_appends_as_single_write(tmp_path, monkeypatch):
    calls: list[bytes] = []
    real_write = __import__("os").write

    def spy_write(fd, payload):
        calls.append(payload)
        return real_write(fd, payload)

    import src.ledger as ledger_module

    monkeypatch.setattr(ledger_module.os, "write", spy_write)
    ledger = Ledger(tmp_path / "ledger.jsonl")
    record = _record(
        "long-record",
        result_snapshot={"uri": "file:///tmp/" + "x" * 8000, "sha256": "deadbeef"},
    )

    ledger.append(record)

    assert len(calls) == 1
    assert calls[0].endswith(b"\n")
    assert len(calls[0]) > 8000
