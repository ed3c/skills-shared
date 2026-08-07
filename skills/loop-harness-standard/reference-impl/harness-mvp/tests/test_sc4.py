from src.gates import L3Config
from src.ledger import Ledger
from src.loop import run_loop


def _executor_from(results):
    iterator = iter(results)

    def _executor(_step):
        return next(iterator)

    return _executor


def test_sc4_resume_rebuilds_from_jsonl_and_finishes(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    config = L3Config(
        max_iterations=5, duplicate_threshold=3, duplicate_window=4, max_tokens=10
    )
    steps = [{"tool": "poll", "args": {"slot": slot}} for slot in ("A", "B", "C")]

    first_exit = run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=steps[:2],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-1",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "a",
                    "budget": {"tokens_used": 2, "usd": 0.1},
                },
                {
                    "id": "r-2",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "b",
                    "budget": {"tokens_used": 3, "usd": 0.2},
                },
            ]
        ),
        l3_config=config,
    )

    resumed_exit = run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=steps[2:],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-3",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "c",
                    "budget": {"tokens_used": 1, "usd": 0.05},
                },
            ]
        ),
        l3_config=config,
    )

    records = ledger.read_all()

    assert first_exit == 0
    assert resumed_exit == 0
    assert [record["id"] for record in records] == ["r-1", "r-2", "r-3"]
    assert [record["parentId"] for record in records] == [None, "r-1", "r-2"]


def test_sc4_rebuilt_duplicate_window_kills_on_combined_threshold(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    config = L3Config(
        max_iterations=6, duplicate_threshold=2, duplicate_window=3, max_interleaving=3
    )
    steps = [{"tool": "poll", "args": {"slot": slot}} for slot in ("A", "B", "C", "A")]

    run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=steps[:3],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-1",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "same",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
                {
                    "id": "r-2",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "same",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
                {
                    "id": "r-3",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "same",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
            ]
        ),
        l3_config=config,
    )

    resumed_exit = run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=steps[3:],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-4",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "same",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
            ]
        ),
        l3_config=config,
    )

    assert resumed_exit == 21


def test_sc4_resume_keeps_cumulative_budget_instead_of_resetting(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    config = L3Config(
        max_iterations=5, duplicate_threshold=3, duplicate_window=4, max_tokens=4
    )

    run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "A"}}],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-1",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "a",
                    "budget": {"tokens_used": 3, "usd": 0.1},
                },
            ]
        ),
        l3_config=config,
    )

    resumed_exit = run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "B"}}],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-2",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "b",
                    "budget": {"tokens_used": 1, "usd": 0.1},
                },
            ]
        ),
        l3_config=config,
    )

    records = ledger.read_all()

    assert resumed_exit == 20
    assert records[-1]["budget"]["tokens_used"] == 4


def test_sc4_parent_chain_can_be_rebuilt_after_resume(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    config = L3Config(max_iterations=5, duplicate_threshold=3, duplicate_window=4)

    run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "A"}} for _ in range(2)],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-1",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "a",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
                {
                    "id": "r-2",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "b",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
            ]
        ),
        l3_config=config,
    )
    run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "C"}}],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-3",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "c",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
            ]
        ),
        l3_config=config,
    )

    lineage = ledger.read_lineage("r-3")

    assert [record["id"] for record in lineage] == ["r-1", "r-2", "r-3"]


def test_sc4_resume_accepts_replayed_thresholds_and_returns_pending_stop(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")

    run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "A"}} for _ in range(2)],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-1",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "same",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
                {
                    "id": "r-2",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "same",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
            ]
        ),
        l3_config=L3Config(max_iterations=5, duplicate_threshold=3, duplicate_window=4),
    )

    resumed_exit = run_loop(
        task_packet={"packet_id": "SC4", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "C"}}],
        ledger=ledger,
        executor=_executor_from(
            [
                {
                    "id": "r-3",
                    "command": "poll",
                    "exit_code": 0,
                    "result_snapshot": "c",
                    "budget": {"tokens_used": 1, "usd": 0.0},
                },
            ]
        ),
        l3_config=L3Config(max_iterations=5, duplicate_threshold=2, duplicate_window=4),
    )

    assert resumed_exit == 21
