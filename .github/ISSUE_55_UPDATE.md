# Issue #55 Update: Add Support for External Databases

## Context

Based on comprehensive stress testing (PR #84), we've identified specific performance bottlenecks and scaling requirements that necessitate migration to external databases at scale.

## Performance Test Insights

### Test Configuration
We conducted stress tests across 3 intensity levels:

| Level | Repositories | Automations | Use Case |
|-------|--------------|-------------|----------|
| L1 (Light) | 100 | 1,000 | Personal/small community |
| L2 (Medium) | 500 | 5,000 | Medium organizations |
| L3 (Heavy) | 2,000 | 20,000 | Large-scale public |

### Key Findings

#### Level 1 (100 repos, 1K automations) - ✅ SQLite Sufficient
- **Search**: 4-10ms average
- **Facet generation**: 10-13ms
- **Status**: All operations under 100ms
- **Database size**: ~2.1MB
- **Recommendation**: Current SQLite architecture is optimal
- **Cost**: $0-7/month

#### Level 2 (500 repos, 5K automations) - ⚠️ Caching Recommended
- **Search**: 9-17ms average (2x slower)
- **Facet generation**: 33-57ms (4x slower, approaching limits)
- **Status**: Acceptable but shows degradation
- **Database size**: ~10.3MB
- **Recommendation**: Add Redis for facet caching (see issue #[NEW_CACHING_ISSUE])
- **Cost**: $20-45/month with caching

#### Level 3 (2,000 repos, 20K automations) - 🚨 Migration Required
- **Search**: 28-65ms average (6x slower)
- **Facet generation**: 94-159ms (12x slower - bottleneck)
- **Concurrent load**: 1.8s for 50 queries
- **Database size**: ~41MB
- **Recommendation**: Full infrastructure migration needed
- **Cost**: $125-275/month

## Critical Bottlenecks Identified

1. **SQLite LIKE queries** - Non-linear performance degradation at scale
2. **Facet aggregation** - 12x slowdown from L1 to L3
3. **Concurrent query handling** - Sequential processing limits

## Proposed Solution: Phased Migration

### Phase 1: Add Redis Caching (Level 2+)
**Priority**: High for Medium scale  
**Timeline**: 1-2 weeks  
**Details**: See issue #[NEW_CACHING_ISSUE]

Benefits:
- Reduce facet generation time by 70-80%
- Cache search results (TTL: 1-5 min)
- Implement rate limiting
- Cost: +$10-20/month

### Phase 2: Implement External Database Support (Level 3)
**Priority**: Medium (only for large-scale deployments)  
**Timeline**: 4-6 weeks

#### 2.1 PostgreSQL Migration
**Rationale**: Better concurrency, read replicas, advanced indexing

Implementation:
- Add database abstraction layer (SQLAlchemy supports both)
- Implement GiST/GIN indexes for full-text search
- Enable `pg_trgm` extension for fuzzy matching
- Set up read replicas for query load distribution
- Use connection pooling (pgBouncer: 50-100 connections)

Configuration:
```python
# Environment variable based DB selection
DATABASE_TYPE=postgresql  # or sqlite for backwards compatibility
DATABASE_URL=postgresql://user:pass@host/db
```

Expected improvements:
- 40-50% faster search at scale
- Better concurrent query handling
- Horizontal scaling capability

#### 2.2 Dedicated Search Engine Integration
**Rationale**: Specialized search engines excel at text search and faceting

Options (in order of recommendation):
1. **Meilisearch** (Recommended for ease)
   - Pros: Fast, easy deployment, excellent DX, typo-tolerant
   - Cons: Newer, smaller community
   - Setup time: 1-2 days
   
2. **Elasticsearch**
   - Pros: Battle-tested, full-featured, great analytics
   - Cons: Heavy, complex configuration
   - Setup time: 1-2 weeks
   
3. **Typesense**
   - Pros: Low latency, simpler than ES, typo-tolerant
   - Cons: Fewer features than ES
   - Setup time: 2-3 days
   
4. **OpenSearch**
   - Pros: AWS-friendly, Elasticsearch fork
   - Cons: Similar complexity to ES
   - Setup time: 1-2 weeks

Implementation approach:
- Keep PostgreSQL as source of truth
- Sync to search engine asynchronously
- Use search engine for all query operations
- Implement fallback to PostgreSQL if search engine unavailable

Expected improvements:
- Search queries under 10ms at any scale
- Facet generation under 20ms
- Better relevance ranking
- Advanced features (typo tolerance, synonyms, etc.)

### Phase 3: Horizontal Scaling Architecture (Level 3+)
**Priority**: Low (only for very large scale)  
**Timeline**: 6-8 weeks

Components:
- Container orchestration (Kubernetes)
- Load balancer (multiple API instances)
- Separate indexing workers from API servers
- CDN for API responses (CloudFlare/Fastly)
- APM tool (New Relic/DataDog/Sentry)

## Implementation Considerations

### Backwards Compatibility
- Keep SQLite as default for small deployments
- Use environment variables for database selection
- Maintain feature parity across database backends
- Provide migration scripts

### Configuration Example
```env
# SQLite (default, Level 1)
DATABASE_TYPE=sqlite
DATABASE_PATH=/data/hadiscover.db

# PostgreSQL (Level 3)
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost/hadiscover
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Search Engine (optional, Level 3)
SEARCH_ENGINE=meilisearch  # or elasticsearch, typesense, opensearch
SEARCH_ENGINE_URL=http://localhost:7700
SEARCH_ENGINE_API_KEY=masterKey
```

### Migration Path
1. User starts with SQLite (Level 1)
2. Add Redis when reaching Level 2 scale (issue #[NEW_CACHING_ISSUE])
3. Migrate to PostgreSQL + Search Engine when reaching Level 3 scale
4. Each step is optional and based on actual scale needs

## Infrastructure Cost Estimates

| Configuration | Monthly Cost | Suitable For |
|--------------|--------------|--------------|
| SQLite only | $0-7 | Level 1 (<100 repos) |
| SQLite + Redis | $20-45 | Level 2 (500 repos) |
| PostgreSQL + Redis | $50-100 | Level 3 (2K repos) |
| Full Stack (PG + Search + Redis + CDN) | $125-275 | Level 3+ (5K+ repos) |

## Success Metrics

- Search queries consistently under 20ms at Level 3 scale
- Facet generation under 30ms at Level 3 scale
- Support 100+ concurrent queries without degradation
- Database size scales linearly with content
- API response time P95 under 100ms

## Related Issues

- Issue #[NEW_CACHING_ISSUE]: Implement Redis caching for facets and search results
- PR #84: Comprehensive stress testing results (merged)

## Implementation Priority

1. **High**: Implement Redis caching (addresses Level 2 bottleneck)
2. **Medium**: Add PostgreSQL support (enables Level 3 scale)
3. **Low**: Search engine integration (optimizes Level 3 experience)
4. **Low**: Horizontal scaling architecture (future-proofing)

## Testing Requirements

- Maintain stress test suite from PR #84
- Add integration tests for each database backend
- Performance regression tests in CI/CD
- Load testing before production deployment

## Documentation Needs

- Database configuration guide
- Migration guide from SQLite to PostgreSQL
- Performance tuning recommendations
- Troubleshooting guide
- Cost estimation calculator
