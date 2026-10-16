# PathruleBench

A benchmark of memory for coding agents: does what a person told the agent in earlier sessions reach
the work of later sessions, at what cost, and does it ever do harm? Three arms, the same agent, the
same model, the same prompts:

| Arm | What persists between sessions |
| --- | --- |
| `none` | Nothing (`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`). |
| `claude_md` | The repository's CLAUDE.md files, as the agent leaves them, plus Claude Code's own auto memory. The team's knowledge is seeded into per-folder CLAUDE.md files the way Claude Code recommends. |
| `pathrule` | The Pathrule store. The same team knowledge is seeded as path-scoped memories at the same paths. |

Both memory arms are asked, in their own channel, to keep the knowledge current. Nothing in the code
points at either channel.

## Why this shape

Real-repository runs swing by trial, cost more and let one early deviation change everything after it.
So: every session starts from the scenario's fixed repository state, never from the agent's own previous
output, and a check in session 5 measures whether what was said in sessions 1 to 4 reached session 5 and
nothing else. The repositories are small, realistic, standard-library-only projects (no installs, no
caches; the TypeScript one runs on Node 24 without a build step). Three trials per arm, paired per probe, bootstrap intervals; no model judge, every check is
executable or structural.

## Scenario

8 sessions x 4 turns, one scenario, worded for each of three languages (Python, Go, TypeScript). Knowledge enters only through the person's
prompts (a habit, a team decision, a change of decision, a lesson a failing command teaches) and the
seeded team knowledge. Probes, by category:

| Category | What is measured | Example |
| --- | --- | --- |
| present | Seeded team knowledge applied | an app option is registered and documented the team's way |
| habit | A personal habit, stated once, applied in later sessions untold | a one-line docstring on every new test |
| decision | A team decision applied in later sessions untold | a new response header is registered in `ADDED_HEADERS` |
| superseded | A changed decision: the new one applied, the old one kept where it was | new error types use the new domain |
| adjacent | A rule for one package not applied to another | CLI errors stay plain text, never the problem format |
| abstention | Something the team has not decided is not invented | "use our standard per-route limits" when none exist |
| lesson | An operational fact a failing command taught | the team suite needs `ACME_TEAM_SUITE=1` |
| stale | Knowledge a teammate's commit made stale is noticed | the limits file moved |
| told | What the session's own prompts asked (harm control) | the feature's hidden tests pass |

## Validation before any product run

`oracle` (the knowledge each turn needs pasted under the prompt) must pass every probe; `none` must
fail every memory probe. A probe that fails this is removed. The scenario, the probes and the analysis
are sealed (SEAL.txt) before the product arms run, and no product change is made between trials.

## Cost and footprint

A chain (8 sessions × 4 turns) costs about $1.3 to $3.6 with claude-sonnet-5-5, the CLAUDE.md arm's cost
rising with the knowledge file; a chain leaves about 4 MB on disk (its transcripts and checks). Only
transcripts, checks and the memory state are kept; the worktree is deleted after each session.
