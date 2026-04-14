from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_local_mac_validation_script_enforces_runtime_selection() -> None:
    content = _read("scripts/verify-local-mac.sh")

    assert "Usage: bash scripts/verify-local-mac.sh <podman|docker|all>" in content
    assert "case \"$selection\" in" in content
    assert "podman)" in content
    assert "docker)" in content
    assert "all)" in content


def test_local_mac_validation_script_is_darwin_only() -> None:
    content = _read("scripts/verify-local-mac.sh")

    assert 'uname -s' in content
    assert '!= "Darwin"' in content
    assert "This validation flow is for macOS only." in content


def test_local_mac_validation_script_checks_runtime_readiness() -> None:
    content = _read("scripts/verify-local-mac.sh")

    assert 'podman machine list --format json' in content
    assert 'podman info >/dev/null 2>&1' in content
    assert 'docker info >/dev/null 2>&1' in content
    assert "podman machine start" in content
    assert "Docker Desktop" in content


def test_local_mac_validation_script_reuses_runtime_verification_and_pytest() -> None:
    content = _read("scripts/verify-local-mac.sh")

    assert 'bash "$RUNTIME_VERIFY" "$runtime"' in content
    assert 'pytest -q' in content
    assert 'set -eu' in content
