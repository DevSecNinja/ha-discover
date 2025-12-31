"""Indexing service for discovering and storing Home Assistant automations."""

import logging
from datetime import datetime
from typing import List

import httpx
from app.models.database import Automation, IndexingMetadata, Repository
from app.services.github_service import GitHubRateLimitError, GitHubService
from app.services.parser import AutomationParser
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing Home Assistant automations from GitHub repositories."""

    def __init__(self, github_token: str = None):
        """Initialize indexing service with GitHub API access."""
        self.github_service = GitHubService(token=github_token)
        self.parser = AutomationParser()

    async def index_repositories(self, db: Session) -> dict:
        """
        Discover and index all repositories with hadiscover topic.

        Args:
            db: Database session

        Returns:
            Dictionary with indexing statistics
        """
        stats = {
            "repositories_found": 0,
            "repositories_indexed": 0,
            "automations_indexed": 0,
            "errors": 0,
            "rate_limited": False,
        }

        try:
            # Search for repositories
            repositories = await self.github_service.search_repositories()
            stats["repositories_found"] = len(repositories)

            # Index each repository
            for repo_data in repositories:
                try:
                    result = await self._index_repository(db, repo_data)
                    if result["success"]:
                        stats["repositories_indexed"] += 1
                        stats["automations_indexed"] += result["automations_count"]
                    else:
                        stats["errors"] += 1
                except GitHubRateLimitError as e:
                    logger.warning(
                        f"Rate limit hit while indexing repository {repo_data['owner']}/{repo_data['name']}: {e}"
                    )
                    stats["rate_limited"] = True
                    stats["errors"] += 1
                    # Stop indexing when rate limited
                    break
                except Exception as e:
                    logger.error(
                        f"Error indexing repository {repo_data['owner']}/{repo_data['name']}: {e}"
                    )
                    stats["errors"] += 1

            # Only store completion timestamp if indexing was not rate limited
            if not stats["rate_limited"]:
                self._store_completion_timestamp(db)
                # Also fetch and store hadiscover repo star count
                await self._store_repo_star_count(db)
                logger.info("Indexing completed successfully")
            else:
                logger.warning(
                    "Indexing halted due to rate limiting. Completion timestamp not stored."
                )

            logger.info(f"Indexing stats: {stats}")

        except GitHubRateLimitError as e:
            logger.error(f"Rate limit hit during repository search: {e}")
            stats["rate_limited"] = True
            stats["errors"] += 1
        except Exception as e:
            logger.error(f"Error in indexing process: {e}")
            stats["errors"] += 1

        return stats

    def _store_completion_timestamp(self, db: Session) -> None:
        """
        Store the completion timestamp of a successful indexing run.

        Args:
            db: Database session
        """
        try:
            # Check if metadata record exists
            metadata = (
                db.query(IndexingMetadata).filter_by(key="last_completed_at").first()
            )

            current_time = datetime.utcnow()

            if metadata:
                # Update existing record
                metadata.value = current_time.isoformat() + "Z"
                metadata.updated_at = current_time
            else:
                # Create new record
                metadata = IndexingMetadata(
                    key="last_completed_at",
                    value=current_time.isoformat() + "Z",
                    updated_at=current_time,
                )
                db.add(metadata)

            db.commit()
            logger.info(
                f"Stored indexing completion timestamp: {current_time.isoformat()}"
            )
        except Exception as e:
            logger.error(f"Error storing completion timestamp: {e}")
            db.rollback()

    async def _store_repo_star_count(self, db: Session) -> None:
        """
        Fetch and store the hadiscover repository star count.

        Args:
            db: Database session
        """
        try:
            async with httpx.AsyncClient() as client:
                url = f"{self.github_service.BASE_URL}/repos/DevSecNinja/hadiscover"
                response = await client.get(
                    url, headers=self.github_service.headers, timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    star_count = data.get("stargazers_count", 0)

                    # Check if metadata record exists
                    metadata = (
                        db.query(IndexingMetadata)
                        .filter_by(key="repo_star_count")
                        .first()
                    )

                    current_time = datetime.utcnow()

                    if metadata:
                        # Update existing record
                        metadata.value = str(star_count)
                        metadata.updated_at = current_time
                    else:
                        # Create new record
                        metadata = IndexingMetadata(
                            key="repo_star_count",
                            value=str(star_count),
                            updated_at=current_time,
                        )
                        db.add(metadata)

                    db.commit()
                    logger.info(f"Stored repository star count: {star_count}")
                else:
                    logger.warning(
                        f"Failed to fetch repo star count. Status: {response.status_code}"
                    )
        except Exception as e:
            logger.error(f"Error storing repo star count: {e}")
            db.rollback()

    async def _index_repository(self, db: Session, repo_data: dict) -> dict:
        """
        Index a single repository.

        Args:
            db: Database session
            repo_data: Repository metadata from GitHub

        Returns:
            Dictionary with indexing result
        """
        result = {"success": False, "automations_count": 0}

        owner = repo_data["owner"]
        name = repo_data["name"]
        url = repo_data["url"]
        branch = repo_data.get("default_branch", "main")

        try:
            # Check if repository already exists
            existing_repo = db.query(Repository).filter_by(url=url).first()

            if existing_repo:
                # Update existing repository
                repository = existing_repo
                repository.description = repo_data.get("description", "")
                logger.info(f"Updating existing repository: {owner}/{name}")

                # Remove old automations to re-index
                for automation in repository.automations:
                    db.delete(automation)
            else:
                # Create new repository
                repository = Repository(
                    name=name,
                    owner=owner,
                    description=repo_data.get("description", ""),
                    url=url,
                )
                db.add(repository)
                logger.info(f"Adding new repository: {owner}/{name}")

            # Flush to get repository ID without committing
            # This allows us to rollback if rate limiting occurs
            db.flush()

            # Find automation files
            automation_files = await self.github_service.find_automation_files(
                owner, name, branch
            )

            if not automation_files:
                logger.warning(f"No automation files found in {owner}/{name}")
                # Commit the repository even if no automations found
                db.commit()
                result["success"] = True  # Still consider it successful
                return result

            # Process each automation file
            for file_path in automation_files:
                content = await self.github_service.get_file_content(
                    owner, name, file_path, branch
                )

                if not content:
                    logger.warning(
                        f"Could not fetch content for {owner}/{name}/{file_path}"
                    )
                    continue

                # Parse automations
                automations = self.parser.parse_automation_file(content)

                # Store automations
                for auto_data in automations:
                    automation = Automation(
                        alias=auto_data.get("alias"),
                        description=auto_data.get("description"),
                        trigger_types=",".join(auto_data.get("trigger_types", [])),
                        blueprint_path=auto_data.get("blueprint_path"),
                        action_calls=",".join(auto_data.get("action_calls", [])),
                        source_file_path=file_path,
                        github_url=f"{url}/blob/{branch}/{file_path}",
                        start_line=auto_data.get("start_line"),
                        end_line=auto_data.get("end_line"),
                        repository_id=repository.id,
                    )
                    db.add(automation)
                    result["automations_count"] += 1

            # Only commit if all GitHub API calls succeeded
            db.commit()
            result["success"] = True
            logger.info(
                f"Indexed {result['automations_count']} automations from {owner}/{name}"
            )

        except GitHubRateLimitError:
            # Propagate rate limit errors to halt indexing
            db.rollback()
            raise
        except Exception as e:
            logger.error(f"Error indexing repository {owner}/{name}: {e}")
            db.rollback()
            result["success"] = False

        return result
