#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the unified social crawl tool.")
    parser.add_argument("--platform", required=True, choices=["douyin", "xiaohongshu", "kuaishou"])
    parser.add_argument("--content-mode", default="auto", choices=["auto", "image", "video"])
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--max-items", type=int, default=5)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--no-material-queries", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skill_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(skill_root / "src"))

    from social_crawl_skill.console_encoding import configure_utf8_stdio
    from social_crawl_skill.social_crawl_tool import SocialCrawlTool

    configure_utf8_stdio()
    tool = SocialCrawlTool(root)
    result = tool.run(
        platform=args.platform,
        keyword=args.keyword,
        limit=args.max_items,
        content_mode=args.content_mode,
        use_material_queries=not args.no_material_queries,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
