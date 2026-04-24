#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def _build_cases(script_path: Path, max_items: int) -> list[dict[str, object]]:
    return [
        {
            "case_id": "douyin_image_keyword",
            "platform": "douyin",
            "content_mode": "image",
            "keyword": "跨境电商",
            "argv": [
                sys.executable,
                "-X",
                "utf8",
                str(script_path),
                "--platform",
                "douyin",
                "--content-mode",
                "image",
                "--keyword",
                "跨境电商",
                "--max-items",
                str(max_items),
            ],
        },
        {
            "case_id": "douyin_video_keyword",
            "platform": "douyin",
            "content_mode": "video",
            "keyword": "跨境电商",
            "argv": [
                sys.executable,
                "-X",
                "utf8",
                str(script_path),
                "--platform",
                "douyin",
                "--content-mode",
                "video",
                "--keyword",
                "跨境电商",
                "--max-items",
                str(max_items),
            ],
        },
        {
            "case_id": "xiaohongshu_image_keyword",
            "platform": "xiaohongshu",
            "content_mode": "image",
            "keyword": "跨境电商",
            "argv": [
                sys.executable,
                "-X",
                "utf8",
                str(script_path),
                "--platform",
                "xiaohongshu",
                "--content-mode",
                "image",
                "--keyword",
                "跨境电商",
                "--max-items",
                str(max_items),
            ],
        },
        {
            "case_id": "xiaohongshu_video_material_queries",
            "platform": "xiaohongshu",
            "content_mode": "video",
            "keyword": None,
            "argv": [
                sys.executable,
                "-X",
                "utf8",
                str(script_path),
                "--platform",
                "xiaohongshu",
                "--content-mode",
                "video",
                "--max-items",
                str(max_items),
            ],
        },
        {
            "case_id": "kuaishou_video_keyword",
            "platform": "kuaishou",
            "content_mode": "video",
            "keyword": "跨境电商",
            "argv": [
                sys.executable,
                "-X",
                "utf8",
                str(script_path),
                "--platform",
                "kuaishou",
                "--content-mode",
                "video",
                "--keyword",
                "跨境电商",
                "--max-items",
                str(max_items),
            ],
        },
    ]


def _run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        argv,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        env=env,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run reproducible smoke tests for the social crawl skill.")
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument("--output", default=None)
    parser.add_argument("--max-items", type=int, default=1)
    parser.add_argument("--open-browsers", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output_path = Path(args.output).resolve() if args.output else root / "outputs" / "skill_test_results.json"
    wrapper_script = Path(__file__).resolve().parent / "run_social_crawl.py"
    browser_open_script = Path(__file__).resolve().parent / "browser_open.py"

    results: list[dict[str, object]] = []
    cases = _build_cases(wrapper_script, max_items=args.max_items)

    opened_platforms: set[str] = set()
    for case in cases:
        platform = str(case["platform"])
        if args.open_browsers and platform not in opened_platforms:
            browser_open_argv = [
                sys.executable,
                "-X",
                "utf8",
                str(browser_open_script),
                "--platform",
                platform,
            ]
            open_result = _run(browser_open_argv, cwd=root)
            results.append(
                {
                    "case_id": f"{platform}_browser_open",
                    "platform": platform,
                    "step": "browser-open",
                    "argv": browser_open_argv,
                    "display_command": subprocess.list2cmdline(browser_open_argv),
                    "returncode": open_result.returncode,
                    "stdout": open_result.stdout,
                    "stderr": open_result.stderr,
                }
            )
            opened_platforms.add(platform)

        completed = _run(list(case["argv"]), cwd=root)
        results.append(
            {
                "case_id": case["case_id"],
                "platform": case["platform"],
                "content_mode": case["content_mode"],
                "keyword": case["keyword"],
                "argv": case["argv"],
                "display_command": subprocess.list2cmdline(list(case["argv"])),
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(output_path))


if __name__ == "__main__":
    main()
