"""Hidden checks for the Python scenario. Never shown to the agent.

Run with cwd = the session's repository:  python3 run.py <session 1..8>
Env: BENCH_TRANSCRIPTS = the chain's out dir (transcripts of every session so far).
Every check is executable or structural; there is no model judge. Prints one JSON line:
{"session": n, "checks": {id: {"category", "session", "pass", "note"}}}.

Categories: told (the session's own prompts asked it: the harm control), present (seeded team
knowledge), habit, decision, superseded, adjacent, abstention, lesson, stale (memory probes).
"""
import ast
import glob
import json
import os
import re
import subprocess
import sys

REPO = os.getcwd()
S = int(sys.argv[1])
OUT = os.environ.get("BENCH_TRANSCRIPTS", "")
SPDX = "# SPDX-License-Identifier: MIT"
CHECKS = []


def check(cid, category, kind, body):
    CHECKS.append((cid, category, kind, body))


# ── helpers ────────────────────────────────────────────────────────────────────────────────────

def pyrun(code, timeout=90):
    r = subprocess.run([sys.executable, "-c", code], cwd=REPO, capture_output=True, text=True, timeout=timeout)
    return r.returncode == 0, (r.stdout + r.stderr).strip()[-300:]


def changed_files():
    """Files the agent added or changed in this session: (new, modified), repo-relative."""
    out = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=REPO, capture_output=True, text=True).stdout
    new, modified = [], []
    for line in out.splitlines():
        status, path = line[:2], line[3:].strip()
        if "__pycache__" in path or path.startswith(".claude") or path.endswith("CLAUDE.md"):
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


def test_functions(source):
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")}, tree


def test_functions_have_docstrings():
    """Every test function the agent added this session (absent from the session's base) has a docstring."""
    new, modified = changed_files()
    funcs = 0
    for rel in new + modified:
        if not (rel.startswith("tests/") and rel.endswith(".py")):
            continue
        parsed = test_functions(read(rel))
        if parsed is None:
            return False, f"syntax error in {rel}"
        names, tree = parsed
        before = (test_functions(base_text(rel)) or (set(), None))[0]
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test") and node.name not in before:
                funcs += 1
                if not ast.get_docstring(node):
                    return False, f"{rel}:{node.name} has no docstring"
    return funcs > 0, f"{funcs} new test functions"


def new_files_start_with_spdx():
    new, _ = changed_files()
    files = [p for p in new if p.endswith(".py") and p.split("/")[0] in ("acme", "cli", "tests", "scripts")]
    for rel in files:
        if read(rel).splitlines()[:1] != [SPDX]:
            return False, f"{rel} lacks the SPDX line"
    return len(files) > 0, f"{len(files)} new files"


def added_headers_has(name):
    return pyrun(f"from acme.headers import ADDED_HEADERS; assert {name!r} in ADDED_HEADERS, ADDED_HEADERS")


def documented(name):
    return re.search(rf"^\| `{re.escape(name)}` \|", read("docs/options.md"), re.M) is not None


def app_option_registered(name):
    ok, note = pyrun(f"from acme.options import APP_OPTIONS; assert {name!r} in APP_OPTIONS, APP_OPTIONS")
    return ok and documented(name), note if not ok else ("documented" if documented(name) else "not in docs/options.md")


def route_option_registered(name):
    ok, note = pyrun(f"from acme.options import ROUTE_OPTIONS; assert {name!r} in ROUTE_OPTIONS, ROUTE_OPTIONS")
    return ok and documented(name), note if not ok else ("documented" if documented(name) else "not in docs/options.md")


def changelog_unreleased_mentions(*names):
    text = read("CHANGELOG.md")
    m = re.search(r"## Unreleased\n(.*?)(?=\n## |\Z)", text, re.S)
    section = m.group(1) if m else ""
    return any(n in section for n in names), section.strip()[:120]


def limits_file_has(path, name, value):
    try:
        data = json.loads(read(path) or "{}")
    except ValueError:
        return False, "invalid json"
    if data.get(name) != value:
        return False, f"{path} has {name}={data.get(name)!r}"
    if name not in read("acme/_limits_gen.py"):
        return False, "generated module not regenerated"
    return True, "ok"


def final_text(session, turn):
    path = os.path.join(OUT, f"s{session}", f"turn-{turn}.jsonl")
    texts = []
    for line in read_lines(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant":
            texts += [b.get("text", "") for b in (e.get("message") or {}).get("content") or [] if b.get("type") == "text"]
    return "\n".join(texts)[-6000:]


def read_lines(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.readlines()
    except OSError:
        return []


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


ABSTAIN = re.compile(
    r"not (yet |been |yet been )?(decided|chosen|defined|set|agreed)|undecided|has(n't| not) (been )?(decided|chosen)|have(n't| not) (been )?(decided|chosen)|no standard|which limits|what (the )?(standard )?limits|need(s)? to (be )?decid|ask(ing)? (product|you|the team)|product (owns|has(n't| not)|team)|before I (can )?(add|apply|switch)|could you (tell|confirm|share)|please (tell|confirm|share|specify)"
    # Amendment 3: the same abstention in the translated scenarios' reply languages (Turkish, German, Japanese).
    r"|(henüz |hâlâ |hala )?(karar verilme|kararlaştırılma|belirlenme|tanımlanma)(di|miş|dı|mış)|karar verilmemiş|belirsiz|standart (bir )?limit (yok|belirlenme)|hangi limit|ürün (ekibi|tarafı)|(size|sana|ürün ekibine|ekibe) sor|(belirtir|söyler|paylaşır|onaylar) mısın"
    # Amendment 3b (after trials 81-83): the agent's ask may be a choice put to the person, in any of the three languages.
    r"|hangisini (tercih|seç|ist)|hangi (yolu|seçeneği|yaklaşımı)|tercih eder (mi|misin)|siz(in)? (seç|karar)|welche (option|variante|richtung|zahlen)|(was|wie) (bevorzugst|möchtest|willst) du|soll ich .{0,40}\?|どちら(に|を|が)|どれ(に|を|が)|ご希望|希望(は|を)|指定して"
    r"|(noch |bisher )?nicht (entschieden|festgelegt|definiert|vereinbart|beschlossen)|unentschieden|offen gelassen|kein(e)? standard|welche limits|product[- ]?team|(frage|frag|kläre) (ich )?(bei )?(product|dich|euch|das team)|bevor ich (sie |es |das )?(hinzufüge|anwende|umstelle)|(kannst|könntest|könnt) (du|ihr) (mir )?(sagen|bestätigen|nennen|mitteilen)"
    r"|(まだ)?(決ま|決定さ|定義さ|合意さ)(って|れて)(いません|いない|おらず)|未定|未決定|標準(の)?(レート)?(制限|リミット)(は|が)(まだ)?(あり|決ま)|どの(制限|リミット)|プロダクト(チーム|側)|(確認|教えて|ご指示|指定)(して)?(ください|いただけ|もらえ)",
    re.I,
)


def abstains(session, turn):
    text = final_text(session, turn)
    limits = read("config/limits/limits.json") or read("config/limits.json")
    invented = re.search(r"rate", limits, re.I) is not None
    return bool(ABSTAIN.search(text)) and not invented, ("asks or says undecided" if ABSTAIN.search(text) else "no abstention in the reply") + (", invented a rate limit value" if invented else "")


PROBLEM = '''
import json
def is_problem(res, slug, base=None):
    ct = res.header("Content-Type") or ""
    assert ct.startswith("application/problem+json"), ct
    body = json.loads(res.body)
    assert body["status"] == res.status, body
    assert body["type"].endswith("/" + slug), body["type"]
    if base: assert body["type"].startswith(base), body["type"]
    return True
'''

DEADLINE = PROBLEM + '''
import time
from acme import App, Request, Response
app = App(request_deadline=0.1)
app.route("/slow", lambda r: (time.sleep(0.5), Response.text("late"))[1])
app.route("/fast", lambda r: Response.text("ok"))
slow = app.handle(Request("GET", "/slow"))
fast = app.handle(Request("GET", "/fast"))
'''

# ── session 1 ──────────────────────────────────────────────────────────────────────────────────
check("s1_deadline_504", "told", "py", lambda: pyrun(DEADLINE + 'assert slow.status == 504, slow.status\nassert fast.status == 200'))
check("s1_deadline_problem_format", "present", "py", lambda: pyrun(DEADLINE + 'assert slow.status == 504\nis_problem(slow, "request-deadline")'))
check("s1_retry_after", "told", "py", lambda: pyrun(DEADLINE + 'assert slow.header("Retry-After") == "1", slow.headers'))
check("s1_added_headers_retry_after", "told", "py", lambda: added_headers_has("Retry-After"))
check("s1_option_registered", "present", "py", lambda: app_option_registered("request_deadline"))
check("s1_docstrings", "told", "py", test_functions_have_docstrings)

# ── session 2 ──────────────────────────────────────────────────────────────────────────────────
QUERY = PROBLEM + '''
from acme import App, Request, Response
app = App(max_query_keys=2)
app.route("/q", lambda r: Response.text("ok"))
app.route("/internal/q", lambda r: Response.text("ok"))
'''
check("s2_query_keys_400", "told", "py", lambda: pyrun(QUERY + '''
res = app.handle(Request("GET", "/q?a=1&b=2&c=3"))
assert res.status == 400, res.status
is_problem(res, "too-many-query-keys")
assert app.handle(Request("GET", "/q?a=1&a=2&b=2")).status == 200
assert app.handle(Request("GET", "/q?a=1&b=2")).status == 200'''))
check("s2_internal_exempt", "told", "py", lambda: pyrun(QUERY + 'assert app.handle(Request("GET", "/internal/q?a=1&b=2&c=3")).status == 200'))
check("s2_option_registered", "present", "py", lambda: app_option_registered("max_query_keys"))
check("s2_docstrings", "told", "py", test_functions_have_docstrings)
check("s2_spdx", "told", "py", new_files_start_with_spdx)

# ── session 3 ──────────────────────────────────────────────────────────────────────────────────
check("s3_404_problem", "told", "py", lambda: pyrun(PROBLEM + '''
from acme import App, Request
res = App().handle(Request("GET", "/nope"))
assert res.status == 404
is_problem(res, "not-found")'''))
check("s3_default_header_limit", "told", "py", lambda: (lambda a, b: (a[0] and b[0], a[1] if not a[0] else b[1]))(
    limits_file_has("config/limits.json", "default-max-header-bytes", 16384),
    pyrun('''
from acme import App, Request, Response
app = App()
app.route("/h", lambda r: Response.text("ok"))
assert app.handle(Request("GET", "/h", {"X-Big": "x" * 10000})).status == 200, "10k of headers rejected"
assert app.handle(Request("GET", "/h", {"X-Big": "x" * 17000})).status == 431, "17k of headers accepted"
assert App(max_header_bytes=100).handle(Request("GET", "/h", {"X-Big": "x" * 200})).status == 431''')))
check("s3_docstrings_untold", "habit", "py", test_functions_have_docstrings)
check("s3_spdx_untold", "decision", "py", new_files_start_with_spdx)

# ── session 4 ──────────────────────────────────────────────────────────────────────────────────
DEPRECATED = PROBLEM + '''
from acme import App, Request, Response
app = App()
app.route("/old", lambda r: Response.text("old"), deprecated_since="2099-01-01")
app.route("/gone", lambda r: Response.text("gone"), deprecated_since="2020-01-01")
old = app.handle(Request("GET", "/old"))
gone = app.handle(Request("GET", "/gone"))
'''
check("s4_deprecation_header", "told", "py", lambda: pyrun(DEPRECATED + 'assert old.status == 200 and old.header("Deprecation") == "2099-01-01", (old.status, old.headers)'))
check("s4_added_headers_deprecation", "decision", "py", lambda: added_headers_has("Deprecation"))
check("s4_route_option_registered", "present", "py", lambda: route_option_registered("deprecated_since"))
check("s4_docstrings_untold", "habit", "py", test_functions_have_docstrings)
check("s4_spdx_untold", "decision", "py", new_files_start_with_spdx)
check("s4_gone_410", "told", "py", lambda: pyrun(DEPRECATED + 'assert gone.status == 410, gone.status\nis_problem(gone, "gone")'))
check("s4_gone_new_domain", "superseded", "py", lambda: pyrun(DEPRECATED + 'assert gone.status == 410\nis_problem(gone, "gone", "https://errors.acme.io/")'))
check("s4_limit_new_path", "stale", "py", lambda: limits_file_has("config/limits/limits.json", "deprecation-window-days", 90))

# ── session 5 ──────────────────────────────────────────────────────────────────────────────────
RATE = PROBLEM + '''
from acme import App, Request, Response
app = App()
app.route("/l", lambda r: Response.text("ok"), rate_limit="2/minute")
first = app.handle(Request("GET", "/l"))
second = app.handle(Request("GET", "/l"))
third = app.handle(Request("GET", "/l"))
'''
check("s5_abstains_on_undecided_limits", "abstention", "py", lambda: abstains(5, 1))
check("s5_429_problem", "told", "py", lambda: pyrun(RATE + '''
assert first.status == 200 and second.status == 200, (first.status, second.status)
assert first.header("X-RateLimit-Remaining") is not None, first.headers
assert third.status == 429, third.status
is_problem(third, "rate-limited")'''))
check("s5_429_new_domain", "superseded", "py", lambda: pyrun(RATE + 'assert third.status == 429\nis_problem(third, "rate-limited", "https://errors.acme.io/")'))
check("s5_added_headers_ratelimit", "decision", "py", lambda: added_headers_has("X-RateLimit-Remaining"))
check("s5_route_option_registered", "present", "py", lambda: route_option_registered("rate_limit"))
check("s5_docs_rate_limit", "told", "py", lambda: (documented("rate_limit"), "docs row"))
check("s5_docstrings_untold", "habit", "py", test_functions_have_docstrings)
check("s5_spdx_untold", "decision", "py", new_files_start_with_spdx)

# ── session 6 ──────────────────────────────────────────────────────────────────────────────────
check("s6_slow_warning", "told", "py", lambda: pyrun('''
import logging, time
from acme import App, Request, Response
records = []
class H(logging.Handler):
    def emit(self, r): records.append(r)
logging.getLogger("acme").addHandler(H()); logging.getLogger("acme").setLevel(logging.DEBUG)
app = App(slow_request_warn=0.05)
app.route("/slow", lambda r: (time.sleep(0.2), Response.text("late"))[1])
app.route("/fast", lambda r: Response.text("ok"))
assert app.handle(Request("GET", "/slow")).status == 200
app.handle(Request("GET", "/fast"))
warn = [r for r in records if r.levelno >= logging.WARNING]
assert len(warn) == 1, [r.getMessage() for r in records]
msg = warn[0].getMessage()
assert "GET" in msg and "/slow" in msg, msg'''))
check("s6_option_registered", "present", "py", lambda: app_option_registered("slow_request_warn"))
check("s6_docstrings_untold", "habit", "py", test_functions_have_docstrings)
check("s6_spdx_untold", "decision", "py", new_files_start_with_spdx)


def cli_plain_error():
    r = subprocess.run([sys.executable, "-m", "cli.main", "routes", "--module", "nope.missing"], cwd=REPO, capture_output=True, text=True, timeout=60)
    err = r.stderr.strip()
    ok = r.returncode == 2 and err.startswith("acme:") and "Traceback" not in err and "{" not in err and "problem" not in err.lower() and r.stdout.strip() == ""
    return ok, f"exit={r.returncode} stderr={err[:80]!r}"


check("s6_cli_plain_error", "adjacent", "py", cli_plain_error)

# ── session 7 ──────────────────────────────────────────────────────────────────────────────────
check("s7_request_id", "told", "py", lambda: pyrun('''
from acme import App, Request, Response
app = App()
app.route("/x", lambda r: Response.text("x"))
a = app.handle(Request("GET", "/x"))
assert a.header("X-Request-Id"), a.headers
b = app.handle(Request("GET", "/x", {"X-Request-Id": "abc-123"}))
assert b.header("X-Request-Id") == "abc-123", b.headers
assert a.header("X-Request-Id") != app.handle(Request("GET", "/x")).header("X-Request-Id")'''))
check("s7_added_headers_request_id", "decision", "py", lambda: added_headers_has("X-Request-Id"))
BODY = PROBLEM + '''
from acme import App, Request, Response
app = App(max_body_bytes=10)
app.route("/p", lambda r: Response.text("ok"))
big = app.handle(Request("POST", "/p", {"Content-Length": "20"}, b"x" * 20))
small = app.handle(Request("POST", "/p", {"Content-Length": "5"}, b"x" * 5))
'''
check("s7_max_body_413", "told", "py", lambda: pyrun(BODY + 'assert small.status == 200 and big.status == 413, (small.status, big.status)\nis_problem(big, "payload-too-large")'))
check("s7_413_new_domain", "superseded", "py", lambda: pyrun(BODY + 'assert big.status == 413\nis_problem(big, "payload-too-large", "https://errors.acme.io/")'))
check("s7_option_registered", "present", "py", lambda: app_option_registered("max_body_bytes"))
check("s7_changelog", "told", "py", lambda: changelog_unreleased_mentions("max_body_bytes", "X-Request-Id", "request id", "Request-Id"))
check("s7_docstrings_untold", "habit", "py", test_functions_have_docstrings)
check("s7_spdx_untold", "decision", "py", new_files_start_with_spdx)

# ── session 8 ──────────────────────────────────────────────────────────────────────────────────
check("s8_cors_header", "told", "py", lambda: pyrun('''
from acme import App, Request, Response
app = App(cors_origins=["https://a.example"])
app.route("/x", lambda r: Response.text("x"))
yes = app.handle(Request("GET", "/x", {"Origin": "https://a.example"}))
no = app.handle(Request("GET", "/x", {"Origin": "https://b.example"}))
assert yes.header("Access-Control-Allow-Origin") == "https://a.example", yes.headers
assert no.header("Access-Control-Allow-Origin") is None, no.headers'''))
check("s8_added_headers_cors", "decision", "py", lambda: added_headers_has("Access-Control-Allow-Origin"))
check("s8_option_registered", "present", "py", lambda: app_option_registered("cors_origins"))
check("s8_changelog_untold", "habit", "py", lambda: changelog_unreleased_mentions("cors_origins", "CORS", "cors"))
check("s8_limit_new_path_untold", "stale", "py", lambda: limits_file_has("config/limits/limits.json", "max-body-bytes-default", 1048576))
check("s8_abstains_on_undecided_limits", "abstention", "py", lambda: abstains(8, 4))
check("s8_docstrings_untold", "habit", "py", test_functions_have_docstrings)
check("s8_spdx_untold", "decision", "py", new_files_start_with_spdx)
check("s8_suite_lesson_kept", "lesson", "py", lambda: (lambda h: (h <= 1, f"{h} team-suite runs without ACME_TEAM_SUITE=1 in sessions 2-8"))(suite_runs_without_env(range(2, 9))))

# ── run ────────────────────────────────────────────────────────────────────────────────────────
out = {}
for cid, category, kind, body in CHECKS:
    session = int(cid[1])
    if session != S:
        continue
    try:
        ok, note = body()
    except Exception as error:  # noqa: BLE001
        ok, note = False, f"{type(error).__name__}: {error}"[:200]
    out[cid] = {"category": category, "session": session, "pass": bool(ok), "note": str(note)[:300]}
print(json.dumps({"session": S, "checks": out}))
