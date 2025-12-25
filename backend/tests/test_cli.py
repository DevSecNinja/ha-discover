"""Tests for CLI commands."""
import asyncio
import os
import pytest
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.cli import run_indexing, get_db_session, main
from app.models import Base


@pytest.fixture
def test_db():
    """Create a test database."""
    # Use in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


@pytest.mark.asyncio
async def test_run_indexing_success(test_db):
    """Test successful indexing run."""
    # Mock the indexer service
    mock_stats = {
        "repositories_found": 5,
        "repositories_indexed": 5,
        "automations_indexed": 20,
        "errors": 0
    }
    
    with patch('app.cli.IndexingService') as mock_indexer_class, \
         patch('app.cli.get_db_session', return_value=test_db):
        
        mock_indexer = AsyncMock()
        mock_indexer.index_repositories.return_value = mock_stats
        mock_indexer_class.return_value = mock_indexer
        
        # Set environment variable
        os.environ["GITHUB_TOKEN"] = "test_token"
        
        try:
            exit_code = await run_indexing()
            
            # Verify success
            assert exit_code == 0
            mock_indexer.index_repositories.assert_called_once()
        finally:
            # Clean up
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]


@pytest.mark.asyncio
async def test_run_indexing_with_errors(test_db):
    """Test indexing run with errors."""
    # Mock the indexer service with errors
    mock_stats = {
        "repositories_found": 5,
        "repositories_indexed": 3,
        "automations_indexed": 15,
        "errors": 2
    }
    
    with patch('app.cli.IndexingService') as mock_indexer_class, \
         patch('app.cli.get_db_session', return_value=test_db):
        
        mock_indexer = AsyncMock()
        mock_indexer.index_repositories.return_value = mock_stats
        mock_indexer_class.return_value = mock_indexer
        
        exit_code = await run_indexing()
        
        # Should return 1 due to errors
        assert exit_code == 1
        mock_indexer.index_repositories.assert_called_once()


@pytest.mark.asyncio
async def test_run_indexing_exception(test_db):
    """Test indexing run with exception."""
    with patch('app.cli.IndexingService') as mock_indexer_class, \
         patch('app.cli.get_db_session', return_value=test_db):
        
        mock_indexer = AsyncMock()
        mock_indexer.index_repositories.side_effect = Exception("Test error")
        mock_indexer_class.return_value = mock_indexer
        
        exit_code = await run_indexing()
        
        # Should return 1 due to exception
        assert exit_code == 1


def test_main_no_args():
    """Test CLI main with no arguments."""
    with patch('sys.argv', ['cli.py']), \
         pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_main_unknown_command():
    """Test CLI main with unknown command."""
    with patch('sys.argv', ['cli.py', 'unknown']), \
         pytest.raises(SystemExit) as exc_info:
        main()
    
    assert exc_info.value.code == 1


def test_main_index_now_command():
    """Test CLI main with index-now command."""
    mock_stats = {
        "repositories_found": 5,
        "repositories_indexed": 5,
        "automations_indexed": 20,
        "errors": 0
    }
    
    with patch('sys.argv', ['cli.py', 'index-now']), \
         patch('app.cli.IndexingService') as mock_indexer_class, \
         patch('app.cli.get_db_session'), \
         pytest.raises(SystemExit) as exc_info:
        
        mock_indexer = AsyncMock()
        mock_indexer.index_repositories.return_value = mock_stats
        mock_indexer_class.return_value = mock_indexer
        
        main()
    
    # Should exit with 0 for success
    assert exc_info.value.code == 0


def test_get_db_session_default():
    """Test database session creation with default URL."""
    with patch.dict(os.environ, {}, clear=True):
        with patch('app.cli.create_engine') as mock_engine:
            get_db_session()
            mock_engine.assert_called_once_with("sqlite:///./data/hadiscover.db", connect_args={"check_same_thread": False})


def test_get_db_session_custom_url():
    """Test database session creation with custom URL."""
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///custom.db"}):
        with patch('app.cli.create_engine') as mock_engine:
            get_db_session()
            mock_engine.assert_called_once_with("sqlite:///custom.db", connect_args={"check_same_thread": False})
