#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Open a platform browser for the social crawl skill.")
    parser.add_argument("--platform", required=True, choices=["douyin", "xiaohongshu", "kuaishou"])
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    args = parser.parse_args()

    root = Path(args.root).resolve()
    skill_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(skill_root / "src"))

    from social_crawl_skill.browser_runtime import BrowserRuntime
    from social_crawl_skill.console_encoding import configure_utf8_stdio

    configure_utf8_stdio()
    runtime = BrowserRuntime(root)
    print(json.dumps(runtime.launch_manual_browser(args.platform), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
