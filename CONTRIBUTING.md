# Contributing to PathruleBench

Thank you for your interest in PathruleBench. The benchmark exists to be reproduced and challenged,
so the most valuable contribution is a run of your own, above all one that disagrees with a
published result.

By taking part, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Report a reproduction.** Run a chain and open a
  [reproduction report](https://github.com/pathrule/benchmark/issues/new?template=reproduction.yml)
  with the commit, the agent and model versions, the knowledge file and the raw chain output
  (`runs/<lang>/<arm>-t<n>/`). Reports that match the published results are welcome too.
- **Report a harness bug.** Something in `harness/` that crashes, miscounts or aggregates
  differently from the published `RESULTS.md`: open a
  [bug report](https://github.com/pathrule/benchmark/issues/new?template=bug_report.yml).
- **Propose a new condition.** A language, a knowledge size or another memory arm. Open an issue
  first so the protocol can be agreed before any paid run.
- **Improve the documentation.** Fixes to the READMEs and to the comments in the harness.

## What can change, and how

- **Sealed files.** The fixtures, scenarios, hidden checks, oracle contexts and knowledge files are
  fingerprinted in [`SEAL.txt`](SEAL.txt), together with `PROTOCOL.md` and `DESIGN.md`. A change to
  any of them is a new benchmark version: every published chain is re-run or marked as run on the
  earlier seal. Say so in the pull request.
- **The harness.** `harness/` can change freely, as long as every published `results.json` still
  aggregates to the same `RESULTS.md`.
- **New conditions.** A new language, knowledge size or arm comes with its own `results/<group>/`,
  including a `PROVENANCE.md` that says what was run, when and against which Pathrule commit.

## Running a chain

See [Run it yourself](README.md#run-it) in the README. You need Claude Code 2.1, Node.js 24, Python 3,
Go 1.22 or newer and your own `ANTHROPIC_API_KEY`. A chain costs about $1.2 to $4.4.

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Keep the pull request focused on one change, and fill in the template.
3. Sign off every commit (see below).

## Developer Certificate of Origin

We use the [Developer Certificate of Origin](https://developercertificate.org/) (DCO) instead of a
contributor licence agreement. Sign off every commit to certify that you have the right to submit it:

```bash
git commit -s -m "harness: ..."
```

If you forgot, sign off the commits already on your branch with `git rebase --signoff main` and push
again.

## Reporting security issues

Please do not open a public issue for a security problem. See [SECURITY.md](SECURITY.md).

## License

By contributing, you agree that your contributions are licensed under the
[Apache License 2.0](LICENSE).
