#!/usr/bin/env python3
"""
Interactive browser-based authentication for the Plaud MCP server.

Use this for accounts that sign in with Google/Apple SSO (which cannot use the
email/password login endpoint). The flow:

  1. We compute the HMAC'd device UUID and open the Plaud web login URL.
  2. You sign in via your normal SSO method on web.plaud.ai.
  3. The browser redirects to a `plaud://?auth_code=...` URL — copy that URL
     from the address bar (or from the "open external app" dialog).
  4. Paste it back here. We exchange the auth code for a long-lived token
     (~10 months) and write it to the configured token file.

Run again whenever the token expires (the script prints the expiry date).
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Make the package importable when running from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plaud_mcp.auth import (  # noqa: E402
    TokenManager,
    decode_jwt_expiry,
    generate_login_url,
)


def _parse_auth_code(redirect_url: str) -> str:
    """Extract the ``auth_code`` query param from a ``plaud://`` redirect URL."""
    parsed = urlparse(redirect_url.strip())
    query = parse_qs(parsed.query)
    code = query.get("auth_code", [None])[0]
    if not code:
        raise SystemExit(
            "Could not find auth_code in the URL. Make sure you pasted the "
            "full plaud://?auth_code=... URL from your browser."
        )
    return code


async def _exchange(
    auth_code: str,
    device_uuid: str,
    base_url: str,
    token_file: str,
) -> str:
    manager = TokenManager(
        token_file=token_file,
        base_url=base_url,
        device_id=device_uuid,
        app_version="5.3.9",
    )
    token = await manager.exchange_auth_code(auth_code, device_uuid)
    manager._write_token(token)
    return token


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device-uuid",
        default=os.environ.get("PLAUD_DEVICE_ID"),
        help="Device UUID (defaults to PLAUD_DEVICE_ID env var; generated if absent)",
    )
    parser.add_argument(
        "--token-file",
        default=os.environ.get("PLAUD_TOKEN_FILE", "./data/plaud.token"),
        help="Where to write the token (defaults to PLAUD_TOKEN_FILE or ./data/plaud.token)",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("PLAUD_BASE_URL", "https://api.plaud.ai"),
        help="Plaud API base URL",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Just print the login URL instead of opening a browser",
    )
    args = parser.parse_args()

    device_uuid = args.device_uuid or str(uuid.uuid4()).upper()
    if not args.device_uuid:
        print(f"No device UUID provided — generated: {device_uuid}")
        print("Set this as PLAUD_DEVICE_ID in your .env so the server uses it too.\n")

    login_url = generate_login_url(device_uuid)
    print("Plaud login URL:")
    print(f"  {login_url}\n")

    if not args.no_browser:
        print("Opening your browser…")
        webbrowser.open(login_url)
    print("Sign in with Google / Apple / email as usual.")
    print(
        "After login, your browser will try to open a plaud:// URL. "
        "Cancel the system prompt and copy the full URL from the address bar.\n"
    )

    redirect_url = input("Paste the plaud:// redirect URL here: ").strip()
    auth_code = _parse_auth_code(redirect_url)

    token = asyncio.run(
        _exchange(auth_code, device_uuid, args.base_url, args.token_file)
    )

    exp = decode_jwt_expiry(token)
    print(f"\nToken written to: {args.token_file}")
    if exp is not None:
        import datetime
        expiry = datetime.datetime.fromtimestamp(exp, tz=datetime.timezone.utc)
        print(f"Token expires:    {expiry.strftime('%Y-%m-%d')} (re-run this script before then)")
    print("\nDone. Start the MCP server with PLAUD_TOKEN_FILE pointing to this file.")


if __name__ == "__main__":
    main()
