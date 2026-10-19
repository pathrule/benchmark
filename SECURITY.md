# Security policy

## Reporting a vulnerability

Please do **not** report security problems through public GitHub issues or pull requests. Email
**security@pathrule.io** instead, with:

- a description of the issue and its impact;
- the steps to reproduce it, with a minimal proof of concept if you can;
- the affected commit.

We acknowledge a report within three business days, keep you informed while we work on a fix and
credit you once it is released, unless you prefer to stay anonymous. Please give us a reasonable time
to release a fix before you disclose the issue publicly.

## Scope

This repository holds PathruleBench: the fixture projects, the scenarios, the hidden checks, the
harness and the published results. The harness runs Claude Code on your machine with your own API
key and sends nothing to Pathrule; the `pathrule` arm runs the open-source CLI in local mode.

Vulnerabilities in Pathrule itself belong to
[pathrule/pathrule](https://github.com/pathrule/pathrule/security/policy).

## Supported versions

Fixes target the `main` branch.
