"""HTML templates for the Sentra SaaS — marketing site, auth, docs, dashboard.
All CSS inline / offline (no CDN). One shared layout for a cohesive design.
"""
import html

CSS = """
:root{--bg:#0b0f19;--panel:#111827;--panel2:#0f1626;--line:#1f2937;
  --txt:#e5e9f0;--mut:#94a3b8;--cyan:#38bdf8;--violet:#a78bfa;--green:#34d399;
  --red:#f87171;--amber:#fbbf24}
*{box-sizing:border-box}
body{margin:0;font:15px/1.6 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;
  background:var(--bg);color:var(--txt)}
a{color:var(--cyan);text-decoration:none}a:hover{text-decoration:underline}
.nav{display:flex;align-items:center;gap:22px;padding:16px 34px;
  border-bottom:1px solid var(--line);background:rgba(17,24,39,.7);
  position:sticky;top:0;backdrop-filter:blur(8px);z-index:10}
.brand{font-weight:800;font-size:18px;margin-right:auto}
.brand b{color:var(--cyan)}
.nav a{color:var(--mut);font-size:14px}.nav a:hover{color:var(--txt);text-decoration:none}
.btn{background:var(--cyan);color:#04121e;padding:9px 16px;border-radius:8px;
  font-weight:700;border:0;cursor:pointer;font-size:14px;display:inline-block}
.btn:hover{text-decoration:none;filter:brightness(1.08)}
.btn.ghost{background:transparent;color:var(--txt);border:1px solid var(--line)}
.wrap{max-width:1040px;margin:0 auto;padding:0 24px}
.hero{text-align:center;padding:90px 24px 60px}
.hero h1{font-size:46px;line-height:1.1;margin:0 0 18px;letter-spacing:-1px}
.hero h1 span{background:linear-gradient(90deg,var(--cyan),var(--violet));
  -webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{font-size:19px;color:var(--mut);max-width:640px;margin:0 auto 30px}
.pill{display:inline-block;border:1px solid var(--line);color:var(--mut);
  padding:5px 13px;border-radius:999px;font-size:12.5px;margin-bottom:22px}
.grid{display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));margin:34px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px}
.card h3{margin:0 0 8px;font-size:16px}.card p{color:var(--mut);margin:0;font-size:14px}
.card .ico{font-size:22px;margin-bottom:10px}
h2.sec{font-size:26px;margin:56px 0 6px;text-align:center}
.sub{color:var(--mut);text-align:center;margin:0 auto 10px;max-width:620px}
pre{background:#0a1020;border:1px solid var(--line);border-radius:10px;padding:16px;
  overflow:auto;font:13px/1.55 ui-monospace,Menlo,Consolas,monospace;color:#cbd5e1}
code{font-family:ui-monospace,Menlo,Consolas,monospace}
.steps{counter-reset:s;display:grid;gap:14px;margin:26px 0}
.step{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:18px 20px;position:relative;padding-left:60px}
.step:before{counter-increment:s;content:counter(s);position:absolute;left:18px;top:16px;
  width:28px;height:28px;border-radius:50%;background:var(--cyan);color:#04121e;
  font-weight:800;display:grid;place-items:center}
footer{border-top:1px solid var(--line);color:var(--mut);text-align:center;
  padding:30px;margin-top:60px;font-size:13px}
.authbox{max-width:400px;margin:60px auto;background:var(--panel);border:1px solid var(--line);
  border-radius:16px;padding:30px}
.authbox h2{margin:0 0 6px}.authbox p.m{color:var(--mut);margin:0 0 20px;font-size:14px}
label{display:block;font-size:13px;color:var(--mut);margin:12px 0 5px}
input{width:100%;padding:11px;background:#0a1020;border:1px solid var(--line);
  border-radius:8px;color:var(--txt);font-size:14px}
.err{background:#3b1116;border:1px solid #7f1d1d;color:#fecaca;padding:10px 12px;
  border-radius:8px;font-size:13px;margin-bottom:12px}
.ok{background:#062e22;border:1px solid #065f46;color:#a7f3d0;padding:12px;
  border-radius:8px;font-size:13px;margin-bottom:12px}
.kv{display:flex;gap:10px;align-items:center;background:#0a1020;border:1px solid var(--line);
  border-radius:8px;padding:10px 12px;margin:8px 0;font-family:ui-monospace,monospace;font-size:13px;
  word-break:break-all}
.kv b{color:var(--mut);font-family:system-ui;min-width:110px}
.stats{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}
.stat{flex:1;min-width:130px;background:var(--panel);border:1px solid var(--line);
  border-radius:12px;padding:16px 18px}
.stat b{font-size:28px;display:block}
.s-allow b{color:var(--green)}.s-redact b{color:var(--cyan)}
.s-quarantine b{color:var(--amber)}.s-block b{color:var(--red)}
table{width:100%;border-collapse:collapse;margin-top:8px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line);font-size:13px}
th{color:var(--mut)}
.tag{padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700}
.t-block{background:#7f1d1d;color:#fecaca}.t-quarantine{background:#78350f;color:#fde68a}
.t-redact{background:#075985;color:#bae6fd}.t-allow{background:#064e3b;color:#a7f3d0}
.dashgrid{display:grid;grid-template-columns:1fr;gap:20px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:22px}
.muted{color:var(--mut)}.mono{font-family:ui-monospace,monospace}
.warn{color:var(--amber);font-size:12.5px}
.doc h2{margin-top:38px;border-bottom:1px solid var(--line);padding-bottom:6px}
.doc h3{margin-top:26px;color:var(--cyan)}
.toc{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:20px 0}
.toc a{display:inline-block;margin:3px 12px 3px 0;font-size:14px}
"""


def _nav(tenant=None):
    right = ('<a href="/dashboard">Dashboard</a><a href="/logout">Log out</a>'
             if tenant else
             '<a href="/login">Log in</a><a class="btn" href="/signup">Get API Key</a>')
    return f"""<div class="nav"><div class="brand">◈ <b>Sentra</b></div>
      <a href="/">Home</a><a href="/products">Product</a>
      <a href="/docs">Docs</a><a href="/pricing">Pricing</a>{right}</div>"""


def layout(title, body, tenant=None):
    return f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head>
<body>{_nav(tenant)}{body}
<footer>◈ Sentra — a security immune system for the AI era · self-hostable · © 2026</footer>
</body></html>"""


# ----------------------------- pages ---------------------------------------

def landing(tenant=None):
    features = [
        ("🦠", "Injection & jailbreak defense", "Block prompt-injection and jailbreaks inbound — regex signals + a trained ML classifier that catches paraphrased attacks."),
        ("🩸", "AI-DLP", "Redact secrets & PII (API keys, tokens, SSNs, cards) before they leak to any AI provider. Stay GDPR / DPDP compliant."),
        ("🧠", "Behavioral immune memory", "Learn each user's normal AI-usage fingerprint and flag anomalies — catch account takeover & insider exfiltration."),
        ("🛡️", "Agent guardrails", "Gate autonomous-agent actions (shell, delete, external POST, payments) behind risk-based allow / approve / deny policy."),
    ]
    cards = "".join(
        f'<div class="card"><div class="ico">{i}</div><h3>{t}</h3><p>{d}</p></div>'
        for i, t, d in features)
    body = f"""
    <div class="hero">
      <div class="pill">Security for the AI era — not AI for security</div>
      <h1>Defend every <span>AI interaction</span><br>in your organization</h1>
      <p>Firewalls and antivirus can't see prompt injection, data leaking into
         ChatGPT, or a rogue AI agent. Sentra is the inline immune layer that can.</p>
      <a class="btn" href="/signup">Get your API key — free</a>
      &nbsp;<a class="btn ghost" href="/docs">Read the docs</a>
    </div>
    <div class="wrap">
      <div class="grid">{cards}</div>

      <h2 class="sec">Install once. Everything just works.</h2>
      <p class="sub">Sentra speaks the OpenAI/Anthropic protocol. Point your client at it — one line — and every AI call is inspected.</p>
      <pre># before
client = OpenAI(base_url="https://api.openai.com/v1")

# after  — the entire integration
client = OpenAI(
    base_url="https://gateway.sentra.io/v1",
    default_headers={{"X-Sentra-Client-Id": "sentra_ci_...",
                      "X-Sentra-Client-Secret": "sentra_sk_..."}})</pre>

      <h2 class="sec">How it works</h2>
      <div class="steps">
        <div class="step"><b>Sign up</b> and get a Client ID + Secret for your tenant.</div>
        <div class="step"><b>Point your AI client</b> at the Sentra gateway (or wrap it with our SDK).</div>
        <div class="step"><b>Every prompt & response is inspected</b> — injection blocked, secrets redacted, anomalies flagged.</div>
        <div class="step"><b>Watch it live</b> in your multitenant dashboard with a full audit trail.</div>
      </div>
      <div style="text-align:center;margin:40px 0">
        <a class="btn" href="/signup">Create your free account</a>
      </div>
    </div>"""
    return layout("Sentra — AI-era security", body, tenant)


def products(tenant=None):
    body = f"""<div class="wrap">
      <h2 class="sec">The Sentra platform</h2>
      <p class="sub">Four detection layers, one inline gateway, a multitenant control plane.</p>
      <div class="grid">
        <div class="card"><h3>1 · Inbound Defense</h3><p>Prompt-injection & jailbreak
          detection. Ensemble of explainable regex signals and a from-scratch logistic-
          regression classifier on hashed n-gram features that generalizes to paraphrases.</p></div>
        <div class="card"><h3>2 · Outbound AI-DLP</h3><p>Detects & redacts secrets
          (AWS/OpenAI/GitHub keys, JWTs, private keys via format + Shannon entropy) and
          PII (email, SSN, Luhn-validated cards, phones) before they leave your org.</p></div>
        <div class="card"><h3>3 · Behavioral Immune Memory</h3><p>Per-user rolling
          baselines (message size, request rate) with z-score anomaly scoring to catch
          slow-drip exfiltration that keyword filters miss.</p></div>
        <div class="card"><h3>4 · Agent Guardrails</h3><p>Risk-tiered authorization for
          autonomous-agent tool calls: read-only auto-allows, destructive or exfiltrating
          actions require human approval or are denied.</p></div>
      </div>
      <h2 class="sec">Deployment</h2>
      <p class="sub">Cloud gateway, self-hosted container, or in-process SDK — same engine, your choice.</p>
      <div class="grid">
        <div class="card"><h3>Transparent Gateway</h3><p>Drop-in OpenAI/Anthropic-compatible
          proxy. Zero app changes beyond the base URL.</p></div>
        <div class="card"><h3>SDK Wrapper</h3><p><code>guard(OpenAI())</code> — inspect calls
          in-process for teams that prefer code-level control.</p></div>
        <div class="card"><h3>Self-hosted</h3><p>Pure-stdlib core runs anywhere. Docker image
          for one-command deploy inside your VPC.</p></div>
      </div>
      <div style="text-align:center;margin:40px 0"><a class="btn" href="/signup">Get started</a></div>
    </div>"""
    return layout("Sentra — Product", body, tenant)


def pricing(tenant=None):
    tiers = [
        ("Free", "$0", ["1 tenant", "10k inspected calls/mo", "All 4 detectors", "Community support"]),
        ("Team", "$99/mo", ["Unlimited users", "1M calls/mo", "Custom policies", "90-day audit retention", "Email support"]),
        ("Enterprise", "Custom", ["Self-hosted / VPC", "SSO & RBAC", "Unlimited retention", "SLA & DPA", "Dedicated support"]),
    ]
    cards = ""
    for name, price, feats in tiers:
        li = "".join(f"<p>✓ {f}</p>" for f in feats)
        cards += (f'<div class="card"><h3>{name}</h3>'
                  f'<div style="font-size:30px;font-weight:800;margin:6px 0">{price}</div>'
                  f'{li}<div style="margin-top:14px"><a class="btn" href="/signup">Choose</a></div></div>')
    body = f"""<div class="wrap"><h2 class="sec">Simple pricing</h2>
      <p class="sub">Built to be affordable for SMEs, scalable for enterprises.</p>
      <div class="grid">{cards}</div></div>"""
    return layout("Sentra — Pricing", body, tenant)


def auth_page(kind, error=None):
    is_signup = kind == "signup"
    title = "Create your account" if is_signup else "Log in"
    org = '<label>Organization</label><input name="org" placeholder="Acme Inc" required>' if is_signup else ""
    err = f'<div class="err">{html.escape(error)}</div>' if error else ""
    alt = ('Already have an account? <a href="/login">Log in</a>' if is_signup
           else "New here? <a href=\"/signup\">Create an account</a>")
    body = f"""<div class="authbox"><h2>{title}</h2>
      <p class="m">{'Get a Client ID & Secret in seconds.' if is_signup else 'Access your Sentra dashboard.'}</p>
      {err}
      <form method="post" action="/{kind}">
        {org}
        <label>Work email</label><input name="email" type="email" placeholder="you@acme.com" required>
        <label>Password</label><input name="password" type="password" placeholder="••••••••" required>
        <div style="margin-top:18px"><button class="btn" style="width:100%">{title}</button></div>
      </form>
      <p class="m" style="margin-top:16px">{alt}</p></div>"""
    return layout(f"Sentra — {title}", body)


def signup_success(creds):
    body = f"""<div class="authbox" style="max-width:560px">
      <div class="ok">✅ Account created. Save these now — the secret is shown only once.</div>
      <h2>Your API credentials</h2>
      <div class="kv"><b>Client ID</b><span class="mono">{creds['client_id']}</span></div>
      <div class="kv"><b>Client Secret</b><span class="mono">{creds['client_secret']}</span></div>
      <p class="warn">⚠ Store the secret in a password manager or env var. We only keep a hash — you can regenerate it in the dashboard but cannot retrieve it.</p>
      <div style="margin-top:16px"><a class="btn" href="/dashboard">Go to dashboard →</a></div>
      <pre style="margin-top:18px">export SENTRA_CLIENT_ID={creds['client_id']}
export SENTRA_CLIENT_SECRET={creds['client_secret']}
</pre>
    </div>"""
    return layout("Sentra — Credentials", body)


def dashboard(tenant, stats, events, new_secret=None):
    s = lambda k: stats.get(k, 0)
    rows = ""
    for e in events:
        import json as _j
        rs = ", ".join(_j.loads(e["reasons"] or "[]"))
        t = e["preview"] or ""
        rows += (f'<tr><td class="muted">{_fmt(e["ts"])}</td><td>{html.escape(e["user"] or "")}</td>'
                 f'<td><span class="tag t-{e["action"]}">{e["action"]}</span></td>'
                 f'<td>{html.escape(rs)}</td><td class="mono">{html.escape(t[:70])}</td></tr>')
    rows = rows or '<tr><td colspan="5" class="muted">No traffic yet — make a call through the gateway.</td></tr>'
    secret_block = ""
    if new_secret:
        secret_block = (f'<div class="ok">New secret generated (shown once): '
                        f'<span class="mono">{new_secret}</span></div>')
    body = f"""<div class="wrap" style="padding-top:26px">
      <h2 style="margin:6px 0">Dashboard · {html.escape(tenant['org'] or tenant['email'])}</h2>
      <p class="muted">Plan: {tenant['plan']} · tenant #{tenant['id']}</p>

      <div class="stats">
        <div class="stat s-allow"><b>{s('allow')}</b>Allowed</div>
        <div class="stat s-redact"><b>{s('redact')}</b>Redacted</div>
        <div class="stat s-quarantine"><b>{s('quarantine')}</b>Quarantined</div>
        <div class="stat s-block"><b>{s('block')}</b>Blocked</div>
      </div>

      <div class="dashgrid">
        <div class="panel">
          <h3 style="margin-top:0">API credentials</h3>
          {secret_block}
          <div class="kv"><b>Client ID</b><span class="mono">{tenant['client_id']}</span></div>
          <div class="kv"><b>Client Secret</b><span class="muted">•••••••• (hashed — not retrievable)</span></div>
          <form method="post" action="/dashboard/regen" style="margin-top:10px">
            <button class="btn ghost">Regenerate secret</button></form>
          <p class="muted" style="font-size:13px;margin-top:12px">Use these to authenticate the gateway/SDK. See <a href="/docs">the docs</a>.</p>
        </div>

        <div class="panel">
          <h3 style="margin-top:0">Live threat feed <span class="muted" style="font-size:12px">(auto-refresh 3s)</span></h3>
          <table><thead><tr><th>Time</th><th>User</th><th>Action</th><th>Reasons</th><th>Preview</th></tr></thead>
          <tbody id="feed">{rows}</tbody></table>
        </div>
      </div></div>
    <script>
      async function refresh(){{
        try{{
          const r=await fetch('/api/events');const d=await r.json();
          document.getElementById('feed').innerHTML=(d.events||[]).map(e=>{{
            const rs=(JSON.parse(e.reasons||'[]')).join(', ');
            const t=new Date(e.ts*1000).toLocaleTimeString();
            return `<tr><td class="muted">${{t}}</td><td>${{e.user||''}}</td>
              <td><span class="tag t-${{e.action}}">${{e.action}}</span></td>
              <td>${{rs}}</td><td class="mono">${{(e.preview||'').replace(/[<>&]/g,'')}}</td></tr>`;
          }}).join('')|| '<tr><td colspan=5 class=muted>No traffic yet.</td></tr>';
        }}catch(e){{}}
      }}
      setInterval(refresh,3000);
    </script>"""
    return layout("Sentra — Dashboard", body, tenant)


def _fmt(ts):
    import datetime
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
    except Exception:
        return ""
