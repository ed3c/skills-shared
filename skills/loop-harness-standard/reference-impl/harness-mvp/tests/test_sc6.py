from src.envelope import make_envelope
from src.gates import L3Config, L3State, l3_after_record, l3_preflight


def _record(record_id: str, *, result: str, tokens_used: int) -> dict[str, object]:
    return make_envelope(
        id=record_id,
        parentId=None,
        loop_layer="L0",
        task_ref={"packet_id": "SC6", "priority": "high", "passes": False},
        event={"kind": "tool_result", "tool": "poll", "args": {"slot": "A"}},
        exec={
            "command": "poll",
            "exit_code": 0,
            "result_snapshot": result,
            "error_snapshot": None,
        },
        budget={"tokens_used": tokens_used, "usd": 0.0},
    )


def test_sc6_budget_wins_when_budget_dup_and_max_iterations_all_hit():
    config = L3Config(
        max_iterations=2, max_tokens=2, duplicate_threshold=2, duplicate_window=4
    )
    state = L3State()

    first = l3_after_record(state, config, _record("r-1", result="same", tokens_used=1))
    second = l3_after_record(
        state, config, _record("r-2", result="same", tokens_used=2)
    )

    assert first.allowed
    assert not second.allowed
    assert second.exit_code == 20
    assert second.reason == "budget"


def test_sc6_max_iterations_is_preflight_fallback_only():
    config = L3Config(max_iterations=2, duplicate_threshold=3, duplicate_window=4)
    state = L3State(iterations=2)

    decision = l3_preflight(state, config)

    assert not decision.allowed
    assert decision.exit_code == 10
    assert decision.reason == "max_iterations"


def test_sc6_duplicate_alone_triggers_dup_reason():
    config = L3Config(max_iterations=10, duplicate_threshold=2, duplicate_window=4)
    state = L3State()

    first = l3_after_record(state, config, _record("r-1", result="same", tokens_used=1))
    second = l3_after_record(
        state, config, _record("r-2", result="same", tokens_used=1)
    )

    assert first.allowed
    assert not second.allowed
    assert second.exit_code == 21
    assert second.reason == "dup"
