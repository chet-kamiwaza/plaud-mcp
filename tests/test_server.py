"""
Unit tests for all 8 Plaud MCP tools in plaud_mcp.server.

Mocking strategy:
  - PlaudClient is patched at "plaud_mcp.server.PlaudClient" so that
    `async with PlaudClient() as client:` yields a MagicMock whose .get
    and .get_all_files are AsyncMocks.
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

def make_mock_client(get_side_effects=None, all_files=None):
    """Return a mock PlaudClient context manager.

    Args:
        get_side_effects: Value(s) for .get(). Single value or list for sequence.
        all_files: Return value for .get_all_files() — a list of file dicts.
    """
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    if get_side_effects is not None:
        if isinstance(get_side_effects, list):
            mock_client.get = AsyncMock(side_effect=get_side_effects)
        else:
            mock_client.get = AsyncMock(return_value=get_side_effects)
    else:
        mock_client.get = AsyncMock(return_value={"status": 0, "data": {}})

    mock_client.get_all_files = AsyncMock(return_value=all_files or [])
    return mock_client


def _ms(seconds_ago):
    """Return a start_time in milliseconds for N seconds ago."""
    return int((time.time() - seconds_ago) * 1000)


# ---------------------------------------------------------------------------
# TOOL-01: check_connection
# ---------------------------------------------------------------------------

class TestCheckConnection:
    async def test_returns_connected_status(self):
        user_resp = {
            "status": 0,
            "data_user": {"id": "user-001", "email": "user@example.com"},
        }
        mock_client = make_mock_client(get_side_effects=user_resp)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import check_connection
            result = await check_connection()

        assert result["status"] == "connected"
        assert result["user_id"] == "user-001"
        assert result["email"] == "user@example.com"
        assert "file_count" not in result

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
    async def test_returns_count_from_all_files(self):
        files = [{"id": f"f{i}"} for i in range(17)]
        mock_client = make_mock_client(all_files=files)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_file_count
            result = await get_file_count()

        assert result == {"count": 17}

    async def test_returns_zero_when_no_files(self):
        mock_client = make_mock_client(all_files=[])

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_file_count
            result = await get_file_count()

        assert result == {"count": 0}


# ---------------------------------------------------------------------------
# TOOL-03: get_recent_files
# ---------------------------------------------------------------------------

class TestGetRecentFiles:
    async def test_filters_by_days(self):
        recent = {"id": "f1", "filename": "Recent", "start_time": _ms(86400)}       # 1 day ago
        old = {"id": "f2", "filename": "Old", "start_time": _ms(10 * 86400)}        # 10 days ago

        mock_client = make_mock_client(all_files=[recent, old])

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_recent_files
            result = await get_recent_files(days=7)

        assert result["count"] == 1
        assert result["days"] == 7
        assert result["files"][0]["id"] == "f1"

    async def test_returns_all_within_window(self):
        file1 = {"id": "a1", "start_time": _ms(100)}
        file2 = {"id": "a2", "start_time": _ms(3600)}

        mock_client = make_mock_client(all_files=[file1, file2])

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_recent_files
            result = await get_recent_files(days=7)

        assert result["count"] == 2
        assert len(result["files"]) == 2

    async def test_returns_empty_when_no_recent_files(self):
        old = {"id": "old", "start_time": _ms(30 * 86400)}

        mock_client = make_mock_client(all_files=[old])

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
            {"id": "x1", "start_time": 1712000000000},
            {"id": "x2", "start_time": 1712100000000},
        ]
        mock_client = make_mock_client(all_files=files)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files(limit=0)

        assert result["count"] == 2
        assert len(result["files"]) == 2

    async def test_start_date_filters(self):
        # start_date 2024-04-01 UTC = 1711929600 seconds = 1711929600000 ms
        before = {"id": "b1", "start_time": 1711800000000}  # before 2024-04-01
        after = {"id": "b2", "start_time": 1712000000000}   # after 2024-04-01

        mock_client = make_mock_client(all_files=[before, after])

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files(start_date="2024-04-01", limit=0)

        assert result["count"] == 1
        assert result["files"][0]["id"] == "b2"

    async def test_end_date_filters(self):
        # end_date 2024-04-01 UTC: anything before 2024-04-02 00:00:00 = 1712016000000 ms passes
        early = {"id": "e1", "start_time": 1711900000000}   # before 2024-04-02 00:00 UTC
        late = {"id": "e2", "start_time": 1712100000000}    # after 2024-04-02 00:00 UTC

        mock_client = make_mock_client(all_files=[early, late])

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files(end_date="2024-04-01", limit=0)

        assert result["count"] == 1
        assert result["files"][0]["id"] == "e1"

    async def test_default_limit_applied(self):
        files = [{"id": f"f{i}", "start_time": _ms(i * 100)} for i in range(100)]
        mock_client = make_mock_client(all_files=files)

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client):
            from plaud_mcp.server import get_files
            result = await get_files()

        assert result["count"] == 50  # default limit


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
        mock_client = make_mock_client(get_side_effects=resp)

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
        mock_client = make_mock_client(get_side_effects=resp)

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
        mock_client = make_mock_client(get_side_effects=detail_resp)

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
        mock_client = make_mock_client(get_side_effects=detail_resp)

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
        mock_client = make_mock_client(get_side_effects=detail_resp)

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
        mock_client = make_mock_client(get_side_effects=detail_resp)

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
        mock_client = make_mock_client(get_side_effects=detail_resp)

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
        mock_client = make_mock_client(get_side_effects=detail_resp)

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
        file_in_window = {
            "id": "match1",
            "filename": "Sales Call",
            "start_time": _ms(86400),  # 1 day ago — within 30-day window
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
        mock_client = make_mock_client(
            get_side_effects=detail_resp,
            all_files=[file_in_window],
        )

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
        assert result["files_searched"] == 1

    async def test_no_matches_returns_empty(self):
        file_in_window = {
            "id": "nomatch",
            "filename": "Unrelated",
            "start_time": _ms(3600),
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
        mock_client = make_mock_client(
            get_side_effects=detail_resp,
            all_files=[file_in_window],
        )

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
        old_file = {
            "id": "old1",
            "filename": "Old Recording",
            "start_time": _ms(60 * 86400),  # 60 days ago — outside 30-day window
        }
        mock_client = make_mock_client(all_files=[old_file])

        with patch("plaud_mcp.server.PlaudClient", return_value=mock_client), \
             patch("plaud_mcp.server.asyncio") as mock_asyncio:
            mock_asyncio.to_thread = AsyncMock()
            from plaud_mcp.server import search_transcripts
            result = await search_transcripts("anything", days=30)

        # Old file was filtered before fetching details, so to_thread was never called
        mock_asyncio.to_thread.assert_not_called()
        assert result["match_count"] == 0

    async def test_file_without_transcript_skipped(self):
        file_no_transcript = {
            "id": "notr",
            "filename": "No transcript",
            "start_time": _ms(3600),
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
        mock_client = make_mock_client(
            get_side_effects=detail_resp,
            all_files=[file_no_transcript],
        )

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
        bad_file = {
            "id": "err1",
            "filename": "Error file",
            "start_time": _ms(3600),
        }
        good_file = {
            "id": "good1",
            "filename": "Good file",
            "start_time": _ms(7200),
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
        mock_client.get_all_files = AsyncMock(return_value=[bad_file, good_file])
        mock_client.get = AsyncMock(
            side_effect=[PlaudAPIError("fetch failed"), good_detail_resp]
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
