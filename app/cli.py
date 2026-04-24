from __future__ import annotations

import argparse
import json

from app.core.settings import Settings
from app.web_ui import serve_ui
from app.workflows.mvp_pipeline import MvpPipeline
from app.workflows.review_pipeline import ReviewPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ozon promotion MVP scaffold")
    subparsers = parser.add_subparsers(dest="command", required=True)

    collect_parser = subparsers.add_parser("collect-articles", help="Collect article-level source material")
    collect_parser.add_argument("--limit", type=int, default=6, help="How many source articles to collect")

    prepare_parser = subparsers.add_parser(
        "prepare-review",
        help="Collect source articles and generate pending Xiaohongshu review drafts",
    )
    prepare_parser.add_argument("--limit", type=int, default=2, help="How many source articles to transform")

    approve_parser = subparsers.add_parser(
        "approve-review",
        help="Approve a review draft and optionally publish it",
    )
    approve_parser.add_argument("--review-id", required=True, help="Review draft id")
    approve_parser.add_argument("--publish", action="store_true", help="Publish after approval")

    run_parser = subparsers.add_parser("run", help="Run the MVP pipeline")
    run_parser.add_argument("--limit", type=int, default=3, help="How many sample raw items to use")
    run_parser.add_argument(
        "--publish",
        action="store_true",
        help="Call the local publisher service instead of stopping after draft creation",
    )

    serve_parser = subparsers.add_parser("serve-ui", help="Start the local article and publish web UI")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Web UI host")
    serve_parser.add_argument("--port", type=int, default=8020, help="Web UI port")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    settings = Settings.load()
    pipeline = MvpPipeline(settings)
    review_pipeline = ReviewPipeline(settings)

    if args.command == "collect-articles":
        result = pipeline.collect_articles(limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "prepare-review":
        result = review_pipeline.prepare_review_drafts(limit=args.limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "approve-review":
        result = review_pipeline.approve_review_draft(review_id=args.review_id, publish=args.publish)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "run":
        result = pipeline.run(limit=args.limit, publish=args.publish)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "serve-ui":
        serve_ui(settings, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
