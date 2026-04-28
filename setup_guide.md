# Ozon 小红书自动推广系统 —— 从 0 到 1 部署与操作说明书

这份说明书整合了该系统的核心架构，并加入了最新升级的“常驻浏览器无痕接管（CDP）”防封号安全发布方案。请按照以下步骤逐步操作。

---

## 第一阶段：环境与依赖准备

### 1. 准备 Python 虚拟环境
为了不干扰您电脑上的其他项目，建议使用项目内的虚拟环境（或直接使用您已有的 Conda 基础环境）。
在项目根目录（`suibian` 文件夹）打开终端（PowerShell 或 CMD），如果是使用默认 Python 环境，确保它是 Python 3.11 或以上版本。

**安装 Python 核心依赖：**
```powershell
python -m pip install -e .
python -m pip install requests playwright
```
*(注：`pip install -e .` 会根据 `pyproject.toml` 自动安装项目中所需的大部分包，而后续补装的 requests 和 playwright 是底层脚本必须的扩展支持。)*

### 2. 准备 Node.js 发布端依赖
小红书的自动发布动作是由一个基于 Node.js 的微服务来驱动的。
1. 在终端中进入 `publisher` 文件夹：
   ```powershell
   cd publisher
   ```
2. 安装 NPM 依赖并下载 Playwright 浏览器内核：
   ```powershell
   npm install
   npx playwright install chromium
   ```
3. 完成后返回上一级根目录：
   ```powershell
   cd ..
   ```

---

## 第二阶段：核心参数配置

在项目根目录下，找到（或创建）名为 `.env` 的环境变量配置文件，用记事本或代码编辑器打开。确保包含以下关键配置：

```ini
APP_ENV=dev
# 必须为 false 才能进行真实发布（如果是 true 则只是模拟流程）
DRY_RUN=false
STORAGE_DIR=storage
STORAGE_BACKEND=local_json
PUBLISHER_URL=http://127.0.0.1:3010

# AI 大模型配置 (这里以使用阿里云/火山引擎为例)
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_MODEL=qwen-plus
DASHSCOPE_API_KEY=您的阿里云API_KEY
ARK_API_KEY=您的火山引擎API_KEY
IMAGE_PROVIDER=ark
ARK_IMAGE_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
ARK_IMAGE_MODEL=doubao-seedream-5-0-260128

# 小红书专属配置
XHS_BROWSER_PROFILE_DIR=./storage/xhs-profile
# 注意：这里必须填真实的网址，不能填中文名！
XHS_CREATE_URL=https://creator.xiaohongshu.com/publish/publish
XHS_CDP_PORT=9333
```

---

## 第三阶段：安全扫码登录（防封号核心步骤）

为了避免频繁开关自动化浏览器导致账号被风控，我们采用**“常驻浏览器无痕接管（CDP）”**模式。

1. 在项目根目录的终端中，运行我们特制的一键安全浏览器启动脚本：
   ```powershell
   python open_browser.py
   ```
   *(如果您使用的是项目的自带爬虫脚本方案也可以：`python -X utf8 skills/social-crawl-tool/scripts/browser_open.py --platform xiaohongshu`)*
2. 此时您的电脑上会自动弹出一个 Edge 或 Chrome 浏览器窗口，并打开小红书创作者平台。
3. **关键动作**：请在弹出的页面中使用小红书 App **扫码登录**。
4. 登录成功，看到创作者中心首页后，**请将这个浏览器窗口最小化（放在后台），千万不要关闭它！** 只要它开着，您的登录状态就会被接下来的自动化程序直接复用。

---

## 第四阶段：启动系统与全流程自动化

### 1. 启动 Web UI 控制台
打开一个新的终端窗口（保持在项目根目录），启动主服务的网页界面：
```powershell
python -m app.cli serve-ui --port 8020
```

### 2. 执行数据流转与审核
1. 在浏览器（随便哪个浏览器都可以）中打开：`http://127.0.0.1:8020`。
2. 页面上会展示出系统已经抓取并经过 AI 改写、自动生成的配图（草稿）。
3. 如果您对某篇草稿满意，可以点击卡片上的“通过”以确认状态。

### 3. 启动并执行“真实发布”
1. 在网页控制台的右上方或发布卡片区域，点击 **“启动发布服务”** 按钮。
   *(这会在后台拉起刚才配置好的 Node.js 服务，监听 3010 端口)*。
2. 当状态由黄色的 `dry-run` 或者加载中变为绿色的 **`ready`** 后，代表系统已经整装待发。
3. 点击卡片上的 **“真实发布”** 按钮。

**背后的魔法：**
此时，系统会静悄悄地连接到您在第三阶段挂在后台的那个常驻浏览器，**自动在里面新建一个标签页**。它会精准找到“上传图文”按钮，全自动填入标题、粘贴正文、上传做好的图片。完成提交后，它会“事了拂衣去”，自动关闭刚刚新建的那个标签页。整个过程宛如真人在操作，绝不会造成闪退，最大程度保障了账号的安全！
