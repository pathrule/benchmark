# PathruleBench

A benchmark of memory for coding agents. The question it answers: when a team's knowledge is carried
between sessions as CLAUDE.md files or as a Pathrule store, with the same items in both, how much of it does
the agent apply in later sessions, at what cost, and does it ever do harm?

Three arms, the same agent (Claude Code, claude-sonnet-5-5), the same prompts, the same hidden checks:

| Arm | What persists between sessions |
| --- | --- |
| `none` | Nothing. |
| `claude_md` | Per-folder CLAUDE.md files seeded with the team's knowledge, kept current by the agent, plus Claude Code's auto memory. |
| `pathrule` | The same items as path-scoped memories in a local Pathrule store (the open-source CLI, local mode, no Cloud, no model). |

Eight sessions of four turns on a small Python, Go or TypeScript toolkit. Knowledge enters only through
the person's prompts and the seeded items: a habit, team decisions, a changed decision, a lesson a
failing command teaches, a teammate's commit that makes an item stale. Probes in session 3 to 8 check,
with executable tests and structural checks, whether what was said earlier reached later work. No model
judges anything.

## Results

Memory probes passed, out of 26 (mean over chains [min–max]); `present` 8/8 and `told` 19/19 in every arm and
every chain, so neither channel costs the agent what the prompt asked. Three chains an arm (five for the
CLAUDE.md arm at Python 1,000), nine conditions: three languages at three sizes of knowledge base. Cost is
a chain of 8 sessions × 4 turns at Claude Code's own accounting.

| Condition | none | claude_md | pathrule | pathrule − claude_md, 95% CI | cost none | cost claude_md | cost pathrule | pathrule / claude_md |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Python, 500 items | 4.7 | 22.3 [21–24] | 25.0 [24–26] | +2.6 [+0.8, +4.9] | $1.30 | $2.06 | $1.70 | 0.82 |
| Python, 1,000 items | 4.3 | 20.8 [15–23] | 25.0 [24–26] | +4.2 [+1.6, +7.3] | $1.30 | $2.62 | $1.71 | 0.65 |
| Python, 2,000 items | 4.0 | 22.3 [20–24] | 25.3 [25–26] | +3.1 [+0.3, +6.0] | $1.31 | $3.89 | $1.76 | 0.45 |
| Go, 500 items | 4.3 | 23.7 [22–25] | 26.0 [26–26] | +2.3 [+0.3, +4.9] | $1.33 | $2.13 | $1.91 | 0.90 |
| Go, 1,000 items | 4.7 | 24.7 [24–26] | 25.3 [25–26] | +0.8 [+0.0, +1.6] | $1.29 | $2.75 | $1.91 | 0.70 |
| Go, 2,000 items | 5.3 | 25.0 [25–25] | 26.0 [26–26] | +1.0 [+0.0, +2.6] | $1.29 | $4.21 | $1.89 | 0.45 |
| TypeScript, 500 items | 3.7 | 24.3 [23–25] | 24.7 [23–26] | +0.3 [-1.3, +2.1] | $1.26 | $2.08 | $1.68 | 0.81 |
| TypeScript, 1,000 items | 3.7 | 22.0 [19–24] | 25.0 [24–26] | +3.1 [+1.3, +4.9] | $1.23 | $2.68 | $1.86 | 0.70 |
| TypeScript, 2,000 items | 3.7 | 22.3 [19–24] | 24.0 [22–26] | +1.6 [-0.8, +3.9] | $1.22 | $4.08 | $1.86 | 0.46 |

Where Pathrule leads: the person's own words. Habits stated once ("every test function starts with a
one-line docstring", "a changelog line for every user-facing change") reach later sessions 6.3 to 7 of 7
in the Pathrule chains and 4.3 to 6.7 in the CLAUDE.md chains, and the CLAUDE.md figure falls as the
knowledge base grows (TypeScript: 6.7 at 500 items, 4.3 at 1,000); a lesson a failing command taught
(`ACME_TEAM_SUITE=1`) is kept in 8 of 9 Pathrule chains in Python and 4 of 9 in TypeScript, in 0 of 20
CLAUDE.md chains in those two languages (both arms keep it in Go); a changed decision (new error types
use the new domain) is applied 3/3 in every Go condition by Pathrule against 1.7 to 2.7 by CLAUDE.md.
Where the two tie: the seeded team knowledge (`present`), decisions stated in prompts (9.6 to 10 of 10 in
both arms), abstention, and the whole TypeScript 500-item condition (+0.3, interval [-1.3, +2.1]); the
difference opens at 1,000 items and more. Where both miss: `superseded` in Python and in TypeScript, a
new error type written with the domain the team moved away from, in about one chain of three in both
arms; the miss is an omission (the agent leaves a default in place), not a wrong value. Cost: the
CLAUDE.md arm reads its files whole on every step, so its cost grows with the knowledge base ($2.06 →
$3.89 in Python, $2.13 → $4.21 in Go, $2.08 → $4.08 in TypeScript from 500 to 2,000 items); Pathrule's
root file stays at 6k characters and the rest is delivered per prompt, so its cost stays flat ($1.70 →
$1.76, $1.91 → $1.89, $1.68 → $1.86).

Two probes `none` passes by construction: `stale` (a teammate moved a file; an agent with no knowledge
has nothing to be misled by) and `adjacent` (a rule for one package is not applied to another). They
measure not being misled, and the memory arms are the ones at risk.

Chains ran with Claude Code 2.1.301 and 2.1.302 (each chain's `meta.json` says which) and
claude-sonnet-5-5 on 2026-10-16/17. The `pathrule` chains ran the open-source CLI in local mode, built from the pathrule/pathrule source of 16 October 2026; each chain's `meta.json` records the authors' source commit of that day, `202a28db5`. The CLAUDE.md chains at Python 1,000 (five) and Go 1,000 (three) were
run earlier on 2026-10-16 on the same sealed fixture, checks and knowledge files; every other chain was
run for this publication (`results/<group>/PROVENANCE.md`).

Read `results/<group>/RESULTS.md` for each condition: passes by category, the paired difference with its
95% interval, cost and steps a chain, and every probe's pass rate. `results/<group>/chains/` holds each
chain's checks and session rows.

## Reproduce

```
git clone https://github.com/pathrule/pathrule && cd pathrule && pnpm install && cd ..
git clone https://github.com/pathrule/benchmark && cd benchmark
export ANTHROPIC_API_KEY=...            # Claude Code's key; a chain costs about $1.3 to $3.6
export PR_SRC=../pathrule               # the pathrule arm runs the CLI and MCP server from this checkout
PRB3_KNOWLEDGE=team-scale-1000.json node harness/run-chain.mjs python pathrule 1   # or go, typescript
python3 harness/collect.py runs python python-1000 1 pathrule
```

`harness/run-batch.py <jobs-file> <parallel>` runs a list of chains; `PROTOCOL.md` says what is fixed,
what each arm gets and how results are reported; `DESIGN.md` says why the benchmark has this shape;
`SEAL.txt` holds the SHA-256 of every file a run depends on. Claude Code 2.1, Python 3, Go 1.22+ and
Node 24 are what the published chains ran with; the TypeScript fixture needs Node 24 (it runs the `.ts`
files directly).

## What it does not measure

Chat recall over long conversations (LongMemEval and the like): this is a coding-agent benchmark where
knowledge arrives in a developer's prompts and is judged by what the code does afterwards. Cloud Pathrule,
embeddings and the Intelligence engine are not run; every published Pathrule chain is the local, open-source
path.

## License

Apache-2.0. The fixture projects, scenarios, checks and harness are original work written for this
benchmark.
