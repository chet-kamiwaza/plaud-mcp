#!/usr/bin/env python3
"""Generate redacted Phase 1 Plaud discovery artifacts.

Source mode inspects the currently deployed Plaud web app, the locally
installed desktop bundle, and desktop logs. Live mode reuses the existing
Plaud request contract when both PLAUD_TOKEN and PLAUD_DEVICE_ID are present.
"""

from __future__ import annotations

import argparse
import asyncio
import gzip
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed-argv invocations of `npx asar extract` only
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import httpx


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = (
    REPO_ROOT
    / ".planning"
    / "phases"
    / "01-api-discovery-contracts"
    / "artifacts"
)
WEB_APP_URL = "https://web.plaud.ai/"
WEB_CHUNK_FALLBACK = Path("/tmp/plaud_web_common.js")
DESKTOP_EXTRACT_ROOT = Path(tempfile.gettempdir()) / "plaud_extract"  # nosec B108 - dev-only discovery script, path is cache-like
APP_ASAR = Path("/Applications/Plaud.app/Contents/Resources/app.asar")
LOG_DIR = Path.home() / "Library" / "Application Support" / "Plaud" / "logs"

ARTIFACT_FILENAMES = {
    "highlights_detail": "highlights-detail-redacted.json",
    "highlights_payload": "highlights-payload-redacted.json",
    "folders_list": "folders-list-redacted.json",
    "folder_files": "folder-files-redacted.json",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
    "Electron/29.0.0 Safari/537.36"
)

QUERY_REDACTION = "[redacted-query]"
ID_REDACTION = "[redacted-id]"
TEXT_REDACTION = "[redacted-text]"
EMAIL_REDACTION = "[redacted-email]"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def collapse_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_snippet(text: str, token: str, radius: int = 180) -> str:
    index = text.find(token)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(token) + radius)
    return collapse_whitespace(text[start:end])


def redact_url(value: str) -> str:
    parts = urlsplit(value)
    if not parts.scheme or not parts.netloc:
        return value
    query = QUERY_REDACTION if parts.query else ""
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, ""))


def redact_string(value: str, *, keep_long_text: bool = False) -> str:
    redacted = re.sub(
        r"bearer\s+[A-Za-z0-9._\-+/=]+",
        "bearer [redacted-token]",
        value,
        flags=re.IGNORECASE,
    )
    redacted = re.sub(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        EMAIL_REDACTION,
        redacted,
    )
    if redacted.startswith("http://") or redacted.startswith("https://"):
        redacted = redact_url(redacted)
    if not keep_long_text and len(redacted) > 120:
        redacted = f"{redacted[:120]}..."
    return redacted


def sanitize(value: Any, *, key: str = "") -> Any:
    if isinstance(value, dict):
        return {k: sanitize(v, key=k) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(item, key=key) for item in value]
    if isinstance(value, str):
        if key.lower().endswith("id") or key.lower() in {
            "id",
            "file_id",
            "data_id",
            "source_id",
            "note_id",
        }:
            return ID_REDACTION
        return redact_string(value)
    return value


def build_http_client() -> httpx.Client:
    return httpx.Client(
        follow_redirects=True,
        timeout=15.0,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/json,text/plain,*/*",
            "Origin": "https://web.plaud.ai",
            "Referer": "https://web.plaud.ai/",
        },
    )


def load_current_web_assets() -> tuple[str, str, str]:
    html = ""
    chunk_url = ""
    chunk_text = ""
    with build_http_client() as client:
        html = client.get(WEB_APP_URL).text
        match = re.search(
            r"https://web-static\.plaud\.ai/web3/js/[^\"' ]*app-initial-common[^\"' ]*\.chunk\.js",
            html,
        )
        if match:
            chunk_url = match.group(0)
            chunk_text = client.get(chunk_url).text
    if not chunk_text and WEB_CHUNK_FALLBACK.exists():
        chunk_url = str(WEB_CHUNK_FALLBACK)
        chunk_text = WEB_CHUNK_FALLBACK.read_text(encoding="utf-8", errors="ignore")
    if not chunk_text:
        raise RuntimeError("Could not load Plaud web bundle for source mode")
    return html, chunk_url, chunk_text


def ensure_desktop_extract() -> Path | None:
    if (DESKTOP_EXTRACT_ROOT / "out-global-online" / "main").exists():
        return DESKTOP_EXTRACT_ROOT
    if not APP_ASAR.exists():
        return None
    npx = shutil.which("npx")
    if npx is None:
        return None
    subprocess.run(  # nosec B603 - fixed argv, resolved `npx`, no shell
        [npx, "--yes", "asar", "extract", str(APP_ASAR), str(DESKTOP_EXTRACT_ROOT)],
        check=True,
        capture_output=True,
        text=True,
    )
    if (DESKTOP_EXTRACT_ROOT / "out-global-online" / "main").exists():
        return DESKTOP_EXTRACT_ROOT
    return None


def first_glob(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[0] if matches else None


def load_desktop_sources() -> dict[str, str]:
    root = ensure_desktop_extract()
    if root is None:
        return {}
    highlight_service = first_glob(
        root, "out-global-online/main/highlightService-*.js"
    )
    transcription_main = first_glob(root, "out-global-online/main/index-Bbfz*.js")
    return {
        "root": str(root),
        "highlight_service": (
            highlight_service.read_text(encoding="utf-8", errors="ignore")
            if highlight_service
            else ""
        ),
        "highlight_service_path": str(highlight_service) if highlight_service else "",
        "transcription_main": (
            transcription_main.read_text(encoding="utf-8", errors="ignore")
            if transcription_main
            else ""
        ),
        "transcription_main_path": (
            str(transcription_main) if transcription_main else ""
        ),
    }


def collect_log_matches() -> list[dict[str, str]]:
    if not LOG_DIR.exists():
        return []
    wanted = (
        "file/workflow/trigger-status",
        "file/list/simple",
        "mark/create_task",
        "get_mark_result",
        "update_source_info",
        "empty source content",
    )
    matches: list[dict[str, str]] = []
    for path in sorted(LOG_DIR.glob("*"), reverse=True):
        if path.suffix not in {".log", ".gz"}:
            continue
        if path.suffix == ".gz":
            try:
                text = gzip.open(path, "rt", encoding="utf-8", errors="ignore").read()
            except OSError:
                continue
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            if any(token in line for token in wanted):
                matches.append(
                    {"path": str(path), "line": redact_string(collapse_whitespace(line))}
                )
        if len(matches) >= 12:
            break
    return matches[:12]


def evidence_source(mode: str, sources: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "mode": mode,
        "generated_at": utc_now(),
        "sources": sources,
    }


def build_source_artifacts() -> dict[str, dict[str, Any]]:
    html, web_chunk_url, web_chunk = load_current_web_assets()
    desktop = load_desktop_sources()
    log_matches = collect_log_matches()

    file_list_prefetch = extract_snippet(
        html, "/file/simple/web?skip=0&limit=20&is_trash=2"
    ) or extract_snippet(web_chunk, "/file/simple/web?")
    selector_snippet = extract_snippet(web_chunk, "al=e=>{let t=null")
    folder_api_snippet = extract_snippet(web_chunk, 'kb(){return await M.get("/filetag/")}')
    folder_filter_snippet = extract_snippet(web_chunk, "filetag_id_list?.includes(J)")
    payload_parser_snippet = extract_snippet(web_chunk, "case F.HIGH_LIGHT:case F.MARK_MEMO")
    payload_roundtrip_snippet = extract_snippet(
        web_chunk, "source_content:JSON.stringify(n)"
    )
    desktop_mark_snippet = extract_snippet(
        desktop.get("highlight_service", ""), "mark_content: block.value"
    )
    file_name_lookup_snippet = extract_snippet(
        desktop.get("transcription_main", ""), '"/file/list/simple"'
    )

    sources = [
        {
            "kind": "web-html",
            "location": WEB_APP_URL,
            "proof": redact_string(file_list_prefetch),
        },
        {
            "kind": "web-bundle",
            "location": web_chunk_url,
            "proof": redact_string(selector_snippet or payload_parser_snippet),
        },
        {
            "kind": "desktop-bundle",
            "location": desktop.get("highlight_service_path", ""),
            "proof": redact_string(desktop_mark_snippet),
        },
    ]
    if file_name_lookup_snippet:
        sources.append(
            {
                "kind": "desktop-bundle",
                "location": desktop.get("transcription_main_path", ""),
                "proof": redact_string(file_name_lookup_snippet),
            }
        )
    if log_matches:
        sources.append(
            {
                "kind": "desktop-log",
                "location": log_matches[0]["path"],
                "proof": log_matches[0]["line"],
            }
        )

    highlights_detail = {
        "feature": "highlights",
        "evidence_source": evidence_source("source", sources),
        "endpoint": "/file/detail/{file_id}",
        "request_params": {
            "path_params": ["file_id"],
            "query_params": [],
            "headers_reused_from_client": [
                "authorization_header",
                "device_id_header",
                "edit-from",
                "app-platform",
                "app-versionNumber",
                "app-language",
            ],
        },
        "response_keys": {
            "detail_root": ["data", "content_list"],
            "content_list_item": [
                "data_type",
                "task_status",
                "data_title",
                "data_id",
                "data_link",
                "err_msg",
            ],
            "selector_data_types": ["high_light", "mark_note", "mark_memo"],
            "selector_precedence": [
                "high_light when task_status == SUCCESS",
                "mark_memo when high_light is present but failed",
                "mark_note",
                "mark_memo",
                "high_light fallback",
            ],
        },
        "empty_or_error_behavior": [
            "If the selected content_list item is missing data_link or data_id, loadHighlightContent returns false.",
            "If task_status is not SUCCESS, loadHighlightContent returns false without downloading payload data.",
            "When a high_light item is present with a negative task_status and a mark_memo item also exists, the selector falls back to mark_memo.",
        ],
        "caveats": [
            "No authenticated /file/detail/{file_id} response was captured in this environment because PLAUD_TOKEN and PLAUD_DEVICE_ID were not available.",
            "The redacted example below is source-derived from field access in the current web bundle, not a live response body.",
            "Timestamp and speaker fields were not directly confirmed from the read-side /file/detail payload.",
        ],
        "observed_selector_path": "data.content_list[] selected by data_type in the web bundle helper that the file detail screen uses before downloading data_link content.",
        "redacted_example": {
            "data": {
                "content_list": [
                    {
                        "data_type": "high_light",
                        "task_status": 1,
                        "data_title": TEXT_REDACTION,
                        "data_id": ID_REDACTION,
                        "data_link": "https://example.invalid/highlight.json?[redacted-query]",
                        "err_msg": "",
                    }
                ]
            }
        },
    }

    highlights_payload = {
        "feature": "highlights",
        "evidence_source": evidence_source(
            "source",
            [
                {
                    "kind": "web-bundle",
                    "location": web_chunk_url,
                    "proof": redact_string(payload_parser_snippet),
                },
                {
                    "kind": "web-bundle",
                    "location": web_chunk_url,
                    "proof": redact_string(payload_roundtrip_snippet),
                },
                {
                    "kind": "desktop-bundle",
                    "location": desktop.get("highlight_service_path", ""),
                    "proof": redact_string(desktop_mark_snippet),
                },
            ],
        ),
        "endpoint": "/file/detail/{file_id} -> content_list[].data_link",
        "request_params": {
            "selector_source": "content_list item selected from /file/detail/{file_id}",
            "selector_data_types": ["high_light", "mark_memo"],
            "download_transport": "signed data_link",
            "wrapper_candidates": ["highlightList", "raw array"],
        },
        "response_keys": {
            "wrapper_object": ["highlightList"],
            "highlight_item": ["title", "content", "mark_content", "picture_link"],
            "accepted_payload_types": ["array", "object-with-highlightList"],
        },
        "empty_or_error_behavior": [
            "An empty array is treated as a valid no-highlights state.",
            "An object with highlightList: [] is treated as a valid no-highlights state.",
            "If the downloaded payload does not expose content or mark_content on the first list item, the web parser rejects it as an unsupported highlight payload.",
        ],
        "caveats": [
            "No signed highlight payload was downloaded in this environment, so the example below is a source-derived shape rather than a live capture.",
            "Read-side timestamp was not directly confirmed. The current desktop and web write paths both preserve timestamp for mark_memo source updates, but the read parser does not require it.",
            "Read-side speaker was not observed in the current web or desktop highlight parsers.",
            "Phase 3 should normalize text from content first, then fall back to mark_content when present.",
        ],
        "redacted_example": {
            "highlightList": [
                {
                    "title": TEXT_REDACTION,
                    "content": TEXT_REDACTION,
                    "mark_content": TEXT_REDACTION,
                    "picture_link": "https://example.invalid/image.webp?[redacted-query]",
                }
            ]
        },
    }

    folders_list = {
        "feature": "folders",
        "evidence_source": evidence_source(
            "source",
            [
                {
                    "kind": "web-bundle",
                    "location": web_chunk_url,
                    "proof": redact_string(folder_api_snippet),
                }
            ],
        ),
        "endpoint": "/filetag/",
        "request_params": {
            "query_params": [],
            "body": None,
        },
        "response_keys": {
            "list_root": ["data_filetag_list"],
            "create_root": ["data_filetag"],
            "folder_item": ["id", "name"],
        },
        "empty_or_error_behavior": [
            "When the current folder cache is stale or empty, the web folder manager refetches /filetag/ and replaces the in-memory list with data_filetag_list or [].",
            "If the request throws, the folder manager clears the current folder list to [].",
        ],
        "caveats": [
            "Folder items were confirmed from source inspection, not a live authenticated response body.",
        ],
        "redacted_example": {
            "data_filetag_list": [
                {
                    "id": ID_REDACTION,
                    "name": TEXT_REDACTION,
                }
            ]
        },
    }

    folder_files = {
        "feature": "folders",
        "evidence_source": evidence_source(
            "source",
            [
                {
                    "kind": "web-html",
                    "location": WEB_APP_URL,
                    "proof": redact_string(file_list_prefetch),
                },
                {
                    "kind": "web-bundle",
                    "location": web_chunk_url,
                    "proof": redact_string(folder_filter_snippet),
                },
                {
                    "kind": "desktop-log",
                    "location": log_matches[0]["path"] if log_matches else "",
                    "proof": log_matches[0]["line"] if log_matches else "",
                },
            ],
        ),
        "endpoint": "/file/simple/web",
        "request_params": {
            "query_params": {
                "skip": 0,
                "limit": 20,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": True,
            },
            "folder_scope": "client-side filter where filetag_id_list includes {folder_id}",
            "ui_route_query": ["tagId", "categoryId"],
        },
        "response_keys": {
            "list_root": ["data_file_list"],
            "file_item": ["id", "filename", "start_time", "filetag_id_list"],
        },
        "empty_or_error_behavior": [
            "If folder_id is missing, the current web store returns an empty list without making an additional request.",
            "If /file/simple/web fails, the current web store clears the in-memory file list to [].",
            "The current web code does not show a dedicated folder-scoped API path; it filters the generic file list by filetag_id_list membership.",
        ],
        "caveats": [
            "No separate folder-files endpoint was observed in the current web or desktop sources.",
            "Downstream get_folder_files(folder_id) can be implemented without guesswork by listing /file/simple/web and filtering items whose filetag_id_list contains the requested folder id.",
            "The redacted example below is source-derived from the generic file list shape already used elsewhere in this repository.",
        ],
        "redacted_example": {
            "data_file_list": [
                {
                    "id": ID_REDACTION,
                    "filename": TEXT_REDACTION,
                    "start_time": 1712000000,
                    "filetag_id_list": [ID_REDACTION],
                }
            ]
        },
    }

    return {
        ARTIFACT_FILENAMES["highlights_detail"]: highlights_detail,
        ARTIFACT_FILENAMES["highlights_payload"]: highlights_payload,
        ARTIFACT_FILENAMES["folders_list"]: folders_list,
        ARTIFACT_FILENAMES["folder_files"]: folder_files,
    }


def fetch_signed_payload(url: str) -> Any:
    with build_http_client() as client:
        response = client.get(url)
        response.raise_for_status()
        raw = response.content
    try:
        raw = gzip.decompress(raw)
    except OSError:
        pass
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw.decode("utf-8", errors="ignore")


def select_highlight_content_item(content_list: list[dict[str, Any]]) -> dict[str, Any] | None:
    high_light = None
    mark_note = None
    mark_memo = None
    for item in content_list:
        data_type = item.get("data_type")
        if data_type == "high_light":
            high_light = item
        elif data_type == "mark_note":
            mark_note = item
        elif data_type == "mark_memo":
            mark_memo = item
    if high_light and high_light.get("task_status") == 1:
        return high_light
    if high_light and isinstance(high_light.get("task_status"), int) and high_light["task_status"] < 0 and mark_memo:
        return mark_memo
    if mark_note:
        return mark_note
    if mark_memo:
        return mark_memo
    return high_light


async def build_live_artifacts() -> dict[str, dict[str, Any]]:
    sys.path.insert(0, str(REPO_ROOT / "src"))
    from plaud_mcp.client import PlaudClient

    async with PlaudClient() as client:
        file_list = await client.get(
            "/file/simple/web",
            params={
                "skip": 0,
                "limit": 20,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": "true",
            },
        )
        folder_list = await client.get("/filetag/")

        data_file_list = file_list.get("data_file_list", [])
        file_id = ""
        for item in data_file_list:
            candidate = item.get("id") or item.get("file_id")
            if candidate:
                file_id = str(candidate)
                break

        detail = {"data": {"content_list": []}}
        if file_id:
            detail = await client.get(f"/file/detail/{file_id}")

    detail_data = detail.get("data", {})
    content_list = detail_data.get("content_list", [])
    selected_content = select_highlight_content_item(content_list)
    payload = None
    if selected_content and selected_content.get("data_link"):
        payload = fetch_signed_payload(str(selected_content["data_link"]))

    folder_items = folder_list.get("data_filetag_list", [])
    selected_folder_id = ""
    if folder_items:
        selected_folder_id = str(folder_items[0].get("id") or "")
    filtered_files = [
        item
        for item in data_file_list
        if selected_folder_id
        and selected_folder_id in {str(tag) for tag in item.get("filetag_id_list", [])}
    ]

    sources = [
        {
            "kind": "live-api",
            "location": "/file/simple/web",
            "proof": f"captured {len(data_file_list)} file list items",
        },
        {
            "kind": "live-api",
            "location": "/filetag/",
            "proof": f"captured {len(folder_items)} folder items",
        },
    ]
    if file_id:
        sources.append(
            {
                "kind": "live-api",
                "location": f"/file/detail/{file_id}",
                "proof": "captured file detail with content_list",
            }
        )

    highlights_detail = {
        "feature": "highlights",
        "evidence_source": evidence_source("live", sources),
        "endpoint": "/file/detail/{file_id}",
        "request_params": {
            "path_params": ["file_id"],
            "file_id_used": ID_REDACTION if file_id else "",
        },
        "response_keys": {
            "detail_root": list(detail.keys()),
            "detail_data": list(detail_data.keys()),
            "content_list_item": sorted(
                {
                    key
                    for item in content_list[:3]
                    for key in item.keys()
                }
            ),
        },
        "empty_or_error_behavior": [
            "If no live file_id was available, the detail capture step was skipped.",
            "If no highlight-like content item was found, selected_content is null.",
        ],
        "caveats": [
            "Live capture reflects one account snapshot. Downstream code should still handle missing highlight items.",
        ],
        "redacted_example": sanitize({"data": {"content_list": content_list[:2]}}),
    }

    payload_keys: list[str] = []
    payload_example: Any = None
    if isinstance(payload, dict):
        payload_keys = sorted(payload.keys())
        payload_example = sanitize(payload)
    elif isinstance(payload, list):
        payload_keys = sorted({key for item in payload[:3] if isinstance(item, dict) for key in item.keys()})
        payload_example = sanitize(payload[:3])
    elif payload is not None:
        payload_example = redact_string(str(payload))

    highlights_payload = {
        "feature": "highlights",
        "evidence_source": evidence_source("live", sources),
        "endpoint": "/file/detail/{file_id} -> content_list[].data_link",
        "request_params": {
            "selected_data_type": selected_content.get("data_type") if selected_content else "",
            "selected_data_id": ID_REDACTION if selected_content else "",
        },
        "response_keys": {
            "payload_root": payload_keys,
        },
        "empty_or_error_behavior": [
            "If no selected content item had data_link, no signed payload download occurred.",
            "Signed payload queries are redacted before writing artifacts.",
        ],
        "caveats": [
            "Live payload shape is still account-specific and may differ between high_light and mark_memo sources.",
        ],
        "redacted_example": payload_example,
    }

    folders_list = {
        "feature": "folders",
        "evidence_source": evidence_source("live", sources),
        "endpoint": "/filetag/",
        "request_params": {
            "query_params": [],
        },
        "response_keys": {
            "list_root": list(folder_list.keys()),
            "folder_item": sorted(
                {
                    key
                    for item in folder_items[:3]
                    for key in item.keys()
                }
            ),
        },
        "empty_or_error_behavior": [
            "An empty data_filetag_list is a valid no-folders state.",
        ],
        "caveats": [
            "Folder examples are redacted and trimmed to the first three items.",
        ],
        "redacted_example": sanitize({"data_filetag_list": folder_items[:3]}),
    }

    folder_files = {
        "feature": "folders",
        "evidence_source": evidence_source("live", sources),
        "endpoint": "/file/simple/web",
        "request_params": {
            "query_params": {
                "skip": 0,
                "limit": 20,
                "is_trash": 2,
                "sort_by": "start_time",
                "is_desc": True,
            },
            "folder_scope": "filtered by filetag_id_list membership after generic listing",
            "selected_folder_id": ID_REDACTION if selected_folder_id else "",
        },
        "response_keys": {
            "list_root": list(file_list.keys()),
            "file_item": sorted(
                {
                    key
                    for item in data_file_list[:3]
                    for key in item.keys()
                }
            ),
        },
        "empty_or_error_behavior": [
            "If there are no folders, selected_folder_id is empty and the filtered list is empty.",
            "No dedicated folder-scoped API path was exercised in live mode because the current client-side flow filters generic file list data.",
        ],
        "caveats": [
            "Filtered examples are redacted and trimmed to the first three matching files.",
        ],
        "redacted_example": sanitize({"data_file_list": filtered_files[:3]}),
    }

    return {
        ARTIFACT_FILENAMES["highlights_detail"]: highlights_detail,
        ARTIFACT_FILENAMES["highlights_payload"]: highlights_payload,
        ARTIFACT_FILENAMES["folders_list"]: folders_list,
        ARTIFACT_FILENAMES["folder_files"]: folder_files,
    }


def write_artifacts(artifacts: dict[str, dict[str, Any]]) -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    for filename, payload in artifacts.items():
        path = ARTIFACT_DIR / filename
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        print(path.relative_to(REPO_ROOT))


def determine_default_mode() -> str:
    if os.getenv("PLAUD_TOKEN") and os.getenv("PLAUD_DEVICE_ID"):
        return "live"
    return "source"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate redacted discovery artifacts for Plaud highlights and folders."
    )
    parser.add_argument(
        "--mode",
        choices=["live", "source"],
        default=determine_default_mode(),
        help="Discovery mode. Defaults to live when PLAUD_TOKEN and PLAUD_DEVICE_ID are both set, otherwise source.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.mode == "live" and not (os.getenv("PLAUD_TOKEN") and os.getenv("PLAUD_DEVICE_ID")):
        raise SystemExit("live mode requires PLAUD_TOKEN and PLAUD_DEVICE_ID")
    if args.mode == "live":
        artifacts = asyncio.run(build_live_artifacts())
    else:
        artifacts = build_source_artifacts()
    write_artifacts(artifacts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
