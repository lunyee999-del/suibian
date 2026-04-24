# Parameters

## Required

- `--platform`
  Supported values: `douyin`, `xiaohongshu`, `kuaishou`

## Optional

- `--content-mode`
  Allowed values:
  - `image`
  - `video`
  - `auto`
  Rules:
  - `douyin`: use `image` or `video`
  - `xiaohongshu`: use `image` or `video`
  - `kuaishou`: use `video`

- `--keyword`
  When omitted, the crawler uses material-derived queries from `planDOC/umlink资料`.

- `--max-items`
  Maximum number of final unique results to keep.

- `--no-material-queries`
  Disable material-derived query expansion and only use the provided keyword.

## Related Scripts

- `scripts/browser_open.py`
  Open a persistent browser instance for one platform through the skill-local runtime.

- `scripts/run_social_crawl.py`
  Run the unified crawler through the skill-local `social_crawl_skill` package.

- `scripts/run_skill_smoke_tests.py`
  Rebuild `outputs/skill_test_results.json` with reproducible UTF-8-safe logs.
