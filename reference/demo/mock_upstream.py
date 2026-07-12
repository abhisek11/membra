"""A fake OpenAI/Claude-compatible model server so the whole demo runs offline.

In production this is NOT needed — SENTRA_UPSTREAM simply points at the real
provider, e.g.  https://api.openai.com  or  https://api.anthropic.com .
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8090


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(length) or b"{}")
        msgs = payload.get("messages", [])
        last = next((m["content"] for m in reversed(msgs) if m.get("role") == "user"), "")
        reply = f"[mock-model] I received your (sanitized) message: {last[:120]}"
        out = {
            "id": "mock-1", "object": "chat.completion",
            "model": payload.get("model", "mock-gpt"),
            "choices": [{"index": 0, "message": {"role": "assistant", "content": reply},
                         "finish_reason": "stop"}],
        }
        data = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


if __name__ == "__main__":
    print(f"Mock upstream model on http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
