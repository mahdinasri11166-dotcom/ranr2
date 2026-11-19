# -*- coding: utf-8 -*-
"""Simple model router / health proxy on :8770"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
LLAMA = "http://127.0.0.1:8080"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[router] {args[0]}")

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/", "/health"):
            llama_ok = False
            try:
                with urlopen(LLAMA + "/health", timeout=2) as r:
                    llama_ok = r.status == 200
            except Exception:
                pass
            models = [p.name for p in (ROOT / "models").glob("*.gguf")] if (ROOT / "models").exists() else []
            return self._json(200, {"ok": True, "llama": llama_ok, "models": models})
        if self.path == "/v1/models":
            models = [{"id": p.name, "object": "model"} for p in sorted((ROOT / "models").glob("*.gguf"))]
            return self._json(200, {"object": "list", "data": models})
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path not in ("/v1/chat/completions", "/chat"):
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        try:
            req = Request(LLAMA + "/v1/chat/completions", data=raw, headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(req, timeout=300) as r:
                body = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self._json(502, {"error": str(e)})


def main():
    print("Model router http://127.0.0.1:8770  ->", LLAMA)
    HTTPServer(("127.0.0.1", 8770), Handler).serve_forever()


if __name__ == "__main__":
    main()
