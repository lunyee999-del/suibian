from __future__ import annotations

from dataclasses import asdict
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import parse_qs, urlparse
from urllib import error, request

from app.core.settings import Settings
from app.services.review_draft_repository import ReviewDraftRepository
from app.workflows.review_pipeline import ReviewPipeline


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Ozon 小红书发布台</title>
  <style>
    :root {
      --ink: #18202a;
      --muted: #667085;
      --paper: #fffaf2;
      --card: #ffffff;
      --line: #eadfce;
      --accent: #d64b2a;
      --accent-dark: #98341f;
      --green: #2f855a;
      --shadow: 0 18px 50px rgba(57, 39, 18, .14);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      color: var(--ink);
      font-family: "Microsoft YaHei UI", "Microsoft YaHei", "PingFang SC", sans-serif;
      background:
        radial-gradient(circle at 10% 10%, rgba(214,75,42,.18), transparent 28%),
        radial-gradient(circle at 92% 18%, rgba(47,133,90,.14), transparent 24%),
        linear-gradient(135deg, #fff7e8 0%, #f5efe4 55%, #eef3ef 100%);
    }
    .shell { max-width: 1180px; margin: 0 auto; padding: 34px 22px 60px; }
    .hero {
      display: grid;
      grid-template-columns: 1.3fr .7fr;
      gap: 20px;
      align-items: stretch;
      margin-bottom: 22px;
    }
    .panel {
      background: rgba(255,255,255,.78);
      border: 1px solid rgba(234,223,206,.95);
      border-radius: 26px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(18px);
    }
    .intro { padding: 30px; }
    h1 { margin: 0 0 12px; font-size: clamp(30px, 5vw, 56px); line-height: 1.03; letter-spacing: -1px; }
    .lead { margin: 0; color: var(--muted); font-size: 16px; line-height: 1.7; max-width: 760px; }
    .controls { padding: 24px; display: flex; flex-direction: column; gap: 14px; }
    .row { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    input {
      width: 92px;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px 13px;
      font-size: 15px;
      background: #fffdf8;
    }
    button {
      border: 0;
      border-radius: 16px;
      padding: 12px 17px;
      font-weight: 700;
      cursor: pointer;
      color: #fff;
      background: var(--accent);
      transition: transform .15s ease, background .15s ease;
    }
    button:hover { transform: translateY(-1px); background: var(--accent-dark); }
    button.secondary { color: var(--ink); background: #efe3d0; }
    button.secondary:hover { background: #e3d1b8; }
    button:disabled { opacity: .55; cursor: not-allowed; transform: none; }
    .status {
      min-height: 48px;
      padding: 13px 15px;
      border-radius: 16px;
      color: var(--muted);
      background: #fff8ec;
      border: 1px dashed #e2c9aa;
      line-height: 1.55;
      white-space: pre-wrap;
    }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 18px; }
    .card { overflow: hidden; }
    .cover { width: 100%; aspect-ratio: 9 / 16; object-fit: cover; background: #eadfce; display: block; }
    .content { padding: 17px; }
    .meta { color: var(--muted); font-size: 13px; line-height: 1.5; margin-bottom: 10px; }
    h2 { font-size: 19px; line-height: 1.35; margin: 0 0 9px; }
    .body { color: #3b4654; line-height: 1.65; font-size: 14px; max-height: 138px; overflow: auto; }
    .pill {
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 6px 10px;
      font-size: 12px;
      font-weight: 700;
      color: var(--accent-dark);
      background: #fff0df;
      margin-right: 7px;
    }
    .pill.published { color: var(--green); background: #eaf7ef; }
    .pill.error { color: #a33a22; background: #fee7e2; }
    .actions { display: flex; gap: 10px; margin-top: 14px; }
    .small { font-size: 13px; color: var(--muted); line-height: 1.6; }
    .service {
      padding: 12px 14px;
      border-radius: 16px;
      background: #fffdf8;
      border: 1px solid var(--line);
    }
    @media (max-width: 760px) {
      .hero { grid-template-columns: 1fr; }
      .intro, .controls { padding: 20px; }
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <div class="panel intro">
        <h1>Ozon 内容发布台</h1>
        <p class="lead">把“文章爬取 -> qwen-plus 改写 -> Wan 出图 -> 小红书发布”放到一个本地页面里。先生成草稿，确认封面和文案后，再点击真实发布。</p>
      </div>
      <div class="panel controls">
        <div class="row">
          <label>抓取篇数 <input id="limit" type="number" min="1" max="10" value="1"></label>
          <button id="prepareBtn">抓取并生成草稿</button>
          <button class="secondary" id="refreshBtn">刷新列表</button>
        </div>
        <div class="service">
          <div class="row">
            <strong>发布服务</strong>
            <span id="publisherState" class="pill">检查中</span>
            <button class="secondary" id="publisherBtn">启动发布服务</button>
          </div>
          <div id="publisherDetail" class="small">正在检查本地 publisher 服务状态。</div>
        </div>
        <div id="status" class="status">准备就绪。真实发布前请确认 publisher 服务为 dry_run=false，且小红书专用 profile 已登录。</div>
      </div>
    </section>
    <section id="drafts" class="grid"></section>
  </main>
  <script>
    const statusEl = document.querySelector("#status");
    const draftsEl = document.querySelector("#drafts");
    const prepareBtn = document.querySelector("#prepareBtn");
    const refreshBtn = document.querySelector("#refreshBtn");
    const publisherBtn = document.querySelector("#publisherBtn");
    const publisherStateEl = document.querySelector("#publisherState");
    const publisherDetailEl = document.querySelector("#publisherDetail");

    function setStatus(text) { statusEl.textContent = text; }
    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }[ch]));
    }
    async function api(path, options) {
      const response = await fetch(path, options);
      const data = await response.json();
      if (!response.ok || data.success === false) {
        throw new Error(data.error || JSON.stringify(data));
      }
      return data;
    }
    function setPublisherState(healthy, detail, dryRun = null) {
      publisherStateEl.className = `pill ${healthy ? "published" : "error"}`;
      publisherStateEl.textContent = healthy ? (dryRun ? "dry-run" : "ready") : "offline";
      publisherDetailEl.textContent = detail;
    }
    async function loadPublisherHealth() {
      try {
        const data = await api("/api/publisher/health");
        const detail = data.ok
          ? `publisher 在线，dry_run=${data.dry_run}，地址=${data.publisher_url}`
          : `publisher 未启动：${data.error || "unknown error"}`;
        setPublisherState(Boolean(data.ok), detail, Boolean(data.dry_run));
      } catch (error) {
        setPublisherState(false, `publisher 未启动：${error.message}`);
      }
    }
    async function startPublisher() {
      publisherBtn.disabled = true;
      setStatus("正在启动本地发布服务 ...");
      try {
        const data = await api("/api/publisher/start", { method: "POST" });
        setStatus(data.message || "发布服务已启动。");
      } catch (error) {
        setStatus(`启动发布服务失败：${error.message}`);
      } finally {
        publisherBtn.disabled = false;
        await loadPublisherHealth();
      }
    }
    async function loadDrafts() {
      const data = await api("/api/drafts");
      draftsEl.innerHTML = data.items.map((item) => `
        <article class="panel card">
          ${item.image_url ? `<img class="cover" src="${item.image_url}" alt="cover">` : ""}
          <div class="content">
            <div class="meta">
              <span class="pill ${item.review_status === "published" ? "published" : ""}">${escapeHtml(item.review_status)}</span>
              ${escapeHtml(item.source_site_name)} · ${escapeHtml(item.source_category_tag)}
            </div>
            <h2>${escapeHtml(item.title)}</h2>
            <div class="meta">来源：<a href="${escapeHtml(item.source_url)}" target="_blank" rel="noreferrer">${escapeHtml(item.source_title)}</a></div>
            <div class="body">${escapeHtml(item.body_text)}</div>
            ${item.publish_error ? `<div class="small" style="margin-top:10px;color:#a33a22;">发布失败：${escapeHtml(item.publish_error)}</div>` : ""}
            <div class="actions">
              <button data-publish="${item.review_id}" ${item.review_status === "published" ? "disabled" : ""}>真实发布</button>
            </div>
          </div>
        </article>
      `).join("");
    }
    async function prepare() {
      const limit = Number(document.querySelector("#limit").value || 1);
      prepareBtn.disabled = true;
      setStatus("正在抓取文章、调用 qwen-plus 改写、调用 Wan 出图。这个步骤可能需要几十秒。");
      try {
        const data = await api("/api/prepare", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ limit })
        });
        setStatus(`已生成 ${data.article_count} 篇草稿。`);
        await loadDrafts();
      } catch (error) {
        setStatus(`生成失败：${error.message}`);
      } finally {
        prepareBtn.disabled = false;
      }
    }
    async function publish(reviewId) {
      setStatus(`正在真实发布 review_id=${reviewId} ...`);
      try {
        const data = await api("/api/publish", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ review_id: reviewId })
        });
        const detail = data.publish_result?.detail?.error || data.publish_result?.result_status || data.review_status;
        setStatus(`发布结果：${detail}`);
        await loadDrafts();
        await loadPublisherHealth();
      } catch (error) {
        setStatus(`发布失败：${error.message}`);
      }
    }
    draftsEl.addEventListener("click", (event) => {
      const reviewId = event.target?.dataset?.publish;
      if (reviewId) publish(reviewId);
    });
    prepareBtn.addEventListener("click", prepare);
    refreshBtn.addEventListener("click", loadDrafts);
    publisherBtn.addEventListener("click", startPublisher);
    loadDrafts().catch((error) => setStatus(`加载失败：${error.message}`));
    loadPublisherHealth().catch((error) => setPublisherState(false, `publisher 检查失败：${error.message}`));
  </script>
</body>
</html>
"""


class WebUiServer:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.pipeline = ReviewPipeline(settings)
        self.review_repo = ReviewDraftRepository(settings.storage_dir)

    def drafts(self) -> dict:
        items = []
        for draft in reversed(self.review_repo.list_all()):
            image_path = draft.image_asset.local_path
            publish_error = None
            if draft.publish_result:
                publish_error = (
                    draft.publish_result.get("detail", {}).get("error")
                    or draft.publish_result.get("result_status")
                )
            items.append(
                {
                    "review_id": draft.review_id,
                    "draft_id": draft.content_draft.draft_id,
                    "title": draft.content_draft.title,
                    "body_text": draft.content_draft.body_text,
                    "review_status": draft.review_status,
                    "source_title": draft.source_title,
                    "source_url": draft.source_url,
                    "source_site_name": draft.source_site_name,
                    "source_category_tag": draft.source_category_tag,
                    "image_path": image_path,
                    "image_url": f"/image?path={image_path}" if image_path else "",
                    "publish_result": draft.publish_result,
                    "publish_error": publish_error,
                }
            )
        return {"items": items}

    def prepare(self, limit: int) -> dict:
        return self.pipeline.prepare_review_drafts(limit=limit)

    def publish(self, review_id: str) -> dict:
        return self.pipeline.approve_review_draft(review_id=review_id, publish=True)

    def publisher_health(self) -> dict:
        health_url = f"{self.settings.publisher_url.rstrip('/')}/health"
        try:
            with request.urlopen(health_url, timeout=3) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return {
                "ok": True,
                "dry_run": bool(payload.get("dry_run")),
                "publisher_url": self.settings.publisher_url,
            }
        except Exception as exc:
            return {
                "ok": False,
                "dry_run": None,
                "publisher_url": self.settings.publisher_url,
                "error": str(exc),
            }

    def start_publisher(self) -> dict:
        health = self.publisher_health()
        if health["ok"]:
            return {
                "success": True,
                "message": f"publisher 已在线，dry_run={health['dry_run']}",
                "health": health,
            }

        node_path = shutil.which("node")
        if not node_path:
            raise RuntimeError("未找到 node，可先手动启动 publisher/src/server.js")

        env = os.environ.copy()
        env["DRY_RUN"] = "false"
        env["HOST"] = "127.0.0.1"
        env["PORT"] = "3010"
        env["XHS_BROWSER_PROFILE_DIR"] = os.environ.get(
            "XHS_BROWSER_PROFILE_DIR",
            str(self.settings.storage_dir / "xhs-profile"),
        )
        env["XHS_CREATE_URL"] = os.environ.get(
            "XHS_CREATE_URL",
            "https://creator.xiaohongshu.com/publish/publish",
        )

        stdout_path = self.settings.storage_dir / "publisher.stdout.log"
        stderr_path = self.settings.storage_dir / "publisher.stderr.log"
        stdout_path.parent.mkdir(parents=True, exist_ok=True)

        with stdout_path.open("ab") as stdout, stderr_path.open("ab") as stderr:
            subprocess.Popen(
                [node_path, "src/server.js"],
                cwd=str(self.settings.base_dir / "publisher"),
                stdout=stdout,
                stderr=stderr,
                env=env,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

        for _ in range(10):
            time.sleep(1)
            health = self.publisher_health()
            if health["ok"]:
                return {
                    "success": True,
                    "message": f"publisher 启动成功，dry_run={health['dry_run']}",
                    "health": health,
                }
        raise RuntimeError("publisher 启动后仍未通过健康检查，请检查 storage/publisher.stderr.log")


def create_handler(app: WebUiServer) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self._send_text(INDEX_HTML, "text/html; charset=utf-8")
            elif parsed.path == "/api/drafts":
                self._send_json(app.drafts())
            elif parsed.path == "/api/publisher/health":
                self._send_json(app.publisher_health())
            elif parsed.path == "/image":
                self._send_image(parse_qs(parsed.query).get("path", [""])[0])
            else:
                self._send_json({"success": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                payload = self._read_json()
                if parsed.path == "/api/prepare":
                    limit = max(1, min(10, int(payload.get("limit", 1))))
                    self._send_json(app.prepare(limit))
                elif parsed.path == "/api/publish":
                    review_id = str(payload.get("review_id", "")).strip()
                    if not review_id:
                        raise ValueError("review_id is required")
                    self._send_json(app.publish(review_id))
                elif parsed.path == "/api/publisher/start":
                    self._send_json(app.start_publisher())
                else:
                    self._send_json({"success": False, "error": "Not found"}, HTTPStatus.NOT_FOUND)
            except Exception as exc:
                self._send_json({"success": False, "error": str(exc)}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def _read_json(self) -> dict:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            return json.loads(self.rfile.read(length).decode("utf-8"))

        def _send_text(self, body: str, content_type: str, status: HTTPStatus = HTTPStatus.OK) -> None:
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
            self._send_text(json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8", status)

        def _send_image(self, raw_path: str) -> None:
            image_path = Path(raw_path).resolve()
            image_dir = (app.settings.storage_dir / "images").resolve()
            if not image_path.is_file() or image_dir not in image_path.parents:
                self._send_json({"success": False, "error": "image not found"}, HTTPStatus.NOT_FOUND)
                return
            content_type = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
            data = image_path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve_ui(settings: Settings, host: str = "127.0.0.1", port: int = 8020) -> None:
    server = ThreadingHTTPServer((host, port), create_handler(WebUiServer(settings)))
    print(f"Ozon web UI listening on http://{host}:{port}")
    server.serve_forever()
