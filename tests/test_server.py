"""
Unit tests for all 8 Plaud MCP tools in plaud_mcp.server.

Mocking strategy:
  - PlaudClient is patched at "plaud_mcp.server.PlaudClient" so that
    `async with PlaudClient() as client:` yields a MagicMock whose .get
    is an AsyncMock.
  - _fetch_s3_content (sync, called via asyncio.to_thread) is tested by
    patching "plaud_mcp.server.asyncio" so that asyncio.to_thread becomes
    an AsyncMock returning fixture content directly.
"""
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_mock_client(*side_effects):
    """Return a mock PlaudClient context manager whose .get returns given values.

    If one value is provided, .get always returns it.
    If multiple values are provided, .get returns them in sequence.
    """
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    if len(side_effects) == 1:
        mock_client.get = AsyncMock(return_value=side_effects[0])
    else:
        mock_client.get = AsyncMock(side_effect=list(side_effects))
    return mock_client


# ---------------------------------------------------------------------------
# TOOL-01: check_connection
# ---------------------------------------------------------------------------

class TestCheckConnection:
    async def test_returns_connected_status_and_file_count(self):
        user_resp = {
            "status": 0,
            "data": {"user_id": "user-001", "email": "user@example.com"},
        }
        count_resp = {
            "status": 0,
            "data": {"list": [], "total": 42},
        }
        mock_client = make_mock_client(user_resp, count_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import check_connection
            result = await check_connection()

        assert result["status"] == "connected"
        assert result["user_id"] == "user-001"
        assert result["email"] == "user@example.com"
        assert result["file_count"] == 42

    async def test_auth_error_propagates(self):
        from plaud_mcp.errors import PlaudAuthError

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(side_effect=PlaudAuthError("token invalid"))

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import check_connection
            with pytest.raises(PlaudAuthError):
                await check_connection()


# ---------------------------------------------------------------------------
# TOOL-02: get_file_count
# ---------------------------------------------------------------------------

class TestGetFileCount:
    async def test_returns_count_from_total(self):
        resp = {"status": 0, "data": {"list": [], "total": 17}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_file_count
            result = await get_file_count()

        assert result == {"count": 17}

    async def test_returns_zero_when_total_missing(self):
        resp = {"status": 0, "data": {}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_file_count
            result = await get_file_count()

        assert result == {"count": 0}


# ---------------------------------------------------------------------------
# TOOL-03: get_recent_files
# ---------------------------------------------------------------------------

class TestGetRecentFiles:
    async def test_filters_by_days(self):
        now = time.time()
        recent = {"file_id": "f1", "title": "Recent", "created_at": int(now - 86400)}      # 1 day ago
        old = {"file_id": "f2", "title": "Old", "created_at": int(now - 10 * 86400)}        # 10 days ago

        resp = {"status": 0, "data": {"list": [recent, old], "total": 2}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_recent_files
            result = await get_recent_files(days=7)

        assert result["count"] == 1
        assert result["days"] == 7
        assert result["files"][0]["file_id"] == "f1"

    async def test_returns_all_within_window(self):
        now = time.time()
        file1 = {"file_id": "a1", "created_at": int(now - 100)}
        file2 = {"file_id": "a2", "created_at": int(now - 3600)}

        resp = {"status": 0, "data": {"list": [file1, file2], "total": 2}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_recent_files
            result = await get_recent_files(days=7)

        assert result["count"] == 2
        assert len(result["files"]) == 2

    async def test_returns_empty_when_no_recent_files(self):
        now = time.time()
        old = {"file_id": "old", "created_at": int(now - 30 * 86400)}

        resp = {"status": 0, "data": {"list": [old], "total": 1}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_recent_files
            result = await get_recent_files(days=7)

        assert result["count"] == 0
        assert result["files"] == []


# ---------------------------------------------------------------------------
# TOOL-04: get_files
# ---------------------------------------------------------------------------

class TestGetFiles:
    async def test_no_filter_returns_all(self):
        files = [
            {"file_id": "x1", "created_at": 1712000000},
            {"file_id": "x2", "created_at": 1712100000},
        ]
        resp = {"status": 0, "data": {"list": files, "total": 2}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files()

        assert result["count"] == 2
        assert len(result["files"]) == 2

    async def test_start_date_filters(self):
        # start_date 2024-04-01 UTC = 1711929600
        before = {"file_id": "b1", "created_at": 1711800000}  # before 2024-04-01
        after = {"file_id": "b2", "created_at": 1712000000}   # after 2024-04-01

        resp = {"status": 0, "data": {"list": [before, after], "total": 2}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files(start_date="2024-04-01")

        assert result["count"] == 1
        assert result["files"][0]["file_id"] == "b2"

    async def test_end_date_filters(self):
        # end_date 2024-04-01 UTC: anything before 2024-04-02 00:00:00 = 1712016000 passes
        early = {"file_id": "e1", "created_at": 1711900000}   # before 2024-04-02 00:00 UTC
        late = {"file_id": "e2", "created_at": 1712100000}    # after 2024-04-02 00:00 UTC

        resp = {"status": 0, "data": {"list": [early, late], "total": 2}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files(end_date="2024-04-01")

        assert result["count"] == 1
        assert result["files"][0]["file_id"] == "e1"

    async def test_limit_clamped_to_200(self):
        """Verify that limit > 200 is silently clamped to 200 in the API call."""
        resp = {"status": 0, "data": {"list": [], "total": 0}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files(limit=999)

        # Verify the API was called with limit=200 (clamped)
        call_kwargs = mock_client.get.call_args
        params = call_kwargs[1].get("params", call_kwargs[0][1] if len(call_kwargs[0]) > 1 else {})
        # params dict passed as keyword arg
        assert params["limit"] == 200
        assert result["count"] == 0


# ---------------------------------------------------------------------------
# TOOL-05: get_file
# ---------------------------------------------------------------------------

class TestGetFile:
    async def test_returns_file_detail(self):
        detail_data = {
            "file_id": "abc123",
            "title": "Test Recording",
            "content_list": [],
        }
        resp = {"status": 0, "data": detail_data}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_file
            result = await get_file("abc123")

        assert result["file_id"] == "abc123"
        assert result["title"] == "Test Recording"

    async def test_empty_file_id_raises_value_error(self):
        with patch("plaud_mcp.server.PlaudClient"):
            from plaud_mcp.server import get_file
            with pytest.raises(ValueError, match="file_id must be a non-empty string"):
                await get_file("")

    async def test_whitespace_file_id_raises_value_error(self):
        with patch("plaud_mcp.server.PlaudClient"):
            from plaud_mcp.server import get_file
            with pytest.raises(ValueError, match="file_id must be a non-empty string"):
                await get_file("   ")

    async def test_strips_whitespace_from_file_id(self):
        resp = {"status": 0, "data": {"file_id": "abc123"}}
        mock_client = make_mock_client(resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_file
            await get_file("  abc123  ")

        # Verify the stripped ID was used in the path
        call_args = mock_client.get.call_args[0]
        assert call_args[0] == "/file/detail/abc123"


# ---------------------------------------------------------------------------
# TOOL-06: get_transcript
# ---------------------------------------------------------------------------

class TestGetTranscript:
    async def test_returns_transcript_with_speaker_count(self):
        transcript_data = {
            "list": [
                {"speaker": "Speaker 1", "text": "Hello there", "start": 0.0},
                {"speaker": "Speaker 2", "text": "Hi back", "start": 2.0},
                {"speaker": "Speaker 1", "text": "How are you", "start": 4.0},
            ]
        }
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "abc123",
                "content_list": [
                    {
                        "data_type": "transaction",
                        "data_link": "https://s3.example.com/t.json.gz",
                    }
                ],
            },
        }
        mock_client = make_mock_client(detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock(return_value=transcript_data)
            from plaud_mcp.server import get_transcript
            result = await get_transcript("abc123")

        assert result["file_id"] == "abc123"
        assert result["speaker_count"] == 2  # Speaker 1 and Speaker 2 (unique)
        assert result["transcript"] == transcript_data

    async def test_no_transcript_in_content_list_raises(self):
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "xyz",
                "content_list": [
                    {"data_type": "auto_sum_note", "data_link": "https://s3.example.com/s.json.gz"}
                ],
            },
        }
        mock_client = make_mock_client(detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_transcript
            with pytest.raises(ValueError, match="No transcript found"):
                await get_transcript("xyz")

    async def test_empty_file_id_raises(self):
        with patch("plaud_mcp.server.PlaudClient"):
            from plaud_mcp.server import get_transcript
            with pytest.raises(ValueError, match="file_id must be a non-empty string"):
                await get_transcript("")

    async def test_empty_content_list_raises(self):
        detail_resp = {
            "status": 0,
            "data": {"file_id": "empty", "content_list": []},
        }
        mock_client = make_mock_client(detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_transcript
            with pytest.raises(ValueError, match="No transcript found"):
                await get_transcript("empty")

    async def test_single_speaker_count(self):
        transcript_data = {
            "list": [
                {"speaker": "Host", "text": "Welcome"},
                {"speaker": "Host", "text": "Let us begin"},
            ]
        }
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "mono",
                "content_list": [
                    {"data_type": "transaction", "data_link": "https://s3.example.com/m.json.gz"}
                ],
            },
        }
        mock_client = make_mock_client(detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock(return_value=transcript_data)
            from plaud_mcp.server import get_transcript
            result = await get_transcript("mono")

        assert result["speaker_count"] == 1


# ---------------------------------------------------------------------------
# TOOL-07: get_summary
# ---------------------------------------------------------------------------

class TestGetSummary:
    async def test_returns_summary_data(self):
        summary_data = {"content": "This meeting discussed quarterly goals."}
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "sum123",
                "content_list": [
                    {
                        "data_type": "auto_sum_note",
                        "data_link": "https://s3.example.com/sum.json.gz",
                    }
                ],
            },
        }
        mock_client = make_mock_client(detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock(return_value=summary_data)
            from plaud_mcp.server import get_summary
            result = await get_summary("sum123")

        assert result["file_id"] == "sum123"
        assert result["summary"] == summary_data

    async def test_no_summary_in_content_list_raises(self):
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "nope",
                "content_list": [
                    {"data_type": "transaction", "data_link": "https://s3.example.com/t.json.gz"}
                ],
            },
        }
        mock_client = make_mock_client(detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_summary
            with pytest.raises(ValueError, match="No summary found"):
                await get_summary("nope")

    async def test_empty_file_id_raises(self):
        with patch("plaud_mcp.server.PlaudClient"):
            from plaud_mcp.server import get_summary
            with pytest.raises(ValueError, match="file_id must be a non-empty string"):
                await get_summary("")


# ---------------------------------------------------------------------------
# TOOL-08: search_transcripts
# ---------------------------------------------------------------------------

class TestSearchTranscripts:
    async def test_finds_matching_file(self):
        now = time.time()
        file_in_window = {
            "file_id": "match1",
            "title": "Sales Call",
            "created_at": int(now - 86400),  # 1 day ago — within 30-day window
        }
        list_resp = {
            "status": 0,
            "data": {"list": [file_in_window], "total": 1},
        }
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "match1",
                "content_list": [
                    {"data_type": "transaction", "data_link": "https://s3.example.com/m.json.gz"}
                ],
            },
        }
        transcript_data = {
            "list": [
                {"speaker": "Alice", "text": "We discussed the quarterly budget forecast"},
                {"speaker": "Bob", "text": "The budget looks good"},
            ]
        }
        mock_client = make_mock_client(list_resp, detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock(return_value=transcript_data)
            from plaud_mcp.server import search_transcripts
            result = await search_transcripts("budget")

        assert result["query"] == "budget"
        assert result["match_count"] == 1
        assert result["matches"][0]["file_id"] == "match1"
        assert result["matches"][0]["title"] == "Sales Call"
        assert "budget" in result["matches"][0]["snippet"].lower()

    async def test_no_matches_returns_empty(self):
        now = time.time()
        file_in_window = {
            "file_id": "nomatch",
            "title": "Unrelated",
            "created_at": int(now - 3600),
        }
        list_resp = {
            "status": 0,
            "data": {"list": [file_in_window], "total": 1},
        }
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "nomatch",
                "content_list": [
                    {"data_type": "transaction", "data_link": "https://s3.example.com/u.json.gz"}
                ],
            },
        }
        transcript_data = {
            "list": [{"speaker": "X", "text": "Hello world how are you"}]
        }
        mock_client = make_mock_client(list_resp, detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock(return_value=transcript_data)
            from plaud_mcp.server import search_transcripts
            result = await search_transcripts("xyznotfound")

        assert result["match_count"] == 0
        assert result["matches"] == []

    async def test_empty_query_raises(self):
        with patch("plaud_mcp.server.PlaudClient"):
            from plaud_mcp.server import search_transcripts
            with pytest.raises(ValueError, match="query must be a non-empty string"):
                await search_transcripts("")

    async def test_whitespace_query_raises(self):
        with patch("plaud_mcp.server.PlaudClient"):
            from plaud_mcp.server import search_transcripts
            with pytest.raises(ValueError, match="query must be a non-empty string"):
                await search_transcripts("   ")

    async def test_files_outside_days_excluded(self):
        now = time.time()
        old_file = {
            "file_id": "old1",
            "title": "Old Recording",
            "created_at": int(now - 60 * 86400),  # 60 days ago — outside 30-day window
        }
        list_resp = {
            "status": 0,
            "data": {"list": [old_file], "total": 1},
        }
        mock_client = make_mock_client(list_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock()
            from plaud_mcp.server import search_transcripts
            result = await search_transcripts("anything", days=30)

        # Old file was filtered before fetching details, so to_thread was never called
        mock_asyncio.to_thread.assert_not_called()
        assert result["match_count"] == 0

    async def test_file_without_transcript_skipped(self):
        now = time.time()
        file_no_transcript = {
            "file_id": "notr",
            "title": "No transcript",
            "created_at": int(now - 3600),
        }
        list_resp = {
            "status": 0,
            "data": {"list": [file_no_transcript], "total": 1},
        }
        detail_resp = {
            "status": 0,
            "data": {
                "file_id": "notr",
                "content_list": [
                    {"data_type": "auto_sum_note", "data_link": "https://s3.example.com/s.json.gz"}
                ],
            },
        }
        mock_client = make_mock_client(list_resp, detail_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock()
            from plaud_mcp.server import search_transcripts
            result = await search_transcripts("anything")

        # File without transaction content_type should be skipped silently
        mock_asyncio.to_thread.assert_not_called()
        assert result["match_count"] == 0

    async def test_file_fetch_error_skipped(self):
        """Files that raise an exception during detail fetch are silently skipped."""
        now = time.time()
        bad_file = {
            "file_id": "err1",
            "title": "Error file",
            "created_at": int(now - 3600),
        }
        good_file = {
            "file_id": "good1",
            "title": "Good file",
            "created_at": int(now - 7200),
        }
        list_resp = {
            "status": 0,
            "data": {"list": [bad_file, good_file], "total": 2},
        }
        good_detail_resp = {
            "status": 0,
            "data": {
                "file_id": "good1",
                "content_list": [
                    {"data_type": "transaction", "data_link": "https://s3.example.com/g.json.gz"}
                ],
            },
        }
        from plaud_mcp.errors import PlaudAPIError

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(
            side_effect=[list_resp, PlaudAPIError("fetch failed"), good_detail_resp]
        )

        transcript_data = {"list": [{"speaker": "A", "text": "target keyword found here"}]}

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock(return_value=transcript_data)
            from plaud_mcp.server import search_transcripts
            result = await search_transcripts("target keyword")

        # bad_file errored out, good_file matched
        assert result["match_count"] == 1
        assert result["matches"][0]["file_id"] == "good1"
