"""Append-only JSONL ledger for unified envelopes."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .envelope import validate_envelope
from .gates import L3Config, L3State, l3_after_record


class Ledger:
    """Append records as one complete JSON line per single ``os.write`` call."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def append(self, record: dict[str, Any]) -> None:
        validate_envelope(record)
        self._validate_dag(self.read_all(), record)
        line = json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        payload = line.encode("utf-8")
        flags = os.O_APPEND | os.O_CREAT | os.O_WRONLY
        fd = os.open(self.path, flags, 0o644)
        try:
            written = os.write(fd, payload)
        finally:
            os.close(fd)
        if written != len(payload):
            raise OSError(f"short ledger write: {written}/{len(payload)} bytes")

    def read_all(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.endswith("\n"):
                    raise ValueError(
                        f"ledger line {line_number} is not newline-terminated"
                    )
                record = json.loads(line)
                validate_envelope(record)
                self._validate_dag(records, record)
                records.append(record)
        return records

    def read_lineage(self, record_id: str) -> list[dict[str, Any]]:
        records = self.read_all()
        by_id = {record["id"]: record for record in records}
        if record_id not in by_id:
            raise KeyError(f"record id not found: {record_id}")

        lineage: list[dict[str, Any]] = []
        current = by_id[record_id]
        while True:
            lineage.append(current)
            parent_id = current["parentId"]
            if parent_id is None:
                break
            current = by_id[parent_id]
        lineage.reverse()
        return lineage

    def rebuild_l3_state(self, config: L3Config) -> tuple[L3State, str | None]:
        records = self.read_all()
        state = L3State()
        previous_id: str | None = None

        for index, record in enumerate(records):
            if previous_id is not None and record["parentId"] != previous_id:
                raise ValueError("ledger cannot resume: latest chain is not contiguous")

            decision = l3_after_record(state, config, record)
            if not decision.allowed and index != len(records) - 1:
                raise ValueError(
                    f"ledger cannot resume with supplied L3 config: stop_reason={decision.reason} at record {record['id']}"
                )
            previous_id = record["id"]

        return state, previous_id

    def _validate_dag(
        self, existing: list[dict[str, Any]], record: dict[str, Any]
    ) -> None:
        seen_ids = {item["id"] for item in existing}
        if record["id"] in seen_ids:
            raise ValueError(f"duplicate record id: {record['id']}")
        parent_id = record["parentId"]
        if parent_id is not None and parent_id not in seen_ids:
            raise ValueError(f"parentId not found in ledger: {parent_id}")
