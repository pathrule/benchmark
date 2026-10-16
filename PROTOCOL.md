# Protocol

## What is fixed before any product run

- The scenarios (`<lang>/sessions.json`), the seeded team knowledge (`<lang>/knowledge/team.json` and the
  scale files its generator writes), the teammate overlays, the hidden checks (`<lang>/checks/run.py`) and
  the oracle contexts (`<lang>/oracle.json`). `SEAL.txt` records their SHA-256.
- The analysis (`harness/aggregate.py`): the headline is the 26 memory probes (habit, decision, superseded,
  adjacent, abstention, lesson, stale), paired per probe between arms, with bootstrap 95% intervals over
  probes. `present` (8 seeded-knowledge probes) and `told` (19 probes of what the session's own prompts
  asked, the harm control) are reported beside it.
- Validation: `oracle` (the needed knowledge pasted under each prompt) passes every probe and `none` fails
  every memory probe, else the probe is removed before sealing.

## Arms, identically

- Claude Code 2.1.x, `claude-sonnet-5-5`, `--permission-mode dontAsk`, the same allowed tools (plus
  Pathrule's MCP tools in its arm), `--max-budget-usd 3` a turn.
- Every session is a new Claude Code session that starts from the scenario's repository state for that
  session (the fixture plus the teammate overlays due by then), never from the agent's own previous output.
  Turns inside a session resume it; `/compact` is sent as a turn. Only memory carries between sessions.
- `none`: nothing carries (`CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`).
- `claude_md`: the seeded knowledge rendered into per-folder CLAUDE.md files the way Claude Code
  recommends (`harness/render-claude-md.py`), the root file asking the agent to keep them current; the
  CLAUDE.md files the agent leaves are carried to the next session; Claude's auto memory stays on.
- `pathrule`: the same items as path-scoped memories at the same paths in a local Pathrule store
  (`pathrule setup --local`, `sync --local`), typed as the product types an untyped save; the store is
  carried. Local edition, no Cloud, no embedding key, no Intelligence engine: what a person gets from
  the open-source CLI.
- Hidden checks run in the session's worktree after its last turn; the agent never sees them.

## Conditions

`PRB3_KNOWLEDGE` selects the knowledge file both memory arms receive: `team-scale-500.json`,
`team-scale-1000.json`, `team-scale-2000.json`. Each is `team.json` (the 20 items the probes need) plus
decision-log entries a platform team accumulates, written deterministically by `knowledge/gen-scale.py`
(`480`, `980`, `1980`); the extra entries are coherent for the fixture project and none answers a probe.
The same 20 items are in every condition, so the conditions differ only in how much else the channel
carries.

## Reported

Per condition: memory, present and told passes with trial ranges; probes by category; the paired
difference pathrule minus claude_md with its interval; cost (USD, from Claude Code's own `total_cost_usd`,
which includes cache writes) and model steps a chain; every probe's pass rate per arm. Incomplete chains
are listed, never dropped. The per-chain checks and session rows are in `results/<group>/chains/`;
transcripts are not published (they hold the model's full output) but are kept by the authors.

## Provenance of the published chains

Every chain's `meta.json` names the Pathrule commit it ran against and the knowledge file. The
`claude_md` and `none` arms do not depend on a Pathrule build; the published ones were run on the same
sealed fixture, checks and knowledge files as the `pathrule` chains. Where a group reuses chains run
earlier in the same day's work, its RESULTS.md says so.
