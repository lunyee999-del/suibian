# Agent Team Playground

这是一个按你给出的《分层架构方案》和《开发实施清单》落下来的最小可运行版 `agent team`。

当前版本包含：

- `Task Kernel`：任务创建、状态推进、schema 校验、审计日志
- `Production Agents`：研究、图文、视频三个生产 agent
- `QA / Review / Publish Agents`：自动质检、人工审核、受控发布
- `Provider Abstraction`：支持 mock 与 Google GenAI 两种 provider

## 快速运行

```powershell
python -m pip install -e .
python -m agent_team.cli demo --provider mock
```

使用真实 Google GenAI：

```powershell
$env:GOOGLE_API_KEY="***"
python -m pip install google-genai pillow
python -m agent_team.cli demo --provider google
```

## 免费主路线

当前推荐的数据采集方案是：

- 主方案：`本地常驻浏览器 + CDP 接管 + 结构化采集`
- 备用方案：`TikHub`

推荐入口只保留两步：

```powershell
python -m agent_team.cli browser-open --platform xiaohongshu
python -X utf8 skills/social-crawl-tool/scripts/run_social_crawl.py --platform xiaohongshu --content-mode video --max-items 5
```

也可以直接使用统一 CLI：

```powershell
python -m agent_team.cli browser-open --platform douyin
python -X utf8 -m agent_team.cli social-crawl --platform douyin --content-mode image --keyword "跨境电商" --max-items 5
```

说明：

- 浏览器会使用独立 profile 目录，不污染日常浏览器。
- 浏览器窗口必须保持打开，crawler 会通过 CDP 接管现有实例。
- 如果不传 `--keyword`，工具会自动使用素材驱动查询集。
- Windows 下建议统一使用 `python -X utf8`，减少中文参数和 stdout 乱码。

Docker 运行建议：

- 将 `runtime/browser_profiles/` 挂载为持久卷。
- 容器内使用独立 Chromium，不与宿主浏览器 profile 混用。
- 可通过 `AGENT_TEAM_BROWSER_EXECUTABLE` 或 `AGENT_TEAM_BROWSER_CHANNEL` 指定浏览器。
