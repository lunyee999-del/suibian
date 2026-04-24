from __future__ import annotations

from dataclasses import asdict

from app.collectors.domestic_article_collector import DomesticArticleCollector
from app.core.settings import Settings
from app.domain.models import ReviewDraft
from app.services.cover_layout_service import CoverLayoutService
from app.services.image_service import ImageService
from app.services.llm_rewrite_service import LlmRewriteService
from app.services.prompt_loader import PromptLoader
from app.services.publish_service import PublishService
from app.services.review_draft_repository import ReviewDraftRepository
from app.services.storage_router import StorageRouter
from app.services.visual_prompt_service import VisualPromptService


class ReviewPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        prompt_loader = PromptLoader(settings.prompts_dir)
        self.collector = DomesticArticleCollector(settings.base_dir / "config" / "domestic_articles.example.json")
        self.rewriter = LlmRewriteService(settings, prompt_loader)
        self.cover_layout_service = CoverLayoutService(settings, prompt_loader)
        self.visual_prompt_service = VisualPromptService(settings, prompt_loader)
        self.image_service = ImageService(
            settings.storage_dir,
            settings.wanx_model,
            settings.dry_run,
            api_key=settings.wanx_api_key,
            base_url=settings.llm_base_url,
            provider=settings.image_provider,
            ark_api_key=settings.ark_api_key,
            ark_base_url=settings.ark_image_base_url,
            ark_model=settings.ark_image_model,
        )
        self.review_repo = ReviewDraftRepository(settings.storage_dir)
        self.store = StorageRouter(settings)
        self.publish_service = PublishService(settings.publisher_url, settings.dry_run, self.store)

    def prepare_review_drafts(self, limit: int) -> dict:
        articles = self.collector.fetch_articles(limit=limit)
        article_store = self.store.write("source_articles", articles, "source_articles")
        saved_items = []

        for article in articles:
            content_draft = self.rewriter.generate_from_article(article)
            content_draft.cover_layout = self.cover_layout_service.generate_from_article(article, content_draft)
            content_draft.image_prompt = self.visual_prompt_service.generate_from_article(article, content_draft)
            image_asset = self.image_service.generate_cover(content_draft)
            review_draft = ReviewDraft(
                source_article_id=article.article_id,
                source_title=article.title,
                source_url=article.source_url,
                source_site_name=article.site_name,
                source_category_tag=article.category_tag,
                content_draft=content_draft,
                image_asset=image_asset,
                review_status="pending_review",
                llm_provider=self.rewriter.provider,
                llm_model=self.rewriter.model,
            )
            file_path = self.review_repo.save(review_draft)
            saved_items.append(
                {
                    "review_id": review_draft.review_id,
                    "draft_id": review_draft.content_draft.draft_id,
                    "title": review_draft.content_draft.title,
                    "source_title": review_draft.source_title,
                    "review_path": str(file_path),
                    "image_path": review_draft.image_asset.local_path,
                    "review_status": review_draft.review_status,
                }
            )

        return {
            "article_count": len(articles),
            "article_store": article_store,
            "errors": self.collector.last_errors,
            "items": saved_items,
        }

    def approve_review_draft(self, review_id: str, publish: bool) -> dict:
        review_draft = self.review_repo.get(review_id)
        review_draft.review_status = "approved"
        publish_result = None
        if publish:
            result = self.publish_service.publish(
                review_draft.content_draft,
                review_draft.image_asset,
                enabled=True,
            )
            publish_result = asdict(result)
            if result.success and result.result_status == "published":
                review_draft.review_status = "published"
            elif result.result_status == "dry_run":
                review_draft.review_status = "approved_dry_run"
            review_draft.publish_result = publish_result

        file_path = self.review_repo.save(review_draft)
        return {
            "review_id": review_draft.review_id,
            "review_status": review_draft.review_status,
            "review_path": str(file_path),
            "publish_result": publish_result,
        }
