# Security policy

## Reporting a vulnerability

Please do **not** open a public GitHub issue for a security vulnerability.

Email **security@pathrule.io** with:

- a description of the issue and its impact;
- the steps to reproduce it, with a minimal proof of concept if you can;
- the affected version or commit.

We aim to acknowledge a report within 3 business days and to keep you updated as we investigate.
We credit reporters who wish to be named once a fix is released.

## Scope

This repository holds PathruleBench: the fixture projects, the scenarios, the hidden checks, the
harness and the published results. The harness runs Claude Code on your machine with your own
API key and sends nothing to Pathrule; the `pathrule` arm runs the open-source CLI in local mode.

## Supported versions

Fixes target the `main` branch.
