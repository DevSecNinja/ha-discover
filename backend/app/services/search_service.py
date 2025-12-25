"""Search service for querying Home Assistant automations."""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.database import Automation, Repository

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching Home Assistant automations."""
    
    @staticmethod
    def search_automations(db: Session, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search automations by text query across multiple fields.
        
        Args:
            db: Database session
            query: Search query string
            limit: Maximum number of results to return
            
        Returns:
            List of automation results with repository information
        """
        if not query:
            # Return recent automations if no query
            return SearchService._get_recent_automations(db, limit)
        
        try:
            # Perform case-insensitive search across multiple fields
            search_pattern = f"%{query}%"
            
            results = db.query(Automation, Repository).join(
                Repository, Automation.repository_id == Repository.id
            ).filter(
                or_(
                    func.lower(Automation.alias).like(func.lower(search_pattern)),
                    func.lower(Automation.description).like(func.lower(search_pattern)),
                    func.lower(Automation.trigger_types).like(func.lower(search_pattern)),
                    func.lower(Repository.name).like(func.lower(search_pattern)),
                    func.lower(Repository.description).like(func.lower(search_pattern))
                )
            ).limit(limit).all()
            
            # Format results
            formatted_results = []
            for automation, repository in results:
                formatted_results.append({
                    "id": automation.id,
                    "alias": automation.alias,
                    "description": automation.description,
                    "trigger_types": automation.trigger_types.split(",") if automation.trigger_types else [],
                    "blueprint_path": automation.blueprint_path,
                    "action_calls": automation.action_calls.split(",") if automation.action_calls else [],
                    "source_file_path": automation.source_file_path,
                    "github_url": automation.github_url,
                    "repository": {
                        "name": repository.name,
                        "owner": repository.owner,
                        "description": repository.description,
                        "url": repository.url
                    },
                    "indexed_at": automation.indexed_at.isoformat() if automation.indexed_at else None
                })
            
            logger.info(f"Search query '{query}' returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching automations: {e}")
            return []
    
    @staticmethod
    def _get_recent_automations(db: Session, limit: int) -> List[Dict[str, Any]]:
        """
        Get most recently indexed automations.
        
        Args:
            db: Database session
            limit: Maximum number of results
            
        Returns:
            List of recent automations
        """
        try:
            results = db.query(Automation, Repository).join(
                Repository, Automation.repository_id == Repository.id
            ).order_by(Automation.indexed_at.desc()).limit(limit).all()
            
            formatted_results = []
            for automation, repository in results:
                formatted_results.append({
                    "id": automation.id,
                    "alias": automation.alias,
                    "description": automation.description,
                    "trigger_types": automation.trigger_types.split(",") if automation.trigger_types else [],
                    "blueprint_path": automation.blueprint_path,
                    "action_calls": automation.action_calls.split(",") if automation.action_calls else [],
                    "source_file_path": automation.source_file_path,
                    "github_url": automation.github_url,
                    "repository": {
                        "name": repository.name,
                        "owner": repository.owner,
                        "description": repository.description,
                        "url": repository.url
                    },
                    "indexed_at": automation.indexed_at.isoformat() if automation.indexed_at else None
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error getting recent automations: {e}")
            return []
    
    @staticmethod
    def get_statistics(db: Session) -> Dict[str, int]:
        """
        Get statistics about indexed data.
        
        Args:
            db: Database session
            
        Returns:
            Dictionary with statistics
        """
        try:
            repo_count = db.query(func.count(Repository.id)).scalar()
            automation_count = db.query(func.count(Automation.id)).scalar()
            
            return {
                "total_repositories": repo_count or 0,
                "total_automations": automation_count or 0
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "total_repositories": 0,
                "total_automations": 0
            }
