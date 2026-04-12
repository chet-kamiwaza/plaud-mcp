"""
Plaud MCP Server — package entrypoint.

Reads MCP_TRANSPORT env var (default: "stdio") and starts the server
on the appropriate transport.

  stdio        — MCP over stdin/stdout (Claude Code, Claude Desktop)
  http         — MCP over streamable-http on 0.0.0.0:8080 (Kubernetes)
"""
import os

from .server import mcp


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower().strip()
    if transport == "http":
        # HTTP mode is intended for container/Kubernetes deployments, so
        # binding all interfaces is required for the service to be reachable.
        mcp.run(transport="streamable-http", host="0.0.0.0", port=8080)  # nosec B104
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
