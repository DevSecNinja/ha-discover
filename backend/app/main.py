"""Main FastAPI application for HA Discover."""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.models import init_db
from app.api.routes import router
from app.version import __version__

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Get root_path from environment variable
# This allows the app to work correctly behind reverse proxies or when deployed
# to cloud platforms with different base paths (e.g., Azure Container Apps)
root_path = os.getenv("ROOT_PATH", "")

# Create FastAPI app
app = FastAPI(
    title="HA Discover API",
    description="Search engine for Home Assistant automations from GitHub",
    version=__version__,
    root_path=root_path
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://devsecninja.github.io"],  # Next.js default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Determine the API route prefix based on root_path configuration
# If root_path is already set to /api/v1, don't add it again to routes
# This allows the app to work correctly when deployed behind reverse proxies
api_prefix = "" if root_path else "/api/v1"

# Include API routes
app.include_router(router, prefix=api_prefix)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    init_db()
    logging.info("Database initialized")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "HA Discover API",
        "version": __version__,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
