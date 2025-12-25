"""API routes for HA Discover."""
import logging
import os
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models import get_db
from app.services.search_service import SearchService
from app.services.indexer import IndexingService

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
    repository: RepositoryResponse
    indexed_at: Optional[str]


class SearchResponse(BaseModel):
    """Search API response."""
    query: str
    results: List[AutomationResponse]
    count: int


class StatisticsResponse(BaseModel):
    """Statistics API response."""
    total_repositories: int
    total_automations: int


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
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Search for Home Assistant automations.
    
    Args:
        q: Search query string (searches across automation name, description, triggers, and repository)
        limit: Maximum number of results (default: 50, max: 100)
        db: Database session
        
    Returns:
        Search results with matching automations
    """
    if limit > 100:
        limit = 100
    
    results = SearchService.search_automations(db, q, limit)
    
    return {
        "query": q,
        "results": results,
        "count": len(results)
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
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
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
            detail="This endpoint is not available in production. Indexing runs on a daily schedule."
        )
    
    global last_indexing_time
    
    # Check if indexing was recently triggered
    if last_indexing_time is not None:
        time_since_last = datetime.utcnow() - last_indexing_time
        cooldown = timedelta(minutes=INDEXING_COOLDOWN_MINUTES)
        
        if time_since_last < cooldown:
            remaining_seconds = int((cooldown - time_since_last).total_seconds())
            remaining_minutes = remaining_seconds // 60
            remaining_seconds = remaining_seconds % 60
            
            raise HTTPException(
                status_code=429,
                detail=f"Indexing rate limit exceeded. Please wait {remaining_minutes}m {remaining_seconds}s before triggering again."
            )
    
    # Update last indexing time
    last_indexing_time = datetime.utcnow()
    
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
        "message": "Indexing started in background",
        "started": True
    }


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Simple health status
    """
    return {"status": "healthy"}
