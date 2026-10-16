#!/usr/bin/env python3
"""The scale condition for TypeScript: the team's knowledge base after a year, not after a week.

The TypeScript counterpart of python/knowledge/gen-scale.py: team.json plus N decision-log entries a
platform team accumulates, worded for the TypeScript toolkit (`api/`, `cli/`, `teamtests/`, `scripts/`).
Same kinds, same spread across areas, same seed; no entry answers a probe. Both memory arms receive the
same items: CLAUDE.md files on one side, Pathrule memories on the other. Deterministic: the same file
every time.
Usage: gen-scale.py <extra>   (480 -> team-scale-500.json, 980 -> team-scale-1000.json, 1980 -> team-scale-2000.json)
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
base = json.load(open(os.path.join(HERE, "team.json")))
rng = random.Random(20261016)

areas = ["/"] * 7 + ["/api", "/cli", "/docs", "/teamtests", "/scripts"]
subjects = ["request parsing", "response headers", "the router", "middleware", "the problem helper", "limits", "the CLI", "the docs tables",
            "test fixtures", "logging", "the node:http adapter", "error slugs", "option defaults", "the changelog", "release notes", "doc comments",
            "import ordering", "module layout", "naming", "deprecations", "timeouts", "retries", "encoding", "query strings", "path matching",
            "header size", "body size", "the generated limits file", "maintenance scripts", "review process"]
kinds = [
    ("Review outcome", "In the {date} API review the team agreed that {subject} {verdict}. {follow}"),
    ("Naming", "Names in {subject}: {rule}. Existing names stay until their next change."),
    ("Incident note", "Incident {inc}: {subject} {incident}. Lesson: {lesson}"),
    ("Compatibility", "{subject}: {compat}"),
    ("Release note", "Release {ver}: {subject} {release}."),
    ("Layout", "{subject} lives in {where}; do not add a second place for it."),
]
verdicts = ["keeps its current shape", "gets no new exported surface this quarter", "is documented before it is extended", "stays dependency-free",
            "is covered by the team suite", "answers errors in the problem format", "keeps backwards compatibility for one release"]
follows = ["The slug list in the review doc was updated.", "No code change was needed.", "The docs table carries the note.", "Tests were added in the following week."]
rules = ["camelCase for members and functions, PascalCase for types", "options are nouns, never verbs", "slugs are kebab-case nouns", "test files are <area>.test.ts",
         "module-private helpers are not exported", "UPPER_SNAKE only for true constants such as TYPE_BASE", "no abbreviations in exported names"]
incidents = ["dropped a header when the value contained a comma", "logged a request body at info level", "answered 500 for a malformed query string",
             "counted a repeated query key twice", "regenerated the limits file with stale values", "served a deprecated route after its window",
             "retried a non-idempotent request", "truncated a long log line mid-character"]
lessons = ["add a regression test before the fix", "never log bodies, only sizes", "parse once, in the request constructor", "the generated file is never edited by hand",
           "check the window with dates, not durations", "retries need an idempotency key", "cap log lines by bytes, not characters"]
compats = ["Node 24 is the floor; 22 is not tested.", "Header names compare case-insensitively everywhere; Headers does that.", "Query values are strings; conversion is the handler's job.",
           "A response without a Content-Type is sent as text/plain.", "The node:http adapter never sets Server or Date headers.", "Limits are read at import time, not per request."]
releases = ["gained a default", "lost its last positional argument", "is documented in docs/options.md", "answers 431 for oversized headers", "moved to its own module",
            "is covered by the team suite", "got a changelog entry"]
wheres = ["api/app.ts", "api/http.ts", "api/problem.ts", "cli/acme.ts", "docs/options.md", "scripts/genlimits.ts", "teamtests/", "api/log.ts"]
extra = int(sys.argv[1])
items = []
for i in range(extra):
    kind, template = rng.choice(kinds)
    subject = rng.choice(subjects)
    body = template.format(date=f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}", subject=subject, verdict=rng.choice(verdicts), follow=rng.choice(follows),
                           rule=rng.choice(rules), inc=f"INC-{rng.randint(100,999)}", incident=rng.choice(incidents), lesson=rng.choice(lessons),
                           compat=rng.choice(compats), ver=f"0.{rng.randint(1,3)}.{rng.randint(0,9)}", release=rng.choice(releases), where=rng.choice(wheres))
    items.append({"path": rng.choice(areas), "title": f"{kind}: {subject} ({i + 1})", "body": body[0].upper() + body[1:]})
out = base + items
json.dump(out, open(os.path.join(HERE, f"team-scale-{len(out)}.json"), "w"), indent=1)
print(len(out), "items;", sum(len(i["body"]) for i in out), "chars;", sum(1 for i in out if i["path"] == "/"), "at /")
