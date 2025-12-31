# Architecture Documentation

**hadiscover** is a search engine for Home Assistant automations, built with Python/FastAPI backend, Next.js frontend, and SQLite database.

## Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy, APScheduler
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS
- **Database**: SQLite with full-text search
- **External**: GitHub REST API

## Architecture Diagram

```text
User Browser (Next.js)
       ↓ HTTP/JSON
FastAPI Backend
  ├─ Search Service
  ├─ Indexing Service (hourly scheduled)
  ├─ GitHub Service
  └─ Parser Service
       ↓
SQLite Database ←→ GitHub API
```

## Data Flow

### Indexing (Hourly Automated)

1. **Discovery**: Search GitHub for repositories with `hadiscover` topic
2. **File Fetch**: Locate `automations.yaml` in common paths, fetch raw content
3. **Parse**: Extract metadata (alias, description, triggers, blueprints, actions, line numbers)
4. **Store**: Save to SQLite with repository relationship
5. **Continue**: Best-effort parsing; failures logged but don't stop indexing

### Search

1. User enters query → Frontend calls `/api/v1/search?q={query}`
2. Backend performs case-insensitive search across: alias, description, triggers, repo name
3. Returns results with GitHub links (including precise line numbers)
4. Frontend renders with repository context

## Backend Services

### GitHub Service (`app/services/github_service.py`)

- Search repositories by topic via GitHub API
- Fetch file contents from repos
- Discover automation files using path patterns
- Optional GitHub token for higher rate limits (5k/hr vs 60/hr)

### Parser Service (`app/services/parser.py`)

- Parse Home Assistant YAML files with best-effort approach
- Extract: alias, description, triggers, blueprints, action calls, line numbers
- Support both old (`platform`, `service`) and new (`trigger`, `action`) YAML formats
- Recursively process nested actions (if/then/else, choose, repeat)
- Auto-deduplicate trigger types and action calls

### Indexing Service (`app/services/indexer.py`)

- Orchestrate GitHub, Parser, and Database operations
- Update existing repositories (upsert pattern)
- Per-repository transactions for isolation
- Return statistics on success/failure

### Search Service (`app/services/search_service.py`)

- Full-text search with filtering (repository, blueprint, trigger)
- Generate facets for repositories, blueprints, triggers
- Return statistics (repo/automation counts, last indexed time, star count)
- Include line numbers for precise GitHub links

### Scheduler Service (`app/services/scheduler.py`)

- Automated hourly indexing using APScheduler
- Runs at top of each hour (minute 0)
- Single instance protection prevents overlaps

## Database Schema

### repositories

```sql
id, name, owner, description, url (unique), stars, default_branch, indexed_at
```

### automations

```sql
id, alias, description, trigger_types, blueprint_path, action_calls,
source_file_path, github_url, start_line, end_line,
repository_id (FK), indexed_at
```

### indexing_metadata

```sql
id, key (unique), value, updated_at
-- Keys: last_completed_at, repo_star_count
```

**Indexes**: `repositories.url`, `automations.alias`, `automations.blueprint_path`, `automations.repository_id`

## API Endpoints

### `GET /api/v1/search`

**Query Parameters**: `q` (query), `limit` (50 default, 100 max), `repo` (filter), `blueprint` (filter), `trigger` (filter)

**Returns**: JSON with results array, count, and facets (repositories, blueprints, triggers)

### `GET /api/v1/statistics`

**Returns**: Total repositories/automations, last indexed timestamp, star count

### `POST /api/v1/index`

**Availability**: Development mode only (`ENVIRONMENT=development`)

**Rate Limit**: Once per 10 minutes (returns 429 if exceeded)

### `GET /api/v1/health`

**Returns**: `{"status": "healthy"}`

**CORS**: Allows `localhost:3000`, `localhost:8080`, `hadiscover.com`, `www.hadiscover.com`, `api.hadiscover.com`

## Key Design Decisions

### SQLite Database

Zero-config, file-based storage sufficient for MVP. Can migrate to PostgreSQL if needed.

### Best-Effort Parsing

Fault-tolerant YAML parsing handles varied Home Assistant configurations. Partial data better than none.

### Opt-In via GitHub Topic

Only indexes repositories with explicit `hadiscover` topic. Respects privacy and user consent.

### Hourly Scheduled Indexing

APScheduler runs automatic indexing every hour. Manual trigger available in development mode only.

### Background Processing

Indexing runs in background thread to prevent API timeouts. Returns immediate response.

### Line Number Tracking

Store start/end lines for precise GitHub links using YAML parser's node marks.

### Faceted Search

Repository, blueprint, and trigger facets enable filtering and pattern discovery.

### No Authentication (MVP)

Read-only public data, reduces complexity. Can add authentication later if needed.

### Client-Side Rendering

Next.js CSR for simpler deployment. Can migrate to SSR for SEO if beneficial.

## Future Enhancements

- Advanced search (fuzzy matching, boolean operators)
- Pagination for large result sets
- Redis caching for performance
- Analytics and popular automation tracking
- User contributions (ratings, comments)
- API authentication and rate limiting
- Kubernetes deployment guides
- Frontend and E2E testing
- Application monitoring and metrics
