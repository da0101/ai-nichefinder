import json
from functools import partial
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from nichefinder_core.settings import Settings

from nichefinder_cli.viewer_data import load_dashboard, load_keyword_detail

HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI Nichefinder Viewer</title>
  <style>
    :root { --bg:#f7f3ea; --panel:#fffdf8; --ink:#1f2937; --muted:#6b7280; --line:#e5dcc9; --accent:#b45309; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:ui-sans-serif,system-ui,sans-serif; background:linear-gradient(180deg,#fbf7ef 0%,#f4efe5 100%); color:var(--ink); }
    header { padding:24px 28px 12px; border-bottom:1px solid var(--line); background:rgba(255,253,248,.92); position:sticky; top:0; backdrop-filter:blur(8px); }
    h1,h2,h3 { margin:0; font-family:Georgia,Cambria,"Times New Roman",serif; }
    h1 { font-size:28px; }
    main { padding:20px 28px 32px; display:grid; gap:18px; }
    .cards,.layout,.usage { display:grid; gap:14px; }
    .cards { grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); }
    .layout { grid-template-columns:minmax(280px,360px) 1fr; align-items:start; }
    .panel { background:var(--panel); border:1px solid var(--line); border-radius:18px; padding:16px; box-shadow:0 12px 30px rgba(39,24,0,.05); }
    .metric { font-size:28px; font-weight:700; margin-top:6px; }
    .label,.muted { color:var(--muted); }
    .list { display:grid; gap:10px; max-height:72vh; overflow:auto; }
    button.item { width:100%; text-align:left; border:1px solid var(--line); background:#fff; border-radius:14px; padding:12px; cursor:pointer; }
    button.item.active { border-color:var(--accent); box-shadow:0 0 0 2px rgba(180,83,9,.12); }
    .term { font-weight:700; margin-bottom:6px; }
    .chips { display:flex; flex-wrap:wrap; gap:6px; }
    .chip { font-size:12px; padding:4px 8px; border-radius:999px; background:#f4ead7; color:#7c3d09; }
    table { width:100%; border-collapse:collapse; font-size:14px; }
    td,th { padding:8px 0; border-bottom:1px solid var(--line); vertical-align:top; text-align:left; }
    pre { white-space:pre-wrap; overflow:auto; background:#faf6ee; padding:12px; border-radius:12px; border:1px solid var(--line); }
    a { color:#92400e; }
    @media (max-width: 900px) { .layout { grid-template-columns:1fr; } .list { max-height:none; } }
  </style>
</head>
<body>
  <header>
    <h1>AI Nichefinder Viewer</h1>
    <div class="muted">Read-only local view over the SQLite research and draft outputs.</div>
  </header>
  <main>
    <section id="summary" class="cards"></section>
    <section class="layout">
      <div class="panel">
        <h2>Keywords</h2>
        <div id="keywords" class="list" style="margin-top:14px;"></div>
      </div>
      <div id="detail" class="panel"><div class="muted">Select a keyword to inspect its work.</div></div>
    </section>
    <section class="panel">
      <h2>Articles</h2>
      <div id="articles" class="list" style="margin-top:14px;"></div>
    </section>
    <section class="panel">
      <h2>Usage</h2>
      <div id="usage" class="usage" style="margin-top:14px;"></div>
    </section>
  </main>
  <script>
    const state = { selectedId: null, keywords: [] };

    async function loadJson(path) {
      const response = await fetch(path);
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    }

    function card(title, value, note = "") {
      return `<div class="panel"><div class="label">${title}</div><div class="metric">${value}</div><div class="muted">${note}</div></div>`;
    }

    function renderDashboard(data) {
      document.getElementById("summary").innerHTML = [
        card("Keywords", data.summary.total_keywords, data.paths.database),
        card("Briefed", data.summary.briefed_keywords, "Saved content briefs"),
        card("Articles", data.summary.articles, data.paths.articles_dir),
        card("Published", data.summary.published_articles, "Human-approved output"),
      ].join("");
      state.keywords = data.keywords;
      renderKeywords();
      document.getElementById("articles").innerHTML = data.articles.length ? data.articles.map(article => `
        <div class="panel">
          <div class="term">${article.title}</div>
          <div class="chips">
            <span class="chip">${article.status}</span>
            <span class="chip">${article.created_at || "unknown date"}</span>
          </div>
          <div class="muted" style="margin-top:8px;">${article.file_path}</div>
          ${article.published_url ? `<div style="margin-top:8px;"><a href="${article.published_url}" target="_blank" rel="noreferrer">${article.published_url}</a></div>` : ""}
        </div>`).join("") : `<div class="muted">No articles yet.</div>`;
      document.getElementById("usage").innerHTML = data.usage.length ? data.usage.map(row => `
        <div class="panel">
          <div class="term">${row.provider}</div>
          <div class="chips">
            <span class="chip">${row.calls} calls</span>
            <span class="chip">$${row.spend_usd.toFixed(2)}</span>
            <span class="chip">${row.tokens_in} in / ${row.tokens_out} out</span>
          </div>
        </div>`).join("") : `<div class="muted">No usage rows yet.</div>`;
      if (data.keywords.length && !state.selectedId) selectKeyword(data.keywords[0].id);
    }

    function renderKeywords() {
      document.getElementById("keywords").innerHTML = state.keywords.length ? state.keywords.map(keyword => `
        <button class="item ${keyword.id === state.selectedId ? "active" : ""}" onclick="selectKeyword('${keyword.id}')">
          <div class="term">${keyword.term}</div>
          <div class="chips">
            <span class="chip">score ${keyword.score ?? "-"}</span>
            <span class="chip">${keyword.intent || "no intent"}</span>
            <span class="chip">${keyword.trend || "no trend"}</span>
            ${keyword.has_brief ? `<span class="chip">briefed</span>` : ""}
          </div>
        </button>`).join("") : `<div class="muted">No keywords yet.</div>`;
    }

    function kvRows(rows) {
      return `<table>${rows.map(([key, value]) => `<tr><th>${key}</th><td>${value ?? "-"}</td></tr>`).join("")}</table>`;
    }

    function listSection(title, items, render) {
      return `<div class="panel" style="margin-top:14px;"><h3>${title}</h3><div class="list" style="margin-top:12px;">${items.length ? items.map(render).join("") : `<div class="muted">No ${title.toLowerCase()}.</div>`}</div></div>`;
    }

    async function selectKeyword(keywordId) {
      state.selectedId = keywordId;
      renderKeywords();
      const data = await loadJson(`/api/keywords/${keywordId}`);
      const serp = data.serp || { competition: {}, pages: [] };
      document.getElementById("detail").innerHTML = `
        <h2>${data.keyword.term}</h2>
        ${kvRows([
          ["Source", data.keyword.source],
          ["Seed", data.keyword.seed_keyword],
          ["Intent", data.keyword.intent],
          ["Trend", data.keyword.trend],
          ["Score", data.keyword.score],
          ["Volume", data.keyword.volume],
          ["Difficulty", data.keyword.difficulty],
          ["Discovered", data.keyword.discovered_at],
          ["Rankable", serp.competition.rankable],
          ["Competition", serp.competition.competition_level],
          ["Angle", serp.competition.recommended_content_angle],
        ])}
        ${listSection("SERP Pages", serp.pages, page => `<div class="panel"><div class="term">${page.title}</div><div class="muted">${page.domain}</div><div style="margin-top:8px;"><a href="${page.url}" target="_blank" rel="noreferrer">${page.url}</a></div></div>`)}
        ${listSection("Scraped Competitors", data.competitors, page => `<div class="panel"><div class="term">${page.title}</div><div class="chips"><span class="chip">${page.word_count} words</span><span class="chip">${page.reading_time_min} min</span></div><div style="margin-top:8px;"><a href="${page.url}" target="_blank" rel="noreferrer">${page.url}</a></div></div>`)}
        ${data.brief ? `<div class="panel" style="margin-top:14px;"><h3>Brief</h3>${kvRows([
          ["Title", data.brief.title],
          ["Type", data.brief.content_type],
          ["Tone", data.brief.tone],
          ["Word count target", data.brief.word_count_target],
          ["Secondary keywords", data.brief.secondary_keywords.join(", ")],
          ["H2 structure", data.brief.suggested_h2_structure.join(" | ")],
          ["Questions", data.brief.questions_to_answer.join(" | ")],
        ])}</div>` : ""}
        ${listSection("Articles", data.articles, article => `<div class="panel"><div class="term">${article.title}</div><div class="chips"><span class="chip">${article.status}</span><span class="chip">${article.word_count} words</span>${article.latest_rank_position ? `<span class="chip">rank ${article.latest_rank_position}</span>` : ""}</div><div class="muted" style="margin-top:8px;">${article.file_path}</div>${article.content_preview ? `<pre>${article.content_preview}</pre>` : ""}</div>`)}
      `;
    }

    loadJson("/api/dashboard").then(renderDashboard).catch(error => {
      document.getElementById("detail").innerHTML = `<div class="muted">${error.message}</div>`;
    });
  </script>
</body>
</html>"""


class ViewerHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, settings: Settings, **kwargs):
        self.settings = settings
        super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html(HTML)
            return
        if parsed.path == "/api/dashboard":
            self._json(load_dashboard(self.settings))
            return
        if parsed.path.startswith("/api/keywords/"):
            keyword_id = parsed.path.removeprefix("/api/keywords/")
            detail = load_keyword_detail(self.settings, keyword_id)
            if detail is None:
                self._json({"error": "keyword not found"}, status=404)
                return
            self._json(detail)
            return
        self._json({"error": "not found"}, status=404)

    def log_message(self, format, *args):  # noqa: A003
        return

    def _html(self, body: str, status: int = 200):
        payload = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, payload: dict, status: int = 200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve_viewer(settings: Settings, host: str, port: int) -> None:
    handler = partial(ViewerHandler, settings=settings)
    with ThreadingHTTPServer((host, port), handler) as server:
        server.serve_forever()
