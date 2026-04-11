import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "get-token.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("plaud_get_token", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_output_writes_token_file_without_echoing_secret(tmp_path, monkeypatch, capsys):
    module = load_script_module()
    encryption_path = tmp_path / "encryption.json"
    encryption_path.write_text('{"authToken":"encrypted-value"}', encoding="utf-8")
    output_path = tmp_path / "nested" / "plaud.token"

    monkeypatch.setattr(module, "ENCRYPTION_JSON", encryption_path)
    monkeypatch.setattr(module, "ensure_cryptography_installed", lambda: None)
    monkeypatch.setattr(module, "get_keychain_password", lambda: "pw")
    monkeypatch.setattr(module, "derive_key", lambda password: b"key")
    monkeypatch.setattr(module, "decrypt_token", lambda encrypted_b64, key: "secret-token")
    monkeypatch.setattr(module, "get_device_id", lambda: "device-123")

    module.main(["--output", str(output_path)])

    captured = capsys.readouterr().out
    assert output_path.read_text(encoding="utf-8") == "secret-token\n"
    assert "Token written to" in captured
    assert "PLAUD_DEVICE_ID=device-123" in captured
    assert "secret-token" not in captured


def test_default_mode_preserves_env_style_stdout(tmp_path, monkeypatch, capsys):
    module = load_script_module()
    encryption_path = tmp_path / "encryption.json"
    encryption_path.write_text('{"authToken":"encrypted-value"}', encoding="utf-8")

    monkeypatch.setattr(module, "ENCRYPTION_JSON", encryption_path)
    monkeypatch.setattr(module, "ensure_cryptography_installed", lambda: None)
    monkeypatch.setattr(module, "get_keychain_password", lambda: "pw")
    monkeypatch.setattr(module, "derive_key", lambda password: b"key")
    monkeypatch.setattr(module, "decrypt_token", lambda encrypted_b64, key: "plain-token")
    monkeypatch.setattr(module, "get_device_id", lambda: "device-123")

    module.main([])

    captured = capsys.readouterr().out
    assert "PLAUD_TOKEN=plain-token" in captured
    assert "PLAUD_DEVICE_ID=device-123" in captured
