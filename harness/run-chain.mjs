#!/usr/bin/env node
// One PathruleBench v3 chain = one language x one arm x one trial: 8 sessions x 4 turns.
//   node run-chain.mjs <python|go> <none|oracle|claude_md|pathrule> <trial> [--sessions 1,2,...]
// Every session starts from the scenario's repository state (the fixture plus the teammate overlays due
// by then), never from the agent's previous output. Only memory carries over: CLAUDE.md files and Claude's
// auto memory (claude_md), the Pathrule store (pathrule), nothing (none, oracle). Turns inside a session
// resume one Claude Code session; each session is a new one. Hidden checks run in the worktree after the
// session; the worktree is deleted after the chain. Nothing is installed and nothing is copied twice.
import { execFileSync, spawnSync } from "node:child_process";
import { appendFileSync, cpSync, existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { dirname, join, relative } from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";

const HARNESS = dirname(fileURLToPath(import.meta.url));
const BENCH = dirname(HARNESS);
const [lang, arm, trial] = process.argv.slice(2);
const argv = (k, d) => { const i = process.argv.indexOf(`--${k}`); return i > 0 ? process.argv[i + 1] : d; };
if (!["none", "oracle", "claude_md", "pathrule"].includes(arm)) throw new Error(`unknown arm ${arm}`);
const LANGDIR = join(BENCH, lang);
if (!existsSync(join(LANGDIR, "fixture"))) throw new Error(`unknown language ${lang}`);

// Where chains run and spend is kept (PRB3_ROOT, default ./runs next to this repository); the model; the
// spend cap in USD after which no turn starts; and PR_SRC, a checkout of pathrule/pathrule the pathrule
// arm runs from (its `setup --local`, `sync --local` and MCP server, through tsx from source).
const ROOT = process.env.PRB3_ROOT ?? join(BENCH, "runs");
const MODEL = process.env.PRB3_MODEL ?? "claude-sonnet-5-5";
const CAP = Number(process.env.PRB3_CAP_USD ?? "50");
const PR_SRC = process.env.PR_SRC ?? "";
if (arm === "pathrule" && !PR_SRC) throw new Error("PR_SRC must name a checkout of pathrule/pathrule (pnpm install, pnpm natives:node) for the pathrule arm");
const LEDGER = join(ROOT, "spend.jsonl");
// PRB3_SESSIONS names a translated scenario (sessions.tr.json): the same turns in another language, same checks.
const SESSIONS_FILE = process.env.PRB3_SESSIONS ?? "sessions.json";
const sessions = JSON.parse(readFileSync(join(LANGDIR, SESSIONS_FILE), "utf8"));
const sessionsToRun = argv("sessions", sessions.map((_, i) => i + 1).join(",")).split(",").map(Number);
const ORACLE = arm === "oracle" ? JSON.parse(readFileSync(join(LANGDIR, "oracle.json"), "utf8")) : {};
const KNOWLEDGE = join(LANGDIR, "knowledge", process.env.PRB3_KNOWLEDGE ?? "team.json");
const CHAIN = `${lang}-${arm}-t${trial}`;
const D = join(ROOT, "runs", CHAIN);
const REPO = join(D, "repo"), HOME = join(D, "home"), FAKEHOME = join(D, "fakehome"), OUT = join(D, "out"), MEM = join(D, "memory");
// The Anthropic key: ANTHROPIC_API_KEY, or a file anthropic.key under PRB3_ROOT.
const keyFile = join(ROOT, "anthropic.key");
const apiKey = (process.env.ANTHROPIC_API_KEY ?? (existsSync(keyFile) ? readFileSync(keyFile, "utf8") : "")).trim();
if (!apiKey) throw new Error("set ANTHROPIC_API_KEY (or write it to <PRB3_ROOT>/anthropic.key)");
const node = process.execPath;
const tsx = PR_SRC ? execFileSync("readlink", ["-f", join(PR_SRC, "node_modules/tsx")], { encoding: "utf8" }).trim() : "";

const spent = () => (existsSync(LEDGER) ? readFileSync(LEDGER, "utf8").trim().split("\n").filter(Boolean).reduce((s, l) => s + (JSON.parse(l).cost ?? 0), 0) : 0);
const env = {
  PATH: process.env.PATH, HOME: FAKEHOME, CLAUDE_CONFIG_DIR: join(FAKEHOME, ".claude"), PATHRULE_HOME: HOME,
  ANTHROPIC_API_KEY: apiKey, DISABLE_AUTOUPDATER: "1", DISABLE_TELEMETRY: "1", GOFLAGS: "-mod=mod", GOTOOLCHAIN: "local",
  ...(arm === "none" || arm === "oracle" ? { CLAUDE_CODE_DISABLE_AUTO_MEMORY: "1" } : {}),
};
const pr = (...args) => execFileSync(node, [join(PR_SRC, "scripts/with-sqlite-native.mjs"), node, "--import", `file://${tsx}/dist/loader.mjs`, ...args], { cwd: REPO, env: { ...env, PR_SRC }, encoding: "utf8", maxBuffer: 64 << 20 });
const git = (...args) => execFileSync("git", ["-c", "user.email=team@acme.dev", "-c", "user.name=Acme Platform", ...args], { cwd: REPO, encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });

/** The scenario's repository state before session s: the fixture, then every teammate overlay due by then. */
function buildRepo(s) {
  spawnSync("pkill", ["-f", `${D}/`]);
  rmSync(REPO, { recursive: true, force: true, maxRetries: 10, retryDelay: 500 });
  cpSync(join(LANGDIR, "fixture"), REPO, { recursive: true });
  for (let k = 2; k <= s; k += 1) {
    const overlay = join(LANGDIR, "overlays", `s${k}`);
    if (existsSync(overlay)) cpSync(overlay, REPO, { recursive: true, filter: (src) => !src.endsWith("NOTE.txt") });
  }
  if (arm === "claude_md") {
    if (s === 1) execFileSync("python3", ["-I", join(HARNESS, "render-claude-md.py"), REPO, KNOWLEDGE], { encoding: "utf8" });
    else if (existsSync(MEM)) cpSync(MEM, REPO, { recursive: true });
  }
  git("init", "-q"); git("add", "-A"); git("commit", "-qm", `team state before session ${s}`);
  if (arm === "pathrule") {
    if (s === 1) {
      pr(join(PR_SRC, "packages/cli/src/index.ts"), "setup", "--local", "--no-intelligence", "--yes");
      return JSON.parse(pr(join(HARNESS, "seed-pathrule.mts"), KNOWLEDGE).trim().split("\n").pop());
    }
    pr(join(PR_SRC, "packages/cli/src/index.ts"), "sync", "--local");
  }
  return null;
}

/** What the claude_md arm carries to the next session: every CLAUDE.md the agent left, by path. */
function carryMemory() {
  if (arm !== "claude_md") return;
  rmSync(MEM, { recursive: true, force: true });
  const walk = (dir) => {
    for (const name of readdirSync(dir)) {
      if (name === ".git" || name === "__pycache__") continue;
      const abs = join(dir, name);
      if (statSync(abs).isDirectory()) walk(abs);
      else if (name === "CLAUDE.md") { const rel = relative(REPO, abs); mkdirSync(dirname(join(MEM, rel)), { recursive: true }); cpSync(abs, join(MEM, rel)); }
    }
  };
  walk(REPO);
}

function runTurn(s, t, prompt, sessionId, prev) {
  const before = spent();
  if (before >= CAP) throw new Error(`spend cap reached: ${before.toFixed(2)} >= ${CAP}`);
  const allowed = ["Read", "Edit", "Write", "Glob", "Grep", "Bash", "mcp__pathrule__*"];
  const args = ["-p", prompt, "--output-format", "stream-json", "--verbose", "--model", MODEL, "--permission-mode", "dontAsk",
    "--allowedTools", allowed.join(","), "--max-budget-usd", "3", ...(t === 1 ? ["--session-id", sessionId] : ["--resume", sessionId]),
    "--strict-mcp-config", "--setting-sources", "project", ...(arm === "pathrule" ? ["--mcp-config", join(D, "mcp.json")] : [])];
  const started = Date.now();
  const r = spawnSync("claude", args, { cwd: REPO, env, encoding: "utf8", timeout: 15 * 60_000, maxBuffer: 256 << 20 });
  const dir = join(OUT, `s${s}`); mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, `turn-${t}.jsonl`), r.stdout ?? "");
  if (r.stderr) writeFileSync(join(dir, `turn-${t}.stderr`), r.stderr);
  const events = (r.stdout ?? "").split("\n").filter(Boolean).map((l) => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  const result = events.findLast((e) => e.type === "result") ?? {};
  const tools = {};
  for (const e of events) if (e.type === "assistant") for (const b of e.message?.content ?? []) if (b.type === "tool_use") tools[b.name] = (tools[b.name] ?? 0) + 1;
  const cumulative = Number(result.total_cost_usd ?? 0);
  const cost = Math.max(0, cumulative - prev);
  appendFileSync(LEDGER, JSON.stringify({ at: new Date().toISOString(), chain: CHAIN, s, t, cost }) + "\n");
  return { row: { s, t, exit: r.status, wallMs: Date.now() - started, apiMs: result.duration_api_ms ?? null, cost, usage: result.usage ?? null, steps: result.num_turns ?? null, subtype: result.subtype ?? null, isError: result.is_error ?? null, tools }, cumulative };
}

function runChecks(s) {
  const r = spawnSync("python3", [join(LANGDIR, "checks/run.py"), String(s)], { cwd: REPO, env: { PATH: process.env.PATH, HOME: process.env.HOME, BENCH_TRANSCRIPTS: OUT, GOFLAGS: "-mod=mod", GOTOOLCHAIN: "local" }, encoding: "utf8", timeout: 10 * 60_000, maxBuffer: 64 << 20 });
  const line = (r.stdout ?? "").trim().split("\n").filter((l) => l.startsWith("{")).pop();
  const res = line ? JSON.parse(line) : { error: (r.stderr ?? "").slice(-2000) };
  writeFileSync(join(OUT, `checks-s${s}.json`), JSON.stringify(res, null, 2));
  return res;
}

if (sessionsToRun[0] === 1) {
  rmSync(D, { recursive: true, force: true, maxRetries: 10, retryDelay: 500 });
  for (const d of [OUT, HOME, join(FAKEHOME, ".claude")]) mkdirSync(d, { recursive: true });
  if (arm === "pathrule") writeFileSync(join(D, "mcp.json"), JSON.stringify({ mcpServers: { pathrule: { type: "stdio", command: node,
    args: [join(PR_SRC, "scripts/with-sqlite-native.mjs"), node, "--import", `file://${tsx}/dist/loader.mjs`, join(PR_SRC, "packages/cli/src/index.ts"), "mcp", "run"],
    env: { PATHRULE_LOCAL: "1", PATHRULE_HOME: HOME, HOME: FAKEHOME } } } }));
  const meta = { lang, arm, trial, model: MODEL, knowledge: process.env.PRB3_KNOWLEDGE ?? "team.json", sessions: SESSIONS_FILE, pathrule: execFileSync("git", ["-C", PR_SRC, "rev-parse", "--short", "HEAD"], { encoding: "utf8" }).trim(), claude: execFileSync("claude", ["--version"], { encoding: "utf8" }).trim(), startedAt: new Date().toISOString() };
  writeFileSync(join(OUT, "meta.json"), JSON.stringify(meta, null, 2));
}
for (const s of sessionsToRun) {
  const seed = buildRepo(s);
  if (seed) { const meta = JSON.parse(readFileSync(join(OUT, "meta.json"), "utf8")); meta.seed = seed; writeFileSync(join(OUT, "meta.json"), JSON.stringify(meta, null, 2)); }
  const sessionId = randomUUID(); let prev = 0; const rows = [];
  for (const [i, base] of sessions[s - 1].turns.entries()) {
    const extra = ORACLE[`${s}-${i + 1}`];
    const prompt = extra && base !== "/compact" ? `${base}\n\nContext you need:\n${extra}` : base;
    const { row, cumulative } = runTurn(s, i + 1, prompt, sessionId, prev);
    prev = cumulative; rows.push(row);
    console.log(JSON.stringify({ chain: CHAIN, ...row, usage: undefined, tools: undefined }));
  }
  const checks = runChecks(s);
  carryMemory();
  writeFileSync(join(OUT, `session-s${s}.json`), JSON.stringify({ sessionId, name: sessions[s - 1].name, rows, checks }, null, 2));
  const failed = Object.entries(checks.checks ?? {}).filter(([, c]) => !c.pass).map(([id]) => id);
  console.log(JSON.stringify({ chain: CHAIN, session: s, cost: rows.reduce((a, r) => a + r.cost, 0).toFixed(3), failed }));
}
spawnSync("pkill", ["-f", `${D}/`]);
rmSync(REPO, { recursive: true, force: true, maxRetries: 10, retryDelay: 500 });
console.log(JSON.stringify({ chain: CHAIN, done: true, spend: spent().toFixed(2) }));
