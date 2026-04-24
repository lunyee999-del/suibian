from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any
from uuid import uuid4


class JsonStore:
    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir

    def write(self, bucket: str, payload: Any, prefix: str) -> Path:
        target_dir = self.storage_dir / bucket
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        file_path = target_dir / f"{prefix}_{stamp}_{uuid4().hex[:8]}.json"
        normalized = self._normalize(payload)
        file_path.write_text(
            json.dumps(normalized, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return file_path

    def _normalize(self, payload: Any) -> Any:
        if is_dataclass(payload):
            return asdict(payload)
        if isinstance(payload, dict):
            return {key: self._normalize(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._normalize(item) for item in payload]
        if hasattr(payload, "__dict__"):
            return self._normalize(vars(payload))
        return payload

