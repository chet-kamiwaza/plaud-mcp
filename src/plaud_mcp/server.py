"""
Plaud MCP Server — FastMCP application exposing Plaud cloud API data as tools.

Provides 11 tools:
  TOOL-01: check_connection     — verify token, return file count
  TOOL-02: get_file_count       — return total recordings count
  TOOL-03: get_recent_files     — list files from last N days
  TOOL-04: get_files            — list files with optional date range
  TOOL-05: get_file             — get metadata for a specific recording
  TOOL-06: get_transcript       — fetch transcript via signed S3 URL
  TOOL-07: get_summary          — fetch AI summary via signed S3 URL
  TOOL-08: get_highlights       — fetch AI highlights via signed S3 URL
  TOOL-09: list_folders         — list Plaud folders (file tags)
  TOOL-10: get_folder_files     — list files scoped to a folder
  TOOL-11: search_transcripts   — client-side transcript search

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
from typing import Any

from .client import PlaudClient

mcp = FastMCP("plaud")

HIGHLIGHT_SUCCESS_STATUS = 1
FILE_LIST_PAGE_SIZE = 100
MAX_FILE_LIST_PAGES = 20


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for Kubernetes liveness probe (HTTP mode only)."""
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok"})


@mcp.tool()
async def check_connection() -> dict:
    """Verify the Plaud token is valid and return total file count.

    Returns a dict with status, user_id, email, and file_count.
    Raises PlaudAuthError if the token is invalid or expired.
    """
    async with PlaudClient() as client:
        user_resp = await client.get("/user/me")
        user_data = user_resp.get("data_user", {})
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
    return {
        "status": "connected",
        "user_id": user_data.get("id"),
        "email": user_data.get("email"),
        "file_count": count_resp.get("data_file_total", 0),
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
    return {"count": resp.get("data_file_total", 0)}


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
    all_files = resp.get("data_file_list", [])
    cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp()
    files = [f for f in all_files if f.get("start_time", 0) >= cutoff]
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
    files = resp.get("data_file_list", [])
    if start_date is not None:
        start_ts = (
            datetime.strptime(start_date, "%Y-%m-%d")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        files = [f for f in files if f.get("start_time", 0) >= start_ts]
    if end_date is not None:
        end_ts = (
            datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            + timedelta(days=1)
        ).timestamp()
        files = [f for f in files if f.get("start_time", 0) < end_ts]
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


def _fetch_s3_content(data_link: str) -> Any:
    """Fetch and decompress gzip-compressed content from a signed S3 URL.

    This is a synchronous helper — call via asyncio.to_thread() from async tools.
    No Plaud auth headers are sent; S3 signed URLs are self-authenticating.

    Security: T-02-02 — data_link must be sourced from Plaud API content_list[].data_link,
    never from MCP caller input.

    Args:
        data_link: Signed S3 URL from content_list[].data_link.

    Returns parsed JSON when the payload is JSON; otherwise returns decoded text.
    """
    response = httpx.get(data_link, follow_redirects=True, timeout=30.0)
    response.raise_for_status()
    raw = gzip.decompress(response.content)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode("utf-8")


def _highlight_item_is_ready(item: dict) -> bool:
    """Return True when the Plaud content item is downloadable."""
    return (
        item.get("task_status") == HIGHLIGHT_SUCCESS_STATUS
        and bool(item.get("data_id"))
        and bool(item.get("data_link"))
    )


def _select_highlight_content_item(content_list: list[dict]) -> dict | None:
    """Select the Plaud highlight content item using the Phase 1 precedence."""
    ready_high_light = None
    ready_mark_memo = None
    ready_mark_note = None
    fallback_high_light = None
    fallback_mark_memo = None
    fallback_mark_note = None
    failed_high_light_present = False

    for item in content_list:
        if not isinstance(item, dict):
            continue

        data_type = item.get("data_type")
        if data_type == "high_light":
            fallback_high_light = fallback_high_light or item
            if isinstance(item.get("task_status"), (int, float)) and item.get("task_status") < 0:
                failed_high_light_present = True
            if _highlight_item_is_ready(item):
                ready_high_light = ready_high_light or item
        elif data_type == "mark_memo":
            fallback_mark_memo = fallback_mark_memo or item
            if _highlight_item_is_ready(item):
                ready_mark_memo = ready_mark_memo or item
        elif data_type == "mark_note":
            fallback_mark_note = fallback_mark_note or item
            if _highlight_item_is_ready(item):
                ready_mark_note = ready_mark_note or item

    if ready_high_light is not None:
        return ready_high_light
    if failed_high_light_present and ready_mark_memo is not None:
        return ready_mark_memo
    if ready_mark_note is not None:
        return ready_mark_note
    if ready_mark_memo is not None:
        return ready_mark_memo
    if fallback_high_light is not None:
        return fallback_high_light
    if fallback_mark_note is not None:
        return fallback_mark_note
    if fallback_mark_memo is not None:
        return fallback_mark_memo
    return None


def _normalize_highlight_entry(item: Any) -> dict | None:
    """Normalize one Plaud highlight list item into the MCP response shape."""
    if not isinstance(item, dict):
        return None

    text = item.get("content") or item.get("mark_content")
    if not isinstance(text, str) or not text.strip():
        return None

    normalized = {"text": text.strip()}
    if "timestamp" in item:
        normalized["timestamp"] = item.get("timestamp")
    if "speaker" in item:
        normalized["speaker"] = item.get("speaker")
    return normalized


def _extract_markdown_text(payload: Any) -> str | None:
    """Extract markdown-style highlight text from a non-list payload."""
    if isinstance(payload, str):
        return payload.strip() or None

    if isinstance(payload, dict):
        for key in ("markdown", "content", "mark_content", "text"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return None


def _normalize_highlight_payload(payload: Any, source_type: str | None) -> tuple[list[dict], str | None]:
    """Normalize list-style highlights and optional markdown fallback text."""
    if source_type == "mark_note":
        return [], _extract_markdown_text(payload)

    items: list[Any] = []
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict):
        highlight_list = payload.get("highlightList")
        if isinstance(highlight_list, list):
            items = highlight_list

    highlights = []
    for item in items:
        normalized = _normalize_highlight_entry(item)
        if normalized is not None:
            highlights.append(normalized)

    return highlights, None


def _normalize_folder_item(item: Any) -> dict | None:
    """Normalize one Plaud folder item into the MCP response shape."""
    if not isinstance(item, dict) or item.get("id") in (None, ""):
        return None

    name = item.get("name")
    return {"id": item.get("id"), "name": name if isinstance(name, str) else ""}


def _normalize_folder_file_item(item: Any) -> dict | None:
    """Normalize one Plaud file item for folder-scoped results."""
    if not isinstance(item, dict) or item.get("id") in (None, ""):
        return None

    filetag_ids = item.get("filetag_id_list")
    if not isinstance(filetag_ids, list):
        filetag_ids = []

    return {
        "id": item.get("id"),
        "filename": item.get("filename", ""),
        "start_time": item.get("start_time"),
        "filetag_id_list": filetag_ids,
    }


def _build_file_list_params(skip: int = 0, limit: int = FILE_LIST_PAGE_SIZE) -> dict:
    """Return the standard Plaud generic file-list query params."""
    return {
        "skip": skip,
        "limit": limit,
        "is_trash": 2,
        "sort_by": "start_time",
        "is_desc": "true",
    }


async def _fetch_all_folder_candidate_files(client: PlaudClient) -> list[dict]:
    """Fetch a bounded set of Plaud file-list pages for folder filtering."""
    files: list[dict] = []
    skip = 0

    for _ in range(MAX_FILE_LIST_PAGES):
        resp = await client.get("/file/simple/web", params=_build_file_list_params(skip=skip))
        page_files = resp.get("data_file_list", [])
        if not isinstance(page_files, list) or not page_files:
            break

        files.extend(page_files)

        total = resp.get("data_file_total")
        if isinstance(total, int) and len(files) >= total:
            break
        if len(page_files) < FILE_LIST_PAGE_SIZE:
            break

        skip += FILE_LIST_PAGE_SIZE

    return files


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
async def get_highlights(file_id: str) -> dict:
    """Return normalized AI highlights for a recording.

    Fetches the file detail from Plaud API, selects the most useful highlight
    source from `content_list`, then downloads and normalizes the highlight
    payload from the signed S3 URL when it is ready.

    Args:
        file_id: The Plaud file identifier (non-empty string).

    Returns a dict with file_id, source_type, highlights, count, and optional
    empty-state metadata. Raises ValueError only for invalid caller input.
    """
    if not file_id or not file_id.strip():
        raise ValueError("file_id must be a non-empty string")

    normalized_file_id = file_id.strip()
    async with PlaudClient() as client:
        resp = await client.get(f"/file/detail/{normalized_file_id}")
        detail = resp.get("data", {})

    selected = _select_highlight_content_item(detail.get("content_list", []))
    if selected is None:
        return {
            "file_id": normalized_file_id,
            "source_type": None,
            "highlights": [],
            "count": 0,
            "message": "No highlight source available for this recording.",
        }

    source_type = selected.get("data_type")
    if not _highlight_item_is_ready(selected):
        return {
            "file_id": normalized_file_id,
            "source_type": source_type,
            "highlights": [],
            "count": 0,
            "message": "Highlight content exists but is not ready to download.",
        }

    payload = await asyncio.to_thread(_fetch_s3_content, selected["data_link"])
    highlights, note_markdown = _normalize_highlight_payload(payload, source_type)

    result = {
        "file_id": normalized_file_id,
        "source_type": source_type,
        "highlights": highlights,
        "count": len(highlights),
    }

    if note_markdown is not None:
        result["note_markdown"] = note_markdown

    if not highlights:
        if note_markdown is not None:
            result["message"] = (
                "Plaud returned markdown highlight notes but no structured highlight items."
            )
        else:
            result["message"] = "No highlight items available for this recording."

    return result


@mcp.tool()
async def list_folders() -> dict:
    """Return the normalized Plaud folder list."""
    async with PlaudClient() as client:
        resp = await client.get("/filetag/")

    folders = []
    for item in resp.get("data_filetag_list", []):
        normalized = _normalize_folder_item(item)
        if normalized is not None:
            folders.append(normalized)

    return {"folders": folders, "count": len(folders)}


@mcp.tool()
async def get_folder_files(folder_id: str) -> dict:
    """Return recordings that belong to the requested Plaud folder."""
    if not folder_id or not folder_id.strip():
        raise ValueError("folder_id must be a non-empty string")

    normalized_folder_id = folder_id.strip()

    async with PlaudClient() as client:
        folder_resp = await client.get("/filetag/")
        folders = []
        for item in folder_resp.get("data_filetag_list", []):
            normalized = _normalize_folder_item(item)
            if normalized is not None:
                folders.append(normalized)

        folder = next(
            (item for item in folders if str(item["id"]) == normalized_folder_id),
            None,
        )
        if folder is None:
            return {
                "folder_id": normalized_folder_id,
                "folder_name": None,
                "folder_exists": False,
                "files": [],
                "count": 0,
                "message": "Folder not found.",
            }

        all_files = await _fetch_all_folder_candidate_files(client)

    files = []
    for item in all_files:
        normalized = _normalize_folder_file_item(item)
        if normalized is None:
            continue
        if normalized_folder_id in {str(value) for value in normalized["filetag_id_list"]}:
            files.append(normalized)

    result = {
        "folder_id": normalized_folder_id,
        "folder_name": folder["name"],
        "folder_exists": True,
        "files": files,
        "count": len(files),
    }
    if not files:
        result["message"] = "Folder exists but contains no recordings."
    return result


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
        all_files = resp.get("data_file_list", [])
        cutoff = (datetime.now(tz=timezone.utc) - timedelta(days=days)).timestamp()
        files = [f for f in all_files if f.get("start_time", 0) >= cutoff]

        matches = []
        for f in files:
            try:
                detail_resp = await client.get(f"/file/detail/{f['id']}")
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
                        "file_id": f["id"],
                        "title": f.get("filename", ""),
                        "start_time": f.get("start_time"),
                        "snippet": snippet,
                    }
                )

    return {"query": query, "days": days, "matches": matches, "match_count": len(matches)}
