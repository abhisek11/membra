"""Rendered documentation page for the website (mirrors /docs/*.md)."""
from .templates import layout


def docs_page(tenant=None):
    body = r"""<div class="wrap doc" style="padding-top:20px">
    <h1>Sentra Documentation</h1>
    <p class="muted">Everything you need to secure your organization's AI layer.</p>
    <div class="toc"><b>Contents</b><br>
      <a href="#overview">Overview</a><a href="#quickstart">Quickstart</a>
      <a href="#auth">Authentication</a><a href="#gateway">Gateway integration</a>
      <a href="#sdk">SDK integration</a><a href="#agent">Agent guardrails</a>
      <a href="#api">API reference</a><a href="#flows">Sequence diagrams</a>
      <a href="#selfhost">Self-hosting</a>
    </div>

    <h2 id="overview">Overview</h2>
    <p>Sentra is an inline security layer for AI traffic. It inspects every prompt
    and response flowing between your apps and any LLM provider (OpenAI, Anthropic/
    Claude, Azure, …) and enforces policy across four layers:</p>
    <ul>
      <li><b>Inbound</b> — block prompt injection & jailbreaks (regex + ML ensemble).</li>
      <li><b>Outbound</b> — redact secrets & PII (AI-DLP).</li>
      <li><b>Behavioral</b> — per-user anomaly detection (immune memory).</li>
      <li><b>Agentic</b> — authorize autonomous-agent tool actions.</li>
    </ul>

    <h2 id="quickstart">Quickstart</h2>
    <div class="steps">
      <div class="step"><b>Create an account</b> at <code>/signup</code>. You receive a
        <code>client_id</code> and <code>client_secret</code> (shown once).</div>
      <div class="step"><b>Set env vars</b>:<pre>export SENTRA_CLIENT_ID=sentra_ci_...
export SENTRA_CLIENT_SECRET=sentra_sk_...</pre></div>
      <div class="step"><b>Point your AI client at the gateway</b> (below) and send traffic.</div>
      <div class="step"><b>Open your dashboard</b> to watch the live threat feed.</div>
    </div>

    <h2 id="auth">Authentication</h2>
    <p>Every API call must carry your tenant credentials, sent as headers:</p>
    <pre>X-Sentra-Client-Id:     sentra_ci_xxxxxxxxxxxx
X-Sentra-Client-Secret: sentra_sk_xxxxxxxxxxxxxxxxxxxxxxxx
X-Sentra-User:          alice@acme.com     # optional: who is making the call</pre>
    <p>The secret is verified against a stored hash. Events are isolated per tenant —
    you only ever see your own traffic. Rotate the secret anytime from the dashboard.</p>

    <h2 id="gateway">Gateway integration (zero code change)</h2>
    <p>Change one line — the <code>base_url</code> — and keep using your existing SDK:</p>
    <pre>from openai import OpenAI

client = OpenAI(
    base_url="https://gateway.sentra.io/v1",   # or http://localhost:8100/v1 self-hosted
    default_headers={
        "X-Sentra-Client-Id": os.environ["SENTRA_CLIENT_ID"],
        "X-Sentra-Client-Secret": os.environ["SENTRA_CLIENT_SECRET"],
    },
)
resp = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Summarize this ticket..."}],
)</pre>
    <p>Set <code>SENTRA_UPSTREAM</code> on the gateway to your real provider
    (<code>https://api.openai.com</code> or <code>https://api.anthropic.com</code>).</p>

    <h2 id="sdk">SDK integration (in-process)</h2>
    <pre>from sentra.sdk import guard
from openai import OpenAI

client = guard(OpenAI())            # inspects every call before it leaves
client.chat.completions.create(model="gpt-4o",
    messages=[{"role":"user","content":"..."}], user="alice@acme.com")</pre>

    <h2 id="agent">Agent guardrails</h2>
    <p>Before your autonomous agent executes a tool, ask Sentra to authorize it:</p>
    <pre>POST /v1/agent/authorize
{ "tool": "shell_exec", "args": {"cmd": "rm -rf /"} }

-> { "decision": "deny", "tier": "critical",
     "reasons": ["destructive_shell"], "tool": "shell_exec" }</pre>
    <p>Decisions: <code>allow</code> (auto-run), <code>approve</code> (pause for a
    human), <code>deny</code> (refuse). Only execute the tool on <code>allow</code>.</p>

    <h2 id="api">API reference</h2>
    <table>
      <tr><th>Method</th><th>Path</th><th>Purpose</th></tr>
      <tr><td>POST</td><td class="mono">/v1/chat/completions</td><td>Inspect + forward a chat completion (OpenAI-compatible)</td></tr>
      <tr><td>POST</td><td class="mono">/v1/agent/authorize</td><td>Authorize an autonomous-agent tool action</td></tr>
      <tr><td>GET</td><td class="mono">/api/events</td><td>Your tenant's recent events + stats (JSON)</td></tr>
    </table>
    <p>Response headers on every inspected call: <code>X-Sentra-Action</code>
    (allow/redact/quarantine/block) and <code>X-Sentra-Reasons</code>.</p>

    <h2 id="flows">Sequence diagrams</h2>

    <h3>1 · Signup & credential issuance</h3>
    <pre>
 User            Sentra Web           TenantStore (DB)
  |  POST /signup    |                      |
  |----------------->|                      |
  |                  |  create tenant       |
  |                  |  gen client_id       |
  |                  |  gen client_secret   |
  |                  |  store secret HASH   |
  |                  |--------------------->|
  |                  |         ok           |
  |                  |<---------------------|
  |  client_id +     |                      |
  |  client_secret   |   (secret shown      |
  |<-----------------|    ONCE)             |
    </pre>

    <h3>2 · Inline inspection of an AI call</h3>
    <pre>
 App/SDK        Sentra Gateway        Engine            LLM Provider
   |  POST /v1/chat    |                 |                    |
   |  + client creds   |                 |                    |
   |------------------>|                 |                    |
   |                   | verify tenant   |                    |
   |                   | inspect(text)   |                    |
   |                   |---------------->|                    |
   |                   |                 | injection? (regex+ML)
   |                   |                 | anomaly? (z-score)  |
   |                   |                 | DLP? (redact)       |
   |                   |   Decision      |                    |
   |                   |<----------------|                    |
   |          BLOCK ---X (never forwarded, safe refusal)      |
   |          REDACT ->| forward sanitized text ------------->|
   |          ALLOW  ->| forward as-is ---------------------->|
   |                   |         model response               |
   |<------------------|<-------------------------------------|
   |  + X-Sentra-Action / X-Sentra-Reasons headers           |
   |            (event logged to tenant's audit trail)        |
    </pre>

    <h3>3 · Autonomous-agent action authorization</h3>
    <pre>
 AI Agent        Sentra              AgentGuard
   |  propose tool   |                   |
   |  (shell_exec)   |                   |
   |---------------->| assess(tool,args) |
   |                 |------------------>|
   |                 |  arg signatures?  |
   |                 |  data egress?     |
   |                 |  category tier?   |
   |                 |   decision        |
   |                 |<------------------|
   |  allow/approve/ |                   |
   |  deny           |                   |
   |<----------------|                   |
   | (execute only on allow)            |
    </pre>

    <h2 id="selfhost">Self-hosting</h2>
    <pre># run everything (site + dashboard + gateway) on one port
python3 -m sentra.app          # -> http://localhost:8100

# point the gateway at your real provider
export SENTRA_UPSTREAM=https://api.openai.com

# or with Docker
docker build -t sentra .
docker run -p 8100:8100 -e SENTRA_UPSTREAM=https://api.openai.com sentra</pre>
    <p>The core is pure Python standard library — no dependencies, runs anywhere.</p>
    </div>"""
    return layout("Sentra — Docs", body, tenant)
