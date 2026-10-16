"""Middleware: a callable taking the request and the next step, returning a Response."""

from __future__ import annotations

from typing import Callable

from .http import Request, Response

Next = Callable[[Request], Response]
Middleware = Callable[[Request, Next], Response]


def chain(middlewares: list[Middleware], handler: Next) -> Next:
    def build(index: int) -> Next:
        if index == len(middlewares):
            return handler
        middleware = middlewares[index]
        following = build(index + 1)
        return lambda request: middleware(request, following)

    return build(0)
