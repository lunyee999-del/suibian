import http from "node:http";
import path from "node:path";
import { fetchPageData } from "./pageFetcher.js";
import { publishToXhs } from "./xhsPublisher.js";
import { writeJson } from "./resultRecorder.js";

const host = process.env.HOST || "127.0.0.1";
const port = Number(process.env.PORT || 3010);
const dryRun = (process.env.DRY_RUN || "true").toLowerCase() !== "false";
const profileDir = process.env.XHS_BROWSER_PROFILE_DIR || path.resolve("../storage/xhs-profile");
const createUrl =
  process.env.XHS_CREATE_URL || "https://creator.xiaohongshu.com/publish/publish";
const cdpPort = process.env.XHS_CDP_PORT || 9333;
const resultDir = path.resolve("../storage/publish_payloads");

function jsonResponse(res, statusCode, payload) {
  res.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(payload));
}

const server = http.createServer(async (req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    jsonResponse(res, 200, { ok: true, dry_run: dryRun });
    return;
  }

  if (req.method !== "POST" || !["/internal/publish/xiaohongshu", "/internal/fetch/page"].includes(req.url)) {
    jsonResponse(res, 404, { success: false, error: "Not found" });
    return;
  }

  const chunks = [];
  for await (const chunk of req) {
    chunks.push(chunk);
  }

  try {
    const payload = JSON.parse(Buffer.concat(chunks).toString("utf8"));
    const result =
      req.url === "/internal/fetch/page"
        ? await fetchPageData(payload, {
            dryRun,
            profileDir
          })
        : await publishToXhs(payload, {
            dryRun,
            profileDir,
            createUrl,
            cdpPort
          });
    const suffix = req.url === "/internal/fetch/page" ? "fetch_result" : "publisher_result";
    writeJson(resultDir, `${payload.draft_id || Date.now()}_${suffix}.json`, {
      request: payload,
      response: result
    });
    jsonResponse(res, 200, result);
  } catch (error) {
    jsonResponse(res, 500, {
      success: false,
      result_status: "error",
      error: error instanceof Error ? error.message : String(error)
    });
  }
});

server.listen(port, host, () => {
  console.log(`publisher listening on http://${host}:${port} dryRun=${dryRun}`);
});
