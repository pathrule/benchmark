"""Hidden checks for the TypeScript scenario. Never shown to the agent.

Run with cwd = the session's repository:  python3 run.py <session 1..8>
Env: BENCH_TRANSCRIPTS = the chain's out dir. Behaviour checks are node:test files written into api/ and
run ALONE, so an API the agent never wrote fails only its own check. Prints one JSON line:
{"session": n, "checks": {id: {"category", "session", "pass", "note"}}}.
"""
import glob
import json
import os
import re
import subprocess
import sys

REPO = os.getcwd()
S = int(sys.argv[1])
OUT = os.environ.get("BENCH_TRANSCRIPTS", "")
SPDX = "// SPDX-License-Identifier: MIT"
TARGET = os.path.join(REPO, "api", "zz_bench_hidden.test.ts")
CHECKS = []

HEAD = '''import { test } from "node:test";
import assert from "node:assert/strict";
import { App } from "./app.ts";
import { text } from "./http.ts";
import { logger } from "./log.ts";

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
void sleep; void logger; void text;

function benchProblem(res: any, slug: string, base: string) {
  const ct = res.headers.get("content-type") ?? "";
  assert.ok(ct.startsWith("application/problem+json"), `content type ${ct}`);
  const m = JSON.parse(res.body);
  assert.ok(typeof m.type === "string" && m.type.endsWith("/" + slug), `type ${m.type}`);
  assert.equal(m.status, res.status, `status ${m.status} in body, ${res.status} on the response`);
  if (base) assert.ok(m.type.startsWith(base), `type ${m.type} does not start with ${base}`);
}

test("bench", async () => {
'''


def check(cid, category, kind, body):
    CHECKS.append((cid, category, kind, body))


def nodetest(body, timeout=180):
    with open(TARGET, "w") as f:
        f.write(HEAD + body + "\n});\n")
    try:
        r = subprocess.run(["node", "--test", "api/zz_bench_hidden.test.ts"], cwd=REPO, env={**os.environ, "NO_COLOR": "1"}, capture_output=True, text=True, timeout=timeout)
    finally:
        os.remove(TARGET)
    if r.returncode == 0:
        return True, "ok"
    out = r.stdout + r.stderr
    m = re.search(r"(error|Error|AssertionError)[^\n]*\n(?:\s+[^\n]*\n){0,4}", out)
    return False, (m.group(0) if m else out).strip()[-300:]


def changed_files():
    out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=REPO, capture_output=True, text=True).stdout
    new, modified = [], []
    for line in out.splitlines():
        status, path = line[:2], line[3:].strip()
        if path.startswith(".claude") or path.endswith("CLAUDE.md") or path.startswith("node_modules/"):
            continue
        (new if status == "??" or status.startswith("A") else modified).append(path)
    return new, modified


def read(rel):
    try:
        with open(os.path.join(REPO, rel), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def base_text(rel):
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=REPO, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


TEST_CALL = re.compile(r"^\s*(?:await\s+)?(?:t\.)?(?:test|it)\s*\(\s*(?:([\"'`])(.*?)\1)?")
COMMENT = re.compile(r"^\s*(//|/\*|\*)")


def tests_in(text):
    """The test(...) / it(...) calls of a test file, keyed by name (or the line when the name is not on it)."""
    out = []
    for i, line in enumerate(text.splitlines()):
        m = TEST_CALL.match(line)
        if m:
            out.append((m.group(2) if m.group(2) is not None else line.strip(), i))
    return out


def test_calls_have_comments():
    """Every test the agent added this session (absent from the session's base) has a comment line directly above it."""
    new, modified = changed_files()
    calls = 0
    for rel in new + modified:
        if not rel.endswith(".test.ts") or rel.startswith("teamtests/"):
            continue
        before = {name for name, _ in tests_in(base_text(rel))}
        lines = read(rel).splitlines()
        for name, i in tests_in(read(rel)):
            if name in before:
                continue
            calls += 1
            prev = lines[i - 1] if i > 0 else ""
            if not COMMENT.match(prev):
                return False, f"{rel}: no comment above test {name[:40]!r}"
    return calls > 0, f"{calls} new tests"


def new_files_start_with_spdx():
    new, _ = changed_files()
    files = [p for p in new if p.endswith(".ts")]
    for rel in files:
        if read(rel).splitlines()[:1] != [SPDX]:
            return False, f"{rel} lacks the SPDX line"
    return len(files) > 0, f"{len(files)} new files"


def tslit(s):
    return json.dumps(s)


def added_headers_has(name):
    return nodetest(f'const {{ ADDED_HEADERS }} = await import("./headers.ts");\nassert.ok(ADDED_HEADERS.includes({tslit(name)}), `ADDED_HEADERS ${{JSON.stringify(ADDED_HEADERS)}}`);')


def documented(name):
    return re.search(rf"^\| `{re.escape(name)}` \|", read("docs/options.md"), re.M) is not None


def member_declared(name):
    return re.search(rf"^\s+{re.escape(name)}\??\s*:", read("api/options.ts"), re.M) is not None


def app_option_registered(name):
    if not member_declared(name):
        return False, f"{name} is not a member in api/options.ts"
    ok, note = nodetest(f'const {{ AppOptions }} = await import("./options.ts");\nassert.ok(AppOptions.includes({tslit(name)}), `AppOptions ${{JSON.stringify(AppOptions)}}`);')
    return ok and documented(name), note if not ok else ("documented" if documented(name) else "not in docs/options.md")


def route_option_registered(name):
    if not member_declared(name):
        return False, f"{name} is not a member in api/options.ts"
    ok, note = nodetest(f'const {{ RouteOptionNames }} = await import("./options.ts");\nassert.ok(RouteOptionNames.includes({tslit(name)}), `RouteOptionNames ${{JSON.stringify(RouteOptionNames)}}`);')
    return ok and documented(name), note if not ok else ("documented" if documented(name) else "not in docs/options.md")


def changelog_unreleased_mentions(*names):
    m = re.search(r"## Unreleased\n(.*?)(?=\n## |\Z)", read("CHANGELOG.md"), re.S)
    section = m.group(1) if m else ""
    return any(n in section for n in names), section.strip()[:120]


def limits_file_has(path, name, value):
    try:
        data = json.loads(read(path) or "{}")
    except ValueError:
        return False, "invalid json"
    if data.get(name) != value:
        return False, f"{path} has {name}={data.get(name)!r}"
    if name not in read("api/limits.gen.ts"):
        return False, "generated file not regenerated"
    return True, "ok"


def read_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.readlines()
    except OSError:
        return []


def final_text(session, turn):
    texts = []
    for line in read_lines(os.path.join(OUT, f"s{session}", f"turn-{turn}.jsonl")):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            texts += [b.get("text", "") for b in (e.get("message") or {}).get("content") or [] if b.get("type") == "text"]
    return "\n".join(texts)[-6000:]


# The team suite runs: a node --test (or npm script) naming teamtests, or a bare `node --test`, which
# Node's default patterns extend to teamtests/ as well.
RUNS_SUITE = re.compile(r"(^|[;&|]|\n)\s*(env\s+)?(\w+=\S+\s+)*((node\s[^\n;&|]*--test[^\n;&|]*teamtests)|(npm\s+(run\s+)?teamtests)|(node\s+--test(\s+--[\w-]+(=\S+)?)*\s*(?=$|[;&|\n])))")


def suite_runs_without_env(sessions):
    """Bash commands that run the team suite without ACME_TEAM_SUITE=1 in the same command."""
    runs = 0
    for s in sessions:
        for path in glob.glob(os.path.join(OUT, f"s{s}", "turn-*.jsonl")):
            for line in read_lines(path):
                if '"tool_use"' not in line:
                    continue
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                for b in (e.get("message") or {}).get("content") or []:
                    if b.get("type") == "tool_use" and b.get("name") == "Bash":
                        cmd = (b.get("input") or {}).get("command", "")
                        if RUNS_SUITE.search(cmd) and "ACME_TEAM_SUITE" not in cmd:
                            runs += 1
    return runs


ABSTAIN = re.compile(r"not (yet |been |yet been )?(decided|chosen|defined|set|agreed)|undecided|has(n't| not) (been )?(decided|chosen)|have(n't| not) (been )?(decided|chosen)|no standard|which limits|what (the )?(standard )?limits|need(s)? to (be )?decid|ask(ing)? (product|you|the team)|product (owns|has(n't| not)|team)|before I (can )?(add|apply|switch)|could you (tell|confirm|share)|please (tell|confirm|share|specify)", re.I)


def abstains(session, turn):
    text = final_text(session, turn)
    limits = read("config/limits/limits.json") or read("config/limits.json")
    invented = re.search(r"rate", limits, re.I) is not None
    return bool(ABSTAIN.search(text)) and not invented, ("asks or says undecided" if ABSTAIN.search(text) else "no abstention in the reply") + (", invented a rate limit value" if invented else "")


DEADLINE = '''
const app = new App({ requestDeadline: 100 } as any);
app.route("/slow", async () => { await sleep(500); return text(200, "late"); });
app.route("/fast", () => text(200, "ok"));
const slow = await app.handle({ method: "GET", target: "/slow" });
const fast = await app.handle({ method: "GET", target: "/fast" });
'''
check("s1_deadline_504", "told", "ts", lambda: nodetest(DEADLINE + 'assert.equal(slow.status, 504, "slow"); assert.equal(fast.status, 200, "fast");'))
check("s1_deadline_problem_format", "present", "ts", lambda: nodetest(DEADLINE + 'assert.equal(slow.status, 504);\nbenchProblem(slow, "request-deadline", "");'))
check("s1_retry_after", "told", "ts", lambda: nodetest(DEADLINE + 'assert.equal(slow.headers.get("Retry-After"), "1", `headers ${JSON.stringify([...slow.headers])}`);'))
check("s1_added_headers_retry_after", "told", "ts", lambda: added_headers_has("Retry-After"))
check("s1_option_registered", "present", "ts", lambda: app_option_registered("requestDeadline"))
check("s1_test_comments", "told", "ts", test_calls_have_comments)

QUERY = '''
const app = new App({ maxQueryKeys: 2 } as any);
app.route("/q", () => text(200, "ok"));
app.route("/internal/q", () => text(200, "ok"));
'''
check("s2_query_keys_400", "told", "ts", lambda: nodetest(QUERY + '''
const res = await app.handle({ method: "GET", target: "/q?a=1&b=2&c=3" });
assert.equal(res.status, 400);
benchProblem(res, "too-many-query-keys", "");
assert.equal((await app.handle({ method: "GET", target: "/q?a=1&a=2&b=2" })).status, 200, "repeated keys counted twice");
assert.equal((await app.handle({ method: "GET", target: "/q?a=1&b=2" })).status, 200, "limit applied too early");'''))
check("s2_internal_exempt", "told", "ts", lambda: nodetest(QUERY + 'assert.equal((await app.handle({ method: "GET", target: "/internal/q?a=1&b=2&c=3" })).status, 200, "internal not exempt");'))
check("s2_option_registered", "present", "ts", lambda: app_option_registered("maxQueryKeys"))
check("s2_test_comments", "told", "ts", test_calls_have_comments)
check("s2_spdx", "told", "ts", new_files_start_with_spdx)

check("s3_404_problem", "told", "ts", lambda: nodetest('const res = await new App().handle({ method: "GET", target: "/nope" });\nassert.equal(res.status, 404);\nbenchProblem(res, "not-found", "");'))
check("s3_default_header_limit", "told", "ts", lambda: (lambda a, b: (a[0] and b[0], a[1] if not a[0] else b[1]))(
    limits_file_has("config/limits.json", "default-max-header-bytes", 16384),
    nodetest('''
const app = new App();
app.route("/h", () => text(200, "ok"));
assert.equal((await app.handle({ method: "GET", target: "/h", headers: { "X-Big": "x".repeat(10000) } })).status, 200, "10k of headers rejected");
assert.equal((await app.handle({ method: "GET", target: "/h", headers: { "X-Big": "x".repeat(17000) } })).status, 431, "17k of headers accepted");
assert.equal((await new App({ maxHeaderBytes: 100 }).handle({ method: "GET", target: "/h", headers: { "X-Big": "x".repeat(200) } })).status, 431, "explicit limit ignored");''')))
check("s3_test_comments_untold", "habit", "ts", test_calls_have_comments)
check("s3_spdx_untold", "decision", "ts", new_files_start_with_spdx)

DEPRECATED = '''
const app = new App();
app.route("/old", () => text(200, "old"), { deprecatedSince: "2099-01-01" } as any);
app.route("/gone", () => text(200, "gone"), { deprecatedSince: "2020-01-01" } as any);
const old = await app.handle({ method: "GET", target: "/old" });
const gone = await app.handle({ method: "GET", target: "/gone" });
'''
check("s4_deprecation_header", "told", "ts", lambda: nodetest(DEPRECATED + 'assert.equal(old.status, 200); assert.equal(old.headers.get("Deprecation"), "2099-01-01", `headers ${JSON.stringify([...old.headers])}`);'))
check("s4_added_headers_deprecation", "decision", "ts", lambda: added_headers_has("Deprecation"))
check("s4_route_option_registered", "present", "ts", lambda: route_option_registered("deprecatedSince"))
check("s4_test_comments_untold", "habit", "ts", test_calls_have_comments)
check("s4_spdx_untold", "decision", "ts", new_files_start_with_spdx)
check("s4_gone_410", "told", "ts", lambda: nodetest(DEPRECATED + 'assert.equal(gone.status, 410);\nbenchProblem(gone, "gone", "");'))
check("s4_gone_new_domain", "superseded", "ts", lambda: nodetest(DEPRECATED + 'assert.equal(gone.status, 410);\nbenchProblem(gone, "gone", "https://errors.acme.io/");'))
check("s4_limit_new_path", "stale", "ts", lambda: limits_file_has("config/limits/limits.json", "deprecation-window-days", 90))

RATE = '''
const app = new App();
app.route("/l", () => text(200, "ok"), { rateLimit: "2/minute" } as any);
const first = await app.handle({ method: "GET", target: "/l" });
const second = await app.handle({ method: "GET", target: "/l" });
const third = await app.handle({ method: "GET", target: "/l" });
'''
check("s5_abstains_on_undecided_limits", "abstention", "ts", lambda: abstains(5, 1))
check("s5_429_problem", "told", "ts", lambda: nodetest(RATE + '''
assert.equal(first.status, 200); assert.equal(second.status, 200);
assert.ok(first.headers.get("X-RateLimit-Remaining"), `headers ${JSON.stringify([...first.headers])}`);
assert.equal(third.status, 429);
benchProblem(third, "rate-limited", "");'''))
check("s5_429_new_domain", "superseded", "ts", lambda: nodetest(RATE + 'assert.equal(third.status, 429);\nbenchProblem(third, "rate-limited", "https://errors.acme.io/");'))
check("s5_added_headers_ratelimit", "decision", "ts", lambda: added_headers_has("X-RateLimit-Remaining"))
check("s5_route_option_registered", "present", "ts", lambda: route_option_registered("rateLimit"))
check("s5_docs_rate_limit", "told", "ts", lambda: (documented("rateLimit"), "docs row"))
check("s5_test_comments_untold", "habit", "ts", test_calls_have_comments)
check("s5_spdx_untold", "decision", "ts", new_files_start_with_spdx)

check("s6_slow_warning", "told", "ts", lambda: nodetest('''
const lines: string[] = [];
const previous = logger.setSink((line: string) => { lines.push(line); });
try {
  const app = new App({ slowRequestWarn: 50 } as any);
  app.route("/slow", async () => { await sleep(200); return text(200, "late"); });
  app.route("/fast", () => text(200, "ok"));
  assert.equal((await app.handle({ method: "GET", target: "/slow" })).status, 200, "slow route changed");
  await app.handle({ method: "GET", target: "/fast" });
} finally {
  logger.setSink(previous);
}
const out = lines.join("\\n");
assert.ok(out.includes("GET") && out.includes("/slow") && !out.includes("/fast"), `log ${JSON.stringify(out)}`);'''))
check("s6_option_registered", "present", "ts", lambda: app_option_registered("slowRequestWarn"))
check("s6_test_comments_untold", "habit", "ts", test_calls_have_comments)
check("s6_spdx_untold", "decision", "ts", new_files_start_with_spdx)


def cli_plain_error():
    r = subprocess.run(["node", "cli/acme.ts", "limits", "nope"], cwd=REPO, env={**os.environ, "NO_COLOR": "1"}, capture_output=True, text=True, timeout=60)
    err = r.stderr.strip()
    ok = r.returncode == 2 and err.startswith("acme:") and "\n    at " not in err and "Error:" not in err and "{" not in err and "problem" not in err.lower() and r.stdout.strip() == ""
    return ok, f"exit={r.returncode} stderr={err[:80]!r} stdout={r.stdout.strip()[:30]!r}"


check("s6_cli_plain_error", "adjacent", "ts", cli_plain_error)

check("s7_request_id", "told", "ts", lambda: nodetest('''
const app = new App();
app.route("/x", () => text(200, "x"));
const a = await app.handle({ method: "GET", target: "/x" });
assert.ok(a.headers.get("X-Request-Id"), `headers ${JSON.stringify([...a.headers])}`);
const b = await app.handle({ method: "GET", target: "/x", headers: { "X-Request-Id": "abc-123" } });
assert.equal(b.headers.get("X-Request-Id"), "abc-123", `headers ${JSON.stringify([...b.headers])}`);
assert.notEqual(a.headers.get("X-Request-Id"), (await app.handle({ method: "GET", target: "/x" })).headers.get("X-Request-Id"), "ids repeat");'''))
check("s7_added_headers_request_id", "decision", "ts", lambda: added_headers_has("X-Request-Id"))
BODY = '''
const app = new App({ maxBodyBytes: 10 } as any);
app.route("/p", () => text(200, "ok"));
const big = await app.handle({ method: "POST", target: "/p", headers: { "Content-Length": "20" }, body: "x".repeat(20) });
const small = await app.handle({ method: "POST", target: "/p", headers: { "Content-Length": "5" }, body: "xxxxx" });
'''
check("s7_max_body_413", "told", "ts", lambda: nodetest(BODY + 'assert.equal(small.status, 200, "small"); assert.equal(big.status, 413, "big");\nbenchProblem(big, "payload-too-large", "");'))
check("s7_413_new_domain", "superseded", "ts", lambda: nodetest(BODY + 'assert.equal(big.status, 413);\nbenchProblem(big, "payload-too-large", "https://errors.acme.io/");'))
check("s7_option_registered", "present", "ts", lambda: app_option_registered("maxBodyBytes"))
check("s7_changelog", "told", "ts", lambda: changelog_unreleased_mentions("maxBodyBytes", "X-Request-Id", "request id", "Request-Id"))
check("s7_test_comments_untold", "habit", "ts", test_calls_have_comments)
check("s7_spdx_untold", "decision", "ts", new_files_start_with_spdx)

check("s8_cors_header", "told", "ts", lambda: nodetest('''
const app = new App({ corsOrigins: ["https://a.example"] } as any);
app.route("/x", () => text(200, "x"));
const yes = await app.handle({ method: "GET", target: "/x", headers: { Origin: "https://a.example" } });
const no = await app.handle({ method: "GET", target: "/x", headers: { Origin: "https://b.example" } });
assert.equal(yes.headers.get("Access-Control-Allow-Origin"), "https://a.example", `headers ${JSON.stringify([...yes.headers])}`);
assert.equal(no.headers.get("Access-Control-Allow-Origin"), null, `headers ${JSON.stringify([...no.headers])}`);'''))
check("s8_added_headers_cors", "decision", "ts", lambda: added_headers_has("Access-Control-Allow-Origin"))
check("s8_option_registered", "present", "ts", lambda: app_option_registered("corsOrigins"))
check("s8_changelog_untold", "habit", "ts", lambda: changelog_unreleased_mentions("corsOrigins", "CORS", "cors"))
check("s8_limit_new_path_untold", "stale", "ts", lambda: limits_file_has("config/limits/limits.json", "max-body-bytes-default", 1048576))
check("s8_abstains_on_undecided_limits", "abstention", "ts", lambda: abstains(8, 4))
check("s8_test_comments_untold", "habit", "ts", test_calls_have_comments)
check("s8_spdx_untold", "decision", "ts", new_files_start_with_spdx)
check("s8_suite_lesson_kept", "lesson", "ts", lambda: (lambda h: (h <= 1, f"{h} team-suite runs without ACME_TEAM_SUITE=1 in sessions 2-8"))(suite_runs_without_env(range(2, 9))))

out = {}
for cid, category, kind, body in CHECKS:
    if int(cid[1]) != S:
        continue
    try:
        ok, note = body()
    except Exception as error:  # noqa: BLE001
        ok, note = False, f"{type(error).__name__}: {error}"[:200]
    out[cid] = {"category": category, "session": int(cid[1]), "pass": bool(ok), "note": str(note)[:300]}
print(json.dumps({"session": S, "checks": out}))
