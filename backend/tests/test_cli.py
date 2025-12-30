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
        "errors": 0,
    }

    with patch("app.cli.IndexingService") as mock_indexer_class, patch(
        "app.cli.get_db_session", return_value=test_db
    ):

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
        "errors": 2,
    }

    with patch("app.cli.IndexingService") as mock_indexer_class, patch(
        "app.cli.get_db_session", return_value=test_db
    ):

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
    with patch("app.cli.IndexingService") as mock_indexer_class, patch(
        "app.cli.get_db_session", return_value=test_db
    ):

        mock_indexer = AsyncMock()
        mock_indexer.index_repositories.side_effect = Exception("Test error")
        mock_indexer_class.return_value = mock_indexer

        exit_code = await run_indexing()

        # Should return 1 due to exception
        assert exit_code == 1


def test_main_no_args():
    """Test CLI main with no arguments."""
    with patch("sys.argv", ["cli.py"]), pytest.raises(SystemExit) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_unknown_command():
    """Test CLI main with unknown command."""
    with patch("sys.argv", ["cli.py", "unknown"]), pytest.raises(
        SystemExit
    ) as exc_info:
        main()

    assert exc_info.value.code == 1


def test_main_index_now_command():
    """Test CLI main with index-now command."""
    mock_stats = {
        "repositories_found": 5,
        "repositories_indexed": 5,
        "automations_indexed": 20,
        "errors": 0,
    }

    with patch("sys.argv", ["cli.py", "index-now"]), patch(
        "app.cli.IndexingService"
    ) as mock_indexer_class, patch("app.cli.get_db_session"), pytest.raises(
        SystemExit
    ) as exc_info:

        mock_indexer = AsyncMock()
        mock_indexer.index_repositories.return_value = mock_stats
        mock_indexer_class.return_value = mock_indexer

        main()

    # Should exit with 0 for success
    assert exc_info.value.code == 0


def test_get_db_session_default():
    """Test database session creation with default URL."""
    with patch.dict(os.environ, {}, clear=True):
        with patch("app.cli.create_engine") as mock_engine:
            get_db_session()
            mock_engine.assert_called_once_with(
                "sqlite:///./data/hadiscover.db",
                connect_args={"check_same_thread": False},
            )


def test_get_db_session_custom_url():
    """Test database session creation with custom URL."""
    with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///custom.db"}):
        with patch("app.cli.create_engine") as mock_engine:
            get_db_session()
            mock_engine.assert_called_once_with(
                "sqlite:///custom.db", connect_args={"check_same_thread": False}
            )


def test_standalone_index_now_script():
    """Test that the standalone index-now script exists and is executable."""
    import subprocess
    import sys
    from pathlib import Path

    # Get the path to the backend directory
    backend_dir = Path(__file__).parent.parent
    script_path = backend_dir / "index-now"

    # Verify the script exists
    assert script_path.exists(), f"index-now script not found at {script_path}"

    # Verify it's executable (at least readable)
    assert os.access(script_path, os.R_OK), "index-now script is not readable"

    # Test that the script can be parsed as valid Python
    with open(script_path, "r") as f:
        script_content = f.read()
        # Try to compile it to check for syntax errors
        try:
            compile(script_content, str(script_path), "exec")
        except SyntaxError as e:
            pytest.fail(f"index-now script has syntax errors: {e}")

    # Verify the shebang is correct
    with open(script_path, "r") as f:
        first_line = f.readline().strip()
        assert first_line in [
            "#!/usr/bin/env python3",
            "#!/usr/bin/env python",
        ], f"Invalid shebang: {first_line}"

    # Verify key script content
    assert (
        "from app.cli import main" in script_content
    ), "Script should import main from app.cli"
    assert "sys.argv = [" in script_content, "Script should set sys.argv"
    assert "main()" in script_content, "Script should call main()"


def test_standalone_script_execution_simulation():
    """Test the standalone script logic by simulating container execution."""
    from pathlib import Path

    backend_dir = Path(__file__).parent.parent
    script_path = backend_dir / "index-now"

    # Read and verify script behavior
    with open(script_path, "r") as f:
        script_lines = f.readlines()

    # Check the script logic for container path detection
    script_content = "".join(script_lines)

    # Verify it handles /usr/local/bin path (container scenario)
    assert (
        "/usr/local/bin" in script_content
    ), "Script should handle container path /usr/local/bin"
    assert (
        "app_dir = '/app'" in script_content
    ), "Script should use /app directory in container"

    # Verify it changes directory
    assert (
        "os.chdir(app_dir)" in script_content
    ), "Script should change to app directory"

    # Verify it adds to Python path
    assert (
        "sys.path.insert(0, app_dir)" in script_content
    ), "Script should add app_dir to Python path"
