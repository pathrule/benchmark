"""The App: routes, options and the request pipeline."""

from __future__ import annotations

from .http import Request, Response
from .log import logger
from .middleware import Middleware, chain
from .options import APP_OPTIONS, ROUTE_OPTIONS
from .router import Handler, Route, Router


class App:
    def __init__(self, **options) -> None:
        for name in options:
            if name not in APP_OPTIONS:
                raise TypeError(f"unknown App option: {name}")
        self.request_log: bool = bool(options.get("request_log", False))
        self.max_header_bytes: int = int(options.get("max_header_bytes", 8192))
        self._router = Router()
        self._middlewares: list[Middleware] = []

    def route(self, path: str, handler: Handler, **options) -> Route:
        for name in options:
            if name not in ROUTE_OPTIONS:
                raise TypeError(f"unknown route option: {name}")
        route = Route(path, handler, dict(options))
        self._router.add(route)
        return route

    def routes(self) -> list[Route]:
        return self._router.routes()

    def use(self, middleware: Middleware) -> None:
        self._middlewares.append(middleware)

    def handle(self, request: Request) -> Response:
        header_bytes = sum(len(k) + len(v) for k, v in request.headers.items())
        if header_bytes > self.max_header_bytes:
            return Response.text("Request Header Fields Too Large", 431)
        route = self._router.match(request)
        if route is None:
            return Response.text("Not Found", 404)
        pipeline = chain(self._middlewares, lambda req: route.handler(req))
        response = pipeline(request)
        if self.request_log:
            logger.info("%s %s -> %s", request.method, request.path, response.status)
        return response
