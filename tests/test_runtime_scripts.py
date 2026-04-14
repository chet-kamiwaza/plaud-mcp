from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def test_container_runtime_script_supports_docker_and_podman() -> None:
    content = _read("scripts/container-runtime.sh")

    assert 'docker|podman' in content
    assert 'docker compose' in content
    assert 'podman compose' in content
    assert 'build|up|down|logs|ps|config' in content
    assert 'brew install podman' in content


def test_verify_script_uses_helper_and_cleanup_trap() -> None:
    content = _read("scripts/verify-container-runtime.sh")

    assert 'trap cleanup EXIT INT TERM' in content
    assert 'bash "$HELPER" "$runtime" build' in content
    assert 'bash "$HELPER" "$runtime" up' in content
    assert 'bash "$HELPER" "$runtime" down' in content
    assert "127.0.0.1:8080:8080" in content
    assert "lsof -nP -iTCP:8080 -sTCP:LISTEN" in content


def test_compose_file_is_loopback_only() -> None:
    content = _read("docker-compose.yml")

    assert '127.0.0.1:8080:8080' in content
    assert '/app/data' in content
    assert 'MCP_TRANSPORT=http' in content


def test_env_example_keeps_runtime_neutral_auth_contract() -> None:
    content = _read(".env.example")

    assert 'PLAUD_TOKEN_FILE=/app/data/plaud.token' in content
    assert 'PLAUD_DEVICE_ID=your_device_uuid_here' in content
    assert 'bash scripts/container-runtime.sh docker up' in content
    assert 'bash scripts/container-runtime.sh podman up' in content
