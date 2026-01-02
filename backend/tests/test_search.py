"""Tests for search service."""

from app.models.database import Automation, Repository
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
    results, total = SearchService.search_automations(test_db, "Light", page=1, per_page=10)

    assert len(results) == 1
    assert total == 1
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

    results, total = SearchService.search_automations(test_db, "temperature", page=1, per_page=10)

    assert len(results) == 1
    assert total == 1
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
    results, total = SearchService.search_automations(test_db, "motion", page=1, per_page=10)
    assert len(results) == 1
    assert total == 1

    # Search with uppercase
    results, total = SearchService.search_automations(test_db, "SENSOR", page=1, per_page=10)
    assert len(results) == 1
    assert total == 1


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

    results, total = SearchService.search_automations(test_db, "", page=1, per_page=10)
    assert len(results) == 1
    assert total == 1


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

    results, total = SearchService.search_automations(test_db, "nonexistent", page=1, per_page=10)
    assert len(results) == 0
    assert total == 0


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
        start_line=10,
        end_line=25,
        repository_id=repo.id,
    )
    test_db.add(automation)
    test_db.commit()

    results, total = SearchService.search_automations(test_db, "test", page=1, per_page=10)

    assert len(results) == 1
    assert total == 1
    result = results[0]

    # Check result structure
    assert "id" in result
    assert "alias" in result
    assert "description" in result
    assert "trigger_types" in result
    assert "source_file_path" in result
    assert "github_url" in result
    assert "start_line" in result
    assert "end_line" in result
    assert "repository" in result
    assert "indexed_at" in result

    # Check line numbers
    assert result["start_line"] == 10
    assert result["end_line"] == 25

    # Check repository structure
    assert "name" in result["repository"]
    assert "owner" in result["repository"]
    assert "description" in result["repository"]
    assert "url" in result["repository"]

    # Check trigger types are parsed
    assert isinstance(result["trigger_types"], list)
    assert len(result["trigger_types"]) == 2


def test_pagination_first_page(test_db):
    """Test pagination first page."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    # Create 35 automations
    for i in range(35):
        automation = Automation(
            alias=f"Automation {i}",
            description="Test description",
            trigger_types="state",
            source_file_path="automations.yaml",
            github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
            repository_id=repo.id,
        )
        test_db.add(automation)
    test_db.commit()

    # Get first page with 30 results
    results, total = SearchService.search_automations(test_db, "", page=1, per_page=30)
    
    assert len(results) == 30
    assert total == 35


def test_pagination_second_page(test_db):
    """Test pagination second page."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    # Create 35 automations
    for i in range(35):
        automation = Automation(
            alias=f"Automation {i}",
            description="Test description",
            trigger_types="state",
            source_file_path="automations.yaml",
            github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
            repository_id=repo.id,
        )
        test_db.add(automation)
    test_db.commit()

    # Get second page with remaining 5 results
    results, total = SearchService.search_automations(test_db, "", page=2, per_page=30)
    
    assert len(results) == 5
    assert total == 35


def test_pagination_with_search_query(test_db):
    """Test pagination with search query."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    # Create 25 matching automations
    for i in range(25):
        automation = Automation(
            alias=f"Light Automation {i}",
            description="Controls lights",
            trigger_types="state",
            source_file_path="automations.yaml",
            github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
            repository_id=repo.id,
        )
        test_db.add(automation)
    
    # Create 10 non-matching automations
    for i in range(10):
        automation = Automation(
            alias=f"Temperature Automation {i}",
            description="Monitors temperature",
            trigger_types="numeric_state",
            source_file_path="automations.yaml",
            github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
            repository_id=repo.id,
        )
        test_db.add(automation)
    test_db.commit()

    # Search for "Light" - first page
    results, total = SearchService.search_automations(test_db, "Light", page=1, per_page=20)
    assert len(results) == 20
    assert total == 25
    
    # Search for "Light" - second page
    results, total = SearchService.search_automations(test_db, "Light", page=2, per_page=20)
    assert len(results) == 5
    assert total == 25


def test_pagination_out_of_range_page(test_db):
    """Test pagination with page number beyond available pages."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    # Create 25 automations
    for i in range(25):
        automation = Automation(
            alias=f"Test Automation {i}",
            description="Test description",
            trigger_types="state",
            source_file_path="automations.yaml",
            github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
            repository_id=repo.id,
        )
        test_db.add(automation)
    test_db.commit()

    # Request page 100 (well beyond the 1 page available with 30 per page)
    results, total = SearchService.search_automations(test_db, "", page=100, per_page=30)
    
    # Should return empty results but correct total count
    assert len(results) == 0
    assert total == 25
