"""Tests for automation parser."""
import pytest
from app.services.parser import AutomationParser
from tests.conftest import SAMPLE_AUTOMATION_YAML, SAMPLE_AUTOMATION_SINGLE


def test_parse_automation_list():
    """Test parsing a list of automations."""
    parser = AutomationParser()
    automations = parser.parse_automation_file(SAMPLE_AUTOMATION_YAML)
    
    assert len(automations) == 3
    
    # Check first automation
    assert automations[0]["alias"] == "Motion Activated Light"
    assert "motion is detected" in automations[0]["description"]
    assert "state" in automations[0]["trigger_types"]
    
    # Check second automation
    assert automations[1]["alias"] == "Temperature Alert"
    assert "numeric_state" in automations[1]["trigger_types"]
    
    # Check third automation
    assert automations[2]["alias"] == "Daily Backup"
    assert "time" in automations[2]["trigger_types"]


def test_parse_single_automation():
    """Test parsing a single automation dict."""
    parser = AutomationParser()
    automations = parser.parse_automation_file(SAMPLE_AUTOMATION_SINGLE)
    
    assert len(automations) == 1
    assert automations[0]["alias"] == "Simple Automation"
    assert automations[0]["description"] == "A simple test automation"
    assert "state" in automations[0]["trigger_types"]


def test_parse_empty_yaml():
    """Test parsing empty YAML."""
    parser = AutomationParser()
    automations = parser.parse_automation_file("")
    
    assert len(automations) == 0


def test_parse_invalid_yaml():
    """Test parsing invalid YAML."""
    parser = AutomationParser()
    invalid_yaml = "this is not valid: yaml: content::"
    automations = parser.parse_automation_file(invalid_yaml)
    
    assert len(automations) == 0


def test_parse_automation_without_alias():
    """Test parsing automation without alias."""
    yaml_without_alias = """
- description: "Automation without alias"
  trigger:
    platform: state
    entity_id: sensor.test
  action:
    service: light.turn_on
"""
    parser = AutomationParser()
    automations = parser.parse_automation_file(yaml_without_alias)
    
    assert len(automations) == 1
    assert automations[0]["alias"] is None
    assert automations[0]["description"] == "Automation without alias"


def test_parse_multiple_triggers():
    """Test parsing automation with multiple triggers."""
    yaml_multi_trigger = """
alias: "Multi Trigger"
trigger:
  - platform: state
    entity_id: sensor.test1
  - platform: time
    at: "12:00:00"
  - platform: numeric_state
    entity_id: sensor.temp
    above: 25
action:
  service: notify.notify
"""
    parser = AutomationParser()
    automations = parser.parse_automation_file(yaml_multi_trigger)
    
    assert len(automations) == 1
    assert len(automations[0]["trigger_types"]) == 3
    assert "state" in automations[0]["trigger_types"]
    assert "time" in automations[0]["trigger_types"]
    assert "numeric_state" in automations[0]["trigger_types"]


def test_extract_trigger_types_with_dict():
    """Test extracting trigger types from a dict trigger."""
    trigger = {"platform": "state", "entity_id": "sensor.test"}
    result = AutomationParser._extract_trigger_types(trigger)
    
    assert len(result) == 1
    assert "state" in result


def test_extract_trigger_types_with_list():
    """Test extracting trigger types from a list of triggers."""
    triggers = [
        {"platform": "state"},
        {"platform": "time"},
        {"platform": "state"}  # Duplicate
    ]
    result = AutomationParser._extract_trigger_types(triggers)
    
    assert len(result) == 2  # Duplicates removed
    assert "state" in result
    assert "time" in result


def test_parse_blueprint_automation():
    """Test parsing automation that uses a blueprint."""
    yaml_with_blueprint = """
alias: "Blueprint Based Automation"
use_blueprint:
  path: homeassistant/motion_light.yaml
  input:
    motion_entity: binary_sensor.motion
    light_entity: light.living_room
"""
    parser = AutomationParser()
    automations = parser.parse_automation_file(yaml_with_blueprint)
    
    assert len(automations) == 1
    assert automations[0]["alias"] == "Blueprint Based Automation"
    assert automations[0]["blueprint_path"] == "homeassistant/motion_light.yaml"
    assert automations[0]["blueprint_input"] is not None


def test_extract_action_calls():
    """Test extracting service calls from actions."""
    yaml_with_actions = """
alias: "Test Actions"
trigger:
  platform: state
  entity_id: sensor.test
action:
  - service: light.turn_on
    entity_id: light.living_room
  - service: notify.notify
    data:
      message: "Test"
  - service: media_player.media_pause
"""
    parser = AutomationParser()
    automations = parser.parse_automation_file(yaml_with_actions)
    
    assert len(automations) == 1
    assert len(automations[0]["action_calls"]) == 3
    assert "light.turn_on" in automations[0]["action_calls"]
    assert "notify.notify" in automations[0]["action_calls"]
    assert "media_player.media_pause" in automations[0]["action_calls"]


def test_extract_nested_action_calls():
    """Test extracting service calls from nested actions (choose, if/then)."""
    yaml_with_nested = """
alias: "Nested Actions"
trigger:
  platform: state
  entity_id: sensor.test
action:
  - choose:
      - conditions:
          - condition: state
            entity_id: sun.sun
            state: above_horizon
        sequence:
          - service: light.turn_on
      - conditions:
          - condition: state
            entity_id: sun.sun
            state: below_horizon
        sequence:
          - service: light.turn_off
    default:
      - service: notify.notify
"""
    parser = AutomationParser()
    automations = parser.parse_automation_file(yaml_with_nested)
    
    assert len(automations) == 1
    assert len(automations[0]["action_calls"]) == 3
    assert "light.turn_on" in automations[0]["action_calls"]
    assert "light.turn_off" in automations[0]["action_calls"]
    assert "notify.notify" in automations[0]["action_calls"]
