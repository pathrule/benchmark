#!/usr/bin/env python3
"""Generate acme/_limits_gen.py from config/limits/limits.json. Run it after editing the limits list."""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "config", "limits", "limits.json")
TARGET = os.path.join(ROOT, "acme", "_limits_gen.py")

with open(SOURCE) as f:
    limits = json.load(f)
lines = ["# Generated from config/limits/limits.json by scripts/gen_limits.py. Do not edit.", "", "LIMITS = {"]
for name in sorted(limits):
    lines.append(f"    {name!r}: {limits[name]!r},")
lines += ["}", ""]
with open(TARGET, "w") as f:
    f.write("\n".join(lines))
print(f"wrote {os.path.relpath(TARGET, ROOT)} with {len(limits)} limits")
