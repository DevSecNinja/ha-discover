"""Test fixtures and configuration."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.database import Base

# Sample Home Assistant automation YAML for testing
SAMPLE_AUTOMATION_YAML = """
- alias: "Motion Activated Light"
  description: "Turn on light when motion is detected"
  trigger:
    - platform: state
      entity_id: binary_sensor.motion_sensor
      to: 'on'
  action:
    - service: light.turn_on
      target:
        entity_id: light.living_room

- alias: "Temperature Alert"
  description: "Send notification when temperature is too high"
  trigger:
    - platform: numeric_state
      entity_id: sensor.temperature
      above: 30
  action:
    - service: notify.mobile_app
      data:
        message: "Temperature is too high!"

- alias: "Daily Backup"
  trigger:
    - platform: time
      at: "02:00:00"
  action:
    - service: hassio.backup_full
"""

SAMPLE_AUTOMATION_SINGLE = """
alias: "Simple Automation"
description: "A simple test automation"
trigger:
  platform: state
  entity_id: switch.test
action:
  service: light.toggle
"""


@pytest.fixture
def test_db():
    """Create a test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_repo_data():
    """Sample repository data for testing."""
    return {
        "name": "home-assistant-config",
        "owner": "testuser",
        "description": "My Home Assistant configuration",
        "url": "https://github.com/testuser/home-assistant-config",
        "default_branch": "main",
    }
