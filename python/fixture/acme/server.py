"""Serve an App over HTTP with the standard library server."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .app import App
from .http import Request


def serve(app: App, host: str = "127.0.0.1", port: int = 8080) -> None:
    class Handler(BaseHTTPRequestHandler):
        def _dispatch(self) -> None:
            length = int(self.headers.get("Content-Length", "0") or 0)
            body = self.rfile.read(length) if length else b""
            response = app.handle(Request(self.command, self.path, dict(self.headers.items()), body))
            self.send_response(response.status)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.send_header("Content-Length", str(len(response.body)))
            self.end_headers()
            self.wfile.write(response.body)

        do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = _dispatch

        def log_message(self, format, *args):  # noqa: A002
            return

    ThreadingHTTPServer((host, port), Handler).serve_forever()
