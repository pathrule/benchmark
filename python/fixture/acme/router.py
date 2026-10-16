"""Exact-path routing with per-route options."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .http import Request, Response

Handler = Callable[[Request], Response]


@dataclass
class Route:
    path: str
    handler: Handler
    options: dict = field(default_factory=dict)

    def accepts(self, method: str) -> bool:
        methods = self.options.get("methods")
        return not methods or method in methods


class Router:
    def __init__(self) -> None:
        self._routes: list[Route] = []

    def add(self, route: Route) -> None:
        self._routes.append(route)

    def routes(self) -> list[Route]:
        return list(self._routes)

    def match(self, request: Request) -> Route | None:
        for route in self._routes:
            if route.path == request.path and route.accepts(request.method):
                return route
        return None
