# Contributing

Thanks for considering a contribution. The benchmark is meant to be reproduced: a run that
disagrees with a published result is the most valuable report, with the commit, the agent and
model versions, the knowledge file and the raw chain output (`runs/<lang>/<arm>-t<n>/`).

## What changes where

- The fixtures, scenarios, hidden checks, oracle contexts and knowledge files are sealed
  (`SEAL.txt`): a change to any of them is a new benchmark version, with every published chain
  re-run or marked as run on the earlier seal. Say so in the pull request.
- The harness (`harness/`) and the aggregator can change freely as long as a published
  `results.json` aggregates to the same `RESULTS.md`.
- A new condition (a language, a knowledge size, an arm) comes with its own `results/<group>/`,
  `PROVENANCE.md` included.

## Reporting issues

- **Bugs and feature requests:** open a GitHub issue with repro steps (commit, OS, Node, Python and
  Go versions, Claude Code version, model).
- **Security issues:** please do not open a public issue. Email security@pathrule.io instead (see
  [SECURITY.md](SECURITY.md)).

## Sign-off and license

Every commit carries a [DCO](https://developercertificate.org) sign-off (`git commit -s`). By
contributing, you agree your contributions are licensed under [Apache-2.0](LICENSE).
