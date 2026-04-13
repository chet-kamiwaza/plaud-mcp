"""
TokenManager — automated token lifecycle for the Plaud MCP server.

Supports two authentication strategies:
  1. Email/password login via POST /auth/access-token (fully automatic refresh)
  2. Auth code exchange via POST /auth/access-token-auth-code (browser-based SSO)

JWT expiry is decoded from the token payload using stdlib only (no PyJWT).
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import urlencode

import httpx

from .errors import PlaudAuthError

logger = logging.getLogger(__name__)

HMAC_SALT = "PLAUD-D_E_S_K_T_O_P"

# Standard headers that Plaud expects on auth requests.
_PLAUD_AUTH_HEADERS = {
    "edit-from": "desktop",
    "app-platform": "desktop",
    "app-language": "en",
    "Accept": "application/json, text/plain, */*",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Electron/29.0.0 Safari/537.36"
    ),
}


def decode_jwt_expiry(token: str) -> int | None:
    """Decode the ``exp`` claim from a JWT without signature verification.

    Returns the expiry as a Unix timestamp, or *None* if the token cannot be
    parsed or has no ``exp`` claim.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        # JWT payloads use base64url encoding without padding.
        payload_b64 = parts[1]
        # Add padding if needed.
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        exp = payload.get("exp")
        return int(exp) if exp is not None else None
    except Exception:
        return None


def is_token_expiring(token: str, margin_days: int = 30) -> bool:
    """Return *True* if *token* expires within *margin_days* or is already expired."""
    exp = decode_jwt_expiry(token)
    if exp is None:
        # Cannot determine expiry — treat as expiring to be safe.
        return True
    return time.time() + (margin_days * 86400) >= exp


def encrypt_uuid_hmac(device_uuid: str) -> str:
    """Compute the HMAC-SHA256 ``desktop_uuid`` used in Plaud web login URLs."""
    return hmac.new(
        HMAC_SALT.encode(),
        device_uuid.encode(),
        hashlib.sha256,
    ).hexdigest()


def generate_login_url(device_uuid: str) -> str:
    """Build the ``web.plaud.ai`` login URL that redirects back with an auth code."""
    encrypted = encrypt_uuid_hmac(device_uuid)
    params = urlencode({
        "from": "desktop",
        "desktop_uuid": encrypted,
        "position": "onboarding",
    })
    return f"https://web.plaud.ai/launch-desktop?{params}"


class TokenManager:
    """Manages the Plaud bearer token lifecycle.

    When *email* and *password* are provided, the manager can fully automate
    token refresh by calling the email/password login endpoint.  When only a
    token file is available (e.g. obtained via ``scripts/setup-auth.py``), the
    manager monitors expiry and logs warnings but cannot auto-refresh.
    """

    def __init__(
        self,
        *,
        token_file: str,
        base_url: str,
        device_id: str,
        app_version: str,
        email: str | None = None,
        password: str | None = None,
    ) -> None:
        self._token_file = Path(token_file)
        self._base_url = base_url
        self._device_id = device_id
        self._app_version = app_version
        self._email = email
        self._password = password

    def _read_token(self) -> str | None:
        """Read the current token from the file, or return *None*."""
        try:
            token = self._token_file.read_text(encoding="utf-8").strip()
            return token if token else None
        except OSError:
            return None

    def _write_token(self, token: str) -> None:
        """Persist *token* to the token file with restricted permissions."""
        self._token_file.parent.mkdir(parents=True, exist_ok=True)
        self._token_file.write_text(token + "\n", encoding="utf-8")
        try:
            os.chmod(self._token_file, 0o600)
        except OSError:
            pass  # Best-effort on platforms that don't support chmod.

    def _auth_headers(self) -> dict[str, str]:
        """Return headers required for Plaud auth endpoints."""
        headers = dict(_PLAUD_AUTH_HEADERS)
        headers["app-versionNumber"] = self._app_version
        headers["X-Device-Id"] = self._device_id
        return headers

    async def login_with_password(self) -> str:
        """Authenticate via email/password and return the new access token.

        Raises :class:`PlaudAuthError` on failure.
        """
        if not self._email or not self._password:
            raise PlaudAuthError(
                "Cannot auto-refresh: PLAUD_EMAIL and PLAUD_PASSWORD are not configured"
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/auth/access-token",
                data={"username": self._email, "password": self._password},
                headers=self._auth_headers(),
            )
            resp.raise_for_status()
            body = resp.json()

        status = body.get("status")
        if status != 0:
            msg = body.get("msg", "unknown error")
            raise PlaudAuthError(f"Login failed (status {status}): {msg}")

        token = body.get("access_token")
        if not token:
            raise PlaudAuthError("Login response missing access_token")

        logger.info(  # nosec B105 - logs expiry only, not token value
            "Token refreshed via password login (expires: %s)",
            _format_expiry(token),
        )
        return token

    async def exchange_auth_code(
        self, auth_code: str, device_uuid: str,
    ) -> str:
        """Exchange a browser auth code for an access token.

        This is used by ``scripts/setup-auth.py`` for SSO users.
        """
        encrypted = encrypt_uuid_hmac(device_uuid)

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/auth/access-token-auth-code",
                json={
                    "client_id": "desktop",
                    "auth_code": auth_code,
                    "desktop_uuid": encrypted,
                },
                headers=self._auth_headers(),
            )
            resp.raise_for_status()
            body = resp.json()

        status = body.get("status")
        if status != 0:
            msg = body.get("msg", "unknown error")
            raise PlaudAuthError(
                f"Auth code exchange failed (status {status}): {msg}"
            )

        token = body.get("access_token")
        if not token:
            raise PlaudAuthError("Auth code response missing access_token")

        logger.info(  # nosec B105 - logs expiry only, not token value
            "Token obtained via auth code exchange (expires: %s)",
            _format_expiry(token),
        )
        return token

    async def ensure_valid_token(self) -> str:
        """Return a valid token, refreshing via password login if needed.

        If the current token is missing or expiring and credentials are
        configured, performs an automatic login and writes the new token to the
        file.  If credentials are not configured, returns the existing token
        (or raises if none exists).
        """
        token = self._read_token()

        if token and not is_token_expiring(token):
            return token

        # Token is missing, expired, or expiring soon.
        if self._email and self._password:
            if token:
                logger.info("Token expiring soon — refreshing via password login")
            else:
                logger.info("No token found — performing initial password login")

            new_token = await self.login_with_password()
            self._write_token(new_token)
            return new_token

        # No credentials for auto-refresh.
        if token:
            exp = decode_jwt_expiry(token)
            if exp is not None and time.time() >= exp:
                raise PlaudAuthError(
                    "Token has expired and no credentials are configured for "
                    "auto-refresh. Run scripts/setup-auth.py to obtain a new token."
                )
            # Token is expiring soon but not yet expired — warn and return it.
            logger.warning(
                "Token expires in <30 days but auto-refresh is not configured. "
                "Run scripts/setup-auth.py to obtain a new token."
            )
            return token

        raise PlaudAuthError(
            "No token file found and no credentials configured. "
            "Set PLAUD_EMAIL/PLAUD_PASSWORD for auto-refresh, or run "
            "scripts/setup-auth.py for SSO-based authentication."
        )


def _format_expiry(token: str) -> str:
    """Format a JWT's expiry as an ISO 8601 date string (UTC)."""
    exp = decode_jwt_expiry(token)
    if exp is None:
        return "unknown"
    return (
        datetime.datetime.fromtimestamp(exp, tz=datetime.timezone.utc)
        .date()
        .isoformat()
    )
