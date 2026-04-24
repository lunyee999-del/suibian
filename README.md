# Ozon 小红书自动推广系统

> 一套面向 Ozon 跨境卖家的全自动内容生产与小红书发布流水线

---

## 📌 项目简介

本项目是一套专为 **Ozon 跨境电商运营** 场景设计的自动化内容推广系统，核心目标是：

- 每天自动发布 **10–20 篇**小红书图文笔记
- 内容方向聚焦 `Ozon 热点解读 / 榜单分析 / 选品建议 / 运营干货`
- 内容来源以 Ozon 公开页面及行业资讯为主
- 视觉生成接入阿里云**万相**文生图
- 发布方式采用 **Playwright** 浏览器自动化

---

## 🏗 系统架构

系统分为 4 个逻辑模块：

```
collector        →   content-engine   →   image-engine   →   publisher
(热点采集)           (清洗/选题/文案)      (万相出图)          (小红书自动发布)
```

### 目录结构

```text
Ozon_promotion/
├── app/
│   ├── collectors/        # 外部热点采集器
│   ├── core/              # 核心工具类
│   ├── domain/            # 业务模型定义
│   ├── services/          # 业务逻辑服务
│   └── workflows/         # 流水线编排
├── config/
│   └── prompts/           # Prompt 模板管理
├── publisher/
│   └── src/               # Node.js Playwright 发布服务
│       ├── sessionManager.ts
│       ├── xhsPublisher.ts
│       ├── uploadHelper.ts
│       └── resultRecorder.ts
├── storage/
│   ├── raw/               # 原始抓取数据
│   ├── images/            # 生成图片素材
│   ├── screenshots/       # 发布截图存档
│   ├── source_articles/   # 完整原文存档
│   ├── review_drafts/     # 待审核草稿
│   └── tables/            # CSV 快照（便于人工复查）
├── skills/                # 可复用技能模块
├── sql/
│   └── 001_initial_schema.sql   # 初始化数据库表结构
├── .env.example           # 环境变量示例
├── pyproject.toml         # Python 项目配置
└── README.md
```

---

## ⚡ 快速开始

### 环境准备

**Python 端（标准库，无需额外安装）**

```powershell
Copy-Item .env.example .env
# 按需填写 .env 中的 API Key 等配置
```

**Node.js 端（Playwright 发布服务）**

```powershell
Set-Location publisher
npm install
```

---

### 运行流水线

#### 1. 执行完整干跑（不触发真实发布）

```powershell
python -m app.cli run --limit 3
```

#### 2. 抓取原始 Ozon 资讯

```powershell
python -m app.cli collect-articles --limit 6
```

#### 3. 生成待审核草稿

```powershell
python -m app.cli prepare-review --limit 2
```

#### 4. 审核通过后触发发布

```powershell
python -m app.cli approve-review --review-id <review_id> --publish
```

#### 5. 启动可视化控制台

```powershell
python -m app.cli serve-ui --port 8020
```

浏览器打开 `http://127.0.0.1:8020`，可预览草稿、封面图，并一键触发发布。

#### 6. 启动 Node 发布服务

```powershell
Set-Location publisher
node src/server.js
```

> 默认运行在 `DRY_RUN=true` 模式，只模拟响应，不真实发布。  
> 切换到真实发布：在 `.env` 中设置 `DRY_RUN=false`。

#### 7. 开启 Publisher 的完整流水线

```powershell
python -m app.cli run --limit 2 --publish
```

---

## 🔧 环境变量说明

复制 `.env.example` 为 `.env` 并填入以下配置：

| 变量名 | 说明 | 示例 |
|---|---|---|
| `IMAGE_PROVIDER` | 图片生成服务商 | `wan` / `ark` |
| `WAN_API_KEY` | 阿里云万相 API Key | — |
| `ARK_API_KEY` | 火山方舟 API Key | — |
| `ARK_IMAGE_MODEL` | 方舟图像模型 | `doubao-seedream-5-0-260128` |
| `ARK_IMAGE_BASE_URL` | 方舟 API 地址 | `https://ark.cn-beijing.volces.com/api/v3` |
| `LLM_API_KEY` | 文案生成 LLM Key | — |
| `DRY_RUN` | 是否干跑模式 | `true` / `false` |

---

## 🗄 数据库表结构

初始化 SQL 文件位于 `sql/001_initial_schema.sql`，包含以下核心表：

| 表名 | 用途 |
|---|---|
| `source_configs` | 数据源配置管理 |
| `source_raw_items` | 原始抓取数据存储 |
| `trend_topics` | 清洗聚类后的热点主题 |
| `trend_topic_items` | 热点主题与原始数据关联 |
| `topic_candidates` | 可写选题池 |
| `publish_plan_items` | 每日发布计划 |
| `content_drafts` | 文案草稿 |
| `asset_images` | 图片素材记录 |
| `qa_results` | 质检评分结果 |
| `publish_accounts` | 小红书账号管理 |
| `publish_records` | 发布执行记录 |

---

## 🤖 核心任务流

```text
定时触发采集
  → FetchSourceJob       抓取 Ozon 公开页面
  → ParseSourceJob       解析结构化字段
  → NormalizeTrendJob    关键词归一化
  → ClusterTrendTopicsJob 主题聚类
  → BuildTopicCandidatesJob 生成选题候选
  → BuildDailyPublishPlanJob 生成当日发布计划
  → GenerateContentDraftJob  LLM 生成文案
  → GenerateImageAssetJob    万相出图
  → RunQaCheckJob            质检评分
  → PublishXiaohongshuJob    Playwright 自动发布
```

---

## 📅 调度建议

| 任务 | 频率 |
|---|---|
| 热点抓取 | 每 30–60 分钟 |
| 聚类与选题 | 每 2–3 小时 |
| 发布计划生成 | 每天凌晨一次 |
| 内容生成 | 提前 2–6 小时 |
| 自动发布 | 按时段消费队列，相邻间隔 ≥ 20 分钟 |

---

## 📝 内容规则

### 栏目配比（每日）

| 栏目 | 数量 |
|---|---|
| 热搜词解读 | 6 篇 |
| 榜单拆解 | 5 篇 |
| 选品建议 | 5 篇 |
| 运营技巧 | 2–4 篇 |

### 标题规则

- 字数：16–22 字优先
- 不使用夸张语气，不使用强导购表达
- 必须含一个核心信息点，具备"结论感"或"提醒感"

### 正文结构

1. 开头一句结论
2. 数据或现象描述
3. 原因分析
4. 针对卖家的具体建议
5. 软性导流收尾（250–450 字）

---

## 🖼 图片生成策略

- 封面尺寸：`1040×1472`（3:4 竖版）
- 每篇至少生成 1 张封面图
- 图片后处理：统一压缩 + 重命名
- 参数建议：`n=1`，`watermark=false`，`prompt_extend=true`

---

## 🚀 发布器内部接口

发布服务运行于 Node.js，提供以下内部接口：

```http
POST /internal/publish/xiaohongshu
```

请求体示例：

```json
{
  "publish_record_id": 123,
  "account_id": 1,
  "title": "最近 Ozon 这类词明显在升温",
  "body_text": "正文内容",
  "images": ["storage/images/cover_001.png"],
  "hashtags": ["#Ozon运营", "#跨境电商"]
}
```

---

## 📋 MVP 验收标准

- [x] 接入 ≥ 3 个外部热点来源
- [x] 每天自动生成 ≥ 20 个选题候选
- [x] 每天自动产出 10–20 篇图文草稿
- [x] 每篇内容自动生成 ≥ 1 张封面图
- [x] 自动发布成功率 ≥ 80%
- [x] 所有失败任务有截图和错误记录
- [x] 支持开关暂停发布

---

## 📚 文档索引

| 文档 | 说明 |
|---|---|
| [小红书自动推广技术文档 V2（可开发版）](./小红书自动推广技术文档V2-可开发版.md) | 完整技术设计文档，含数据表、Prompt、发布器设计 |
| [小红书自动推广技术文档 V1](./小红书自动推广技术文档V1.md) | 早期概要版本 |
| [万相文生图使用文档](./万相文生图使用文档.md) | 阿里云万相调用详细说明 |
| [项目功能介绍（RAG 版）](./项目功能介绍-RAG版.md) | 面向 RAG 问答场景的功能概述 |

---

## ⚠️ 注意事项

- Python 端仅使用标准库，可直接运行无需额外安装
- Node 发布服务默认 `DRY_RUN=true`，上线前请确认已切换
- 浏览器 profile 需首次人工扫码登录小红书，之后自动复用 Cookie
- 每天发布分多个时段，避免短时集中触发风控
- 抓取任务建议配置代理，避免频繁访问 Ozon 被封 IP

---

## 🗓 开发排期建议

| 周次 | 目标 |
|---|---|
| 第 1 周 | 建表、打通 2–3 个数据源、原始数据入库 |
| 第 2 周 | 清洗聚类、选题编排、文案生成、万相出图 |
| 第 3 周 | 质检评分、Playwright 自动发布、结果回写 |
| 第 4 周 | 调度优化、风控节奏、后台查看页、小范围试运行 |

---

> 📩 项目维护：umlink 团队  
> 🔗 关联仓库：[https://github.com/lunyee999-del/suibian](https://github.com/lunyee999-del/suibian)
