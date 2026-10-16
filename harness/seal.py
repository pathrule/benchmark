#!/usr/bin/env python3
"""Seal the benchmark: SHA-256 of every file a product run depends on, written to SEAL.txt.

Usage: seal.py <benchmarks/v3 dir>
Run after validation and before the product arms; the commit that carries SEAL.txt is the sealed version.
"""
import hashlib
import os
import sys

root = sys.argv[1]
paths = []
for lang in ("python", "go"):
    for sub in ("fixture", "overlays", "checks", "knowledge"):
        for dirpath, _, files in os.walk(os.path.join(root, lang, sub)):
            paths += [os.path.join(dirpath, f) for f in files if "__pycache__" not in dirpath]
    paths += [os.path.join(root, lang, "sessions.json"), os.path.join(root, lang, "oracle.json")]
paths += [os.path.join(root, "harness", f) for f in ("run-chain.mjs", "seed-pathrule.mts", "render-claude-md.py", "aggregate.py")]
paths += [os.path.join(root, "DESIGN.md"), os.path.join(root, "PROTOCOL.md")]
lines = []
for p in sorted(set(paths)):
    with open(p, "rb") as f:
        lines.append(f"{hashlib.sha256(f.read()).hexdigest()}  {os.path.relpath(p, root)}")
with open(os.path.join(root, "SEAL.txt"), "w") as f:
    f.write("\n".join(lines) + "\n")
print(f"sealed {len(lines)} files")
