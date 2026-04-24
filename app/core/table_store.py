from __future__ import annotations

from dataclasses import asdict, is_dataclass
import csv
import json
from pathlib import Path
from typing import Any


class TableStore:
    def __init__(self, storage_dir: Path) -> None:
        self.tables_dir = storage_dir / "tables"
        self.tables_dir.mkdir(parents=True, exist_ok=True)

    def write_snapshot(self, bucket: str, payload: Any) -> Path | None:
        normalized = self._normalize(payload)
        if isinstance(normalized, list):
            rows = [self._rowify(item) for item in normalized]
        elif isinstance(normalized, dict):
            rows = [self._rowify(normalized)]
        else:
            return None

        if not rows:
            return None

        headers = sorted({key for row in rows for key in row.keys()})
        file_path = self.tables_dir / f"{bucket}_latest.csv"
        with file_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
        return file_path

    def _normalize(self, payload: Any) -> Any:
        if is_dataclass(payload):
            return asdict(payload)
        if isinstance(payload, list):
            return [self._normalize(item) for item in payload]
        if isinstance(payload, dict):
            return {key: self._normalize(value) for key, value in payload.items()}
        if hasattr(payload, "__dict__"):
            return self._normalize(vars(payload))
        return payload

    def _rowify(self, item: dict[str, Any]) -> dict[str, str]:
        row: dict[str, str] = {}
        for key, value in item.items():
            if value is None:
                row[key] = ""
            elif isinstance(value, (str, int, float, bool)):
                row[key] = str(value)
            else:
                row[key] = json.dumps(value, ensure_ascii=False)
        return row
