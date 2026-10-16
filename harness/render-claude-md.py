#!/usr/bin/env python3
"""Render knowledge items into CLAUDE.md files, the way Claude Code recommends using them.

Usage: render-claude-md.py <repo-dir> <items.json> [<items.json> ...]

Items at "/" go to the root CLAUDE.md; items at "/x/y" go to x/y/CLAUDE.md, which Claude Code loads
when it works in that folder. The root file also carries the instruction to keep the knowledge
current, mirroring what Pathrule's protocol asks of the agent, so both arms are asked the same thing.
"""
import json
import os
import sys

repo, files = sys.argv[1], sys.argv[2:]
by_path = {}
for f in files:
    for it in json.load(open(f)):
        by_path.setdefault(it["path"].strip("/"), []).append(it)

HEADER = (
    "# Project knowledge\n\n"
    "This file is the team's maintained project knowledge. Folder-specific knowledge lives in a\n"
    "CLAUDE.md inside that folder. Keep it current: when the user states a decision, a convention or a\n"
    "constraint, or you learn something that is not obvious from the code, record it in the right\n"
    "CLAUDE.md before you finish.\n"
)
stats = {}
for rel, items in sorted(by_path.items()):
    target = os.path.join(repo, rel, "CLAUDE.md") if rel else os.path.join(repo, "CLAUDE.md")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    head = HEADER if not rel else f"# Project knowledge for /{rel}\n"
    body = "\n".join(f"\n## {it['title']}\n\n{it['body']}\n" for it in items)
    open(target, "w").write(head + body)
    stats["/" + rel] = {"items": len(items), "chars": len(head + body)}
if "" not in by_path:
    open(os.path.join(repo, "CLAUDE.md"), "w").write(HEADER)
    stats["/"] = {"items": 0, "chars": len(HEADER)}
print(json.dumps(stats))
