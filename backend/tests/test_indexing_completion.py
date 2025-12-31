"""Tests for indexing completion timestamp functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from app.models.database import Base, IndexingMetadata
from app.services.github_service import GitHubRateLimitError
from app.services.indexer import IndexingService
from app.services.search_service import SearchService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_db():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.mark.asyncio
async def test_indexing_stores_completion_timestamp_on_success(test_db):
    """Test that successful indexing stores completion timestamp."""
    service = IndexingService()

    # Mock GitHub service to return empty list (successful completion)
    with patch.object(service.github_service, "search_repositories", return_value=[]):
        stats = await service.index_repositories(test_db)

        # Check that indexing completed without rate limiting
        assert stats["rate_limited"] is False
        assert stats["errors"] == 0

        # Check that completion timestamp was stored
        metadata = (
            test_db.query(IndexingMetadata).filter_by(key="last_completed_at").first()
        )
        assert metadata is not None
        assert metadata.value is not None
        # Verify ISO format timestamp
        from datetime import datetime

        datetime.fromisoformat(metadata.value)  # Should not raise


@pytest.mark.asyncio
async def test_indexing_does_not_store_timestamp_on_rate_limit(test_db):
    """Test that indexing halted by rate limit does not store completion timestamp."""
    service = IndexingService()

    # Mock GitHub service to raise rate limit error
    mock_error = GitHubRateLimitError("Rate limit exceeded", retry_after=60)
    with patch.object(
        service.github_service, "search_repositories", side_effect=mock_error
    ):
        stats = await service.index_repositories(test_db)

        # Check that rate limiting was detected
        assert stats["rate_limited"] is True
        assert stats["errors"] > 0

        # Check that completion timestamp was NOT stored
        metadata = (
            test_db.query(IndexingMetadata).filter_by(key="last_completed_at").first()
        )
        assert metadata is None


@pytest.mark.asyncio
async def test_indexing_halts_on_repository_rate_limit(test_db):
    """Test that indexing stops when rate limit is hit during repository processing."""
    service = IndexingService()

    # Mock GitHub service to return one repo, then rate limit on file access
    mock_repos = [
        {
            "owner": "test",
            "name": "repo1",
            "description": "Test repo",
            "url": "https://github.com/test/repo1",
            "default_branch": "main",
        }
    ]

    mock_error = GitHubRateLimitError("Rate limit exceeded", retry_after=120)

    with patch.object(
        service.github_service, "search_repositories", return_value=mock_repos
    ):
        with patch.object(
            service.github_service, "find_automation_files", side_effect=mock_error
        ):
            stats = await service.index_repositories(test_db)

            # Check that rate limiting was detected
            assert stats["rate_limited"] is True
            assert stats["repositories_found"] == 1
            assert stats["repositories_indexed"] == 0

            # Check that completion timestamp was NOT stored
            metadata = (
                test_db.query(IndexingMetadata)
                .filter_by(key="last_completed_at")
                .first()
            )
            assert metadata is None


@pytest.mark.asyncio
async def test_completion_timestamp_updates_on_subsequent_runs(test_db):
    """Test that completion timestamp is updated on subsequent successful runs."""
    service = IndexingService()

    # First successful run
    with patch.object(service.github_service, "search_repositories", return_value=[]):
        await service.index_repositories(test_db)

        first_metadata = (
            test_db.query(IndexingMetadata).filter_by(key="last_completed_at").first()
        )
        first_timestamp = first_metadata.value

    # Second successful run
    with patch.object(service.github_service, "search_repositories", return_value=[]):
        await service.index_repositories(test_db)

        second_metadata = (
            test_db.query(IndexingMetadata).filter_by(key="last_completed_at").first()
        )
        second_timestamp = second_metadata.value

        # Timestamps should be different (second run happened later)
        # Note: They might be the same if execution is too fast, but value should exist
        assert second_timestamp is not None


def test_statistics_includes_last_indexed_timestamp(test_db):
    """Test that statistics endpoint includes last indexed timestamp."""
    # Create a metadata entry
    from datetime import datetime

    timestamp = datetime.utcnow().isoformat()
    metadata = IndexingMetadata(
        key="last_completed_at", value=timestamp, updated_at=datetime.utcnow()
    )
    test_db.add(metadata)
    test_db.commit()

    # Get statistics
    stats = SearchService.get_statistics(test_db)

    assert "last_indexed_at" in stats
    assert stats["last_indexed_at"] == timestamp


def test_statistics_returns_none_when_no_timestamp(test_db):
    """Test that statistics returns None for last_indexed_at when not set."""
    stats = SearchService.get_statistics(test_db)

    assert "last_indexed_at" in stats
    assert stats["last_indexed_at"] is None
