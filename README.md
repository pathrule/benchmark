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

Eight sessions of four turns on a small Python (or Go) toolkit. Knowledge enters only through the person's
prompts and the seeded items: a habit, team decisions, a changed decision, a lesson a failing command
teaches, a teammate's commit that makes an item stale. Probes in session 3 to 8 check, with executable
tests and structural checks, whether what was said earlier reached later work. No model judges anything.

## Results

RESULTS_TABLE

Read `results/<group>/RESULTS.md` for each condition: passes by category, the paired difference with its
95% interval, cost and steps a chain, and every probe's pass rate. `results/<group>/chains/` holds each
chain's checks and session rows.

## Reproduce

```
git clone https://github.com/pathrule/pathrule && cd pathrule && pnpm install && pnpm natives:node && cd ..
git clone https://github.com/pathrule/benchmark && cd benchmark
export ANTHROPIC_API_KEY=...            # Claude Code's key; a chain costs about $1.3 to $3.6
export PR_SRC=../pathrule               # the pathrule arm runs the CLI and MCP server from this checkout
PRB3_KNOWLEDGE=team-scale-1000.json node harness/run-chain.mjs python pathrule 1
python3 harness/collect.py runs python python-1000 1 pathrule
```

`harness/run-batch.py <jobs-file> <parallel>` runs a list of chains; `PROTOCOL.md` says what is fixed,
what each arm gets and how results are reported; `DESIGN.md` says why the benchmark has this shape;
`SEAL.txt` holds the SHA-256 of every file a run depends on. Claude Code 2.1 and Node 24 are what the
published chains ran with.

## What it does not measure

Chat recall over long conversations (LongMemEval and the like): this is a coding-agent benchmark where
knowledge arrives in a developer's prompts and is judged by what the code does afterwards. Cloud Pathrule,
embeddings and the Intelligence engine are not run; every published Pathrule chain is the local, open-source
path.

## License

Apache-2.0. The fixture projects, scenarios, checks and harness are original work written for this
benchmark.
