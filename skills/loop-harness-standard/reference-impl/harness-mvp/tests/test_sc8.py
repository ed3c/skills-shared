from src.envelope import make_envelope
from src.gates import l4_after_record
from src.ledger import Ledger


def _record(
    record_id: str,
    *,
    event_kind: str,
    exit_code: int = 0,
    next_action: str | None = None,
    current_diff: str | None = None,
    error_snapshot: object = None,
) -> dict[str, object]:
    return make_envelope(
        id=record_id,
        parentId=None,
        loop_layer="L4",
        task_ref={"packet_id": "SC8", "priority": "high", "passes": False},
        event={"kind": event_kind, "tool": "judge", "args": {"source": "proxy"}},
        exec={
            "command": "judge",
            "exit_code": exit_code,
            "result_snapshot": {
                "verdict": "warn" if event_kind == "judge_warning" else "pass"
            },
            "error_snapshot": error_snapshot,
        },
        handoff={"current_diff": current_diff, "next_action": next_action},
    )


def test_sc8_deterministic_failure_hard_blocks():
    record = _record(
        "det-fail",
        event_kind="verify",
        exit_code=2,
        error_snapshot={"message": "pytest red"},
    )

    decision = l4_after_record(record)

    assert not decision.allowed
    assert decision.exit_code == 30
    assert decision.reason == "l4_unhandled_exec_failure"


def test_sc8_proxy_warning_does_not_block_and_persists_in_ledger(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    record = _record(
        "warn-only",
        event_kind="judge_warning",
        current_diff="judge warned about weak evidence",
        error_snapshot={"warning": "needs human admit"},
    )

    ledger.append(record)
    decision = l4_after_record(record)
    persisted = ledger.read_all()

    assert decision.allowed
    assert decision.exit_code == 0
    assert decision.reason == "proxy_warning"
    assert persisted[0]["event"]["kind"] == "judge_warning"
    assert persisted[0]["handoff"]["current_diff"] == "judge warned about weak evidence"


def test_sc8_hard_block_wins_when_warning_and_deterministic_failure_coexist():
    record = _record(
        "warn-and-fail",
        event_kind="judge_warning",
        exit_code=2,
        error_snapshot={"message": "mypy red"},
    )

    decision = l4_after_record(record)

    assert not decision.allowed
    assert decision.exit_code == 30
    assert decision.reason == "l4_unhandled_exec_failure"


def test_sc8_no_warning_and_no_failure_passes_cleanly():
    record = _record("clean-pass", event_kind="verify")

    decision = l4_after_record(record)

    assert decision.allowed
    assert decision.exit_code == 0
    assert decision.reason is None
