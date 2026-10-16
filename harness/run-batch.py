#!/usr/bin/env python3
"""Run PathruleBench v3 chains from a job list, N at a time.

   PR_SRC=<pathrule source worktree> run-batch.py <jobs-file> [parallel]
   jobs-file lines: <lang> <arm> <trial> <knowledge.json> [sessions.<lang>.json]   (# comments allowed)

Each chain is one run-chain.mjs process with PRB3_KNOWLEDGE set from its line; its output goes to
$PRB3_ROOT/logs/<chain>.log. PR_SRC must not be edited while chains run: every turn starts a fresh MCP
server from that source.
"""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

JOBS, PAR = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 4
HARNESS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.environ.get("PRB3_ROOT", os.path.join(os.path.dirname(HARNESS), "runs"))
LOGS, LEDGER = os.path.join(ROOT, "logs"), os.path.join(ROOT, "spend.jsonl")
os.makedirs(LOGS, exist_ok=True)


def spend():
    return round(sum(json.loads(l)["cost"] for l in open(LEDGER) if l.strip()), 2) if os.path.exists(LEDGER) else 0.0


def run(job):
    lang, arm, trial, know = job[:4]
    chain = f"{lang}-{arm}-t{trial}"
    env = {**os.environ, "PRB3_KNOWLEDGE": know}
    if len(job) > 4:
        env["PRB3_SESSIONS"] = job[4]
    print(time.strftime("%H:%M:%S"), "start", chain, know, flush=True)
    t0 = time.time()
    with open(os.path.join(LOGS, f"{chain}.log"), "w") as log:
        rc = subprocess.call(["node", os.path.join(HARNESS, "run-chain.mjs"), lang, arm, trial], env=env, stdout=log, stderr=subprocess.STDOUT)
    last = open(os.path.join(LOGS, f"{chain}.log")).read().strip().split("\n")[-1][:160]
    print(time.strftime("%H:%M:%S"), "done ", chain, f"rc={rc}", f"{(time.time() - t0) / 60:.0f}min", last, flush=True)
    return chain, rc


jobs = [l.split() for l in open(JOBS) if l.strip() and not l.strip().startswith("#")]
print("jobs:", len(jobs), "parallel:", PAR, "spend before:", spend(), flush=True)
with ThreadPoolExecutor(max_workers=PAR) as ex:
    results = list(ex.map(run, jobs))
print("all done; spend:", spend(), "failed:", [c for c, rc in results if rc != 0], flush=True)
