# Stress Testing Guide

This document describes the stress testing framework for hadiscover and provides performance analysis at different scale levels.

## Overview

The stress testing suite evaluates backend and database performance under three intensity levels:

- **Level 1 (Light)**: 100 repositories, 1,000 automations
- **Level 2 (Medium)**: 500 repositories, 5,000 automations  
- **Level 3 (Heavy)**: 2,000 repositories, 20,000 automations

## Running Stress Tests

### Prerequisites

Ensure dependencies are installed:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Run All Tests

```bash
./run_stress_tests.sh
```

### Run Individual Levels

```bash
./run_stress_tests.sh level1  # Light load
./run_stress_tests.sh level2  # Medium load
./run_stress_tests.sh level3  # Heavy load
```

## What's Tested

Each stress test level evaluates:

1. **Database Write Performance**
   - Repository insertion speed
   - Automation batch insertion
   - Transaction handling

2. **Search Performance**
   - Text search across multiple fields
   - Empty query (recent automations)
   - Filtered searches (trigger types, action domains)
   - Pagination performance

3. **Facet Generation Performance**
   - Repository facets
   - Trigger type facets
   - Action domain facets
   - Blueprint facets

4. **Statistics Queries**
   - Count aggregations
   - Metadata retrieval

5. **Concurrent Query Handling**
   - Level 1: 10 concurrent queries
   - Level 2: 25 concurrent queries
   - Level 3: 50 concurrent queries

## Understanding Results

### Performance Metrics

Each test provides:
- **Min**: Fastest operation time
- **Max**: Slowest operation time
- **Avg**: Average operation time
- **Count**: Number of operations

### Recommendations

The test suite automatically generates performance recommendations based on:
- Query response times
- Database size estimates
- Concurrent load handling
- Memory usage patterns

## Expected Performance Targets

### Level 1 (Light)
- **Database Population**: < 2 seconds
- **Text Search**: < 0.1 seconds
- **Facet Generation**: < 0.5 seconds
- **Concurrent Queries**: < 1 second total

**Suitable for**: Personal projects, small community deployments

### Level 2 (Medium)
- **Database Population**: < 10 seconds
- **Text Search**: < 0.3 seconds
- **Facet Generation**: < 1.5 seconds
- **Concurrent Queries**: < 3 seconds total

**Suitable for**: Medium-sized communities, organization deployments

### Level 3 (Heavy)
- **Database Population**: < 45 seconds
- **Text Search**: < 0.5 seconds
- **Facet Generation**: < 3 seconds
- **Concurrent Queries**: < 8 seconds total

**Suitable for**: Large-scale public deployments

## Performance Optimization Recommendations

### For All Levels

1. **Database Indexes**
   - Ensure indexes on: `repositories.url`, `automations.alias`, `automations.repository_id`, `automations.blueprint_path`
   - Consider composite indexes for common filter combinations

2. **Query Optimization**
   - Use batch operations for inserts
   - Implement connection pooling
   - Add query result caching

### Level 1 Optimizations

✅ **Current Stack is Sufficient**
- SQLite handles this load efficiently
- No additional infrastructure needed
- Focus on code optimization

**Recommended Actions:**
- None required for basic functionality
- Consider basic query caching for frequently accessed data

### Level 2 Optimizations

⚠️ **Consider Infrastructure Improvements**

**Database:**
- Implement Redis caching for:
  - Facet results (TTL: 5-10 minutes)
  - Statistics (TTL: 5 minutes)
  - Recent searches (TTL: 1 minute)
- Consider read-only connection pool for search queries

**Application:**
- Implement API rate limiting (e.g., 100 req/min per IP)
- Add response caching headers
- Consider pagination cursors instead of offset-based pagination

**Monitoring:**
- Track query performance metrics
- Monitor database size and growth
- Set up alerts for slow queries (>1s)

### Level 3 Optimizations

🚨 **Infrastructure Migration Recommended**

**Database Migration:**
- **Migrate to PostgreSQL** with proper indexes:
  - Use GiST/GIN indexes for full-text search
  - Enable pg_trgm for fuzzy matching
  - Implement database read replicas
- Consider database connection pooling (pgBouncer)

**Search Engine:**
- Implement dedicated search solution:
  - **Elasticsearch** - Full-featured, battle-tested
  - **Meilisearch** - Fast, easy to deploy
  - **Typesense** - Typo-tolerant, great DX
  - **OpenSearch** - Elasticsearch fork, cloud-friendly

**Caching Layer:**
- **Redis** for:
  - Search results (TTL: 1-5 minutes)
  - Facets (TTL: 10 minutes)
  - Statistics (TTL: 5 minutes)
  - API rate limiting
- Consider Redis clustering for high availability

**Application Architecture:**
- Implement read replicas for database
- Add CDN for API responses (CloudFlare, Fastly)
- Use connection pooling (50-100 connections)
- Implement cursor-based pagination
- Add request batching and debouncing on frontend

**Performance Monitoring:**
- APM tool (New Relic, DataDog, or Sentry)
- Database query monitoring
- Real-time performance dashboards
- Automated alerting for degraded performance

**Infrastructure:**
- Container orchestration (Kubernetes) for auto-scaling
- Load balancer for horizontal scaling
- Separate services: API, Search, Indexing workers

## Memory Considerations

### Estimated Database Sizes

- **Level 1**: ~3 MB (100 repos, 1,000 automations)
- **Level 2**: ~12 MB (500 repos, 5,000 automations)
- **Level 3**: ~45 MB (2,000 repos, 20,000 automations)

### Application Memory

- **SQLite overhead**: ~5-10 MB
- **FastAPI runtime**: ~50-100 MB
- **Per concurrent request**: ~2-5 MB

**Recommended Minimum Memory:**
- Level 1: 512 MB RAM
- Level 2: 1 GB RAM
- Level 3: 2-4 GB RAM (depending on concurrent load)

## Frontend Performance Considerations

While these tests focus on backend performance, frontend optimization is equally important:

### Data Fetching
- Implement request debouncing (300ms) for search
- Use SWR or React Query for caching
- Implement optimistic UI updates
- Add infinite scroll instead of traditional pagination

### Rendering
- Virtualize long result lists (react-window, react-virtual)
- Lazy load images and non-critical content
- Implement code splitting by route
- Use React.memo for expensive components

### Network
- Enable HTTP/2 or HTTP/3
- Implement service workers for offline capability
- Use CDN for static assets
- Compress API responses (gzip/brotli)

## Cost Estimates

### Level 1 (Light)
**Hosting Options:**
- Railway: $5/month
- Fly.io: $0-5/month (free tier possible)
- Heroku: $7/month (Eco dynos)
- DigitalOcean: $6/month (1GB Droplet)

**Total Monthly**: $0-7

### Level 2 (Medium)
**Infrastructure:**
- App server: $10-15/month (2GB RAM)
- Redis: $10-15/month (managed service)
- Database: Included (SQLite) or $15/month (managed PostgreSQL)

**Total Monthly**: $20-45

### Level 3 (Heavy)
**Infrastructure:**
- App servers (2x): $40-60/month (4GB RAM each)
- PostgreSQL (managed): $25-50/month
- Redis (managed): $15-30/month
- Elasticsearch/Meilisearch: $30-100/month
- CDN: $5-20/month
- Load balancer: $10-15/month

**Total Monthly**: $125-275

## Continuous Monitoring

### Key Metrics to Track

1. **Response Times**
   - P50, P95, P99 for all API endpoints
   - Target: P95 < 500ms, P99 < 1s

2. **Database Performance**
   - Query execution time
   - Connection pool usage
   - Lock contention

3. **Error Rates**
   - 4xx errors (client errors)
   - 5xx errors (server errors)
   - Target: < 0.1% error rate

4. **Resource Usage**
   - CPU utilization (target: < 70% average)
   - Memory usage (target: < 80% of available)
   - Disk I/O

5. **Business Metrics**
   - Search queries per minute
   - Average results per search
   - Popular search terms
   - Repository growth rate

## Troubleshooting

### Slow Searches
1. Check database indexes are present
2. Analyze slow query logs
3. Consider adding Redis caching
4. Profile code with `cProfile` or `py-spy`

### High Memory Usage
1. Check for connection leaks
2. Review query result set sizes
3. Implement pagination limits
4. Consider moving to PostgreSQL

### Database Lock Contention
1. Reduce transaction scope
2. Implement read replicas
3. Use separate databases for read/write
4. Consider connection pooling

## Next Steps

After running stress tests:

1. **Review Performance Reports**: Check recommendations for your target scale
2. **Implement Optimizations**: Start with quick wins (indexes, caching)
3. **Monitor Production**: Track metrics to validate improvements
4. **Plan for Growth**: Set up infrastructure before you need it
5. **Iterate**: Re-run tests after major changes

## Contributing

To add new stress tests or scenarios:

1. Add test functions to `backend/tests/stress/test_stress.py`
2. Follow existing patterns for metrics collection
3. Generate recommendations based on results
4. Update this documentation

## References

- [SQLite Performance Tuning](https://www.sqlite.org/optoverview.html)
- [FastAPI Performance Tips](https://fastapi.tiangolo.com/async/)
- [PostgreSQL Query Performance](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
