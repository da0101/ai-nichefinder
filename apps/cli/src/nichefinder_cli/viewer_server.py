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
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Nichefinder — SEO Research</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fira+Code:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root{--blue:#1E40AF;--blue-lt:#EFF6FF;--amber:#F59E0B;--amber-lt:#FFFBEB;--bg:#F1F5F9;--card:#FFF;--ink:#0F172A;--muted:#64748B;--bdr:#E2E8F0;--green:#059669;--yel:#D97706;--red:#DC2626}
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Inter',ui-sans-serif,sans-serif;background:var(--bg);color:var(--ink);font-size:14px;height:100vh;overflow:hidden;display:flex;flex-direction:column}
    .mono{font-family:'Fira Code',ui-monospace,monospace}
    header{background:var(--blue);color:#fff;padding:14px 24px;display:flex;align-items:center;gap:16px;flex-shrink:0}
    header h1{font-size:18px;font-weight:700}
    header .sub{font-size:12px;opacity:.75}
    .stats-bar{display:flex;gap:0;background:var(--card);border-bottom:1px solid var(--bdr);flex-shrink:0}
    .stat{padding:12px 24px;border-right:1px solid var(--bdr)}
    .stat-val{font-size:22px;font-weight:700;color:var(--blue);font-family:'Fira Code',monospace}
    .stat-lbl{font-size:11px;color:var(--muted);margin-top:2px}
    main{display:grid;grid-template-columns:300px 1fr;flex:1;overflow:hidden}
    .sidebar{border-right:1px solid var(--bdr);overflow-y:auto;background:var(--card)}
    .sidebar-hdr{padding:10px 16px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border-bottom:1px solid var(--bdr);position:sticky;top:0;background:var(--card)}
    .kw{padding:12px 16px;border-bottom:1px solid var(--bdr);cursor:pointer;border-left:3px solid transparent}
    .kw:hover{background:var(--blue-lt)}
    .kw.active{background:var(--blue-lt);border-left-color:var(--blue)}
    .kw-term{font-weight:600;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    .kw-row{display:flex;gap:6px;margin-top:6px;align-items:center;flex-wrap:wrap}
    .badge{font-family:'Fira Code',monospace;font-size:12px;font-weight:600;padding:2px 7px;border-radius:5px}
    .b-hi{background:#D1FAE5;color:#065F46}.b-mid{background:#FEF3C7;color:#92400E}.b-lo{background:#FEE2E2;color:#991B1B}
    .tag{font-size:11px;padding:2px 6px;border-radius:4px;background:var(--bg);color:var(--muted)}
    .tag-green{background:#D1FAE5;color:#065F46}
    .detail{overflow-y:auto;padding:24px;display:flex;flex-direction:column;gap:14px}
    .detail-empty{display:flex;align-items:center;justify-content:center;height:100%;color:var(--muted);font-size:15px}
    .card{background:var(--card);border:1px solid var(--bdr);border-radius:12px;padding:20px}
    .card-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);margin-bottom:16px}
    .big-score{font-size:52px;font-weight:700;font-family:'Fira Code',monospace;line-height:1;text-align:center}
    .pri-badge{display:inline-block;padding:4px 14px;border-radius:999px;font-weight:600;font-size:12px}
    .pri-high{background:#D1FAE5;color:#065F46}.pri-med{background:#FEF3C7;color:#92400E}.pri-low{background:#FEE2E2;color:#991B1B}
    .score-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px}
    .brow{display:grid;grid-template-columns:130px 1fr 38px 44px;align-items:center;gap:8px;margin-bottom:10px}
    .blbl{font-size:13px;color:var(--ink)}.bhint{font-size:11px;color:var(--muted)}
    .btrack{height:7px;background:var(--bg);border-radius:4px;overflow:hidden}
    .bfill{height:100%;border-radius:4px}
    .bval{font-family:'Fira Code',monospace;font-size:13px;font-weight:600;text-align:right}
    .bwt{font-size:10px;color:var(--muted);text-align:right}
    .action-bar{display:flex;align-items:center;gap:10px}
    .act{padding:6px 16px;border-radius:8px;font-weight:600;font-size:13px}
    .act-new{background:var(--amber);color:#fff}.act-rew{background:#6366F1;color:#fff}.act-skip{background:var(--bg);color:var(--muted)}
    .why{font-size:13px;color:var(--muted);line-height:1.5}
    .info-table{width:100%;border-collapse:collapse;font-size:14px}
    .info-table td{padding:9px 0;border-bottom:1px solid var(--bdr);vertical-align:top}
    .info-table td:first-child{color:var(--muted);width:160px;font-weight:500}
    .info-table tr:last-child td{border-bottom:none}
    .brief-card{background:var(--amber-lt);border:1px solid #FDE68A;border-radius:12px;padding:20px}
    .brief-title{font-size:17px;font-weight:700;margin-bottom:12px}
    .brief-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:13px}
    .outline-list{margin:10px 0 0 20px;font-size:13px;line-height:1.8}
    .pages-card{background:var(--card);border:1px solid var(--bdr);border-radius:12px;overflow:hidden}
    .pages-hdr{padding:10px 16px;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);border-bottom:1px solid var(--bdr)}
    .page-item{padding:11px 16px;border-bottom:1px solid var(--bdr)}
    .page-item:last-child{border-bottom:none}
    .page-title{font-weight:600;font-size:13px}
    .page-url{font-size:11px;color:var(--muted);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}
    @media(max-width:768px){main{grid-template-columns:1fr}.sidebar{max-height:260px}}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Nichefinder</h1>
      <div class="sub">Local SEO research viewer — read-only</div>
    </div>
  </header>
  <div class="stats-bar">
    <div class="stat"><div class="stat-val mono" id="s-kw">—</div><div class="stat-lbl">Keywords found</div></div>
    <div class="stat"><div class="stat-val mono" id="s-br">—</div><div class="stat-lbl">Briefs ready</div></div>
    <div class="stat"><div class="stat-val mono" id="s-ar">—</div><div class="stat-lbl">Articles drafted</div></div>
    <div class="stat"><div class="stat-val mono" id="s-pu">—</div><div class="stat-lbl">Published</div></div>
  </div>
  <main>
    <div class="sidebar">
      <div class="sidebar-hdr">Keywords by score</div>
      <div id="kw-list"></div>
    </div>
    <div class="detail" id="detail">
      <div class="detail-empty">Select a keyword from the list to see its analysis.</div>
    </div>
  </main>
  <script>
    const S={id:null,keywords:[]};
    async function api(p){const r=await fetch(p);if(!r.ok)throw new Error(await r.text());return r.json();}
    function sc(v){return v>=70?'green':v>=50?'yel':'red'}
    function bc(v){return v>=70?'b-hi':v>=50?'b-mid':'b-lo'}
    function priCls(p){return p==='high'?'pri-high':p==='medium'?'pri-med':'pri-low'}
    function scoreColor(v){return v>=70?'#059669':v>=50?'#D97706':'#DC2626'}
    function bar(v){const c=sc(v??0),w=Math.round(v??0);return `<div class="btrack"><div class="bfill" style="width:${w}%;background:var(--${c})"></div></div>`}
    function breakdown(bd){
      if(!bd)return '';
      const rows=[
        ['Search Demand','How many people search this (higher = more traffic potential)',bd.volume,'×0.25'],
        ['Ease of Ranking','Can you realistically rank? (higher = easier to beat competition)',bd.difficulty,'×0.30'],
        ['Trend Direction','Is this topic growing? Rising=100, Stable=50, Declining=0',bd.trend,'×0.20'],
        ['Commercial Value','Do searchers want to hire/buy? Transactional=100, Informational=60',bd.intent,'×0.15'],
        ['Low Competition','How easy are the search results to beat? Low competition=100',bd.competition,'×0.10'],
      ];
      return rows.map(([lbl,hint,val,wt])=>`<div class="brow">
        <div><div class="blbl">${lbl}</div><div class="bhint">${hint}</div></div>
        ${bar(val)}
        <div class="bval">${(val??0).toFixed(0)}</div>
        <div class="bwt">${wt}</div>
      </div>`).join('');
    }
    function renderDashboard(d){
      document.getElementById('s-kw').textContent=d.summary.total_keywords;
      document.getElementById('s-br').textContent=d.summary.briefed_keywords;
      document.getElementById('s-ar').textContent=d.summary.articles;
      document.getElementById('s-pu').textContent=d.summary.published_articles;
      S.keywords=d.keywords.sort((a,b)=>(b.score??0)-(a.score??0));
      renderSidebar();
      if(S.keywords.length)selectKeyword(S.keywords[0].id);
    }
    function renderSidebar(){
      const el=document.getElementById('kw-list');
      if(!S.keywords.length){el.innerHTML='<div style="padding:16px;color:var(--muted)">No keywords yet — run <code>seo research "..."</code> first.</div>';return;}
      el.innerHTML=S.keywords.map(kw=>{
        const s=kw.score??0;
        return `<div class="kw${kw.id===S.id?' active':''}" onclick="selectKeyword('${kw.id}')">
          <div class="kw-term" title="${kw.term}">${kw.term}</div>
          <div class="kw-row">
            <span class="badge ${bc(s)} mono">${s.toFixed(0)}</span>
            ${kw.intent?`<span class="tag">${kw.intent}</span>`:''}
            ${kw.trend?`<span class="tag">${kw.trend}</span>`:''}
            ${kw.has_brief?'<span class="tag tag-green">brief ready</span>':''}
          </div>
        </div>`;
      }).join('');
    }
    async function selectKeyword(id){
      S.id=id;renderSidebar();
      const det=document.getElementById('detail');
      det.innerHTML='<div class="detail-empty">Loading...</div>';
      try{
        const d=await api('/api/keywords/'+id);
        const kw=d.keyword,bd=d.score_breakdown,serp=d.serp||{},comp=serp.competition||{},pages=serp.pages||[];
        const s=kw.score??0;
        const actMap={new_article:['act-new','Write new article'],rewrite_existing:['act-rew','Rewrite existing article'],skip:['act-skip','Skip — not worth writing yet']};
        const [actCls,actLbl]=actMap[bd?.action]||['act-skip',bd?.action||'—'];
        det.innerHTML=`
          <h2 style="font-size:20px;font-weight:700">${kw.term}</h2>
          ${bd?`<div class="card">
            <div class="card-title">Opportunity Score</div>
            <div style="text-align:center;margin-bottom:20px">
              <div class="big-score" style="color:${scoreColor(s)}">${s.toFixed(0)}<span style="font-size:20px;color:var(--muted)">/100</span></div>
              <div style="margin-top:8px"><span class="pri-badge ${priCls(bd.priority)}">${(bd.priority||'').toUpperCase()} PRIORITY</span></div>
            </div>
            ${breakdown(bd)}
          </div>`:''}
          ${bd?`<div class="card">
            <div class="card-title">Recommendation</div>
            <div class="action-bar">
              <span class="act ${actCls}">${actLbl}</span>
              ${bd.why?`<span class="why">${bd.why}</span>`:''}
            </div>
          </div>`:''}
          <div class="card">
            <div class="card-title">Keyword Details</div>
            <table class="info-table">
              <tr><td>Search Intent</td><td>${kw.intent||'—'}</td></tr>
              <tr><td>Trend Direction</td><td>${kw.trend||'—'}</td></tr>
              <tr><td>Monthly Searches</td><td class="mono">${kw.volume!=null?kw.volume.toLocaleString():'unknown'}</td></tr>
              <tr><td>SEO Difficulty</td><td class="mono">${kw.difficulty!=null?kw.difficulty+'/100':'unknown'}</td></tr>
              <tr><td>Can You Rank?</td><td>${comp.rankable!=null?(comp.rankable?'Yes':'No — high-authority sites dominate'):'—'}</td></tr>
              <tr><td>Competition Level</td><td>${comp.competition_level||'—'}</td></tr>
              <tr><td>Discovered</td><td>${(kw.discovered_at||'').slice(0,10)||'—'}</td></tr>
            </table>
          </div>
          ${d.brief?`<div class="brief-card">
            <div class="card-title" style="color:#92400E">Content Brief</div>
            <div class="brief-title">${d.brief.title}</div>
            <div class="brief-grid">
              <div><strong>Format:</strong> ${d.brief.content_type||'—'}</div>
              <div><strong>Tone:</strong> ${d.brief.tone||'—'}</div>
              <div><strong>Target length:</strong> ${d.brief.word_count_target||'—'} words</div>
            </div>
            ${d.brief.suggested_h2_structure?.length?`<ul class="outline-list">${d.brief.suggested_h2_structure.map(h=>`<li>${h}</li>`).join('')}</ul>`:''}
          </div>`:''}
          ${pages.length?`<div class="pages-card">
            <div class="pages-hdr">Who currently ranks for this (top ${Math.min(5,pages.length)} results)</div>
            ${pages.slice(0,5).map((p,i)=>`<div class="page-item">
              <div class="page-title"><span style="color:var(--muted);margin-right:8px">#${p.position??i+1}</span>${p.title||'—'}</div>
              <div class="page-url"><a href="${p.url}" target="_blank" rel="noreferrer">${p.url}</a></div>
            </div>`).join('')}
          </div>`:''}
        `;
      }catch(e){det.innerHTML=`<div class="detail-empty" style="color:var(--red)">${e.message}</div>`;}
    }
    api('/api/dashboard').then(renderDashboard).catch(e=>{
      document.getElementById('detail').innerHTML=`<div style="padding:40px;text-align:center"><div style="font-size:16px;color:var(--red);margin-bottom:8px">Could not load data</div><div style="color:var(--muted)">${e.message}</div><div style="color:var(--muted);font-size:12px;margin-top:10px">Run <code>seo db init</code> first if the database is missing.</div></div>`;
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
