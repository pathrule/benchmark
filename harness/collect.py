#!/usr/bin/env python3
"""Collect a group of chains into results/<group>: the per-chain checks, session rows and meta (never the
transcripts), then the group's aggregated tables.

Usage: collect.py <runs-dir> <lang> <group> <trial,trial,...> [arm ...]
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
runs, lang, group, trials = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")
arms = sys.argv[5:] or ["none", "claude_md", "pathrule"]
out = os.path.join(os.path.dirname(HERE), "results", group)
os.makedirs(os.path.join(out, "chains"), exist_ok=True)
for arm in arms:
    for t in trials:
        chain = f"{lang}-{arm}-t{t}"
        src = os.path.join(runs, chain, "out")
        if not os.path.isdir(src):
            continue
        dst = os.path.join(out, "chains", chain)
        os.makedirs(dst, exist_ok=True)
        for name in sorted(os.listdir(src)):
            if name.startswith(("checks-s", "session-s")) or name == "meta.json":
                shutil.copy(os.path.join(src, name), os.path.join(dst, name))
subprocess.run([sys.executable, "-I", os.path.join(HERE, "aggregate.py"), runs, out, lang, ",".join(trials), *arms], check=True)
print(f"collected {group}: {len(os.listdir(os.path.join(out, 'chains')))} chains")
