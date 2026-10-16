"""Platform limits. The values come from the generated module; see scripts/gen_limits.py."""

from ._limits_gen import LIMITS


def limit(name: str) -> int:
    return LIMITS[name]
