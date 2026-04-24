

# Umlink 项目功能介绍（RAG 总览版）

## 1. 文档定位
- 用途：用于售前机器人 RAG 知识库的数据准备，帮助机器人稳定回答“系统能做什么、适合谁、价值在哪里、上线前要准备什么”。
- 适用对象：售前、运营、实施、客服、合作伙伴。
- 版本范围：基于当前代码仓 `D:\umlinks\Umlink` 的已实现能力。

---

## 2. 项目概述
Umlink 是一套面向 Ozon 跨境卖家的一体化运营系统，覆盖“选品 -> 编辑 -> 上架 -> 订单协同 -> 数据分析 -> 商业化收费”的完整链路。

它不是单点工具，而是一套能陪伴商家从“起盘”走向“规模化运营”的工作台。

核心特点：
- 多货源采集：支持 1688、拼多多、淘宝/天猫商品采集与统一入库。
- 智能化运营：支持 AI 文案优化、图片翻译与水印模板管理。
- 发布与履约协同：支持 Ozon 发布、订单处理、采购与支付协同。
- 可经营可增长：内置数据分析、看板、会员与额度体系。

---

## 3. 目标用户与典型场景
目标用户：
- 跨境电商卖家（主账号）
- 卖家运营团队
- 供应商协作角色
- 平台管理员

典型场景：
- 从国内货源平台快速采集商品，并批量上架 Ozon。
- 对标题、关键词、图片进行本地化处理，提高转化效率。
- 围绕订单进行采购、支付、面单等协同操作。
- 通过分析看板快速判断“卖什么、怎么卖、哪里需要优化”。

---

## 4. 核心功能模块

### 4.1 商品采集与货源管理
能力说明：
- 支持按关键词、类目、推荐、图片等方式获取 1688 货源。
- 支持浏览器插件侧批量采集（1688、拼多多、淘宝/天猫）。
- 采集后自动沉淀商品基础字段、规格、图片、价格与来源标识。

业务价值：
- 帮商家快速建立选品池，把时间花在决策上，而不是重复搬运上。

代码锚点：
- `app/Admin/Controllers/Ali1688Controller.php`
- `app/Admin/Controllers/Ali1688mController.php`
- `app/Browser/Controllers/Ali1688Controller.php`
- `app/Browser/Controllers/PinduoduoController.php`
- `app/Browser/Controllers/TaobaoController.php`
- `routes/browser.php`

### 4.2 商品编辑与属性管理
能力说明：
- 商品标题、价格、规格、库存等信息编辑。
- 类目与属性体系管理（同步、联动查询、按类目补全）。
- 支持单品编辑、批量改库存、批量改价格。

业务价值：
- 让商品信息更完整、更规范，明显提升上架成功率和后续运营效率。

代码锚点：
- `app/Admin/Controllers/GoodsController.php`
- `app/Admin/Controllers/GoodsEditController.php`
- `app/Admin/Controllers/CategoryController.php`
- `app/Admin/Controllers/AttributesController.php`

### 4.3 AI 文案优化（标题/关键词/主题标签）
能力说明：
- 基于 AI 生成俄语关键词、主题标签与标题优化内容。
- 生成结果可直接回写商品字段，减少重复录入。

业务价值：
- 缩短文案生产周期，提升本地化质量与搜索匹配度。

代码锚点：
- `app/Admin/Controllers/TextAiController.php`
- `app/Admin/Controllers/GoodsEditController.php`
- `app/Models/TextAiByDeepSeek.php`

### 4.4 图片处理（翻译、编辑、水印）
能力说明：
- 支持商品图片翻译与翻译记录管理。
- 支持图片编辑后回写商品图。
- 支持水印模板新增、编辑、删除、设为默认。

业务价值：
- 在“本地化表达”和“品牌一致性”之间取得平衡，提升页面专业度。

代码锚点：
- `app/Admin/Controllers/GoodsImageController.php`
- `app/Admin/Controllers/WatermarkController.php`
- `database/migrations/2025_01_16_000000_create_watermark_templates_table.php`
- `database/migrations/2025_01_16_100000_add_is_default_to_watermark_templates.php`
- `database/migrations/2025_12_24_144800_create_img_src_trans_table.php`
- `database/migrations/2025_12_25_113300_add_img_src_trans_count_to_merchant_table.php`

### 4.5 平台商品发布（Ozon）
能力说明：
- 支持单商品发布、按店铺发布、批量发布。
- 发布前进行必填项与规则校验（类目、属性、价格、图片等）。
- 发布后记录任务回执并异步跟踪结果。

业务价值：
- 大幅减少“反复发布失败”的成本，让上新节奏更稳定。

代码锚点：
- `app/Admin/Controllers/PlatformGoodsController.php`
- `app/Jobs/OperateSkuShopOzonTask.php`

### 4.6 店铺与渠道管理
能力说明：
- 店铺配置管理（Client ID / API Key / 币种等）。
- Ozon Cookie 状态维护与可用性管理。

业务价值：
- 保证 API 通道稳定，支撑多店铺长期运营。

代码锚点：
- `app/Admin/Controllers/ShopController.php`
- `app/Admin/Controllers/OzonCookiesController.php`

### 4.7 订单与采购协同
能力说明：
- 查看店铺订单、订单状态、子订单明细。
- 支持比价采购、采购单创建、支付联动。
- 支持面单获取与订单关联操作。

业务价值：
- 让“销售订单 -> 采购执行 -> 支付履约”闭环更顺畅。

代码锚点：
- `app/Admin/Controllers/ShopOrdersController.php`
- `app/Admin/Controllers/SkuShopOzonOrdersPlatformController.php`
- `app/Admin/Controllers/Ali1688Controller.php`

### 4.8 数据分析与运营洞察
能力说明：
- 支持多维度指标分析与结果查询。
- 支持热销、新品、蓝海等榜单与热搜词分析。
- 支持“卖什么”分析与类目联动洞察。

业务价值：
- 把经验运营升级为“数据驱动运营”。

代码锚点：
- `app/Admin/Controllers/AnalyticsController.php`
- `app/Admin/Controllers/OzonAnalyticsController.php`
- `app/Admin/Controllers/OzonAnalyticsRankController.php`
- `app/Admin/Controllers/OzonAnalyticsSearchController.php`

### 4.9 运营数据看板
能力说明：
- 核心指标看板（新增、激活、活跃、付费、收入）。
- 支持趋势与实时数据监控。

业务价值：
- 让管理者随时看到业务温度，及时调整策略。

代码锚点：
- `app/Admin/Controllers/DataDashboardController.php`

### 4.10 会员、额度与支付
能力说明：
- 会员等级/套餐管理、激活码能力。
- 微信支付（采购订单支付）、连连支付（会员购买支付）。
- 额度控制：采集、发布、图片翻译等能力配额管理。

业务价值：
- 支持平台商业化闭环，形成可持续运营模式。

代码锚点：
- `app/Admin/Controllers/MerchantController.php`
- `app/Admin/Controllers/MerchantVipBalanceOrdersController.php`
- `app/Admin/Controllers/WxpayController.php`
- `app/Admin/Controllers/LianlianPayController.php`

### 4.11 供应商与协作角色
能力说明：
- 供应商资料与联系方式管理。
- 供应商查看并处理协同订单信息。

业务价值：
- 让外部协作流程可视、可追踪，减少沟通损耗。

代码锚点：
- `app/Admin/Controllers/SupplierController.php`
- `app/Admin/Controllers/SkuShopOzonOrdersSupplierController.php`

### 4.12 公网站点与品牌展示
能力说明：
- 官网首页与价格页展示。
- 对外承接品牌曝光与产品咨询入口。

代码锚点：
- `app/Index/Controllers/IndexController.php`
- `app/Index/Controllers/PriceController.php`
- `routes/web.php`

### 4.13 跨境定价与利润计算器（后台 + 官网）
能力说明：
- 后台定价计算器：支持采购成本、重量、物流、时效、佣金率、毛利率、折扣等参数测算。
- 官网提供两个入口：`/ozon_calculator`（定价）与 `/ozon_profit_calculator`（利润）。
- 计算引擎支持汇率/物流/佣金数据缓存、计费重量计算与物流匹配。

业务价值：
- 售前沟通更直观，运营决策更快速，客户更容易理解 ROI。

代码锚点：
- `app/Admin/Controllers/CalculatorController.php`

- `app/Index/Controllers/OzonCalculatorController.php`

- `app/Admin/routes.php`

- `routes/web.php`

- `resources/views/admin/calculator/index.blade.php`

- `resources/views/index/ozon_calculator/index.blade.php`

- `resources/views/index/ozon_profit_calculator/index.blade.php`

- `public/js/ozon_calculator_engine.js`

- `public/js/ozon_profit_engine.js`

  ### 4.14 权益享用

  | **会员等级** | **价格**   | **图片翻译赠送额度** | **店铺绑定上限** | **核心权益**               |
  | ------------ | ---------- | -------------------- | ---------------- | -------------------------- |
  | **月会员**   | 398元      | 600张                | 3个              | 基础版本                   |
  | **季度会员** | 998元      | 2000张               | 10个             | 单价更优                   |
  | **半年会员** | 1998元     | 3000张               | 20个             | 适合中型团队               |
  | **年会员**   | **2998元** | **6000张**           | **无限制**       | **性价比之王，大卖家首选** |

  ### 4.15翻译功能说明

  - **技术支持**：umlink 调用 **阿里云 (Alibaba Cloud)** 顶级翻译接口，确保翻译准确率与排版美观。
  - **透明计费**：图片翻译底层成本为 **0.035元/张 (3.5分/张)**。
  - **赠送机制**：会员套餐内包含的翻译张数均为免费赠送。
  - **单独充值**：赠送额度用完后，可按 **35元/1000张** 充值（折合仅 3.5分/张，纯成本价对接）。

---

## 5. 典型业务流程（售前高频）

### 流程A：从采集到上架
1. 通过插件采集 1688/拼多多/淘宝商品。
2. 在后台完成标题、属性、价格、图片编辑。
3. 用 AI 生成关键词与主题标签。
4. 选择店铺执行发布并跟踪任务结果。

### 流程B：从订单到采购协同
1. 同步店铺订单并查看订单详情。
2. 创建采购单并执行比价采购。
3. 通过支付链路完成支付。
4. 获取面单并进入履约流程。

### 流程C：多角色协同运营
1. 运营团队完成选品、编辑、上架、分析闭环。
2. 供应商侧处理协同订单信息。
3. 管理端通过看板与分析持续优化经营策略。

---

## 6. 功能边界与前置条件
- Ozon 发布依赖店铺 API 凭证（Client ID / API Key）有效。
- 部分分析能力依赖 Ozon Cookie 或外部接口可用。
- AI 文案与图片翻译能力依赖对应接口配置与额度。
- 会员与支付能力依赖支付回调链路配置正确。
- 计算器能力依赖汇率、物流、佣金数据源；未登录时官网工具可能优先读取本地缓存。
- 计算器部分路由存在预留接口，实际能力以当前控制器实现与前端引擎调用链路为准。

---

## 7. RAG 入库拆分建议
建议按“模块 -> 能力/场景/前置条件/限制/代码锚点”拆分。

建议 metadata 字段：
- `product`: `Umlink`
- `module`: 如 `商品采集`、`图片处理`、`定价计算器`
- `audience`: `售前`、`运营`、`实施`、`客服`
- `intent`: `是什么`、`怎么做`、`适合谁`、`有什么限制`
- `source_file`: 源文件路径
- `updated_at`: 更新时间

分片目录：
- `D:\umlinks\Umlink\RAG功能介绍分片`

---

## 8. 对外一句话介绍（可直接复用）
Umlink 是一套面向 Ozon 跨境卖家的一体化运营系统，提供“多源采集 + AI 优化 + 图片处理 + 定价/利润计算器 + 多店铺发布 + 订单采购协同 + 数据分析 + 会员计费”全链路能力。
