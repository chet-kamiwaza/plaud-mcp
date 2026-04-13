"""
Plaud MCP Server — package entrypoint.

Reads MCP_TRANSPORT env var (default: "stdio") and starts the server
on the appropriate transport.

  stdio        — MCP over stdin/stdout (Claude Code, Claude Desktop)
  http         — MCP over streamable-http on 0.0.0.0:8080 (Kubernetes)
"""
import asyncio
import logging
import os

from .auth import TokenManager
from .config import settings
from .server import mcp


def _bootstrap_token() -> None:
    """Ensure a valid token exists before the MCP server starts.

    Only relevant when ``PLAUD_AUTO_REFRESH=true``. Performs an initial
    password login if the token file is missing or expiring.
    """
    if not settings.plaud_auto_refresh:
        return

    manager = TokenManager(
        token_file=settings.plaud_token_file,
        base_url=settings.plaud_base_url,
        device_id=settings.plaud_device_id,
        app_version=settings.plaud_app_version,
        email=settings.plaud_email,
        password=settings.plaud_password,
    )
    asyncio.run(manager.ensure_valid_token())


def main() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    _bootstrap_token()

    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    if transport == "http":
        # HTTP mode is intended for container/Kubernetes deployments, so
        # binding all interfaces is required for the service to be reachable.
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)  # nosec B104
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
