"""Database models for hadiscover."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Repository(Base):
    """Represents a GitHub repository with Home Assistant automations."""

    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    owner = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    url = Column(String(512), nullable=False, unique=True)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to automations
    automations = relationship(
        "Automation", back_populates="repository", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Repository(owner='{self.owner}', name='{self.name}')>"


class Automation(Base):
    """Represents a Home Assistant automation from a repository."""

    __tablename__ = "automations"

    id = Column(Integer, primary_key=True, index=True)
    alias = Column(String(512), nullable=True, index=True)
    description = Column(Text, nullable=True)
    trigger_types = Column(Text, nullable=True)  # Stored as comma-separated values
    # Note: blueprint_path and action_calls are new fields. Existing databases will need
    # to handle NULL values gracefully. SQLite automatically allows NULL for new columns.
    blueprint_path = Column(
        String(512), nullable=True, index=True
    )  # Blueprint path if using blueprint
    action_calls = Column(
        Text, nullable=True
    )  # Stored as comma-separated service calls
    source_file_path = Column(String(512), nullable=False)
    github_url = Column(String(1024), nullable=False)
    repository_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    indexed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to repository
    repository = relationship("Repository", back_populates="automations")

    def __repr__(self):
        return f"<Automation(alias='{self.alias}', repo_id={self.repository_id})>"


class IndexingMetadata(Base):
    """Tracks metadata about indexing operations."""

    __tablename__ = "indexing_metadata"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), nullable=False, unique=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<IndexingMetadata(key='{self.key}', value='{self.value}')>"
