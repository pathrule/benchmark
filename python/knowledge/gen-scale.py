#!/usr/bin/env python3
"""The scale condition: the team's knowledge base after a year, not after a week.

team-scale.json = team.json plus 280 decision-log entries a platform team accumulates: review
outcomes, naming and layout conventions, incident lessons, compatibility notes, release notes. They
are coherent for the acme toolkit and deliberately spread across areas, most of them project-wide,
the way a team's conventions are. No entry answers a probe; the probes' knowledge is the same as in
team.json. Both memory arms receive the same items: CLAUDE.md files on one side, Pathrule memories
on the other. Deterministic: the same file every time.
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
base = json.load(open(os.path.join(HERE, "team.json")))
rng = random.Random(20261016)

areas = ["/"] * 7 + ["/acme", "/cli", "/docs", "/tests", "/scripts"]
subjects = ["request parsing", "response headers", "the router", "middleware", "the problem helper", "limits", "the CLI", "the docs tables",
            "test fixtures", "logging", "the server adapter", "error slugs", "option defaults", "the changelog", "release notes", "type hints",
            "import order", "module layout", "naming", "deprecations", "timeouts", "retries", "encoding", "query strings", "path matching",
            "header size", "body size", "the generated limits module", "maintenance scripts", "review process"]
kinds = [
    ("Review outcome", "In the {date} API review the team agreed that {subject} {verdict}. {follow}"),
    ("Naming", "Names in {subject}: {rule}. Existing names stay until their next change."),
    ("Incident note", "Incident {inc}: {subject} {incident}. Lesson: {lesson}"),
    ("Compatibility", "{subject}: {compat}"),
    ("Release note", "Release {ver}: {subject} {release}."),
    ("Layout", "{subject} lives in {where}; do not add a second place for it."),
]
verdicts = ["keeps its current shape", "gets no new public surface this quarter", "is documented before it is extended", "stays standard-library only",
            "is covered by the team suite", "answers errors in the problem format", "keeps backwards compatibility for one release"]
follows = ["The slug list in the review doc was updated.", "No code change was needed.", "The docs table carries the note.", "Tests were added in the following week."]
rules = ["snake_case for functions, PascalCase for classes", "options are nouns, never verbs", "slugs are kebab-case nouns", "test modules are test_<area>.py",
         "private helpers start with an underscore", "constants are UPPER_SNAKE", "no abbreviations in public names"]
incidents = ["dropped a header when the value contained a comma", "logged a request body at INFO", "answered 500 for a malformed query string",
             "counted a repeated query key twice", "regenerated the limits module with stale values", "served a deprecated route after its window",
             "retried a non-idempotent request", "truncated a long log line mid-character"]
lessons = ["add a regression test before the fix", "never log bodies, only sizes", "parse once, in the request constructor", "the generated module is never edited by hand",
           "check the window with dates, not durations", "retries need an idempotency key", "cap log lines by bytes, not characters"]
compats = ["Python 3.12 is the floor; 3.11 is not tested.", "Header names compare case-insensitively everywhere.", "Query values are strings; conversion is the handler's job.",
           "A Response without a Content-Type is sent as text/plain.", "The server adapter never sets Server or Date headers.", "Limits are read at import time, not per request."]
releases = ["gained a default", "lost its last positional argument", "is documented in docs/options.md", "answers 431 for oversized headers", "moved to its own module",
            "is covered by the team suite", "got a changelog entry"]
wheres = ["acme/app.py", "acme/http.py", "acme/problem.py", "cli/main.py", "docs/options.md", "scripts/gen_limits.py", "tests/", "acme/log.py"]
# An argument makes a larger base (the first 280 entries are the same ones: one random stream).
extra = int(sys.argv[1]) if len(sys.argv) > 1 else 280
items = []
for i in range(extra):
    kind, template = rng.choice(kinds)
    subject = rng.choice(subjects)
    body = template.format(date=f"2025-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}", subject=subject, verdict=rng.choice(verdicts), follow=rng.choice(follows),
                           rule=rng.choice(rules), inc=f"INC-{rng.randint(100,999)}", incident=rng.choice(incidents), lesson=rng.choice(lessons),
                           compat=rng.choice(compats), ver=f"0.{rng.randint(1,3)}.{rng.randint(0,9)}", release=rng.choice(releases), where=rng.choice(wheres))
    items.append({"path": rng.choice(areas), "title": f"{kind}: {subject} ({i + 1})", "body": body[0].upper() + body[1:]})
out = base + items
json.dump(out, open(os.path.join(HERE, "team-scale.json" if extra == 280 else f"team-scale-{len(out)}.json"), "w"), indent=1)
print(len(out), "items;", sum(len(i["body"]) for i in out), "chars;", sum(1 for i in out if i["path"] == "/"), "at /")
