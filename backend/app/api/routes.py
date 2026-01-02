"""API routes for hadiscover."""

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.models import get_db
from app.services.indexer import IndexingService
from app.services.search_service import SearchService
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def is_development() -> bool:
    """Check if running in development mode."""
    return os.getenv("ENVIRONMENT", "production") == "development"


router = APIRouter()

# Rate limiting for indexing endpoint
last_indexing_time: Optional[datetime] = None
INDEXING_COOLDOWN_MINUTES = 10


# Pydantic models for API
class RepositoryResponse(BaseModel):
    """Repository information in API response."""

    name: str
    owner: str
    description: Optional[str]
    url: str
    stars: int


class RepositoryFacet(BaseModel):
    """Repository facet with count."""

    owner: str
    name: str
    stars: int
    count: int


class BlueprintFacet(BaseModel):
    """Blueprint facet with count."""

    path: str
    count: int


class TriggerFacet(BaseModel):
    """Trigger type facet with count."""

    type: str
    count: int


class ActionFacet(BaseModel):
    """Action call facet with count."""

    call: str
    count: int


class Facets(BaseModel):
    """Facets for filtering."""

    repositories: List[RepositoryFacet]
    blueprints: List[BlueprintFacet]
    triggers: List[TriggerFacet]
    actions: List[ActionFacet]


class AutomationResponse(BaseModel):
    """Automation search result."""

    id: int
    alias: Optional[str]
    description: Optional[str]
    trigger_types: List[str]
    blueprint_path: Optional[str]
    action_calls: List[str]
    source_file_path: str
    github_url: str
    start_line: Optional[int]
    end_line: Optional[int]
    repository: RepositoryResponse
    indexed_at: Optional[str]


class SearchResponse(BaseModel):
    """Search API response."""

    query: str
    results: List[AutomationResponse]
    count: int
    total: int
    page: int
    per_page: int
    facets: Facets


class StatisticsResponse(BaseModel):
    """Statistics API response."""

    total_repositories: int
    total_automations: int
    last_indexed_at: Optional[str] = None
    repo_star_count: int


class IndexResponse(BaseModel):
    """Indexing operation response."""

    message: str
    started: bool


class IndexStatusResponse(BaseModel):
    """Indexing status response."""

    repositories_found: int
    repositories_indexed: int
    automations_indexed: int
    errors: int


@router.get("/search", response_model=SearchResponse)
async def search_automations(
    q: str = "",
    page: int = 1,
    per_page: int = 30,
    repo: Optional[str] = None,
    blueprint: Optional[str] = None,
    trigger: Optional[str] = None,
    action: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Search for Home Assistant automations.

    Args:
        q: Search query string (searches across automation name, description, triggers, actions, and repository)
        page: Page number (default: 1, min: 1)
        per_page: Results per page (default: 30, max: 100)
        repo: Filter by repository (format: "owner/name")
        blueprint: Filter by blueprint path
        trigger: Filter by trigger type
        action: Filter by action call (service name)
        db: Database session

    Returns:
        Search results with matching automations and facets for filtering
    """
    # Validate and constrain parameters
    if page < 1:
        page = 1
    if per_page > 100:
        per_page = 100
    if per_page < 10:
        per_page = 10

    results, total = SearchService.search_automations(
        db,
        q,
        page=page,
        per_page=per_page,
        repo_filter=repo,
        blueprint_filter=blueprint,
        trigger_filter=trigger,
        action_filter=action,
    )

    facets = SearchService.get_facets(
        db,
        q,
        repo_filter=repo,
        blueprint_filter=blueprint,
        trigger_filter=trigger,
        action_filter=action,
    )

    return {
        "query": q,
        "results": results,
        "count": len(results),
        "total": total,
        "page": page,
        "per_page": per_page,
        "facets": facets,
    }


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get statistics about indexed repositories and automations.

    Args:
        db: Database session

    Returns:
        Statistics about indexed data
    """
    stats = SearchService.get_statistics(db)
    return stats


@router.post("/index", response_model=IndexResponse)
async def trigger_indexing(
    background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    """
    Trigger indexing of repositories with hadiscover or ha-discover topics.

    This endpoint is only available in development mode.
    In production, indexing runs on a daily schedule via GitHub Actions.

    Args:
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Confirmation that indexing has started

    Raises:
        HTTPException: If called in production or within the cooldown period
    """
    # Block endpoint in production
    if not is_development():
        raise HTTPException(
            status_code=403,
            detail="This endpoint is not available in production. Indexing runs on a daily schedule.",
        )

    global last_indexing_time

    # Check if indexing was recently triggered
    if last_indexing_time is not None:
        time_since_last = datetime.now(timezone.utc) - last_indexing_time
        cooldown = timedelta(minutes=INDEXING_COOLDOWN_MINUTES)

        if time_since_last < cooldown:
            remaining_seconds = int((cooldown - time_since_last).total_seconds())
            remaining_minutes = remaining_seconds // 60
            remaining_seconds = remaining_seconds % 60

            raise HTTPException(
                status_code=429,
                detail=f"Indexing rate limit exceeded. Please wait {remaining_minutes}m {remaining_seconds}s before triggering again.",
            )

    # Update last indexing time
    last_indexing_time = datetime.now(timezone.utc)

    async def run_indexing():
        """Background task to run indexing."""
        indexer = IndexingService()
        # Create a new session for background task
        from app.models import SessionLocal

        bg_db = SessionLocal()
        try:
            await indexer.index_repositories(bg_db)
        finally:
            bg_db.close()

    background_tasks.add_task(run_indexing)

    return {
        "message": "Indexing started in background. Refresh your browser to see the changes once complete.",
        "started": True,
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Simple health status
    """
    return {"status": "healthy"}
