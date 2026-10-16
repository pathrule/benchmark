#!/usr/bin/env python3
"""Aggregate PathruleBench v3 chains: per arm and category, and paired differences with bootstrap CIs.

Usage: aggregate.py <runs-dir> <out-dir> <lang> <trial,trial,...> [arm ...]
Memory probes (the headline) are the categories habit, decision, superseded, adjacent, abstention,
lesson and stale. present = seeded team knowledge; told = what the prompts asked (the harm control).
"""
import json
import os
import random
import statistics
import sys

runs, out_dir, lang, trials = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4].split(",")
arms = sys.argv[5:] or ["none", "claude_md", "pathrule"]
MEMORY = {"habit", "decision", "superseded", "adjacent", "abstention", "lesson", "stale"}
PRICE = {"input_tokens": 2.0, "cache_creation_input_tokens": 2.5, "cache_read_input_tokens": 0.10, "output_tokens": 10.0}


def chain(arm, t):
    d = os.path.join(runs, f"{lang}-{arm}-t{t}", "out")
    sessions = [json.load(open(os.path.join(d, f"session-s{s}.json"))) for s in range(1, 9) if os.path.exists(os.path.join(d, f"session-s{s}.json"))]
    if len(sessions) < 8:
        return {"arm": arm, "trial": t, "complete": False, "sessions": len(sessions)}
    checks = {cid: c for sess in sessions for cid, c in (sess["checks"].get("checks") or {}).items()}
    rows = [r for sess in sessions for r in sess["rows"]]
    return {
        "arm": arm, "trial": t, "complete": True, "checks": checks,
        "cost_usd": round(sum(r["cost"] for r in rows), 3), "steps": sum(r.get("steps") or 0 for r in rows),
        "tokens": {k: sum(((r.get("usage") or {}).get(k) or 0) for r in rows) for k in PRICE},
    }


results = [chain(a, t) for a in arms for t in trials]
complete = [r for r in results if r["complete"]]
os.makedirs(out_dir, exist_ok=True)
json.dump(results, open(os.path.join(out_dir, "results.json"), "w"), indent=1)


def group(r, cat):
    items = [c for c in r["checks"].values() if (c["category"] in MEMORY if cat == "memory" else c["category"] == cat)]
    return sum(c["pass"] for c in items), len(items)


def fmt_rate(rs, cat):
    if not rs:
        return "-"
    vals = [group(r, cat) for r in rs]
    tot = vals[0][1]
    mean = statistics.mean(v[0] for v in vals)
    rng = f" [{min(v[0] for v in vals)}–{max(v[0] for v in vals)}]" if len(vals) > 1 else ""
    return f"{mean:.1f}{rng} / {tot}"


def probe_rates(rs):
    """Per probe id: the pass rate over trials."""
    ids = sorted({cid for r in rs for cid in r["checks"]})
    return {cid: statistics.mean(1.0 if r["checks"].get(cid, {}).get("pass") else 0.0 for r in rs) for cid in ids}


def paired(a_arm, b_arm, cat):
    a = [r for r in complete if r["arm"] == a_arm]
    b = [r for r in complete if r["arm"] == b_arm]
    if not a or not b:
        return None
    ra, rb = probe_rates(a), probe_rates(b)
    ids = [cid for cid in ra if cid in rb and (a[0]["checks"][cid]["category"] in MEMORY if cat == "memory" else a[0]["checks"][cid]["category"] == cat)]
    if not ids:
        return None
    diffs = [ra[i] - rb[i] for i in ids]
    rng = random.Random(7)
    boots = sorted(statistics.mean(rng.choice(diffs) for _ in diffs) for _ in range(2000))
    return statistics.mean(diffs), boots[50], boots[1949], len(ids)


md = [f"# PathruleBench v3 results: {lang}", "", f"Trials {', '.join(trials)}. Mean passes over trials [min–max] / probes. `memory` = probes of knowledge stated in an earlier session or seeded; `present` = seeded team knowledge; `told` = what the session's own prompts asked (harm control).", "",
      "| Arm | n | memory | present | told | Cost USD | Steps |", "| --- | --- | --- | --- | --- | --- | --- |"]
for arm in arms:
    rs = [r for r in complete if r["arm"] == arm]
    if not rs:
        continue
    cost = statistics.mean(r["cost_usd"] for r in rs)
    md.append(f"| {arm} | {len(rs)} | {fmt_rate(rs, 'memory')} | {fmt_rate(rs, 'present')} | {fmt_rate(rs, 'told')} | {cost:.2f} | {statistics.mean(r['steps'] for r in rs):.0f} |")
md += ["", "## Memory probes by category (mean passes / probes)", "", "| Arm | " + " | ".join(sorted(MEMORY)) + " |", "| --- |" + " --- |" * len(MEMORY)]
for arm in arms:
    rs = [r for r in complete if r["arm"] == arm]
    if rs:
        md.append(f"| {arm} | " + " | ".join(fmt_rate(rs, c) for c in sorted(MEMORY)) + " |")
md += ["", "## Paired differences (pathrule minus claude_md), bootstrap 95% CI over probes", ""]
for cat in ("memory", "present", "told"):
    p = paired("pathrule", "claude_md", cat)
    if p:
        md.append(f"- {cat}: {p[0]:+.2f} [{p[1]:+.2f}, {p[2]:+.2f}] over {p[3]} probes")
md += ["", "## Probes every arm failed or passed in every trial", ""]
if complete:
    ids = sorted({cid for r in complete for cid in r["checks"]})
    rates = {arm: probe_rates([r for r in complete if r["arm"] == arm]) for arm in arms if any(r["arm"] == arm for r in complete)}
    md += ["| Probe | category | " + " | ".join(rates) + " |", "| --- | --- |" + " --- |" * len(rates)]
    for cid in ids:
        cat = next(r["checks"][cid]["category"] for r in complete if cid in r["checks"])
        md.append(f"| {cid} | {cat} | " + " | ".join(f"{rates[a].get(cid, 0):.2f}" for a in rates) + " |")
inc = [r for r in results if not r["complete"]]
if inc:
    md += ["", "## Incomplete chains", ""] + [f"- {r['arm']} t{r['trial']}: {r['sessions']} sessions" for r in inc]
open(os.path.join(out_dir, "RESULTS.md"), "w").write("\n".join(md) + "\n")
print("\n".join(md))
