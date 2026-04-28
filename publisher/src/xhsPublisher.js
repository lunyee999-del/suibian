import path from "node:path";
import { selectors } from "./xhsSelectors.js";
import { ensureProfileDir } from "./sessionManager.js";

async function clickFirst(page, candidates) {
  for (const selector of candidates) {
    const locator = page.locator(selector).first();
    if (await locator.count()) {
      await locator.evaluate((node) => node.click());
      return true;
    }
  }
  return false;
}

async function ensureImageMode(page) {
  const imageReady = await page
    .locator('input[type="file"][accept*="image"], input[type="file"][accept*=".jpg"], input[type="file"][accept*=".png"]')
    .count();
  if (imageReady) {
    return;
  }

  const toggled = await page.evaluate(() => {
    const allElements = Array.from(document.querySelectorAll('*'));
    const target = allElements.find(el => {
      // Only check elements with direct text nodes
      return Array.from(el.childNodes).some(node => node.nodeType === 3 && node.textContent.trim() === '上传图文');
    });

    if (!target) return false;

    // Try to find a clickable parent wrapper
    let clickable = target;
    let curr = target;
    while (curr && curr !== document.body) {
      const cls = (curr.className || '').toString().toLowerCase();
      if (cls.includes('tab') || curr.tagName === 'LI' || curr.getAttribute('role') === 'tab' || cls.includes('btn') || cls.includes('item')) {
        clickable = curr;
        break;
      }
      curr = curr.parentElement;
    }
    
    clickable.click();
    // Also dispatch a React-friendly bubble event just in case
    clickable.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
    return true;
  });

  if (toggled) {
    await page.waitForTimeout(2000);
  }
}

async function fillFirst(page, candidates, value) {
  for (const selector of candidates) {
    const locator = page.locator(selector).first();
    if (await locator.count()) {
      await locator.fill(value);
      return true;
    }
  }
  return false;
}

async function setFiles(page, images) {
  for (const selector of selectors.fileInput) {
    const locator = page.locator(selector).first();
    if (await locator.count()) {
      const accept = (await locator.getAttribute("accept")) || "";
      if (selector === 'input[type="file"]' && accept && !accept.includes("image")) {
        continue;
      }
      await locator.setInputFiles(images);
      return true;
    }
  }
  return false;
}

export async function publishToXhs(payload, options) {
  if (options.dryRun) {
    return {
      success: true,
      result_status: "dry_run",
      note_url: null,
      received_images: payload.images
    };
  }

  const { chromium } = await import("playwright");
  let browser, context, page;
  const useCDP = !!options.cdpPort;

  if (useCDP) {
    try {
      browser = await chromium.connectOverCDP(`http://127.0.0.1:${options.cdpPort}`);
      context = browser.contexts()[0] || (await browser.newContext());
      page = await context.newPage();
    } catch (e) {
      // Fallback if CDP is not running
      const userDataDir = ensureProfileDir(options.profileDir);
      context = await chromium.launchPersistentContext(userDataDir, { headless: false });
      page = await context.newPage();
    }
  } else {
    const userDataDir = ensureProfileDir(options.profileDir);
    context = await chromium.launchPersistentContext(userDataDir, { headless: false });
    page = await context.newPage();
  }

  try {
    await page.goto(options.createUrl, { waitUntil: "networkidle", timeout: 60000 });
    await ensureImageMode(page);

    const uploaded = await setFiles(page, payload.images.map((item) => path.resolve(item)));
    if (!uploaded) {
      throw new Error("No upload input found.");
    }

    await page.waitForTimeout(3000);

    const titleFilled = await fillFirst(page, selectors.title, payload.title);
    if (!titleFilled) {
      throw new Error("Title input not found.");
    }

    const bodyFilled = await fillFirst(page, selectors.body, payload.body_text);
    if (!bodyFilled) {
      throw new Error("Body input not found.");
    }

    const publishButton = page.locator(selectors.publishButton.join(",")).first();
    if (!(await publishButton.count())) {
      throw new Error("Publish button not found.");
    }

    await publishButton.evaluate((node) => node.click());
    await page.waitForTimeout(4000);

    return {
      success: true,
      result_status: "published",
      note_url: null,
      draft_id: payload.draft_id
    };
  } finally {
    if (page) await page.close().catch(() => {});
    if (browser) {
      await browser.close().catch(() => {});
    } else if (context) {
      await context.close().catch(() => {});
    }
  }
}
