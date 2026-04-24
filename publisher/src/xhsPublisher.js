import path from "node:path";
import { selectors } from "./xhsSelectors.js";
import { ensureProfileDir } from "./sessionManager.js";

async function clickFirst(page, candidates) {
  for (const selector of candidates) {
    const locator = page.locator(selector).first();
    if (await locator.count()) {
      await locator.click({ force: true });
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

  await clickFirst(page, selectors.imageModeTab);
  await page.waitForTimeout(1500);

  const toggled = await page.evaluate(() => {
    const walker = Array.from(document.querySelectorAll("div,span,button"));
    const target = walker.find((node) => (node.textContent || "").includes("上传图文"));
    if (!target) {
      return false;
    }
    const clickable =
      target.closest('button,[role="tab"],[role="button"],li,div') || target;
    clickable.click();
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
  const userDataDir = ensureProfileDir(options.profileDir);
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false
  });

  const page = await context.newPage();
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

    await publishButton.click();
    await page.waitForTimeout(4000);

    return {
      success: true,
      result_status: "published",
      note_url: null,
      draft_id: payload.draft_id
    };
  } finally {
    await context.close();
  }
}
