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
        start_line=10,
        end_line=25,
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


def test_search_by_action_calls(test_db):
    """Test searching automations by action calls."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation1 = Automation(
        alias="Turn on lights",
        description="Turns on lights when motion detected",
        trigger_types="state",
        action_calls="light.turn_on,notify.mobile_app",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Climate control",
        description="Controls climate",
        trigger_types="time",
        action_calls="climate.set_temperature",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.commit()

    # Search for "light"
    results = SearchService.search_automations(test_db, "light", limit=10)
    assert len(results) == 1
    assert results[0]["alias"] == "Turn on lights"

    # Search for "climate"
    results = SearchService.search_automations(test_db, "climate", limit=10)
    assert len(results) == 1
    assert results[0]["alias"] == "Climate control"


def test_filter_by_action(test_db):
    """Test filtering automations by action call."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation1 = Automation(
        alias="Light automation",
        description="Controls lights",
        trigger_types="state",
        action_calls="light.turn_on,light.turn_off",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Notification automation",
        description="Sends notifications",
        trigger_types="state",
        action_calls="notify.mobile_app",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.commit()

    # Filter by light action
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="light.turn_on"
    )
    assert len(results) == 1
    assert results[0]["alias"] == "Light automation"

    # Filter by notify action
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="notify.mobile_app"
    )
    assert len(results) == 1
    assert results[0]["alias"] == "Notification automation"


def test_get_action_facets(test_db):
    """Test getting action facets."""
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
        action_calls="light.turn_on,notify.mobile_app",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Auto2",
        description="Test",
        trigger_types="time",
        action_calls="light.turn_on,climate.set_temperature",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.commit()

    facets = SearchService.get_facets(test_db)

    # Check that actions facets are present
    assert "actions" in facets
    assert len(facets["actions"]) > 0

    # light.turn_on should appear twice
    light_facet = next(
        (f for f in facets["actions"] if f["call"] == "light.turn_on"), None
    )
    assert light_facet is not None
    assert light_facet["count"] == 2

    # notify.mobile_app and climate.set_temperature should each appear once
    notify_facet = next(
        (f for f in facets["actions"] if f["call"] == "notify.mobile_app"), None
    )
    climate_facet = next(
        (f for f in facets["actions"] if f["call"] == "climate.set_temperature"), None
    )
    assert notify_facet is not None
    assert notify_facet["count"] == 1
    assert climate_facet is not None
    assert climate_facet["count"] == 1


def test_combined_filters_with_action(test_db):
    """Test combining action filter with other filters."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    automation1 = Automation(
        alias="Light state trigger",
        description="Light automation with state trigger",
        trigger_types="state",
        action_calls="light.turn_on",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Light time trigger",
        description="Light automation with time trigger",
        trigger_types="time",
        action_calls="light.turn_on",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation3 = Automation(
        alias="Climate state trigger",
        description="Climate automation",
        trigger_types="state",
        action_calls="climate.set_temperature",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.add(automation3)
    test_db.commit()

    # Filter by action + trigger
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="light.turn_on", trigger_filter="state"
    )
    assert len(results) == 1
    assert results[0]["alias"] == "Light state trigger"

    # Filter by action only
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="light.turn_on"
    )
    assert len(results) == 2


def test_action_filter_exact_match(test_db):
    """Test that action filter matches exact action names, not substrings."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    # Create automations with similar action names
    automation1 = Automation(
        alias="Turn on light",
        description="Basic light control",
        trigger_types="state",
        action_calls="light.turn_on",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Turn on light with brightness",
        description="Advanced light control",
        trigger_types="state",
        action_calls="light.turn_on_brightness",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation3 = Automation(
        alias="Multiple actions including turn_on",
        description="Combined actions",
        trigger_types="state",
        action_calls="notify.mobile_app,light.turn_on,switch.turn_off",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.add(automation3)
    test_db.commit()

    # Filter by "light.turn_on" should match only exact matches
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="light.turn_on"
    )
    assert len(results) == 2
    aliases = {r["alias"] for r in results}
    assert "Turn on light" in aliases
    assert "Multiple actions including turn_on" in aliases
    assert "Turn on light with brightness" not in aliases

    # Filter by "light.turn_on_brightness" should match only that exact action
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="light.turn_on_brightness"
    )
    assert len(results) == 1
    assert results[0]["alias"] == "Turn on light with brightness"


def test_trigger_filter_exact_match(test_db):
    """Test that trigger filter matches exact trigger names, not substrings."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    # Create automations with similar trigger names
    automation1 = Automation(
        alias="State trigger",
        description="State based",
        trigger_types="state",
        action_calls="light.turn_on",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="Numeric state trigger",
        description="Numeric state based",
        trigger_types="numeric_state",
        action_calls="light.turn_on",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation3 = Automation(
        alias="Multiple triggers",
        description="Combined triggers",
        trigger_types="state,time,zone",
        action_calls="light.turn_on",
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.add(automation3)
    test_db.commit()

    # Filter by "state" should match only exact matches
    results = SearchService.search_automations(
        test_db, "", limit=10, trigger_filter="state"
    )
    assert len(results) == 2
    aliases = {r["alias"] for r in results}
    assert "State trigger" in aliases
    assert "Multiple triggers" in aliases
    assert "Numeric state trigger" not in aliases

    # Filter by "numeric_state" should match only that exact trigger
    results = SearchService.search_automations(
        test_db, "", limit=10, trigger_filter="numeric_state"
    )
    assert len(results) == 1
    assert results[0]["alias"] == "Numeric state trigger"


def test_action_filter_with_sql_wildcards(test_db):
    """Test that SQL wildcard characters in filter values are properly escaped."""
    repo = Repository(
        name="test-repo",
        owner="testuser",
        description="Test repository",
        url="https://github.com/testuser/test-repo",
    )
    test_db.add(repo)
    test_db.commit()

    # Create automations with action names containing SQL wildcard characters
    automation1 = Automation(
        alias="Underscore action",
        description="Action with underscore",
        trigger_types="state",
        action_calls="light_turn_on",  # Contains underscore
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation2 = Automation(
        alias="No underscore action",
        description="Action without underscore",
        trigger_types="state",
        action_calls="lightXturn_on",  # X instead of underscore at first position
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation3 = Automation(
        alias="Percent action",
        description="Action with percent",
        trigger_types="state",
        action_calls="light%turn",  # Contains percent
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    automation4 = Automation(
        alias="Normal action",
        description="Normal action name",
        trigger_types="state",
        action_calls="light.turn.on",  # Normal dots, no wildcards
        source_file_path="automations.yaml",
        github_url="https://github.com/testuser/test-repo/blob/main/automations.yaml",
        repository_id=repo.id,
    )
    test_db.add(automation1)
    test_db.add(automation2)
    test_db.add(automation3)
    test_db.add(automation4)
    test_db.commit()

    # Filter by "light_turn_on" should match only exact underscore, not treat _ as wildcard
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="light_turn_on"
    )
    assert len(results) == 1
    assert results[0]["alias"] == "Underscore action"

    # Filter by "light%turn" should match only exact percent, not treat % as wildcard
    results = SearchService.search_automations(
        test_db, "", limit=10, action_filter="light%turn"
    )
    assert len(results) == 1
    assert results[0]["alias"] == "Percent action"
