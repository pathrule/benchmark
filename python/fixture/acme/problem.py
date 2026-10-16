"""Problem responses (RFC 9457). Every error the toolkit itself answers goes through problem()."""

from __future__ import annotations

import json

from .http import Response

TYPE_BASE = "https://errors.acme.dev/"


def problem(status: int, title: str, detail: str, slug: str) -> Response:
    body = {"type": TYPE_BASE + slug, "title": title, "status": status, "detail": detail}
    return Response(status, json.dumps(body).encode(), {"Content-Type": "application/problem+json"})
