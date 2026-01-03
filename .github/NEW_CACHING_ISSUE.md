# New Issue: Implement Redis Caching for Performance Optimization

## Title
Implement Redis caching for facets, search results, and statistics

## Labels
- enhancement
- backend
- performance

## Description

## Context

Based on stress testing results from PR #84, facet generation and search queries show significant performance degradation at medium scale (Level 2: 500 repos, 5K automations):

- **Facet generation**: 33-57ms at Level 2, 94-159ms at Level 3 (4-12x slower than Level 1)
- **Search queries**: 9-17ms at Level 2, 28-65ms at Level 3 (2-6x slower than Level 1)

Implementing Redis caching is identified as the most cost-effective optimization for medium-scale deployments, providing 70-80% performance improvements before requiring more expensive infrastructure migrations (PostgreSQL, search engines).

## Problem Statement

Current bottlenecks:
1. **Facet aggregation** - SQLite performs expensive COUNT/GROUP BY queries on every request
2. **Repeated searches** - Common search queries re-execute database queries
3. **Statistics endpoint** - Aggregates counts across entire database on each call
4. **No rate limiting** - Vulnerable to abuse without request tracking

## Proposed Solution

Implement Redis as a caching layer with intelligent TTL strategies for different data types.

### Architecture

```
Client Request
    ↓
API Layer
    ↓
Cache Check (Redis) ←→ Cache Miss → Database Query (SQLite/PostgreSQL)
    ↓                                      ↓
Cache Hit                            Store in Cache
    ↓                                      ↓
Return Response ←------------------------┘
```

### What to Cache

#### 1. Facet Results (Highest Priority)
**Problem**: Most expensive operation (94-159ms at Level 3)  
**Solution**: Cache facet results by filter combination

```python
# Cache key: facets:{query_hash}
# Value: JSON facet data
# TTL: 10 minutes
```

Cache keys:
- `facets:all` - All facets with no filters
- `facets:{trigger_hash}` - Facets filtered by trigger
- `facets:{action_hash}` - Facets filtered by action
- `facets:{blueprint_hash}` - Facets filtered by blueprint
- `facets:{combo_hash}` - Combined filters

Expected improvement: 70-80% reduction in facet generation time

#### 2. Search Results (High Priority)
**Problem**: Repeated searches re-query database  
**Solution**: Cache search results by query parameters

```python
# Cache key: search:{query}:{filters}:{page}
# Value: JSON search results
# TTL: 5 minutes
```

Cache keys:
- `search:{text}:p{page}` - Text search with pagination
- `search:{text}:{filters}:p{page}` - Filtered search

Expected improvement: Near-instant responses for cached queries

#### 3. Statistics (Medium Priority)
**Problem**: Expensive aggregation on every stats request  
**Solution**: Cache aggregate statistics

```python
# Cache key: stats:global
# Value: JSON statistics data
# TTL: 5 minutes
```

Expected improvement: Statistics endpoint consistently under 5ms

#### 4. Rate Limiting State (Medium Priority)
**Problem**: No abuse protection  
**Solution**: Track request counts per IP

```python
# Cache key: ratelimit:{ip}:{window}
# Value: Request count
# TTL: 60 seconds
```

Configuration:
- 100 requests per minute per IP (adjustable)
- Exponential backoff for repeated violations

### TTL Strategy

| Cache Type | TTL | Rationale |
|-----------|-----|-----------|
| Facets | 10 minutes | Data changes slowly, facets are expensive |
| Search results | 5 minutes | Balance freshness vs performance |
| Statistics | 5 minutes | Acceptable staleness for aggregate data |
| Rate limiting | 60 seconds | Short window for burst protection |

### Cache Invalidation

#### Trigger Events
1. **New repository indexed** → Clear all caches
2. **Repository updated** → Clear affected repository caches
3. **Repository deleted** → Clear all caches
4. **Manual cache clear** → Admin endpoint

#### Strategies
- **Time-based**: Automatic TTL expiration (primary)
- **Event-based**: Clear specific caches on data changes (secondary)
- **Admin control**: Manual clear via API endpoint (fallback)

## Implementation Plan

### Phase 1: Infrastructure Setup (Week 1)
- [ ] Add Redis to `docker-compose.yml` and `docker-compose.prod.yml`
- [ ] Add Redis Python client (`redis` or `redis-py`)
- [ ] Create Redis connection configuration with environment variables
- [ ] Implement connection pooling and error handling
- [ ] Add health check for Redis connectivity

Configuration:
```yaml
# docker-compose.yml
redis:
  image: redis:7-alpine
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
  command: redis-server --appendonly yes
```

```python
# Environment variables
REDIS_ENABLED=true  # Feature flag
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5
```

### Phase 2: Core Caching Logic (Week 2)
- [ ] Create `backend/app/services/cache_service.py`
  - [ ] Generic get/set/delete methods
  - [ ] Cache key generation utilities
  - [ ] TTL management
  - [ ] Error handling (fallback to DB on Redis failure)
  - [ ] Cache statistics/monitoring
- [ ] Add cache configuration dataclass
- [ ] Implement graceful degradation (app works without Redis)

```python
class CacheService:
    async def get_facets(self, filters: Optional[dict] = None) -> Optional[dict]:
        """Get cached facets or None if not found"""
    
    async def set_facets(self, filters: Optional[dict], data: dict, ttl: int = 600):
        """Cache facet results for 10 minutes"""
    
    async def get_search_results(self, query: str, filters: Optional[dict] = None, page: int = 1) -> Optional[dict]:
        """Get cached search results or None if not found"""
    
    async def invalidate_all(self):
        """Clear all caches (called on indexing)"""
```

### Phase 3: Facet Caching (Week 2)
- [ ] Update `backend/app/api/routes.py` facets endpoint
  - [ ] Check cache before generating facets
  - [ ] Store results in cache after generation
  - [ ] Handle cache misses gracefully
- [ ] Add cache hit/miss metrics
- [ ] Test with stress test suite

Expected improvement: 70-80% reduction in response time at Level 2

### Phase 4: Search Results Caching (Week 3)
- [ ] Update `backend/app/api/routes.py` search endpoint
  - [ ] Generate cache key from search parameters
  - [ ] Check cache before querying database
  - [ ] Store results with 5-minute TTL
- [ ] Handle pagination in cache keys
- [ ] Add cache metrics to response headers

Expected improvement: Near-instant responses for repeated searches

### Phase 5: Statistics Caching (Week 3)
- [ ] Update `backend/app/api/routes.py` statistics endpoint
  - [ ] Cache aggregate statistics
  - [ ] Refresh on indexing completion
- [ ] Add last-updated timestamp to response

Expected improvement: Consistently under 5ms response time

### Phase 6: Rate Limiting (Week 4)
- [ ] Implement rate limiting middleware
- [ ] Track requests per IP in Redis
- [ ] Return 429 status with Retry-After header
- [ ] Add rate limit info to response headers
  - `X-RateLimit-Limit: 100`
  - `X-RateLimit-Remaining: 87`
  - `X-RateLimit-Reset: 1641024000`
- [ ] Whitelist admin IPs (configurable)

### Phase 7: Cache Management (Week 4)
- [ ] Add admin endpoint for cache invalidation: `POST /api/v1/admin/cache/clear`
- [ ] Add endpoint for cache statistics: `GET /api/v1/admin/cache/stats`
- [ ] Implement automatic cache clearing on indexing
- [ ] Add cache warming on application startup

### Phase 8: Monitoring & Documentation (Week 4)
- [ ] Add cache hit/miss rate metrics
- [ ] Log cache performance in application logs
- [ ] Document Redis configuration in README
- [ ] Add deployment guide for Redis
- [ ] Update docker-compose documentation

## Configuration

### Environment Variables
```env
# Redis Configuration
REDIS_ENABLED=true  # Use string comparison: os.getenv("REDIS_ENABLED", "false") == "true"
REDIS_URL=redis://localhost:6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5

# Cache TTLs (seconds)
CACHE_TTL_FACETS=600        # 10 minutes
CACHE_TTL_SEARCH=300        # 5 minutes  
CACHE_TTL_STATS=300         # 5 minutes
CACHE_TTL_RATELIMIT=60      # 1 minute

# Rate Limiting
RATELIMIT_ENABLED=true  # Use string comparison: os.getenv("RATELIMIT_ENABLED", "false") == "true"
RATELIMIT_REQUESTS=100      # requests per window
RATELIMIT_WINDOW=60         # seconds
```

### Graceful Degradation
- Application must work without Redis (development mode)
- Redis connection failures should not crash the app
- Cache misses fall back to database queries
- Log warnings but continue operation

## Testing Requirements

### Unit Tests
- [ ] Test cache key generation
- [ ] Test TTL expiration
- [ ] Test cache invalidation
- [ ] Test graceful degradation without Redis
- [ ] Test rate limiting logic

### Integration Tests
- [ ] Test facet caching end-to-end
- [ ] Test search result caching
- [ ] Test statistics caching
- [ ] Test rate limiting enforcement
- [ ] Test cache invalidation on indexing

### Performance Tests
- [ ] Re-run Level 2 stress tests with caching enabled
- [ ] Measure cache hit rate
- [ ] Verify 70-80% improvement in facet generation
- [ ] Test concurrent cache access

## Success Metrics

- **Facet generation**: Reduce from 33-57ms to 10-15ms at Level 2 (70%+ improvement)
- **Search queries**: Reduce from 9-17ms to 3-5ms for cached results (80%+ improvement)
- **Statistics**: Consistently under 5ms
- **Cache hit rate**: Target 60%+ after warmup period
- **Zero downtime**: App continues working if Redis fails

## Dependencies

### Python Packages
```txt
redis==5.2.2  # or latest
```

### Infrastructure
- Redis 7.x (Alpine image for production)
- Docker Compose updated
- ~10-20MB memory for Redis at Level 2 scale

## Cost Impact

| Deployment | Cost Change | Total Monthly |
|-----------|-------------|---------------|
| Level 1 (development) | +$0 | $0-7 |
| Level 2 (production) | +$10-20 | $20-45 |
| Level 3 (enterprise) | +$15-30 | $140-305 |

Redis options:
- **Self-hosted**: $0 (included in server costs)
- **Redis Cloud**: Free tier available, $10-20/month for production
- **AWS ElastiCache**: $15-30/month for small instances
- **DigitalOcean Managed Redis**: $15/month minimum

## Rollout Strategy

1. **Development**: Test locally with Docker Compose Redis
2. **Staging**: Deploy with caching enabled, validate metrics
3. **Production**: 
   - Phase 1: Enable facet caching only (lowest risk)
   - Phase 2: Enable search result caching
   - Phase 3: Enable statistics caching
   - Phase 4: Enable rate limiting
4. **Monitor**: Track cache hit rates, response times, error rates

## Documentation Updates

- [ ] README.md: Add Redis setup instructions
- [ ] ARCHITECTURE.md: Document caching strategy
- [ ] DEPLOYMENT.md: Add Redis deployment guide
- [ ] API docs: Add cache-related headers documentation
- [ ] Troubleshooting guide: Common Redis issues

## Related Issues

- Issue #55: Add support for external databases (long-term scaling solution)
- PR #84: Stress testing results (context for performance requirements)

## Priority

**High** - Addresses critical performance bottleneck at medium scale before requiring expensive infrastructure migration.

## Estimated Effort

4 weeks for complete implementation and testing

## Acceptance Criteria

- [ ] Redis successfully integrated in development and production environments
- [ ] Facet generation time reduced by 70%+ at Level 2 scale
- [ ] Search response time reduced by 80%+ for cached queries
- [ ] Cache hit rate above 60% after warmup
- [ ] Application gracefully degrades without Redis
- [ ] Rate limiting prevents abuse
- [ ] All tests pass including new cache tests
- [ ] Documentation updated
- [ ] Performance improvements validated with stress tests
