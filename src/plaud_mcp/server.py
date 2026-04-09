"""
Plaud MCP Server — FastMCP application exposing Plaud cloud API data as tools.

Provides 8 tools:
  TOOL-01: check_connection     — verify token, return file count
  TOOL-02: get_file_count       — return total recordings count
  TOOL-03: get_recent_files     — list files from last N days
  TOOL-04: get_files            — list files with optional date range
  TOOL-05: get_file             — get metadata for a specific recording
  TOOL-06: get_transcript       — fetch transcript via signed S3 URL
  TOOL-07: get_summary          — fetch AI summary via signed S3 URL
  TOOL-08: search_transcripts   — client-side transcript search

Security:
  T-02-01: file_id validated non-empty before URL construction.
  T-02-02: S3 URLs only sourced from content_list[].data_link (Plaud API response).
  T-02-04: search_transcripts bounded to 50 files.
"""
from __future__ import annotations

import asyncio
import gzip
import json
import httpx

from datetime import datetime, timezone, timedelta
from fastmcp import FastMCP

from .client import PlaudClient

mcp = FastMCP("plaud")


@mcp.tool()
async def check_connection() -> dict:
    """Verify the Plaud token is valid and return total file count.

    Returns a dict with status, user_id, email, and file_count.
    Raises PlaudAuthError if the token is invalid or expired.
    """
    async with PlaudClient() as client:
        user_resp = await client.get("/user/me")
        user_data = user_resp.get("data", {})
        count_resp = await client.get(
            "/file/simple/web",
            params={
                "skip": 0,
                "limit": 1,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": "true",
            },
        )
        count_data = count_resp.get("data", {})
    return {
        "status": "connected",
        "user_id": user_data.get("user_id"),
        "email": user_data.get("email"),
        "file_count": count_data.get("total", 0),
    }


@mcp.tool()
async def get_file_count() -> dict:
    """Return the total number of recordings in the account.

    Returns a dict with a single key: count.
    """
    async with PlaudClient() as client:
        resp = await client.get(
            "/file/simple/web",
            params={
                "skip": 0,
                "limit": 1,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": "true",
            },
        )
    return {"count": resp.get("data", {}).get("total", 0)}


@mcp.tool()
async def get_recent_files(days: int = 7) -> dict:
    """Return files created in the last N days.

    Args:
        days: Number of days to look back (default 7).

    Returns a dict with files list, count, and days.
    """
    async with PlaudClient() as client:
        resp = await client.get(
            "/file/simple/web",
            params={
                "skip": 0,
                "limit": 100,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": "true",
            },
        )
    all_files = resp.get("data", {}).get("list", [])
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp()
    files = [f for f in all_files if f.get("created_at", 0) >= cutoff]
    return {"files": files, "count": len(files), "days": days}


@mcp.tool()
async def get_files(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int = 50,
) -> dict:
    """Return files with optional date range filter.

    Args:
        start_date: ISO date string "YYYY-MM-DD" (inclusive, UTC midnight).
        end_date: ISO date string "YYYY-MM-DD" (inclusive, end-of-day UTC).
        limit: Maximum files to return (clamped to 200).

    Returns a dict with files list and count.
    """
    limit = min(limit, 200)
    async with PlaudClient() as client:
        resp = await client.get(
            "/file/simple/web",
            params={
                "skip": 0,
                "limit": limit,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": "true",
            },
        )
    files = resp.get("data", {}).get("list", [])
    if start_date is not None:
        start_ts = (
            datetime.strptime(start_date, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        files = [f for f in files if f.get("created_at", 0) >= start_ts]
    if end_date is not None:
        end_ts = (
            datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            + timedelta(days=1)
        ).timestamp()
        files = [f for f in files if f.get("created_at", 0) < end_ts]
    return {"files": files, "count": len(files)}


@mcp.tool()
async def get_file(file_id: str) -> dict:
    """Return metadata and content_list for a specific recording.

    Args:
        file_id: The Plaud file identifier (non-empty string).

    Returns the file detail data dict (includes content_list with S3 URLs).
    Raises ValueError if file_id is empty or whitespace.
    """
    if not file_id or not file_id.strip():
        raise ValueError("file_id must be a non-empty string")
    async with PlaudClient() as client:
        resp = await client.get(f"/file/detail/{file_id.strip()}")
    return resp.get("data", {})


def _fetch_s3_content(data_link: str) -> dict:
    """Fetch and decompress gzip-compressed JSON content from a signed S3 URL.

    This is a synchronous helper — call via asyncio.to_thread() from async tools.
    No Plaud auth headers are sent; S3 signed URLs are self-authenticating.

    Security: T-02-02 — data_link must be sourced from Plaud API content_list[].data_link,
    never from MCP caller input.

    Args:
        data_link: Signed S3 URL from content_list[].data_link.

    Returns the parsed JSON dict from the S3 object.
    """
    response = httpx.get(data_link, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    raw = gzip.decompress(response.content)
    return json.loads(raw)


@mcp.tool()
async def get_transcript(file_id: str) -> dict:
    """Return the full transcript with speaker labels for a recording.

    Fetches the file detail from Plaud API, then downloads and decompresses
    the transcript from the signed S3 URL in content_list.

    Args:
        file_id: The Plaud file identifier (non-empty string).

    Returns a dict with file_id, transcript (full parsed JSON), and speaker_count.
    Raises ValueError if file_id is empty or no transcript is found.
    """
    if not file_id or not file_id.strip():
        raise ValueError("file_id must be a non-empty string")
    async with PlaudClient() as client:
        resp = await client.get(f"/file/detail/{file_id.strip()}")
        detail = resp.get("data", {})
    content_item = next(
        (c for c in detail.get("content_list", []) if c.get("data_type") == "transaction"),
        None,
    )
    if content_item is None:
        raise ValueError(f"No transcript found for file_id={file_id}")
    transcript_data = await asyncio.to_thread(_fetch_s3_content, content_item["data_link"])
    speakers = {
        item.get("speaker")
        for item in transcript_data.get("list", [])
        if item.get("speaker")
    }
    return {
        "file_id": file_id,
        "transcript": transcript_data,
        "speaker_count": len(speakers),
    }


@mcp.tool()
async def get_summary(file_id: str) -> dict:
    """Return the AI-generated summary for a recording.

    Fetches the file detail from Plaud API, then downloads and decompresses
    the summary from the signed S3 URL in content_list.

    Args:
        file_id: The Plaud file identifier (non-empty string).

    Returns a dict with file_id and summary (full parsed JSON).
    Raises ValueError if file_id is empty or no summary is found.
    """
    if not file_id or not file_id.strip():
        raise ValueError("file_id must be a non-empty string")
    async with PlaudClient() as client:
        resp = await client.get(f"/file/detail/{file_id.strip()}")
        detail = resp.get("data", {})
    content_item = next(
        (c for c in detail.get("content_list", []) if c.get("data_type") == "auto_sum_note"),
        None,
    )
    if content_item is None:
        raise ValueError(f"No summary found for file_id={file_id}")
    summary_data = await asyncio.to_thread(_fetch_s3_content, content_item["data_link"])
    return {"file_id": file_id, "summary": summary_data}


@mcp.tool()
async def search_transcripts(query: str, days: int = 30) -> dict:
    """Search transcript content across recent files (client-side).

    Fetches the last 50 files within the given day window, downloads each
    transcript, and performs a case-insensitive substring match. Files with
    no transcript or fetch errors are silently skipped.

    Args:
        query: Search term (non-empty string).
        days: How many days back to search (default 30).

    Returns a dict with query, days, matches list, and match_count.
    Raises ValueError if query is empty.

    Security: T-02-04 — bounded to 50 files per call.
    """
    if not query or not query.strip():
        raise ValueError("query must be a non-empty string")
    async with PlaudClient() as client:
        resp = await client.get(
            "/file/simple/web",
            params={
                "skip": 0,
                "limit": 50,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": "true",
            },
        )
        all_files = resp.get("data", {}).get("list", [])
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp()
        files = [f for f in all_files if f.get("created_at", 0) >= cutoff]

        matches = []
        for f in files:
            try:
                detail_resp = await client.get(f"/file/detail/{f['file_id']}")
                detail = detail_resp.get("data", {})
                content_item = next(
                    (
                        c
                        for c in detail.get("content_list", [])
                        if c.get("data_type") == "transaction"
                    ),
                    None,
                )
                if content_item is None:
                    continue
                transcript_data = await asyncio.to_thread(
                    _fetch_s3_content, content_item["data_link"]
                )
            except Exception:
                continue  # skip files with missing or erroring transcripts

            full_text = " ".join(
                item.get("text", "") for item in transcript_data.get("list", [])
            )
            if query.lower() in full_text.lower():
                idx = full_text.lower().index(query.lower())
                snippet = full_text[max(0, idx - 50) : idx + len(query) + 150].strip()
                matches.append(
                    {
                        "file_id": f["file_id"],
                        "title": f.get("title", ""),
                        "created_at": f.get("created_at"),
                        "snippet": snippet,
                    }
                )

    return {"query": query, "days": days, "matches": matches, "match_count": len(matches)}


if __name__ == "__main__":
    mcp.run(transport="stdio")
