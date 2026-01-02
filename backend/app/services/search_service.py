"""Search service for querying Home Assistant automations."""

import logging
from typing import Any, Dict, List, Optional

from app.models.database import Automation, IndexingMetadata, Repository
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class SearchService:
    """Service for searching Home Assistant automations."""

    @staticmethod
    def _escape_like(value: str, escape_char: str = "\\") -> str:
        """Escape SQL LIKE wildcard characters in a value."""
        # First escape the escape character itself, then '%' and '_'
        escaped = value.replace(escape_char, escape_char + escape_char)
        escaped = escaped.replace("%", escape_char + "%")
        escaped = escaped.replace("_", escape_char + "_")
        return escaped

    @staticmethod
    def _exact_match_in_comma_list(column, value: str):
        """
        Create SQL condition for exact match in comma-separated list.

        Handles these cases:
        - Single value: "value"
        - First in list: "value,..."
        - Middle of list: "...,value,..."
        - Last in list: "...,value"

        Args:
            column: SQLAlchemy column containing comma-separated values
            value: The exact value to match

        Returns:
            SQLAlchemy OR condition for exact matching
        """
        escape_char = "\\"
        escaped_value = SearchService._escape_like(value, escape_char=escape_char)

        return or_(
            column == value,  # Exact match (single value)
            column.like(f"{escaped_value},%", escape=escape_char),  # First in list
            column.like(f"%,{escaped_value},%", escape=escape_char),  # Middle of list
            column.like(f"%,{escaped_value}", escape=escape_char),  # Last in list
        )

    @staticmethod
    def search_automations(
        db: Session,
        query: str,
        limit: int = 50,
        repo_filter: Optional[str] = None,
        blueprint_filter: Optional[str] = None,
        trigger_filter: Optional[str] = None,
        action_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search automations by text query across multiple fields.

        Args:
            db: Database session
            query: Search query string
            limit: Maximum number of results to return
            repo_filter: Filter by repository (format: "owner/name")
            blueprint_filter: Filter by blueprint path
            trigger_filter: Filter by trigger type
            action_filter: Filter by action call (service name)

        Returns:
            List of automation results with repository information
        """
        if (
            not query
            and not repo_filter
            and not blueprint_filter
            and not trigger_filter
            and not action_filter
        ):
            # Return recent automations if no query or filters
            return SearchService._get_recent_automations(db, limit)

        try:
            # Build query with filters
            base_query = db.query(Automation, Repository).join(
                Repository, Automation.repository_id == Repository.id
            )

            # Apply text search if provided
            if query:
                search_pattern = f"%{query}%"
                base_query = base_query.filter(
                    or_(
                        func.lower(Automation.alias).like(func.lower(search_pattern)),
                        func.lower(Automation.description).like(
                            func.lower(search_pattern)
                        ),
                        func.lower(Automation.trigger_types).like(
                            func.lower(search_pattern)
                        ),
                        func.lower(Automation.action_calls).like(
                            func.lower(search_pattern)
                        ),
                        func.lower(Repository.owner).like(func.lower(search_pattern)),
                        func.lower(Repository.name).like(func.lower(search_pattern)),
                        func.lower(Repository.description).like(
                            func.lower(search_pattern)
                        ),
                    )
                )

            # Apply repository filter
            if repo_filter:
                # repo_filter format is "owner/name"
                if "/" in repo_filter:
                    owner, name = repo_filter.split("/", 1)
                    base_query = base_query.filter(
                        Repository.owner == owner, Repository.name == name
                    )

            # Apply blueprint filter
            if blueprint_filter:
                base_query = base_query.filter(
                    Automation.blueprint_path == blueprint_filter
                )

            # Apply trigger filter
            if trigger_filter:
                # Trigger types are stored as comma-separated, use exact match
                base_query = base_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.trigger_types, trigger_filter
                    )
                )

            # Apply action filter
            if action_filter:
                # Action calls are stored as comma-separated, use exact match
                base_query = base_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.action_calls, action_filter
                    )
                )

            results = base_query.limit(limit).all()

            # Format results
            formatted_results = []
            for automation, repository in results:
                formatted_results.append(
                    {
                        "id": automation.id,
                        "alias": automation.alias,
                        "description": automation.description,
                        "trigger_types": (
                            automation.trigger_types.split(",")
                            if automation.trigger_types
                            else []
                        ),
                        "blueprint_path": automation.blueprint_path,
                        "action_calls": (
                            automation.action_calls.split(",")
                            if automation.action_calls
                            else []
                        ),
                        "source_file_path": automation.source_file_path,
                        "github_url": automation.github_url,
                        "start_line": automation.start_line,
                        "end_line": automation.end_line,
                        "repository": {
                            "name": repository.name,
                            "owner": repository.owner,
                            "description": repository.description,
                            "url": repository.url,
                            "stars": repository.stars or 0,
                        },
                        "indexed_at": (
                            automation.indexed_at.isoformat()
                            if automation.indexed_at
                            else None
                        ),
                    }
                )

            logger.info(
                f"Search query '{query}' returned {len(formatted_results)} results"
            )
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
            results = (
                db.query(Automation, Repository)
                .join(Repository, Automation.repository_id == Repository.id)
                .order_by(func.random())
                .limit(limit)
                .all()
            )

            formatted_results = []
            for automation, repository in results:
                formatted_results.append(
                    {
                        "id": automation.id,
                        "alias": automation.alias,
                        "description": automation.description,
                        "trigger_types": (
                            automation.trigger_types.split(",")
                            if automation.trigger_types
                            else []
                        ),
                        "blueprint_path": automation.blueprint_path,
                        "action_calls": (
                            automation.action_calls.split(",")
                            if automation.action_calls
                            else []
                        ),
                        "source_file_path": automation.source_file_path,
                        "github_url": automation.github_url,
                        "start_line": automation.start_line,
                        "end_line": automation.end_line,
                        "repository": {
                            "name": repository.name,
                            "owner": repository.owner,
                            "description": repository.description,
                            "url": repository.url,
                            "stars": repository.stars or 0,
                        },
                        "indexed_at": (
                            automation.indexed_at.isoformat()
                            if automation.indexed_at
                            else None
                        ),
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Error getting recent automations: {e}")
            return []

    @staticmethod
    def get_statistics(db: Session) -> Dict[str, Any]:
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

            # Get last indexed timestamp
            last_indexed = (
                db.query(IndexingMetadata).filter_by(key="last_completed_at").first()
            )

            # Get repository star count
            star_count_metadata = (
                db.query(IndexingMetadata).filter_by(key="repo_star_count").first()
            )
            star_count = int(star_count_metadata.value) if star_count_metadata else 0

            return {
                "total_repositories": repo_count or 0,
                "total_automations": automation_count or 0,
                "last_indexed_at": last_indexed.value if last_indexed else None,
                "repo_star_count": star_count,
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "total_repositories": 0,
                "total_automations": 0,
                "last_indexed_at": None,
                "repo_star_count": 0,
            }

    @staticmethod
    def get_facets(
        db: Session,
        query: str = "",
        repo_filter: Optional[str] = None,
        blueprint_filter: Optional[str] = None,
        trigger_filter: Optional[str] = None,
        action_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get facets (aggregated counts) for filters.

        Args:
            db: Database session
            query: Current search query
            repo_filter: Currently selected repository filter
            blueprint_filter: Currently selected blueprint filter
            trigger_filter: Currently selected trigger filter
            action_filter: Currently selected action filter

        Returns:
            Dictionary with facets for repositories, blueprints, triggers, and actions
        """
        try:
            # Build base query with current filters (except the one we're aggregating)
            base_query = db.query(Automation, Repository).join(
                Repository, Automation.repository_id == Repository.id
            )

            # Apply text search if provided
            if query:
                search_pattern = f"%{query}%"
                base_query = base_query.filter(
                    or_(
                        func.lower(Automation.alias).like(func.lower(search_pattern)),
                        func.lower(Automation.description).like(
                            func.lower(search_pattern)
                        ),
                        func.lower(Automation.trigger_types).like(
                            func.lower(search_pattern)
                        ),
                        func.lower(Automation.action_calls).like(
                            func.lower(search_pattern)
                        ),
                        func.lower(Repository.owner).like(func.lower(search_pattern)),
                        func.lower(Repository.name).like(func.lower(search_pattern)),
                        func.lower(Repository.description).like(
                            func.lower(search_pattern)
                        ),
                    )
                )

            # Get repository facets (excluding current repo filter)
            repo_query = base_query
            if blueprint_filter:
                repo_query = repo_query.filter(
                    Automation.blueprint_path == blueprint_filter
                )
            if trigger_filter:
                repo_query = repo_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.trigger_types, trigger_filter
                    )
                )
            if action_filter:
                repo_query = repo_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.action_calls, action_filter
                    )
                )

            repo_facets = (
                repo_query.with_entities(
                    Repository.owner,
                    Repository.name,
                    func.max(Repository.stars).label("stars"),
                    func.count(Automation.id).label("count"),
                )
                .group_by(Repository.owner, Repository.name)
                .order_by(func.count(Automation.id).desc())
                .limit(20)
                .all()
            )

            # Get blueprint facets (excluding current blueprint filter)
            blueprint_query = base_query
            if repo_filter and "/" in repo_filter:
                owner, name = repo_filter.split("/", 1)
                blueprint_query = blueprint_query.filter(
                    Repository.owner == owner, Repository.name == name
                )
            if trigger_filter:
                blueprint_query = blueprint_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.trigger_types, trigger_filter
                    )
                )
            if action_filter:
                blueprint_query = blueprint_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.action_calls, action_filter
                    )
                )

            blueprint_facets = (
                blueprint_query.filter(Automation.blueprint_path.isnot(None))
                .with_entities(
                    Automation.blueprint_path, func.count(Automation.id).label("count")
                )
                .group_by(Automation.blueprint_path)
                .order_by(func.count(Automation.id).desc())
                .limit(20)
                .all()
            )

            # Get trigger facets (excluding current trigger filter)
            trigger_query = base_query
            if repo_filter and "/" in repo_filter:
                owner, name = repo_filter.split("/", 1)
                trigger_query = trigger_query.filter(
                    Repository.owner == owner, Repository.name == name
                )
            if blueprint_filter:
                trigger_query = trigger_query.filter(
                    Automation.blueprint_path == blueprint_filter
                )
            if action_filter:
                trigger_query = trigger_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.action_calls, action_filter
                    )
                )

            # Get all trigger types and aggregate
            all_triggers = (
                trigger_query.filter(Automation.trigger_types.isnot(None))
                .with_entities(Automation.trigger_types)
                .all()
            )

            # Parse comma-separated trigger types and count
            trigger_counts: Dict[str, int] = {}
            for (trigger_str,) in all_triggers:
                if trigger_str:
                    for trigger in trigger_str.split(","):
                        trigger = trigger.strip()
                        if trigger:
                            trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

            # Sort by count and limit
            trigger_facets = sorted(
                trigger_counts.items(), key=lambda x: x[1], reverse=True
            )[:20]

            # Get action facets (excluding current action filter)
            action_query = base_query
            if repo_filter and "/" in repo_filter:
                owner, name = repo_filter.split("/", 1)
                action_query = action_query.filter(
                    Repository.owner == owner, Repository.name == name
                )
            if blueprint_filter:
                action_query = action_query.filter(
                    Automation.blueprint_path == blueprint_filter
                )
            if trigger_filter:
                action_query = action_query.filter(
                    SearchService._exact_match_in_comma_list(
                        Automation.trigger_types, trigger_filter
                    )
                )

            # Get all action calls and aggregate
            all_actions = (
                action_query.filter(Automation.action_calls.isnot(None))
                .with_entities(Automation.action_calls)
                .all()
            )

            # Parse comma-separated action calls and count
            action_counts: Dict[str, int] = {}
            for (action_str,) in all_actions:
                if action_str:
                    for action in action_str.split(","):
                        action = action.strip()
                        if action:
                            action_counts[action] = action_counts.get(action, 0) + 1

            # Sort by count and limit
            action_facets = sorted(
                action_counts.items(), key=lambda x: x[1], reverse=True
            )[:20]

            return {
                "repositories": [
                    {"owner": owner, "name": name, "stars": stars or 0, "count": count}
                    for owner, name, stars, count in repo_facets
                ],
                "blueprints": [
                    {"path": path, "count": count} for path, count in blueprint_facets
                ],
                "triggers": [
                    {"type": trigger, "count": count}
                    for trigger, count in trigger_facets
                ],
                "actions": [
                    {"call": action, "count": count}
                    for action, count in action_facets
                ],
            }

        except Exception as e:
            logger.error(f"Error getting facets: {e}")
            return {"repositories": [], "blueprints": [], "triggers": [], "actions": []}
