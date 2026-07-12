"""Self-contained live dashboard (no external CDN — CSP-safe, works offline)."""

DASHBOARD_HTML = """<!doctype html><html><head><meta charset="utf-8">
<title>Sentra — AI Security Console</title>
<style>
 body{font:14px/1.5 system-ui,sans-serif;margin:0;background:#0b0f19;color:#e5e9f0}
 header{padding:18px 24px;background:#111827;border-bottom:1px solid #1f2937}
 h1{margin:0;font-size:18px}h1 span{color:#38bdf8}
 .sub{color:#94a3b8;font-size:12px;margin-top:2px}
 .stats{display:flex;gap:12px;padding:16px 24px;flex-wrap:wrap}
 .card{background:#111827;border:1px solid #1f2937;border-radius:10px;padding:14px 18px;min-width:120px}
 .card b{font-size:24px;display:block}
 .block b{color:#f87171}.quarantine b{color:#fbbf24}.redact b{color:#38bdf8}.allow b{color:#34d399}
 table{width:100%;border-collapse:collapse;margin:8px 0}
 th,td{text-align:left;padding:8px 24px;border-bottom:1px solid #1f2937;font-size:13px}
 th{color:#94a3b8;font-weight:600}
 .tag{padding:2px 8px;border-radius:6px;font-size:11px;font-weight:600}
 .t-block{background:#7f1d1d;color:#fecaca}.t-quarantine{background:#78350f;color:#fde68a}
 .t-redact{background:#075985;color:#bae6fd}.t-allow{background:#064e3b;color:#a7f3d0}
 code{color:#cbd5e1}
</style></head><body>
<header><h1><span>◈ Sentra</span> — AI Security Console</h1>
<div class="sub">Live inspection of every AI interaction • auto-refresh 2s</div></header>
<div class="stats" id="stats"></div>
<table><thead><tr><th>Time</th><th>User</th><th>Action</th><th>Reasons</th><th>Preview</th></tr></thead>
<tbody id="rows"></tbody></table>
<script>
async function tick(){
 const r=await fetch('/events');const d=await r.json();
 const s=d.stats||{};
 document.getElementById('stats').innerHTML=
   card('allow','Allowed',s.allow||0)+card('redact','Redacted',s.redact||0)+
   card('quarantine','Quarantined',s.quarantine||0)+card('block','Blocked',s.block||0);
 document.getElementById('rows').innerHTML=(d.events||[]).map(e=>{
   const t=new Date(e.ts*1000).toLocaleTimeString();
   const rs=(JSON.parse(e.reasons||'[]')).join(', ');
   return `<tr><td>${t}</td><td>${e.user}</td>
     <td><span class="tag t-${e.action}">${e.action}</span></td>
     <td>${rs}</td><td><code>${esc(e.preview||'')}</code></td></tr>`;
 }).join('');
}
function card(c,l,n){return `<div class="card ${c}"><b>${n}</b>${l}</div>`}
function esc(s){return s.replace(/[&<>]/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[x]))}
tick();setInterval(tick,2000);
</script></body></html>"""
