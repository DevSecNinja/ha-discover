"""CLI commands for hadiscover backend."""

import asyncio
import logging
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.indexer import IndexingService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_db_session():
    """Create a database session."""
    db_url = os.getenv("DATABASE_URL", "sqlite:///./data/hadiscover.db")
    engine = create_engine(
        db_url, connect_args={"check_same_thread": False} if "sqlite" in db_url else {}
    )

    # Initialize database tables on this engine
    from app.models.database import Base

    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


async def run_indexing():
    """Run the indexing process once and exit."""
    logger.info("Starting indexing job...")

    # Get GitHub token from environment
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        logger.warning("GITHUB_TOKEN not set - API rate limits will be lower")

    # Create indexing service
    indexer = IndexingService(github_token=github_token)

    # Get database session (this also initializes the database)
    db = get_db_session()

    try:
        # Run indexing
        stats = await indexer.index_repositories(db)

        logger.info("Indexing completed successfully")
        logger.info(f"Statistics: {stats}")

        # Return appropriate exit code
        if stats["errors"] > 0:
            logger.warning(f"Indexing completed with {stats['errors']} errors")
            return 1
        return 0

    except Exception as e:
        logger.error(f"Indexing failed: {e}", exc_info=True)
        return 1
    finally:
        db.close()


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m app.cli <command>")
        print("Commands:")
        print("  index-now    Run indexing once and exit")
        sys.exit(1)

    command = sys.argv[1]

    if command == "index-now":
        exit_code = asyncio.run(run_indexing())
        sys.exit(exit_code)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
