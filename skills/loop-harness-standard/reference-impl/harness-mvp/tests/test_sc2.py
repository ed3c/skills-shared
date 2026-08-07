import inspect

from src.gates import L3Config
from src.ledger import Ledger
from src.loop import run_loop
import src.loop as loop_module


def test_sc2_event_stream_order_stays_complete_across_retry_and_next_step(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    config = L3Config(max_iterations=6, duplicate_threshold=3, duplicate_window=8)
    steps = [
        {"tool": "fetch", "args": {"slot": "A"}, "max_attempts": 2},
        {"tool": "verify", "args": {"mode": "fast"}},
    ]
    calls = {"count": 0}

    def executor(step):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("temporary fetch failure")
        if calls["count"] == 2:
            return {
                "id": "retry-ok",
                "command": "fetch",
                "exit_code": 0,
                "result_snapshot": {"status": "ok", "slot": step["args"]["slot"]},
                "budget": {"tokens_used": 1, "usd": 0.0},
            }
        return {
            "id": "verify-ok",
            "command": "verify",
            "exit_code": 0,
            "result_snapshot": "PASS",
            "budget": {"tokens_used": 1, "usd": 0.0},
        }

    exit_code = run_loop(
        task_packet={"packet_id": "SC2", "priority": "high"},
        steps=steps,
        ledger=ledger,
        executor=executor,
        l3_config=config,
    )

    records = ledger.read_all()

    assert exit_code == 0
    assert [record["event"]["kind"] for record in records] == [
        "tool_error",
        "tool_result",
        "tool_result",
    ]
    assert [record["event"]["args"]["attempt"] for record in records] == [1, 2, 1]
    assert [record["parentId"] for record in records] == [
        None,
        records[0]["id"],
        "retry-ok",
    ]


def test_sc2_executor_exception_retries_then_succeeds(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    attempts = {"count": 0}

    def executor(_step):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise ValueError("retry me")
        return {
            "id": "success-after-retry",
            "command": "poll",
            "exit_code": 0,
            "result_snapshot": "done",
            "budget": {"tokens_used": 2, "usd": 0.0},
        }

    exit_code = run_loop(
        task_packet={"packet_id": "SC2", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "A"}, "max_attempts": 2}],
        ledger=ledger,
        executor=executor,
        l3_config=L3Config(max_iterations=4, duplicate_threshold=3, duplicate_window=8),
    )

    records = ledger.read_all()

    assert exit_code == 0
    assert attempts["count"] == 2
    assert len(records) == 2
    assert records[0]["handoff"]["next_action"] == "handled"
    assert records[1]["exec"]["exit_code"] == 0


def test_sc2_retry_exhaustion_writes_failure_envelope_and_blocks_in_l4(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")

    def executor(_step):
        raise RuntimeError("still broken")

    exit_code = run_loop(
        task_packet={"packet_id": "SC2", "priority": "high"},
        steps=[{"tool": "poll", "args": {"slot": "A"}, "max_attempts": 2}],
        ledger=ledger,
        executor=executor,
        l3_config=L3Config(max_iterations=4, duplicate_threshold=3, duplicate_window=8),
    )

    records = ledger.read_all()

    assert exit_code == 30
    assert len(records) == 2
    assert [record["exec"]["exit_code"] for record in records] == [1, 1]
    assert records[0]["handoff"]["next_action"] == "handled"
    assert records[1]["handoff"]["next_action"] is None
    assert records[1]["exec"]["error_snapshot"]["message"] == "still broken"


def test_sc2_l0_module_stays_pure_without_planning_or_orchestration_symbols():
    params = tuple(inspect.signature(loop_module.run_loop).parameters)

    assert params == (
        "task_packet",
        "steps",
        "ledger",
        "executor",
        "l3_config",
        "parent_id",
        "git_commit_sha",
    )
    assert not hasattr(loop_module, "plan")
    assert not hasattr(loop_module, "planner")
    assert not hasattr(loop_module, "subagent")
    assert not hasattr(loop_module, "orchestrate")
    assert not hasattr(loop_module, "orchestrator")
