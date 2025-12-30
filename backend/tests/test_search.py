"""Tests for search service."""

import pytest
from app.models.database import Repository, Automation
from app.services.search_service import SearchService


def test_search_by_alias(test_db):
    """Test searching automations by alias."""
    # Add test data
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation1 = Automation(
        alias="Light Control",
        description="Controls living room light",
        trigger_types="state",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Temperature Monitor",
        description="Monitors temperature",
        trigger_types="numeric_state",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.commit()

    # Search for "Light"
    results = SearchService.search_automations(test_db, "Light", limit=10)

    assert len(results) == 1
    assert results[0]["alias"] == "Light Control"


def test_search_by_description(test_db):
    """Test searching automations by description."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation = Automation(
        alias="Test Automation",
        description="This automation monitors temperature sensors",
        trigger_types="state",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation)
    test_db.commit()

    results = SearchService.search_automations(test_db, "temperature", limit=10)

    assert len(results) == 1
    assert "temperature" in results[0]["description"].lower()


def test_search_case_insensitive(test_db):
    """Test that search is case insensitive."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation = Automation(
        alias="MOTION SENSOR",
        description="Detects motion",
        trigger_types="state",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation)
    test_db.commit()

    # Search with lowercase
    results = SearchService.search_automations(test_db, "motion", limit=10)
    assert len(results) == 1

    # Search with uppercase
    results = SearchService.search_automations(test_db, "SENSOR", limit=10)
    assert len(results) == 1


def test_search_empty_query(test_db):
    """Test search with empty query returns recent automations."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation = Automation(
        alias="Test",
        description="Test automation",
        trigger_types="state",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation)
    test_db.commit()

    results = SearchService.search_automations(test_db, "", limit=10)
    assert len(results) == 1


def test_search_no_results(test_db):
    """Test search with no matching results."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation = Automation(
        alias="Test",
        description="Test automation",
        trigger_types="state",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation)
    test_db.commit()

    results = SearchService.search_automations(test_db, "nonexistent", limit=10)
    assert len(results) == 0


def test_get_statistics(test_db):
    """Test getting statistics."""
    # Add test data
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation1 = Automation(
        alias="Auto1",
        description="Test",
        trigger_types="state",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Auto2",
        description="Test",
        trigger_types="time",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.commit()

    stats = SearchService.get_statistics(test_db)

    assert stats["total_repositories"] == 1
    assert stats["total_automations"] == 2


def test_search_result_format(test_db):
    """Test that search results have correct format."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation = Automation(
        alias="Test Automation",
        description="Test description",
        trigger_types="state,time",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation)
    test_db.commit()

    results = SearchService.search_automations(test_db, "test", limit=10)

    assert len(results) == 1
    result = results[0]

    # Check result structure
    assert "id" in result
    assert "alias" in result
    assert "description" in result
    assert "trigger_types" in result
    assert "source_file_path" in result
    assert "github_url" in result
    assert "repository" in result
    assert "indexed_at" in result

    # Check repository structure
    assert "name" in result["repository"]
    assert "owner" in result["repository"]
    assert "description" in result["repository"]
    assert "url" in result["repository"]

    # Check trigger types are parsed
    assert isinstance(result["trigger_types"], list)
    assert len(result["trigger_types"]) == 2
