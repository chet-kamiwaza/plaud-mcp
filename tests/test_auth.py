"""Tests for the TokenManager and JWT utilities."""
from __future__ import annotations

import base64
import json
import time
from pathlib import Path

import httpx
import pytest
import respx

from plaud_mcp.auth import (
    TokenManager,
    decode_jwt_expiry,
    encrypt_uuid_hmac,
    generate_login_url,
    is_token_expiring,
)
from plaud_mcp.errors import PlaudAuthError


def _make_jwt(exp: int | None) -> str:
    """Build a fake unsigned JWT with the given ``exp`` claim."""
    header = base64.urlsafe_b64encode(b'{"alg":"none"}').rstrip(b"=").decode()
    payload_obj = {} if exp is None else {"exp": exp}
    payload = (
        base64.urlsafe_b64encode(json.dumps(payload_obj).encode())
        .rstrip(b"=")
        .decode()
    )
    return f"{header}.{payload}.signature"


# ---------- JWT decoding ----------

def test_decode_jwt_expiry_valid():
    token = _make_jwt(1234567890)
    assert decode_jwt_expiry(token) == 1234567890


def test_decode_jwt_expiry_missing_exp():
    token = _make_jwt(None)
    assert decode_jwt_expiry(token) is None


def test_decode_jwt_expiry_invalid_format():
    assert decode_jwt_expiry("not.a.jwt.at.all") is None
    assert decode_jwt_expiry("garbage") is None
    assert decode_jwt_expiry("") is None


# ---------- Expiry checking ----------

def test_is_token_expiring_fresh_token():
    # Token that expires in 100 days.
    token = _make_jwt(int(time.time()) + 100 * 86400)
    assert is_token_expiring(token, margin_days=30) is False


def test_is_token_expiring_within_margin():
    # Token that expires in 10 days.
    token = _make_jwt(int(time.time()) + 10 * 86400)
    assert is_token_expiring(token, margin_days=30) is True


def test_is_token_expiring_already_expired():
    token = _make_jwt(int(time.time()) - 100)
    assert is_token_expiring(token) is True


def test_is_token_expiring_undecodable():
    # Cannot decode -> treat as expiring (safe default).
    assert is_token_expiring("garbage") is True


# ---------- HMAC and login URL ----------

def test_encrypt_uuid_hmac_deterministic():
    uuid_val = "00000000-0000-0000-0000-000000000000"
    h1 = encrypt_uuid_hmac(uuid_val)
    h2 = encrypt_uuid_hmac(uuid_val)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_generate_login_url_contains_required_params():
    url = generate_login_url("test-uuid")
    assert url.startswith("https://web.plaud.ai/launch-desktop?")
    assert "from=desktop" in url
    assert "desktop_uuid=" in url
    assert "position=onboarding" in url


# ---------- login_with_password ----------

@pytest.mark.asyncio
@respx.mock
async def test_login_with_password_success(tmp_path: Path):
    new_token = _make_jwt(int(time.time()) + 300 * 86400)
    respx.post("https://api.plaud.ai/auth/access-token").mock(
        return_value=httpx.Response(
            200, json={"status": 0, "access_token": new_token}
        )
    )

    manager = TokenManager(
        token_file=str(tmp_path / "tok"),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
        email="user@example.com",
        password="secret",  # nosec B106 - test fixture
    )
    result = await manager.login_with_password()
    assert result == new_token


@pytest.mark.asyncio
@respx.mock
async def test_login_with_password_wrong_credentials(tmp_path: Path):
    respx.post("https://api.plaud.ai/auth/access-token").mock(
        return_value=httpx.Response(
            200, json={"status": -1, "msg": "wrong password"}
        )
    )

    manager = TokenManager(
        token_file=str(tmp_path / "tok"),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
        email="user@example.com",
        password="wrong",  # nosec B106 - test fixture
    )
    with pytest.raises(PlaudAuthError, match="wrong password"):
        await manager.login_with_password()


@pytest.mark.asyncio
async def test_login_with_password_no_credentials(tmp_path: Path):
    manager = TokenManager(
        token_file=str(tmp_path / "tok"),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
    )
    with pytest.raises(PlaudAuthError, match="not configured"):
        await manager.login_with_password()


# ---------- exchange_auth_code ----------

@pytest.mark.asyncio
@respx.mock
async def test_exchange_auth_code_success(tmp_path: Path):
    new_token = _make_jwt(int(time.time()) + 300 * 86400)
    route = respx.post("https://api.plaud.ai/auth/access-token-auth-code").mock(
        return_value=httpx.Response(
            200, json={"status": 0, "access_token": new_token}
        )
    )

    manager = TokenManager(
        token_file=str(tmp_path / "tok"),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
    )
    result = await manager.exchange_auth_code("auth_xyz", "test-uuid")
    assert result == new_token

    sent = json.loads(route.calls.last.request.content)
    assert sent["client_id"] == "desktop"
    assert sent["auth_code"] == "auth_xyz"
    assert sent["desktop_uuid"] == encrypt_uuid_hmac("test-uuid")


# ---------- ensure_valid_token ----------

@pytest.mark.asyncio
async def test_ensure_valid_token_returns_existing_fresh_token(tmp_path: Path):
    token_file = tmp_path / "tok"
    fresh = _make_jwt(int(time.time()) + 100 * 86400)
    token_file.write_text(fresh)

    manager = TokenManager(
        token_file=str(token_file),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
        email="u@e.com",
        password="pw",  # nosec B106 - test fixture
    )
    assert await manager.ensure_valid_token() == fresh


@pytest.mark.asyncio
@respx.mock
async def test_ensure_valid_token_refreshes_expiring_token(tmp_path: Path):
    token_file = tmp_path / "tok"
    expiring = _make_jwt(int(time.time()) + 5 * 86400)  # within margin
    token_file.write_text(expiring)

    new_token = _make_jwt(int(time.time()) + 300 * 86400)
    respx.post("https://api.plaud.ai/auth/access-token").mock(
        return_value=httpx.Response(
            200, json={"status": 0, "access_token": new_token}
        )
    )

    manager = TokenManager(
        token_file=str(token_file),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
        email="u@e.com",
        password="pw",  # nosec B106 - test fixture
    )
    result = await manager.ensure_valid_token()
    assert result == new_token
    # Token file is updated.
    assert token_file.read_text().strip() == new_token


@pytest.mark.asyncio
@respx.mock
async def test_ensure_valid_token_initial_login_when_no_file(tmp_path: Path):
    token_file = tmp_path / "subdir" / "tok"  # parent dir does not exist yet

    new_token = _make_jwt(int(time.time()) + 300 * 86400)
    respx.post("https://api.plaud.ai/auth/access-token").mock(
        return_value=httpx.Response(
            200, json={"status": 0, "access_token": new_token}
        )
    )

    manager = TokenManager(
        token_file=str(token_file),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
        email="u@e.com",
        password="pw",  # nosec B106 - test fixture
    )
    result = await manager.ensure_valid_token()
    assert result == new_token
    assert token_file.read_text().strip() == new_token


@pytest.mark.asyncio
async def test_ensure_valid_token_expired_no_credentials(tmp_path: Path):
    token_file = tmp_path / "tok"
    expired = _make_jwt(int(time.time()) - 100)
    token_file.write_text(expired)

    manager = TokenManager(
        token_file=str(token_file),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
    )
    with pytest.raises(PlaudAuthError, match="expired"):
        await manager.ensure_valid_token()


@pytest.mark.asyncio
async def test_ensure_valid_token_no_file_no_credentials(tmp_path: Path):
    manager = TokenManager(
        token_file=str(tmp_path / "missing"),
        base_url="https://api.plaud.ai",
        device_id="dev",
        app_version="5.3.9",
    )
    with pytest.raises(PlaudAuthError, match="No token file"):
        await manager.ensure_valid_token()
