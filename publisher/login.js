import { chromium } from "playwright";
import path from "node:path";
import fs from "node:fs";

const profileDir = path.resolve("../storage/xhs-profile");
if (!fs.existsSync(profileDir)) {
  fs.mkdirSync(profileDir, { recursive: true });
}

(async () => {
  console.log("正在为您打开浏览器...");
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: null
  });
  const page = await context.newPage();
  await page.goto("https://creator.xiaohongshu.com/");
  console.log("请在弹出的浏览器中扫码登录小红书。登录成功后，您可以直接关闭浏览器窗口，系统会自动保存登录状态。");
})();
