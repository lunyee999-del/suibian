from __future__ import annotations

from typing import Any

from app.core.json_store import JsonStore
from app.core.settings import Settings
from app.core.table_store import TableStore


class StorageRouter:
    def __init__(self, settings: Settings) -> None:
        self.local_store = JsonStore(settings.storage_dir)
        self.table_store = TableStore(settings.storage_dir)
        self.storage_backend = settings.storage_backend

    def write(self, bucket: str, payload: Any, prefix: str):
        local_path = self.local_store.write(bucket, payload, prefix)
        table_path = self.table_store.write_snapshot(bucket, payload)
        return {
            "local_path": str(local_path),
            "table_path": str(table_path) if table_path else None,
            "storage_backend": self.storage_backend,
        }
