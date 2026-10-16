"""The platform team suite. The platform CI prepares the environment before running it."""

import os

if os.environ.get("ACME_TEAM_SUITE") != "1":
    raise SystemExit("team environment not prepared")
