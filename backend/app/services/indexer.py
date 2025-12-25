"""Indexing service for discovering and storing Home Assistant automations."""
import logging
from typing import List
from sqlalchemy.orm import Session

from app.models.database import Repository, Automation
from app.services.github_service import GitHubService
from app.services.parser import AutomationParser

logger = logging.getLogger(__name__)


class IndexingService:
    """Service for indexing Home Assistant automations from GitHub repositories."""
    
    def __init__(self, github_token: str = None):
        """Initialize indexing service with GitHub API access."""
        self.github_service = GitHubService(token=github_token)
        self.parser = AutomationParser()
    
    async def index_repositories(self, db: Session) -> dict:
        """
        Discover and index all repositories with ha-discover topic.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with indexing statistics
        """
        stats = {
            "repositories_found": 0,
            "repositories_indexed": 0,
            "automations_indexed": 0,
            "errors": 0
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
                except Exception as e:
                    logger.error(f"Error indexing repository {repo_data['owner']}/{repo_data['name']}: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Indexing complete: {stats}")
            
        except Exception as e:
            logger.error(f"Error in indexing process: {e}")
            stats["errors"] += 1
        
        return stats
    
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
                    url=url
                )
                db.add(repository)
                logger.info(f"Adding new repository: {owner}/{name}")
            
            # Commit to get repository ID
            db.commit()
            db.refresh(repository)
            
            # Find automation files
            automation_files = await self.github_service.find_automation_files(owner, name, branch)
            
            if not automation_files:
                logger.warning(f"No automation files found in {owner}/{name}")
                result["success"] = True  # Still consider it successful
                return result
            
            # Process each automation file
            for file_path in automation_files:
                content = await self.github_service.get_file_content(owner, name, file_path, branch)
                
                if not content:
                    logger.warning(f"Could not fetch content for {owner}/{name}/{file_path}")
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
                        repository_id=repository.id
                    )
                    db.add(automation)
                    result["automations_count"] += 1
            
            db.commit()
            result["success"] = True
            logger.info(f"Indexed {result['automations_count']} automations from {owner}/{name}")
            
        except Exception as e:
            logger.error(f"Error indexing repository {owner}/{name}: {e}")
            db.rollback()
            result["success"] = False
        
        return result
