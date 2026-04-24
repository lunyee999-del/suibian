import { ensureProfileDir } from "./sessionManager.js";

function sliceClean(items, limit) {
  return items
    .map((item) => String(item || "").replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .slice(0, limit);
}

export async function fetchPageData(payload, options) {
  if (options.dryRun) {
    return {
      success: true,
      title: "dry-run browser fetch",
      summary: "Browser fetch is disabled because DRY_RUN=true.",
      headings: [],
      paragraphs: []
    };
  }

  const { chromium } = await import("playwright");
  const userDataDir = ensureProfileDir(options.profileDir);
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: true
  });

  const page = await context.newPage();
  try {
    await page.goto(payload.url, {
      waitUntil: "domcontentloaded",
      timeout: 60000
    });
    await page.waitForTimeout(payload.wait_ms || 5000);

    const extracted = await page.evaluate(() => {
      const metaDescription =
        document.querySelector('meta[name="description"]')?.getAttribute("content") ||
        document.querySelector('meta[property="og:description"]')?.getAttribute("content") ||
        "";
      const headings = Array.from(document.querySelectorAll("h1, h2, h3")).map((node) => node.textContent || "");
      const paragraphs = Array.from(document.querySelectorAll("p")).map((node) => node.textContent || "");
      return {
        title: document.title || "",
        summary: metaDescription || "",
        headings,
        paragraphs
      };
    });

    const summary =
      extracted.summary ||
      sliceClean(extracted.paragraphs, 10).find((item) => item.length >= 40) ||
      "";

    return {
      success: true,
      title: extracted.title,
      summary,
      headings: sliceClean(extracted.headings, 10),
      paragraphs: sliceClean(extracted.paragraphs, 10)
    };
  } finally {
    await context.close();
  }
}
