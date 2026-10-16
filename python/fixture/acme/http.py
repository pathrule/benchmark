"""Request and Response values. Handlers take a Request and return a Response."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from urllib.parse import parse_qsl, urlsplit


@dataclass
class Request:
    method: str
    target: str
    headers: dict = field(default_factory=dict)
    body: bytes = b""

    @property
    def path(self) -> str:
        return urlsplit(self.target).path

    @property
    def query(self) -> str:
        return urlsplit(self.target).query

    def query_pairs(self) -> list[tuple[str, str]]:
        return parse_qsl(self.query, keep_blank_values=True)

    def header(self, name: str, default: str | None = None) -> str | None:
        for key, value in self.headers.items():
            if key.lower() == name.lower():
                return value
        return default


@dataclass
class Response:
    status: int = 200
    body: bytes = b""
    headers: dict = field(default_factory=dict)

    @classmethod
    def text(cls, text: str, status: int = 200) -> "Response":
        return cls(status, text.encode(), {"Content-Type": "text/plain; charset=utf-8"})

    @classmethod
    def json(cls, value, status: int = 200) -> "Response":
        return cls(status, json.dumps(value).encode(), {"Content-Type": "application/json"})

    def header(self, name: str, default: str | None = None) -> str | None:
        for key, value in self.headers.items():
            if key.lower() == name.lower():
                return value
        return default
