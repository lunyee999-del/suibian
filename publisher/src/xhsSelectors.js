export const selectors = {
  imageModeTab: [
    'text=上传图文',
    'button:has-text("上传图文")',
    '[role="tab"]:has-text("上传图文")'
  ],
  title: [
    'input[placeholder*="标题"]',
    'textarea[placeholder*="标题"]',
    'input[type="text"]'
  ],
  body: [
    'div[contenteditable="true"]',
    'textarea[placeholder*="正文"]'
  ],
  fileInput: [
    'input[type="file"][accept*="image"]',
    'input[type="file"][accept*=".jpg"]',
    'input[type="file"][accept*=".png"]',
    'input[type="file"]'
  ],
  publishButton: [
    'button:has-text("发布")',
    'button:has-text("立即发布")'
  ]
};
