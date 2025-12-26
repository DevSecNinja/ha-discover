# GitHub Copilot Instructions for hadiscover

**hadiscover** is a Home Assistant automation search engine - a full-stack app with Python/FastAPI backend (SQLite), Next.js/TypeScript frontend, ~50 files, 40 backend tests. Indexes `automations.yaml` from GitHub repos with `hadiscover` topic.

## Backend (Python/FastAPI) - Python 3.12+

**Setup** (first time):
```bash
cd backend && python3 -m venv venv && source venv/bin/activate
pip install --upgrade pip && pip install -r requirements.txt
```

**Test** (ALWAYS before changes): `pytest tests/ -v` - All 40 tests must pass (~2s runtime)

**Dev server**: `python -m uvicorn app.main:app --reload` at http://localhost:8000, docs at /docs

**CLI**: `python -m app.cli index-now` triggers indexing

**Environment** (optional): `GITHUB_TOKEN` for rate limits, `ENVIRONMENT=development` enables `/api/v1/index` endpoint

## Frontend (Next.js/TypeScript) - Node.js 18+

**Setup**: `cd frontend && npm install`

**Build**: `npm run build` (~5s, creates `out/` directory)

**Dev server**: `npm run dev` at http://localhost:3000

**Environment** (optional): `NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1` in `.env.local`

## Docker Testing

```bash
# Backend: docker build -t test ./backend && docker run -d -p 8000:8000 -e ENVIRONMENT=development test
# Wait 5s, then: curl http://localhost:8000/api/v1/health
# Frontend: docker build --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 -t test ./frontend
# docker run -d -p 3000:80 test && sleep 3 && curl http://localhost:3000
```

## CI Workflows (All on PR/main)

**docker-test.yml** (PRIMARY): Builds containers, tests backend API (health, search, stats, docs, index-now CLI), frontend web server, integration tests. Must pass before merge.

**deploy.yml**: Runs 40 backend pytest tests (Python 3.14), builds frontend static export (Node 24). Deployment commented out.

**release.yml**: On version tags (v*.*.*), runs tests, builds/pushes Docker images to GHCR, creates GitHub release.

**CI Requirements**: All 40 backend tests pass, Docker containers build and pass health checks, API endpoints return expected responses.

## Project Structure

```
backend/app/: main.py (FastAPI), cli.py (index-now cmd), version.py, api/routes.py, 
  models/ (SQLAlchemy), services/ (github_service.py, parser.py, indexer.py, search_service.py)
backend/tests/: 40 pytest tests
backend/: requirements.txt, pytest.ini, Dockerfile, entrypoint.sh, .env.example
frontend/app/: page.tsx (search UI), layout.tsx, globals.css
frontend/: package.json, next.config.ts (static export, basePath:'/ha-discover'), Dockerfile
.github/workflows/: docker-test.yml (primary), deploy.yml, release.yml
Root: README.md, ARCHITECTURE.md, DEPLOYMENT.md, docker-compose.yml
```

**Database**: SQLite at `backend/data/hadiscover.db` (auto-created). Tables: repositories, automations.

**Config Files**: backend/pytest.ini, backend/requirements.txt, frontend/next.config.ts, both Dockerfiles have health checks.

## Environment Variables

**Backend**: `GITHUB_TOKEN` (optional, for 5k/hr vs 60/hr rate limit), `ENVIRONMENT=development` (enables /api/v1/index), `ROOT_PATH=/api/v1` (for reverse proxy that strips path), `DATABASE_URL` (default: sqlite:///./data/hadiscover.db)

**Frontend**: `NEXT_PUBLIC_API_URL` (default: http://localhost:8000/api/v1)

## Common Issues

1. **Datetime warnings in tests**: Code uses deprecated `datetime.utcnow()`. Expected; warnings don't fail tests.
2. **Frontend "NEXT_PUBLIC_API_URL not set"**: Normal for local builds; defaults to localhost:8000.
3. **Docker health check fails**: Wait 5-10s after `docker run`. Check logs with `docker logs <container>`.
4. **Backend returns 404**: Don't set `ROOT_PATH` for local dev; only for cloud deployments.
5. **"index-now not found"**: Check Dockerfile installs to /usr/local/bin/.

## Key Implementation Notes

- **CORS**: Backend allows localhost:3000, hadiscover.com. Update `app/main.py` if forking.
- **Rate limit**: /api/v1/index limited to once per 10min (in-memory).
- **Indexing**: Runs in background thread; returns immediately.
- **Parsing**: Best-effort YAML parser; gracefully handles errors.
- **Export**: Frontend uses Next.js static export with unoptimized images.
- **Dual mode**: Backend container runs web server (default) or `index-now` CLI (exits after completion).

## Pre-Commit Validation

**Backend**: Run `pytest tests/ -v` (all 40 pass), check syntax, verify imports at top (PEP 8)
**Frontend**: Run `npm run build` (completes successfully), check TypeScript compiles, verify rendering
**Before merge**: All GitHub workflows pass (especially docker-test.yml), no new security issues, docs updated if needed

## Workflow Scripts

**IMPORTANT**: All multiline scripts in GitHub Actions workflows MUST be extracted to separate files in `.github/scripts/` directory. Do NOT write inline multiline scripts in workflow files.

**Rationale**: Separate script files improve maintainability, testability, and reusability. They can be tested locally and are easier to version control and review.

**Existing scripts**: See `.github/scripts/` directory for examples of properly extracted scripts.

Trust these instructions. Only search if incomplete, conflicting, or encountering undocumented errors.
