---
name: social-crawl-tool
description: "Unified social content crawling tool for Douyin, Xiaohongshu, and Kuaishou. Use when Codex needs to collect platform-native raw samples into local folders for later planning, imitation analysis, or content generation. Supports Douyin image posts and videos, Xiaohongshu image posts and videos, and Kuaishou videos. Best for tasks such as: (1) crawling top N search results for a keyword, (2) using material-derived query sets, (3) downloading post images or videos, and (4) producing structured samples.json and downloads_summary.json outputs for downstream agents."
---

# Social Crawl Tool

## Overview

Use this skill to run the project's crawler tool in a stable, repeatable way.
The tool reuses isolated browser profiles, requests human help for login when needed, and writes structured artifacts under `outputs/raw_crawl/`.
This skill is self-contained: the crawler runtime, query planner, browser runtime, and platform collectors live under `skills/social-crawl-tool/src/social_crawl_skill/`.

## Workflow

1. Open the target platform browser through this skill's own launcher script.
2. Choose platform + content mode + keyword strategy.
3. Run the wrapper script in `scripts/run_social_crawl.py`.
4. Inspect `samples.json` and `downloads_summary.json`.
5. If the platform returns login/captcha walls, ask the user to complete verification in the already-open browser and rerun.
6. If you need a reproducible verification log, run `scripts/run_skill_smoke_tests.py` to regenerate `outputs/skill_test_results.json`.

## Supported Modes

- `douyin`:
  Supports `image` and `video`.
- `xiaohongshu`:
  Supports `image` and `video`.
- `kuaishou`:
  Supports `video` only.

## Required Setup

- Use the skill-local browser launcher first:
  `python -X utf8 skills/social-crawl-tool/scripts/browser_open.py --platform douyin`
  `python -X utf8 skills/social-crawl-tool/scripts/browser_open.py --platform xiaohongshu`
  `python -X utf8 skills/social-crawl-tool/scripts/browser_open.py --platform kuaishou`
- The browser window must stay open because the crawler now connects through CDP instead of restarting the profile.
- Browser profiles live under:
  `runtime/browser_profiles/`
- On Windows, prefer `python -X utf8` for both the CLI and the wrapper script.

## Commands

Run through the wrapper script:

```powershell
python -X utf8 skills/social-crawl-tool/scripts/run_social_crawl.py --platform douyin --content-mode image --keyword "跨境电商" --max-items 5
python -X utf8 skills/social-crawl-tool/scripts/run_social_crawl.py --platform douyin --content-mode video --keyword "跨境电商" --max-items 5
python -X utf8 skills/social-crawl-tool/scripts/run_social_crawl.py --platform xiaohongshu --content-mode image --keyword "跨境电商" --max-items 5
python -X utf8 skills/social-crawl-tool/scripts/run_social_crawl.py --platform xiaohongshu --content-mode video --max-items 5
python -X utf8 skills/social-crawl-tool/scripts/run_social_crawl.py --platform kuaishou --content-mode video --keyword "跨境电商" --max-items 5
```

If `--keyword` is omitted, the tool will use the project's material-derived query set.
See `references/parameters.md` for the full parameter contract and `references/output-contract.md` for output files.

Smoke-test runner:

```powershell
python -X utf8 skills/social-crawl-tool/scripts/run_skill_smoke_tests.py --open-browsers --max-items 1
```

Skill-local source tree:

- `src/social_crawl_skill/browser_runtime.py`
- `src/social_crawl_skill/query_planner.py`
- `src/social_crawl_skill/douyin_crawler.py`
- `src/social_crawl_skill/xiaohongshu_crawler.py`
- `src/social_crawl_skill/kuaishou_crawler.py`
- `src/social_crawl_skill/social_crawl_tool.py`

## Human Assist

If a platform needs login or captcha:
- keep the existing browser window open,
- ask the user to complete verification there,
- rerun the same command after confirmation.

Do not rotate profiles between manual and automated runs by relaunching fresh browser instances for the same platform. Reuse the existing CDP-connected browser.

## Output Contract

Each run writes a platform-specific folder under:
- `outputs/raw_crawl/douyin/`
- `outputs/raw_crawl/xiaohongshu/`
- `outputs/raw_crawl/kuaishou/`

Expected top-level artifacts:
- `samples.json`
- `downloads_summary.json`
- per-query `page.html`
- per-query `raw_responses.json`
- per-item folders with `title.txt`, `metadata.json`, and media files

## Notes

- Recommended crawl entrypoints are:
  `python -X utf8 skills/social-crawl-tool/scripts/browser_open.py --platform <platform>`
  `python -X utf8 skills/social-crawl-tool/scripts/run_social_crawl.py ...`
- Use `douyin` and `xiaohongshu` for both image and video collection.
- Use `kuaishou` only for video collection.
- Prefer `max-items 5` for user-facing validation runs unless the user explicitly asks for more.
