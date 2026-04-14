# Release Checklist

Use this checklist before tagging or publishing a new `plaud-mcp` release.

## Repo surface

- README still matches the actual product, auth modes, and supported execution paths.
- `docs/OPERATIONS.md` still covers install, run, verify, and deploy flows.
- `pyproject.toml` metadata still matches the repository URLs and package intent.

## Tests and packaging

- Run `python -m pip install '.[dev]'`
- Run `pytest -q`
- Run `python -m build`

## Local runtime verification on macOS

- Run `bash scripts/container-runtime.sh docker config`
- Run `bash scripts/container-runtime.sh podman config`
- Run `bash scripts/verify-local-mac.sh docker`
- Run `bash scripts/verify-local-mac.sh podman`

## Final checks

- Confirm local verification is run sequentially because both runtime paths use port `8080`.
- Confirm no unexpected listener remains on `8080` after verification.
- Confirm Podman compose-provider behavior on macOS is still documented if it remains part of the local setup.
- Confirm no build artifacts such as `dist/` are left in the commit unless you explicitly intend to publish them.
