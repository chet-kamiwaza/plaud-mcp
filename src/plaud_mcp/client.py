"""
PlaudClient — authenticated async HTTP client for the Plaud cloud API.

Satisfies:
  AUTH-02: All six required headers sent on every request.
  AUTH-03: -302 domain redirect updates base_url and retries once.
  AUTH-04: -10000 auth failure raises PlaudAuthError.

Security:
  T-01-02: Redirect domain validated against *.plaud.ai before base_url mutation.
  T-01-03: _redirect_attempted flag prevents infinite redirect loops.
  T-01-05: 30-second timeout on all requests prevents hung connections.
  T-01-01: Token value never logged (only last 4 chars safe to log).
"""
from __future__ import annotations

import httpx

from .auth import TokenManager
from .config import settings
from .errors import PlaudAPIError, PlaudAuthError


class PlaudClient:
    """Async HTTP client for the Plaud cloud API with full AUTH-02 header set."""

    def __init__(self) -> None:
        self._redirect_attempted = False
        self._auth_retry_attempted = False
        self._token_manager: TokenManager | None = None
        if settings.plaud_auto_refresh:
            self._token_manager = TokenManager(
                token_file=settings.plaud_token_file,
                base_url=settings.plaud_base_url,
                device_id=settings.plaud_device_id,
                app_version=settings.plaud_app_version,
                email=settings.plaud_email,
                password=settings.plaud_password,
            )
        self._client = httpx.AsyncClient(
            base_url=settings.plaud_base_url,
            follow_redirects=False,
            timeout=httpx.Timeout(30.0),
            headers={
                "edit-from": "desktop",
                "app-platform": "desktop",
                "app-versionNumber": settings.plaud_app_version,
                "app-language": "en",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Electron/29.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://web.plaud.ai",
                "Referer": "https://web.plaud.ai/",
            },
        )

    async def _refresh_auth_headers(self) -> None:
        if self._token_manager is not None:
            token = await self._token_manager.ensure_valid_token()
        else:
            token = settings.get_token()
        self._client.headers["Authorization"] = f"bearer {token}"
        self._client.headers["X-Device-Id"] = settings.plaud_device_id

    async def _force_relogin(self) -> None:
        """Force a fresh password login (used when the API rejects the token)."""
        if self._token_manager is None:
            raise PlaudAuthError(
                "Token rejected by Plaud API and auto-refresh is not configured"
            )
        new_token = await self._token_manager.login_with_password()
        self._token_manager._write_token(new_token)
        self._client.headers["Authorization"] = f"bearer {new_token}"
        self._client.headers["X-Device-Id"] = settings.plaud_device_id

    async def __aenter__(self) -> "PlaudClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        """
        Core request method. Handles Plaud application-level response codes:
          0       -> return parsed response dict
          -302    -> update base_url to redirected domain and retry once
          -10000  -> raise PlaudAuthError (token invalid or expired)
          other   -> raise PlaudAPIError
        """
        try:
            await self._refresh_auth_headers()
        except RuntimeError as exc:
            raise PlaudAuthError(
                f"Plaud token configuration is invalid: {exc}"
            ) from exc

        response = await self._client.request(method, path, **kwargs)
        response.raise_for_status()
        body = response.json()

        status = body.get("status")

        if status == 0:
            return body

        if status == -302:
            if self._redirect_attempted:
                raise PlaudAPIError(
                    "Redirect loop: received -302 on retry request"
                )

            new_domain = (
                body.get("data", {}).get("domains", {}).get("api")
            )
            if new_domain is None:
                raise PlaudAPIError(
                    "Received -302 redirect but no domain in response body"
                )

            # T-01-02: Reject redirects to non-Plaud domains
            if not new_domain.endswith("plaud.ai"):
                raise PlaudAPIError(
                    f"Reject redirect to non-Plaud domain: {new_domain}"
                )

            self._redirect_attempted = True
            self._client.base_url = httpx.URL(f"https://{new_domain}")

            try:
                result = await self._request(method, path, **kwargs)
            finally:
                self._redirect_attempted = False

            return result

        if status == -10000:
            # Auto-refresh mode: force a fresh login and retry once.
            if self._token_manager is not None:
                if self._auth_retry_attempted:
                    msg = body.get("msg", "")
                    raise PlaudAuthError(
                        f"Plaud token still invalid after re-login: {msg}"
                    )

                try:
                    await self._force_relogin()
                except PlaudAuthError:
                    raise
                except Exception as exc:
                    raise PlaudAuthError(
                        f"Re-login failed: {exc}"
                    ) from exc

                self._auth_retry_attempted = True
                try:
                    return await self._request(method, path, **kwargs)
                finally:
                    self._auth_retry_attempted = False

            # File-based token: re-read the file and retry once.
            if settings.plaud_token_file:
                if self._auth_retry_attempted:
                    msg = body.get("msg", "")
                    raise PlaudAuthError(
                        f"Plaud token is invalid or expired after reload retry: {msg}"
                    )

                try:
                    await self._refresh_auth_headers()
                except RuntimeError as exc:
                    raise PlaudAuthError(
                        f"Plaud token reload failed: {exc}"
                    ) from exc

                self._auth_retry_attempted = True
                try:
                    return await self._request(method, path, **kwargs)
                finally:
                    self._auth_retry_attempted = False

            msg = body.get("msg", "")
            raise PlaudAuthError(
                f"Plaud token is invalid or expired: {msg}"
            )

        msg = body.get("msg", "")
        raise PlaudAPIError(
            f"Plaud API returned non-zero status {status}: {msg}"
        )

    async def get(self, path: str, **kwargs) -> dict:
        """Perform a GET request against the Plaud API."""
        return await self._request("GET", path, **kwargs)

    async def get_all_files(
        self, page_size: int = 200, max_pages: int = 100,
    ) -> list[dict]:
        """Paginate through /file/simple/web and return all recordings.

        The Plaud API's ``data_file_total`` field reflects the page size, not
        the account total, so the only way to get a complete list is to paginate
        until a partial page is returned.

        Args:
            page_size: Number of files per request (max 200).
            max_pages: Safety limit on number of pages to fetch (default 100,
                       i.e. up to 20,000 files).

        Returns:
            A list of every file dict in the account, newest first.
        """
        page_size = min(page_size, 200)
        all_files: list[dict] = []
        skip = 0
        for _ in range(max_pages):
            resp = await self.get(
                "/file/simple/web",
                params={
                    "skip": skip,
                    "limit": page_size,
                    "is_trash": 2,
                    "sort_by": "start_time",
                    "is_desc": "true",
                },
            )
            batch = resp.get("data_file_list", [])
            all_files.extend(batch)
            if len(batch) < page_size:
                break
            skip += page_size
        return all_files

    async def aclose(self) -> None:
        """Close the underlying httpx.AsyncClient."""
        await self._client.aclose()
