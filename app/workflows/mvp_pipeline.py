from __future__ import annotations

from app.collectors.domestic_article_collector import DomesticArticleCollector
from app.core.settings import Settings
from app.services.content_service import ContentService
from app.services.image_service import ImageService
from app.services.prompt_loader import PromptLoader
from app.services.publish_service import PublishService
from app.services.storage_router import StorageRouter
from app.services.topic_service import TopicService


class MvpPipeline:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.store = StorageRouter(settings)
        self.article_collector = DomesticArticleCollector(
            settings.base_dir / "config" / "domestic_articles.example.json",
        )
        self.topic_service = TopicService()
        self.content_service = ContentService(PromptLoader(settings.prompts_dir))
        self.image_service = ImageService(
            settings.storage_dir,
            settings.wanx_model,
            settings.dry_run,
            api_key=settings.wanx_api_key,
            base_url=settings.llm_base_url,
        )
        self.publish_service = PublishService(
            settings.publisher_url,
            settings.dry_run,
            self.store,
        )

    def collect_articles(self, limit: int) -> dict:
        articles = self.article_collector.fetch_articles(limit=limit)
        article_store = self.store.write("source_articles", articles, "source_articles")
        return {
            "article_count": len(articles),
            "article_store": article_store,
            "errors": self.article_collector.last_errors,
        }

    def run(self, limit: int, publish: bool) -> dict:
        articles = self.article_collector.fetch_articles(limit=limit)
        article_store = self.store.write("source_articles", articles, "source_articles")
        raw_items = self.article_collector.to_raw_items(articles)
        raw_store = self.store.write("raw", raw_items, "raw_items")

        topics = self.topic_service.build_topics(raw_items)
        topic_store = self.store.write("topics", topics, "trend_topics")

        candidates = self.topic_service.build_candidates(topics)
        results = []

        for candidate in candidates:
            draft = self.content_service.generate(candidate)
            draft_store = self.store.write("drafts", draft, "draft")
            image = self.image_service.generate_cover(draft)
            publish_result = self.publish_service.publish(draft, image, enabled=publish)
            results.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "draft_id": draft.draft_id,
                    "draft_store": draft_store,
                    "image_path": image.local_path,
                    "publish_status": publish_result.result_status,
                }
            )

        return {
            "article_count": len(articles),
            "raw_count": len(raw_items),
            "topic_count": len(topics),
            "candidate_count": len(candidates),
            "article_store": article_store,
            "raw_store": raw_store,
            "topic_store": topic_store,
            "errors": self.article_collector.last_errors,
            "results": results,
        }
