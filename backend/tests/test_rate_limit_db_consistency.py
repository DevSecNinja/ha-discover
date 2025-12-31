"""Tests for database consistency when rate limiting occurs during indexing."""

import pytest
from app.models.database import Automation, Base, Repository
from app.services.github_service import GitHubRateLimitError
from app.services.indexer import IndexingService
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, patch


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
async def test_rate_limit_on_empty_db_keeps_zero_counts(test_db):
    """Test that rate limiting on first call keeps database empty."""
    service = IndexingService()

    # Mock GitHub service to raise rate limit on first call
    mock_error = GitHubRateLimitError("Rate limit exceeded", retry_after=60)
    with patch.object(
        service.github_service, "search_repositories", side_effect=mock_error
    ):
        stats = await service.index_repositories(test_db)

        # Verify rate limiting was detected
        assert stats["rate_limited"] is True
        assert stats["repositories_found"] == 0

        # Verify database is still empty
        repo_count = test_db.query(func.count(Repository.id)).scalar()
        automation_count = test_db.query(func.count(Automation.id)).scalar()

        assert repo_count == 0, "Database should have 0 repositories after rate limit on empty DB"
        assert automation_count == 0, "Database should have 0 automations after rate limit on empty DB"


@pytest.mark.asyncio
async def test_rate_limit_during_indexing_keeps_accurate_counts(test_db):
    """Test that rate limiting during indexing doesn't corrupt database counts."""
    service = IndexingService()

    # Pre-populate database with 1 repository and 5 automations
    existing_repo = Repository(
        name="existing-repo",
        owner="test-owner",
        description="Test repo",
        url="https://github.com/test-owner/existing-repo",
    )
    test_db.add(existing_repo)
    test_db.commit()
    test_db.refresh(existing_repo)

    for i in range(5):
        automation = Automation(
            alias=f"Test Automation {i}",
            description="Test description",
            trigger_types="state",
            source_file_path="automations.yaml",
            github_url=f"https://github.com/test-owner/existing-repo/blob/main/automations.yaml",
            repository_id=existing_repo.id,
        )
        test_db.add(automation)
    test_db.commit()

    # Verify initial counts
    initial_repo_count = test_db.query(func.count(Repository.id)).scalar()
    initial_automation_count = test_db.query(func.count(Automation.id)).scalar()
    assert initial_repo_count == 1
    assert initial_automation_count == 5

    # Mock GitHub service to return repos but rate limit on file access
    mock_repos = [
        {
            "owner": "test",
            "name": "new-repo",
            "description": "New test repo",
            "url": "https://github.com/test/new-repo",
            "default_branch": "main",
        }
    ]

    mock_error = GitHubRateLimitError("Rate limit exceeded", retry_after=60)

    with patch.object(
        service.github_service, "search_repositories", return_value=mock_repos
    ):
        with patch.object(
            service.github_service, "find_automation_files", side_effect=mock_error
        ):
            stats = await service.index_repositories(test_db)

            # Verify rate limiting was detected
            assert stats["rate_limited"] is True
            assert stats["repositories_found"] == 1
            assert stats["repositories_indexed"] == 0

            # Verify database counts remain unchanged
            final_repo_count = test_db.query(func.count(Repository.id)).scalar()
            final_automation_count = test_db.query(func.count(Automation.id)).scalar()

            assert final_repo_count == initial_repo_count, \
                f"Repository count should remain {initial_repo_count}, but got {final_repo_count}"
            assert final_automation_count == initial_automation_count, \
                f"Automation count should remain {initial_automation_count}, but got {final_automation_count}"


@pytest.mark.asyncio
async def test_rate_limit_on_file_content_fetch(test_db):
    """Test rate limiting when fetching file content doesn't corrupt DB."""
    service = IndexingService()

    # Mock GitHub service
    mock_repos = [
        {
            "owner": "test",
            "name": "repo",
            "description": "Test repo",
            "url": "https://github.com/test/repo",
            "default_branch": "main",
        }
    ]

    mock_error = GitHubRateLimitError("Rate limit exceeded", retry_after=60)

    with patch.object(
        service.github_service, "search_repositories", return_value=mock_repos
    ):
        with patch.object(
            service.github_service,
            "find_automation_files",
            return_value=["automations.yaml"],
        ):
            with patch.object(
                service.github_service, "get_file_content", side_effect=mock_error
            ):
                stats = await service.index_repositories(test_db)

                # Verify rate limiting was detected
                assert stats["rate_limited"] is True

                # Verify database is still empty (nothing committed due to rate limit)
                repo_count = test_db.query(func.count(Repository.id)).scalar()
                automation_count = test_db.query(func.count(Automation.id)).scalar()

                assert repo_count == 0, "Database should have 0 repositories when rate limited during file fetch"
                assert automation_count == 0, "Database should have 0 automations when rate limited during file fetch"
