"""Hidden checks for the Go scenario. Never shown to the agent.

Run with cwd = the session's repository:  python3 run.py <session 1..8>
Env: BENCH_TRANSCRIPTS = the chain's out dir. Behaviour checks are Go test files compiled ALONE into
package api, so an API the agent never wrote fails only its own check. Prints one JSON line:
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
TARGET = os.path.join(REPO, "api", "zz_bench_hidden_test.go")
GOENV = {**os.environ, "GOFLAGS": "-mod=mod", "GOTOOLCHAIN": "local"}
CHECKS = []

HEAD = '''package api

import (
	"encoding/json"
	"net/http"
	"strings"
	"testing"
	"time"
)

var _ = json.Marshal
var _ = http.StatusOK
var _ = strings.Contains
var _ = time.Second

func benchProblem(t *testing.T, res Response, slug, base string) {
	t.Helper()
	if !strings.HasPrefix(res.Get("Content-Type"), "application/problem+json") {
		t.Fatalf("content type %q", res.Get("Content-Type"))
	}
	var m map[string]any
	if err := json.Unmarshal(res.Body, &m); err != nil {
		t.Fatalf("body %s", res.Body)
	}
	typ, _ := m["type"].(string)
	status, _ := m["status"].(float64)
	if !strings.HasSuffix(typ, "/"+slug) || int(status) != res.Status {
		t.Fatalf("type %q status %v", typ, status)
	}
	if base != "" && !strings.HasPrefix(typ, base) {
		t.Fatalf("type %q does not start with %q", typ, base)
	}
}

func benchContains(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}

func TestBench(t *testing.T) {
'''


def check(cid, category, kind, body):
    CHECKS.append((cid, category, kind, body))


def gotest(body, timeout=180):
    with open(TARGET, "w") as f:
        f.write(HEAD + body + "\n}\n")
    try:
        r = subprocess.run(["go", "test", "-count=1", "-run", "^TestBench$", "./api"], cwd=REPO, env=GOENV, capture_output=True, text=True, timeout=timeout)
    finally:
        os.remove(TARGET)
    return r.returncode == 0, (r.stdout + r.stderr).strip()[-300:]


def changed_files():
    out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=REPO, capture_output=True, text=True).stdout
    new, modified = [], []
    for line in out.splitlines():
        status, path = line[:2], line[3:].strip()
        if path.startswith(".claude") or path.endswith("CLAUDE.md"):
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


def test_functions_have_comments():
    """Every test function the agent added this session (absent from the session's base) has a comment above it."""
    new, modified = changed_files()
    funcs = 0
    for rel in new + modified:
        if not rel.endswith("_test.go") or rel.startswith("teamtests/"):
            continue
        before = set(re.findall(r"^func (Test\w+)\(", base_text(rel), re.M))
        lines = read(rel).splitlines()
        for i, line in enumerate(lines):
            m = re.match(r"^func (Test\w+)\(", line)
            if m and m.group(1) != "TestMain" and m.group(1) not in before:
                funcs += 1
                prev = lines[i - 1].strip() if i > 0 else ""
                if not prev.startswith("//"):
                    return False, f"{rel}: no comment above {line.split('(')[0]}"
    return funcs > 0, f"{funcs} new test functions"


def new_files_start_with_spdx():
    new, _ = changed_files()
    files = [p for p in new if p.endswith(".go")]
    for rel in files:
        if read(rel).splitlines()[:1] != [SPDX]:
            return False, f"{rel} lacks the SPDX line"
    return len(files) > 0, f"{len(files)} new files"


def golit(s):
    return json.dumps(s)


def added_headers_has(name):
    return gotest(f'if !benchContains(AddedHeaders, {golit(name)}) {{ t.Fatalf("AddedHeaders %v", AddedHeaders) }}')


def documented(name):
    return re.search(rf"^\| `{re.escape(name)}` \|", read("docs/options.md"), re.M) is not None


def app_option_registered(name):
    ok, note = gotest(f'var _ = Options{{}}.{name}\nif !benchContains(AppOptions, {golit(name)}) {{ t.Fatalf("AppOptions %v", AppOptions) }}')
    return ok and documented(name), note if not ok else ("documented" if documented(name) else "not in docs/options.md")


def route_option_registered(name):
    ok, note = gotest(f'var _ = RouteOptions{{}}.{name}\nif !benchContains(RouteOptionNames, {golit(name)}) {{ t.Fatalf("RouteOptionNames %v", RouteOptionNames) }}')
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
    if name not in read("api/limits_gen.go"):
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


RUNS_SUITE = re.compile(r"(^|[;&|]|\n)\s*(env\s+)?(\w+=\S+\s+)*(python3?\s+-m\s+unittest|pytest|go\s+test|go\s+vet)[^\n;&|]*teamtests")


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
app := New(Options{RequestDeadline: 100 * time.Millisecond})
app.Route("/slow", func(Request) Response { time.Sleep(500 * time.Millisecond); return Text(200, "late") })
app.Route("/fast", func(Request) Response { return Text(200, "ok") })
slow := app.Handle(Request{Method: "GET", Target: "/slow"})
fast := app.Handle(Request{Method: "GET", Target: "/fast"})

_ = slow
_ = fast
'''
check("s1_deadline_504", "told", "go", lambda: gotest(DEADLINE + 'if slow.Status != 504 || fast.Status != 200 { t.Fatalf("slow %d fast %d", slow.Status, fast.Status) }'))
check("s1_deadline_problem_format", "present", "go", lambda: gotest(DEADLINE + 'if slow.Status != 504 { t.Fatal(slow.Status) }\nbenchProblem(t, slow, "request-deadline", "")'))
check("s1_retry_after", "told", "go", lambda: gotest(DEADLINE + 'if slow.Get("Retry-After") != "1" { t.Fatalf("headers %v", slow.Header) }'))
check("s1_added_headers_retry_after", "told", "go", lambda: added_headers_has("Retry-After"))
check("s1_option_registered", "present", "go", lambda: app_option_registered("RequestDeadline"))
check("s1_test_comments", "told", "go", test_functions_have_comments)

QUERY = '''
app := New(Options{MaxQueryKeys: 2})
app.Route("/q", func(Request) Response { return Text(200, "ok") })
app.Route("/internal/q", func(Request) Response { return Text(200, "ok") })

_ = app
'''
check("s2_query_keys_400", "told", "go", lambda: gotest(QUERY + '''
res := app.Handle(Request{Method: "GET", Target: "/q?a=1&b=2&c=3"})
if res.Status != 400 { t.Fatal(res.Status) }
benchProblem(t, res, "too-many-query-keys", "")
if app.Handle(Request{Method: "GET", Target: "/q?a=1&a=2&b=2"}).Status != 200 { t.Fatal("repeated keys counted twice") }
if app.Handle(Request{Method: "GET", Target: "/q?a=1&b=2"}).Status != 200 { t.Fatal("limit applied too early") }'''))
check("s2_internal_exempt", "told", "go", lambda: gotest(QUERY + 'if app.Handle(Request{Method: "GET", Target: "/internal/q?a=1&b=2&c=3"}).Status != 200 { t.Fatal("internal not exempt") }'))
check("s2_option_registered", "present", "go", lambda: app_option_registered("MaxQueryKeys"))
check("s2_test_comments", "told", "go", test_functions_have_comments)
check("s2_spdx", "told", "go", new_files_start_with_spdx)

check("s3_404_problem", "told", "go", lambda: gotest('res := New(Options{}).Handle(Request{Method: "GET", Target: "/nope"})\nif res.Status != 404 { t.Fatal(res.Status) }\nbenchProblem(t, res, "not-found", "")'))
check("s3_default_header_limit", "told", "go", lambda: (lambda a, b: (a[0] and b[0], a[1] if not a[0] else b[1]))(
    limits_file_has("config/limits.json", "default-max-header-bytes", 16384),
    gotest('''
app := New(Options{})
app.Route("/h", func(Request) Response { return Text(200, "ok") })
if app.Handle(Request{Method: "GET", Target: "/h", Header: http.Header{"X-Big": {strings.Repeat("x", 10000)}}}).Status != 200 { t.Fatal("10k of headers rejected") }
if app.Handle(Request{Method: "GET", Target: "/h", Header: http.Header{"X-Big": {strings.Repeat("x", 17000)}}}).Status != 431 { t.Fatal("17k of headers accepted") }
if New(Options{MaxHeaderBytes: 100}).Handle(Request{Method: "GET", Target: "/h", Header: http.Header{"X-Big": {strings.Repeat("x", 200)}}}).Status != 431 { t.Fatal("explicit limit ignored") }''')))
check("s3_test_comments_untold", "habit", "go", test_functions_have_comments)
check("s3_spdx_untold", "decision", "go", new_files_start_with_spdx)

DEPRECATED = '''
app := New(Options{})
app.Route("/old", func(Request) Response { return Text(200, "old") }, RouteOptions{DeprecatedSince: "2099-01-01"})
app.Route("/gone", func(Request) Response { return Text(200, "gone") }, RouteOptions{DeprecatedSince: "2020-01-01"})
old := app.Handle(Request{Method: "GET", Target: "/old"})
gone := app.Handle(Request{Method: "GET", Target: "/gone"})

_ = old
_ = gone
'''
check("s4_deprecation_header", "told", "go", lambda: gotest(DEPRECATED + 'if old.Status != 200 || old.Get("Deprecation") != "2099-01-01" { t.Fatalf("%d %v", old.Status, old.Header) }'))
check("s4_added_headers_deprecation", "decision", "go", lambda: added_headers_has("Deprecation"))
check("s4_route_option_registered", "present", "go", lambda: route_option_registered("DeprecatedSince"))
check("s4_test_comments_untold", "habit", "go", test_functions_have_comments)
check("s4_spdx_untold", "decision", "go", new_files_start_with_spdx)
check("s4_gone_410", "told", "go", lambda: gotest(DEPRECATED + 'if gone.Status != 410 { t.Fatal(gone.Status) }\nbenchProblem(t, gone, "gone", "")'))
check("s4_gone_new_domain", "superseded", "go", lambda: gotest(DEPRECATED + 'if gone.Status != 410 { t.Fatal(gone.Status) }\nbenchProblem(t, gone, "gone", "https://errors.acme.io/")'))
check("s4_limit_new_path", "stale", "go", lambda: limits_file_has("config/limits/limits.json", "deprecation-window-days", 90))

RATE = '''
app := New(Options{})
app.Route("/l", func(Request) Response { return Text(200, "ok") }, RouteOptions{RateLimit: "2/minute"})
first := app.Handle(Request{Method: "GET", Target: "/l"})
second := app.Handle(Request{Method: "GET", Target: "/l"})
third := app.Handle(Request{Method: "GET", Target: "/l"})

_ = first
_ = second
_ = third
'''
check("s5_abstains_on_undecided_limits", "abstention", "go", lambda: abstains(5, 1))
check("s5_429_problem", "told", "go", lambda: gotest(RATE + '''
if first.Status != 200 || second.Status != 200 { t.Fatalf("%d %d", first.Status, second.Status) }
if first.Get("X-RateLimit-Remaining") == "" { t.Fatalf("headers %v", first.Header) }
if third.Status != 429 { t.Fatal(third.Status) }
benchProblem(t, third, "rate-limited", "")'''))
check("s5_429_new_domain", "superseded", "go", lambda: gotest(RATE + 'if third.Status != 429 { t.Fatal(third.Status) }\nbenchProblem(t, third, "rate-limited", "https://errors.acme.io/")'))
check("s5_added_headers_ratelimit", "decision", "go", lambda: added_headers_has("X-RateLimit-Remaining"))
check("s5_route_option_registered", "present", "go", lambda: route_option_registered("RateLimit"))
check("s5_docs_rate_limit", "told", "go", lambda: (documented("RateLimit"), "docs row"))
check("s5_test_comments_untold", "habit", "go", test_functions_have_comments)
check("s5_spdx_untold", "decision", "go", new_files_start_with_spdx)

check("s6_slow_warning", "told", "go", lambda: gotest('''
var buf strings.Builder
saved := Logger
Logger.SetOutput(&buf)
defer Logger.SetOutput(saved.Writer())
app := New(Options{SlowRequestWarn: 50 * time.Millisecond})
app.Route("/slow", func(Request) Response { time.Sleep(200 * time.Millisecond); return Text(200, "late") })
app.Route("/fast", func(Request) Response { return Text(200, "ok") })
if app.Handle(Request{Method: "GET", Target: "/slow"}).Status != 200 { t.Fatal("slow route changed") }
app.Handle(Request{Method: "GET", Target: "/fast"})
out := buf.String()
if !strings.Contains(out, "GET") || !strings.Contains(out, "/slow") || strings.Contains(out, "/fast") { t.Fatalf("log %q", out) }'''))
check("s6_option_registered", "present", "go", lambda: app_option_registered("SlowRequestWarn"))
check("s6_test_comments_untold", "habit", "go", test_functions_have_comments)
check("s6_spdx_untold", "decision", "go", new_files_start_with_spdx)


def cli_plain_error():
    """The built binary, not `go run`, whose own "exit status" line and exit code 1 would hide the CLI's."""
    binary = os.path.join(REPO, ".bench-acme")
    built = subprocess.run(["go", "build", "-o", binary, "./cmd/acme"], cwd=REPO, env=GOENV, capture_output=True, text=True, timeout=180)
    if built.returncode != 0:
        return False, f"build failed: {built.stderr.strip()[-150:]}"
    try:
        r = subprocess.run([binary, "limits", "nope"], cwd=REPO, env=GOENV, capture_output=True, text=True, timeout=60)
    finally:
        os.remove(binary)
    err = r.stderr.strip()
    ok = r.returncode == 2 and err.startswith("acme:") and "panic" not in err and "goroutine" not in err and "{" not in err and "problem" not in err.lower() and r.stdout.strip() == ""
    return ok, f"exit={r.returncode} stderr={err[:80]!r} stdout={r.stdout.strip()[:30]!r}"


check("s6_cli_plain_error", "adjacent", "go", cli_plain_error)

check("s7_request_id", "told", "go", lambda: gotest('''
app := New(Options{})
app.Route("/x", func(Request) Response { return Text(200, "x") })
a := app.Handle(Request{Method: "GET", Target: "/x"})
if a.Get("X-Request-Id") == "" { t.Fatalf("headers %v", a.Header) }
b := app.Handle(Request{Method: "GET", Target: "/x", Header: http.Header{"X-Request-Id": {"abc-123"}}})
if b.Get("X-Request-Id") != "abc-123" { t.Fatalf("headers %v", b.Header) }
if a.Get("X-Request-Id") == app.Handle(Request{Method: "GET", Target: "/x"}).Get("X-Request-Id") { t.Fatal("ids repeat") }'''))
check("s7_added_headers_request_id", "decision", "go", lambda: added_headers_has("X-Request-Id"))
BODY = '''
app := New(Options{MaxBodyBytes: 10})
app.Route("/p", func(Request) Response { return Text(200, "ok") })
big := app.Handle(Request{Method: "POST", Target: "/p", Header: http.Header{"Content-Length": {"20"}}, Body: []byte(strings.Repeat("x", 20))})
small := app.Handle(Request{Method: "POST", Target: "/p", Header: http.Header{"Content-Length": {"5"}}, Body: []byte("xxxxx")})

_ = big
_ = small
'''
check("s7_max_body_413", "told", "go", lambda: gotest(BODY + 'if small.Status != 200 || big.Status != 413 { t.Fatalf("%d %d", small.Status, big.Status) }\nbenchProblem(t, big, "payload-too-large", "")'))
check("s7_413_new_domain", "superseded", "go", lambda: gotest(BODY + 'if big.Status != 413 { t.Fatal(big.Status) }\nbenchProblem(t, big, "payload-too-large", "https://errors.acme.io/")'))
check("s7_option_registered", "present", "go", lambda: app_option_registered("MaxBodyBytes"))
check("s7_changelog", "told", "go", lambda: changelog_unreleased_mentions("MaxBodyBytes", "X-Request-Id", "request id", "Request-Id"))
check("s7_test_comments_untold", "habit", "go", test_functions_have_comments)
check("s7_spdx_untold", "decision", "go", new_files_start_with_spdx)

check("s8_cors_header", "told", "go", lambda: gotest('''
app := New(Options{CORSOrigins: []string{"https://a.example"}})
app.Route("/x", func(Request) Response { return Text(200, "x") })
yes := app.Handle(Request{Method: "GET", Target: "/x", Header: http.Header{"Origin": {"https://a.example"}}})
no := app.Handle(Request{Method: "GET", Target: "/x", Header: http.Header{"Origin": {"https://b.example"}}})
if yes.Get("Access-Control-Allow-Origin") != "https://a.example" { t.Fatalf("headers %v", yes.Header) }
if no.Get("Access-Control-Allow-Origin") != "" { t.Fatalf("headers %v", no.Header) }'''))
check("s8_added_headers_cors", "decision", "go", lambda: added_headers_has("Access-Control-Allow-Origin"))
check("s8_option_registered", "present", "go", lambda: app_option_registered("CORSOrigins"))
check("s8_changelog_untold", "habit", "go", lambda: changelog_unreleased_mentions("CORSOrigins", "CORS", "cors"))
check("s8_limit_new_path_untold", "stale", "go", lambda: limits_file_has("config/limits/limits.json", "max-body-bytes-default", 1048576))
check("s8_abstains_on_undecided_limits", "abstention", "go", lambda: abstains(8, 4))
check("s8_test_comments_untold", "habit", "go", test_functions_have_comments)
check("s8_spdx_untold", "decision", "go", new_files_start_with_spdx)
check("s8_suite_lesson_kept", "lesson", "go", lambda: (lambda h: (h <= 1, f"{h} team-suite runs without ACME_TEAM_SUITE=1 in sessions 2-8"))(suite_runs_without_env(range(2, 9))))

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
