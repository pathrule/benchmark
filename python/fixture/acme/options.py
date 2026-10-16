"""The registry of App options and route options.

Every option App() or route() accepts is listed here, and the team suite checks that each one is
documented in docs/options.md.
"""

APP_OPTIONS = ("request_log", "max_header_bytes")

ROUTE_OPTIONS = ("methods",)
