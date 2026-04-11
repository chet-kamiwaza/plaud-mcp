"""
Unit tests for PlaudClient — covers AUTH-01 through AUTH-04.

Uses respx to mock httpx requests so no live network calls are made.
"""
import os
from unittest.mock import patch

import pytest
import respx
import httpx

import plaud_mcp.client as client_module
from plaud_mcp.client import PlaudClient
from plaud_mcp.config import Settings
from plaud_mcp.errors import PlaudAuthError, PlaudAPIError


class TestAuth02Headers:
    """AUTH-02: All six required headers present on every request."""

    @respx.mock
    async def test_all_required_headers_sent(self):
        """Every GET request must include all six AUTH-02 headers."""
        route = respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200, json={"status": 0, "data": {"id": "user-123"}}
            )
        )

        async with PlaudClient() as client:
            await client.get("/user/current")

        request = route.calls[0].request
        headers = {k.lower(): v for k, v in request.headers.items()}

        assert "authorization" in headers, "Missing Authorization header"
        assert headers["authorization"].startswith("bearer "), (
            f"Authorization must start with 'bearer ' (lowercase), got: {headers['authorization']}"
        )
        assert "x-device-id" in headers, "Missing X-Device-Id header"
        assert "edit-from" in headers, "Missing edit-from header"
        assert "app-platform" in headers, "Missing app-platform header"
        assert "app-versionnumber" in headers, "Missing app-versionNumber header"
        assert "app-language" in headers, "Missing app-language header"


class TestAuth03Redirect:
    """AUTH-03: -302 redirect updates base URL and retries once."""

    @respx.mock
    async def test_redirect_updates_base_url_and_retries(self):
        """
        First call returns -302 with new domain.
        Client must update base_url and retry — second call returns success.
        """
        first = respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": -302,
                    "data": {"domains": {"api": "api-eu.plaud.ai"}},
                },
            )
        )
        second = respx.get("https://api-eu.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200, json={"status": 0, "data": {"id": "user-123"}}
            )
        )

        async with PlaudClient() as client:
            result = await client.get("/user/current")

        assert result == {"status": 0, "data": {"id": "user-123"}}
        assert first.called, "Initial request to api.plaud.ai was not made"
        assert second.called, "Retry to api-eu.plaud.ai was not made"

    @respx.mock
    async def test_redirect_loop_guard(self):
        """
        If the retry also returns -302, raise PlaudAPIError (not infinite recursion).
        """
        respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": -302,
                    "data": {"domains": {"api": "api-eu.plaud.ai"}},
                },
            )
        )
        respx.get("https://api-eu.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": -302,
                    "data": {"domains": {"api": "api-us.plaud.ai"}},
                },
            )
        )

        async with PlaudClient() as client:
            with pytest.raises(PlaudAPIError, match="[Rr]edirect"):
                await client.get("/user/current")

    @respx.mock
    async def test_redirect_rejects_non_plaud_domain(self):
        """
        Redirect to a non-plaud.ai domain must be rejected (T-01-02 threat mitigation).
        """
        respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200,
                json={
                    "status": -302,
                    "data": {"domains": {"api": "evil-attacker.com"}},
                },
            )
        )

        async with PlaudClient() as client:
            with pytest.raises(PlaudAPIError, match="[Rr]eject|[Nn]on-[Pp]laud"):
                await client.get("/user/current")


class TestAuth04AuthError:
    """AUTH-04: -10000 status raises PlaudAuthError."""

    @respx.mock
    async def test_auth_error_raises_plaud_auth_error(self):
        """status=-10000 must raise PlaudAuthError."""
        respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200, json={"status": -10000, "msg": "token expired"}
            )
        )

        async with PlaudClient() as client:
            with pytest.raises(PlaudAuthError) as exc_info:
                await client.get("/user/current")

        message = str(exc_info.value).lower()
        assert "invalid" in message or "expired" in message, (
            f"Error message should contain 'invalid' or 'expired', got: {message}"
        )


class TestSuccessPath:
    """status=0 returns data dict without raising."""

    @respx.mock
    async def test_success_returns_full_response(self):
        """status=0 must return the full parsed response dict."""
        respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200, json={"status": 0, "data": {"id": "user-123"}}
            )
        )

        async with PlaudClient() as client:
            result = await client.get("/user/current")

        assert result == {"status": 0, "data": {"id": "user-123"}}


class TestUnknownError:
    """Non-zero, non-(-10000) status raises PlaudAPIError."""

    @respx.mock
    async def test_unknown_status_raises_plaud_api_error(self):
        """status=-500 (unknown) must raise PlaudAPIError."""
        respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200, json={"status": -500, "msg": "internal error"}
            )
        )

        async with PlaudClient() as client:
            with pytest.raises(PlaudAPIError):
                await client.get("/user/current")


class TestTokenSourceSettings:
    def test_accepts_token_file_without_plaud_token(self, tmp_path):
        token_path = tmp_path / "plaud.token"
        token_path.write_text("file-token\n", encoding="utf-8")

        settings = Settings(
            _env_file=None,
            plaud_token_file=str(token_path),
            plaud_device_id="device-123",
        )

        assert settings.get_token() == "file-token"

    def test_requires_some_token_source(self):
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="PLAUD_TOKEN|PLAUD_TOKEN_FILE"):
                Settings(_env_file=None, plaud_device_id="device-123")


class TestTokenFileReload:
    @respx.mock
    async def test_token_file_used_when_configured(self, tmp_path):
        token_path = tmp_path / "plaud.token"
        token_path.write_text("file-token\n", encoding="utf-8")

        route = respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200, json={"status": 0, "data": {"id": "user-123"}}
            )
        )

        with patch.object(client_module.settings, "plaud_token_file", str(token_path)), patch.object(
            client_module.settings, "plaud_token", None
        ):
            async with PlaudClient() as client:
                await client.get("/user/current")

        assert route.calls[0].request.headers["Authorization"] == "bearer file-token"

    @respx.mock
    async def test_reloads_changed_token_before_next_request(self, tmp_path):
        token_path = tmp_path / "plaud.token"
        token_path.write_text("first-token\n", encoding="utf-8")

        route = respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(
                200, json={"status": 0, "data": {"id": "user-123"}}
            )
        )

        with patch.object(client_module.settings, "plaud_token_file", str(token_path)), patch.object(
            client_module.settings, "plaud_token", None
        ):
            async with PlaudClient() as client:
                await client.get("/user/current")
                token_path.write_text("second-token\n", encoding="utf-8")
                await client.get("/user/current")

        assert route.calls[0].request.headers["Authorization"] == "bearer first-token"
        assert route.calls[1].request.headers["Authorization"] == "bearer second-token"

    @respx.mock
    async def test_auth_error_reload_retries_once_with_updated_token(self, tmp_path):
        token_path = tmp_path / "plaud.token"
        token_path.write_text("expired-token\n", encoding="utf-8")
        calls = []

        def handler(request):
            calls.append(request.headers["Authorization"])
            if len(calls) == 1:
                token_path.write_text("fresh-token\n", encoding="utf-8")
                return httpx.Response(200, json={"status": -10000, "msg": "expired"})
            return httpx.Response(200, json={"status": 0, "data": {"id": "user-123"}})

        respx.get("https://api.plaud.ai/user/current").mock(side_effect=handler)

        with patch.object(client_module.settings, "plaud_token_file", str(token_path)), patch.object(
            client_module.settings, "plaud_token", None
        ):
            async with PlaudClient() as client:
                result = await client.get("/user/current")

        assert result == {"status": 0, "data": {"id": "user-123"}}
        assert calls == ["bearer expired-token", "bearer fresh-token"]

    @respx.mock
    async def test_second_auth_error_still_raises_after_single_retry(self, tmp_path):
        token_path = tmp_path / "plaud.token"
        token_path.write_text("expired-token\n", encoding="utf-8")
        calls = []

        def handler(request):
            calls.append(request.headers["Authorization"])
            if len(calls) == 1:
                token_path.write_text("still-bad-token\n", encoding="utf-8")
            return httpx.Response(200, json={"status": -10000, "msg": "expired"})

        respx.get("https://api.plaud.ai/user/current").mock(side_effect=handler)

        with patch.object(client_module.settings, "plaud_token_file", str(token_path)), patch.object(
            client_module.settings, "plaud_token", None
        ):
            async with PlaudClient() as client:
                with pytest.raises(PlaudAuthError, match="expired"):
                    await client.get("/user/current")

        assert calls == ["bearer expired-token", "bearer still-bad-token"]

    @respx.mock
    async def test_non_auth_error_does_not_retry(self, tmp_path):
        token_path = tmp_path / "plaud.token"
        token_path.write_text("file-token\n", encoding="utf-8")
        route = respx.get("https://api.plaud.ai/user/current").mock(
            return_value=httpx.Response(200, json={"status": -500, "msg": "boom"})
        )

        with patch.object(client_module.settings, "plaud_token_file", str(token_path)), patch.object(
            client_module.settings, "plaud_token", None
        ):
            async with PlaudClient() as client:
                with pytest.raises(PlaudAPIError):
                    await client.get("/user/current")

        assert route.call_count == 1

    @respx.mock
    async def test_empty_token_file_raises_clear_auth_error(self, tmp_path):
        token_path = tmp_path / "plaud.token"
        token_path.write_text("\n", encoding="utf-8")

        with patch.object(client_module.settings, "plaud_token_file", str(token_path)), patch.object(
            client_module.settings, "plaud_token", None
        ):
            async with PlaudClient() as client:
                with pytest.raises(PlaudAuthError, match="empty"):
                    await client.get("/user/current")
