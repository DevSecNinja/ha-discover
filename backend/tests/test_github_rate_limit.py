"""Tests for GitHub API rate limit handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.services.github_service import GitHubRateLimitError, GitHubService


@pytest.mark.asyncio
async def test_search_repositories_rate_limit_429():
    """Test that search_repositories raises GitHubRateLimitError on 429 status."""
    service = GitHubService()

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers.get.return_value = "60"
    mock_response.text = "rate limit exceeded"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(GitHubRateLimitError) as exc_info:
            await service.search_repositories()

        assert "rate limit exceeded" in str(exc_info.value).lower()
        assert exc_info.value.retry_after == 60


@pytest.mark.asyncio
async def test_search_repositories_rate_limit_403():
    """Test that search_repositories raises GitHubRateLimitError on 403 with rate limit message."""
    service = GitHubService()

    mock_response = MagicMock()
    mock_response.status_code = 403
    mock_response.headers.get.return_value = None
    mock_response.text = "API rate limit exceeded"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(GitHubRateLimitError) as exc_info:
            await service.search_repositories()

        assert "rate limit exceeded" in str(exc_info.value).lower()
        assert exc_info.value.retry_after is None


@pytest.mark.asyncio
async def test_get_file_content_rate_limit():
    """Test that get_file_content raises GitHubRateLimitError on rate limit."""
    service = GitHubService()

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers.get.return_value = "120"
    mock_response.text = "rate limit exceeded"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(GitHubRateLimitError) as exc_info:
            await service.get_file_content("owner", "repo", "path")

        assert "rate limit exceeded" in str(exc_info.value).lower()
        assert exc_info.value.retry_after == 120


@pytest.mark.asyncio
async def test_find_automation_files_rate_limit():
    """Test that find_automation_files raises GitHubRateLimitError on rate limit."""
    service = GitHubService()

    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_response.headers.get.return_value = "30"
    mock_response.text = "rate limit exceeded"

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(GitHubRateLimitError) as exc_info:
            await service.find_automation_files("owner", "repo")

        assert "rate limit exceeded" in str(exc_info.value).lower()
        assert exc_info.value.retry_after == 30
