import pytest

from src.envelope import make_envelope
from src.gates import L3Config, L3State, l3_after_record


def _record(record_id: str, *, args: dict[str, object], result: str) -> dict[str, object]:
    return make_envelope(
        id=record_id,
        parentId=None,
        loop_layer="L0",
        task_ref={"packet_id": "SC5", "priority": "high", "passes": False},
        event={"kind": "tool_result", "tool": "poll", "args": args},
        exec={"command": "poll", "exit_code": 0, "result_snapshot": result, "error_snapshot": None},
    )


def test_sc5_consecutive_duplicate_kills_on_threshold_step():
    config = L3Config(max_iterations=10, duplicate_threshold=3, duplicate_window=4, max_interleaving=3)
    state = L3State()

    decisions = [
        l3_after_record(state, config, _record(f"r-{index}", args={"slot": "A"}, result="same"))
        for index in range(1, 4)
    ]

    assert [decision.allowed for decision in decisions[:2]] == [True, True]
    assert not decisions[2].allowed
    assert decisions[2].reason == "dup"


def test_sc5_duplicate_window_smaller_than_max_interleaving_is_rejected():
    with pytest.raises(ValueError, match="duplicate_window must be >= max_interleaving"):
        L3Config(duplicate_window=2, max_interleaving=3)


def test_sc5_minimal_window_n_kills_at_threshold_but_leaks_for_n_plus_one():
    config = L3Config(max_iterations=10, duplicate_threshold=2, duplicate_window=3, max_interleaving=3)

    n_state = L3State()
    n_decisions = [
        l3_after_record(n_state, config, _record(f"n-{index}", args={"slot": slot}, result="same"))
        for index, slot in enumerate(["A", "B", "C", "A"], start=1)
    ]

    assert [decision.allowed for decision in n_decisions[:3]] == [True, True, True]
    assert not n_decisions[3].allowed
    assert n_decisions[3].reason == "dup"

    n_plus_one_state = L3State()
    n_plus_one_decisions = [
        l3_after_record(
            n_plus_one_state,
            config,
            _record(f"n+1-{index}", args={"slot": slot}, result="same"),
        )
        for index, slot in enumerate(["A", "B", "C", "D", "A"], start=1)
    ]

    assert all(decision.allowed for decision in n_plus_one_decisions)


def test_sc5_interleaved_duplicate_kills_on_threshold_step():
    config = L3Config(max_iterations=10, duplicate_threshold=2, duplicate_window=4, max_interleaving=4)
    state = L3State()
    decisions = []

    for index, slot in enumerate(["A", "B", "C", "A"], start=1):
        decisions.append(l3_after_record(state, config, _record(f"r-{index}", args={"slot": slot}, result="same")))

    assert [decision.allowed for decision in decisions[:3]] == [True, True, True]
    assert not decisions[3].allowed
    assert decisions[3].reason == "dup"


def test_sc5_polling_with_changing_results_is_not_killed():
    config = L3Config(max_iterations=10, duplicate_threshold=2, duplicate_window=4, max_interleaving=4)
    state = L3State()

    decisions = [
        l3_after_record(state, config, _record(f"r-{index}", args={"slot": "poll"}, result=result))
        for index, result in enumerate(["pending", "working", "done"], start=1)
    ]

    assert all(decision.allowed for decision in decisions)


def test_sc5_retry_with_different_results_is_not_killed():
    config = L3Config(max_iterations=10, duplicate_threshold=2, duplicate_window=4, max_interleaving=4)
    state = L3State()

    decisions = [
        l3_after_record(state, config, _record(f"r-{index}", args={"attempt": 1}, result=result))
        for index, result in enumerate(["timeout", "success"], start=1)
    ]

    assert all(decision.allowed for decision in decisions)
