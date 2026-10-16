"""acme CLI. Errors are plain text on stderr with exit code 2; this is a terminal, not an API."""

from __future__ import annotations

import argparse
import importlib
import sys

from acme.app import App


def load_app(spec: str) -> App:
    module_name, _, attribute = spec.partition(":")
    module = importlib.import_module(module_name)
    app = getattr(module, attribute or "app")
    if not isinstance(app, App):
        raise TypeError(f"{spec} is not an acme App")
    return app


def fail(message: str) -> int:
    print(f"acme: {message}", file=sys.stderr)
    return 2


def cmd_routes(args: argparse.Namespace) -> int:
    app = load_app(args.module)
    for route in app.routes():
        methods = ",".join(route.options.get("methods") or ["*"])
        print(f"{methods:10} {route.path}")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    from acme.server import serve

    try:
        serve(load_app(args.module), args.host, args.port)
    except OSError as error:
        return fail(f"cannot listen on {args.host}:{args.port}: {error.strerror}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="acme")
    sub = parser.add_subparsers(dest="command", required=True)
    routes = sub.add_parser("routes", help="list an app's routes")
    routes.add_argument("--module", required=True, help="module:attribute of the App")
    routes.set_defaults(run=cmd_routes)
    serve = sub.add_parser("serve", help="serve an app")
    serve.add_argument("--module", required=True)
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8080)
    serve.set_defaults(run=cmd_serve)
    args = parser.parse_args(argv)
    try:
        return args.run(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
