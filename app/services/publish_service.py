from __future__ import annotations

import json
from urllib import error, request

from app.services.storage_router import StorageRouter
from app.domain.models import ContentDraft, ImageAsset, PublishPayload, PublishResult


class PublishService:
    def __init__(self, publisher_url: str, dry_run: bool, store: StorageRouter) -> None:
        self.publisher_url = publisher_url.rstrip("/")
        self.dry_run = dry_run
        self.store = store

    def publish(self, draft: ContentDraft, image: ImageAsset, enabled: bool) -> PublishResult:
        payload = PublishPayload(
            title=draft.title,
            body_text=f"{draft.body_text}\n\n{draft.cta_text}",
            hashtags=draft.hashtags,
            images=[image.local_path],
            draft_id=draft.draft_id,
            extra={"cover_text": draft.cover_text},
        )
        self.store.write("publish_payloads", payload, "publish_payload")

        if self.dry_run or not enabled:
            return PublishResult(
                success=True,
                result_status="dry_run",
                note_url=None,
                draft_id=draft.draft_id,
                detail={"reason": "publisher disabled or DRY_RUN=true"},
            )

        body = json.dumps(
            {
                "title": payload.title,
                "body_text": payload.body_text,
                "hashtags": payload.hashtags,
                "images": payload.images,
                "draft_id": payload.draft_id,
                "extra": payload.extra,
            }
        ).encode("utf-8")
        req = request.Request(
            f"{self.publisher_url}/internal/publish/xiaohongshu",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            detail = {"error": str(exc)}
            try:
                body = exc.read().decode("utf-8")
                if body:
                    detail["response_body"] = body
            except Exception:
                pass
            return PublishResult(
                success=False,
                result_status="publisher_error",
                note_url=None,
                draft_id=draft.draft_id,
                detail=detail,
            )
        except error.URLError as exc:
            return PublishResult(
                success=False,
                result_status="publisher_error",
                note_url=None,
                draft_id=draft.draft_id,
                detail={"error": str(exc)},
            )

        return PublishResult(
            success=bool(data.get("success")),
            result_status=data.get("result_status", "unknown"),
            note_url=data.get("note_url"),
            draft_id=draft.draft_id,
            detail=data,
        )
