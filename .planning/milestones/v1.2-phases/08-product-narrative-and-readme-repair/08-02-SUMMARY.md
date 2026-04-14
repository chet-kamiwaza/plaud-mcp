---
phase: 08-product-narrative-and-readme-repair
plan: 02
subsystem: docs
tags: [readme, auth, transport, runtime]
requirements-completed: [DOCS-02]
completed: 2026-04-14
---

# Phase 8 Plan 02 Summary

## Outcome

Aligned the README's auth, transport, and runtime guidance with the actual code and validated scripts.

## What changed

- Documented the three supported auth sources in a recommended order.
- Kept Docker Desktop and Podman support visible without letting runtime setup dominate the entire document.
- Pointed local container usage at `scripts/container-runtime.sh` and local macOS validation at `scripts/verify-local-mac.sh`.

## Result

The top-level docs now describe the real code paths instead of a partial, Docker-first workflow.
