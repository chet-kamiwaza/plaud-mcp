from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_has_release_metadata():
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]

    assert project["description"].startswith("Self-hosted MCP server for browsing Plaud")
    assert project["readme"] == "README.md"
    assert "classifiers" in project
    assert "keywords" in project
    assert project["urls"]["Repository"] == "https://github.com/chet-kamiwaza/plaud-mcp"


def test_dev_dependencies_include_build():
    data = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev_dependencies = data["project"]["optional-dependencies"]["dev"]
    assert any(dep.startswith("build>=") for dep in dev_dependencies)


def test_readme_links_operations_guide():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert "[docs/OPERATIONS.md](docs/OPERATIONS.md)" in readme


def test_operations_guide_covers_public_release_flows():
    operations = (REPO_ROOT / "docs" / "OPERATIONS.md").read_text(encoding="utf-8")

    assert "## Local Python over stdio" in operations
    assert "## Local HTTP on macOS" in operations
    assert "## Local verification" in operations
    assert "## Kubernetes deployment" in operations
    assert "python -m build" in operations
