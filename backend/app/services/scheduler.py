"""Scheduler service for running periodic background tasks."""

import asyncio
import logging
import os
from datetime import datetime

from app.services.indexer import IndexingService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled background tasks."""

    def __init__(self):
        """Initialize the scheduler service."""
        self.scheduler = AsyncIOScheduler()
        self.indexer = None
        self._setup_database()

    def _setup_database(self):
        """Set up database connection for scheduled tasks."""
        db_url = os.getenv("DATABASE_URL", "sqlite:///./data/hadiscover.db")
        self.engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def _get_db(self) -> Session:
        """Get a database session for scheduled tasks."""
        return self.SessionLocal()

    async def run_indexing_task(self):
        """Run the indexing task (called by scheduler)."""
        logger.info(f"Starting scheduled indexing at {datetime.now()}")

        # Get GitHub token from environment
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            logger.warning("GITHUB_TOKEN not set - API rate limits will be lower")

        # Create indexing service if not already created
        if not self.indexer:
            self.indexer = IndexingService(github_token=github_token)

        # Get database session
        db = self._get_db()

        try:
            # Run indexing
            stats = await self.indexer.index_repositories(db)
            logger.info(f"Scheduled indexing completed: {stats}")

        except Exception as e:
            logger.error(f"Scheduled indexing failed: {e}", exc_info=True)
        finally:
            db.close()

    def start(self):
        """Start the scheduler with hourly indexing."""
        # Add hourly indexing job
        self.scheduler.add_job(
            self.run_indexing_task,
            trigger=IntervalTrigger(hours=1),
            id="hourly_indexing",
            name="Index Home Assistant automations from GitHub",
            replace_existing=True,
            max_instances=1,  # Only one instance at a time
        )

        # Start the scheduler
        self.scheduler.start()
        logger.info("Scheduler started - indexing will run every hour")

        # Run indexing immediately on startup (optional, but recommended)
        asyncio.create_task(self.run_indexing_task())

    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down")
