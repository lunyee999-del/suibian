from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path

from app.core.table_store import TableStore
from app.domain.models import ContentDraft, ImageAsset, ReviewDraft


class ReviewDraftRepository:
    def __init__(self, storage_dir: Path) -> None:
        self.review_dir = storage_dir / "review_drafts"
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.table_store = TableStore(storage_dir)

    def save(self, review_draft: ReviewDraft) -> Path:
        file_path = self.review_dir / f"{review_draft.review_id}.json"
        file_path.write_text(
            json.dumps(asdict(review_draft), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self.table_store.write_snapshot("review_drafts", self.list_all())
        return file_path

    def list_all(self) -> list[ReviewDraft]:
        drafts: list[ReviewDraft] = []
        for file_path in sorted(self.review_dir.glob("*.json")):
            drafts.append(self._load_dict(json.loads(file_path.read_text(encoding="utf-8"))))
        return drafts

    def get(self, review_id: str) -> ReviewDraft:
        file_path = self.review_dir / f"{review_id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"review draft not found: {review_id}")
        return self._load_dict(json.loads(file_path.read_text(encoding="utf-8")))

    def _load_dict(self, payload: dict) -> ReviewDraft:
        return ReviewDraft(
            source_article_id=payload["source_article_id"],
            source_title=payload["source_title"],
            source_url=payload["source_url"],
            source_site_name=payload["source_site_name"],
            source_category_tag=payload["source_category_tag"],
            content_draft=ContentDraft(**payload["content_draft"]),
            image_asset=ImageAsset(**payload["image_asset"]),
            review_status=payload["review_status"],
            llm_provider=payload["llm_provider"],
            llm_model=payload["llm_model"],
            review_notes=payload.get("review_notes"),
            publish_result=payload.get("publish_result"),
            generated_at=payload["generated_at"],
            review_id=payload["review_id"],
        )
