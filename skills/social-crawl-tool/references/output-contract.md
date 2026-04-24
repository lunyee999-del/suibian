# Output Contract

The crawler writes structured outputs under `outputs/raw_crawl/<platform>/...`.
The skill smoke-test runner writes reproducible verification logs to `outputs/skill_test_results.json`.

## Top-level files

- `samples.json`
  Final selected items for the run
- `downloads_summary.json`
  Final downloaded items with local paths
- `outputs/skill_test_results.json`
  Reproducible smoke-test report with `argv`, `display_command`, `returncode`, `stdout`, and `stderr`

## Per-query debug files

- `page.html`
- `page.png` when available
- `raw_responses.json`

## Per-item files

- `title.txt`
- `metadata.json`
- Media files:
  - image posts: `image_01.*`, `image_02.*`, ...
  - videos: `*.mp4`
