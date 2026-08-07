import json

import pytest

from src.envelope import EnvelopeError, make_envelope
from src.gates import L3Config, L3State, l3_after_record, l4_after_record
from src.ledger import Ledger
from src.loop import run_loop


def test_sc1_envelope_enters_ledger_gates_emit_exit_code(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")

    exit_code = run_loop(
        task_packet={"packet_id": "SC1", "priority": "high"},
        steps=[{"tool": "verify", "args": {"mode": "fast"}}],
        ledger=ledger,
        executor=lambda step: {
            "id": "rec-1",
            "command": "bash verify.sh --fast",
            "exit_code": 0,
            "result_snapshot": "VERIFY: PASS",
            "budget": {"tokens_used": 1, "usd": 0.0},
        },
        l3_config=L3Config(max_iterations=3, max_tokens=10, duplicate_threshold=3, duplicate_window=8),
        git_commit_sha="abc123",
    )

    assert exit_code == 0
    records = ledger.read_all()
    assert len(records) == 1
    assert records[0]["id"] == "rec-1"
    assert records[0]["parentId"] is None
    assert records[0]["exec"]["result_snapshot"] == "VERIFY: PASS"


def test_sc1_l4_blocks_nonzero_exit_without_handled_handoff():
    record = make_envelope(
        id="bad-1",
        parentId=None,
        loop_layer="L0",
        task_ref={"packet_id": "SC1", "priority": "high", "passes": False},
        event={"kind": "verify"},
        exec={
            "command": "bash verify.sh --fast",
            "exit_code": 2,
            "result_snapshot": None,
            "error_snapshot": "pytest red",
        },
    )

    decision = l4_after_record(record)

    assert not decision.allowed
    assert decision.exit_code == 30
    assert decision.reason == "l4_unhandled_exec_failure"


def test_sc1_l3_budget_wins_over_duplicate_when_both_hit():
    config = L3Config(max_iterations=5, max_tokens=2, duplicate_threshold=2, duplicate_window=8)
    state = L3State()
    record = make_envelope(
        id="dup-budget",
        parentId=None,
        loop_layer="L0",
        task_ref={"packet_id": "SC1", "priority": "high", "passes": False},
        event={"kind": "tool_result", "tool": "poll", "args": {"id": 1}},
        exec={"command": "poll", "exit_code": 0, "result_snapshot": "same", "error_snapshot": None},
        budget={"tokens_used": 2, "usd": 0.0},
    )

    assert l3_after_record(state, config, record).reason == "budget"
    assert l3_after_record(state, config, record).reason == "budget"


def test_sc1_l3_interleaved_duplicate_uses_per_signature_window():
    config = L3Config(max_iterations=10, duplicate_threshold=2, duplicate_window=3, max_interleaving=3)
    state = L3State()
    decisions = []

    for index, result in enumerate(["A", "B", "C", "A"], start=1):
        record = make_envelope(
            id=f"r-{index}",
            parentId=None,
            loop_layer="L0",
            task_ref={"packet_id": "SC1", "priority": "high", "passes": False},
            event={"kind": "tool_result", "tool": "poll", "args": {"slot": result}},
            exec={"command": "poll", "exit_code": 0, "result_snapshot": "same", "error_snapshot": None},
        )
        decisions.append(l3_after_record(state, config, record))

    assert decisions[-1].reason == "dup"


def test_sc1_ledger_append_uses_one_os_write_for_complete_line(tmp_path, monkeypatch):
    calls = []
    real_write = __import__("os").write

    def spy_write(fd, payload):
        calls.append(payload)
        return real_write(fd, payload)

    import src.ledger as ledger_module

    monkeypatch.setattr(ledger_module.os, "write", spy_write)
    ledger = Ledger(tmp_path / "ledger.jsonl")
    record = make_envelope(
        id="one-write",
        parentId=None,
        loop_layer="L0",
        task_ref={"packet_id": "SC1", "priority": "high", "passes": False},
        event={"kind": "tool_result"},
        exec={"command": "noop", "exit_code": 0, "result_snapshot": "ok", "error_snapshot": None},
    )

    ledger.append(record)

    assert len(calls) == 1
    assert calls[0].endswith(b"\n")
    parsed = json.loads(calls[0])
    assert parsed["id"] == "one-write"


def test_sc1_envelope_rejects_schema_drift():
    record = make_envelope(
        id="valid",
        parentId=None,
        loop_layer="L0",
        task_ref={"packet_id": "SC1", "priority": "high", "passes": False},
        event={"kind": "tool_result"},
        exec={"command": "noop", "exit_code": 0, "result_snapshot": "ok", "error_snapshot": None},
    )
    record["extra"] = "not in ssot"

    with pytest.raises(EnvelopeError):
        Ledger("/tmp/unused.jsonl").append(record)
