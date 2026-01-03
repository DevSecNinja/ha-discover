# GitHub Issues Update Instructions

This directory contains prepared content for updating GitHub issues based on the performance test insights from PR #84.

## Files

### 1. ISSUE_55_UPDATE.md
Content to **update** existing issue #55 ("Add support for external databases")

**What to do:**
1. Go to https://github.com/DevSecNinja/hadiscover/issues/55
2. Click "Edit" on the issue description
3. Replace the current (empty) description with the content from `ISSUE_55_UPDATE.md`
4. Save the changes

**Summary of updates:**
- Comprehensive performance test insights from PR #84
- Three-level scaling analysis (L1: 100 repos, L2: 500 repos, L3: 2K repos)
- Specific bottlenecks identified (SQLite LIKE queries, facet aggregation)
- Phased migration approach:
  - Phase 1: Redis caching (Level 2)
  - Phase 2: PostgreSQL + Search Engine (Level 3)
  - Phase 3: Horizontal scaling (Level 3+)
- Cost estimates for each configuration ($0-7 to $125-275/month)
- Implementation priorities and success metrics
- Link to new caching issue

### 2. NEW_CACHING_ISSUE.md
Content for **creating** a new issue about implementing Redis caching

**What to do:**
1. Go to https://github.com/DevSecNinja/hadiscover/issues/new
2. Use the title: "Implement Redis caching for facets, search results, and statistics"
3. Add labels: `enhancement`, `backend`, `performance`
4. Paste the content from `NEW_CACHING_ISSUE.md` as the issue description
5. After creating the issue, note the issue number (e.g., #91)
6. Go back to issue #55 and replace `[NEW_CACHING_ISSUE]` with the actual issue number

**Summary of new issue:**
- Addresses medium-scale (Level 2) performance bottleneck
- Four-week implementation plan
- Caches facets (70-80% improvement), search results (80% improvement), and statistics
- Includes rate limiting implementation
- Complete with configuration, testing requirements, and rollout strategy
- Cost: +$10-20/month for production Redis
- Priority: High (addresses critical bottleneck before expensive migration)

## Post-Creation Tasks

After creating the new caching issue (let's say it's #91):

1. **Update issue #55:**
   - Replace all instances of `[NEW_CACHING_ISSUE]` with `#91`
   
2. **Update issue #91 (the new caching issue):**
   - The content already references issue #55, which is correct
   
3. **Optional: Update PR #84 description:**
   - Add a comment linking to the updated issues
   - "Performance test results have been incorporated into issue #55 and led to the creation of issue #91 for caching implementation"

## Context

This update is based on:
- **PR #84**: Comprehensive stress testing framework with 3 levels
  - Level 1 (100 repos): SQLite sufficient
  - Level 2 (500 repos): Caching recommended (4-12x facet slowdown)
  - Level 3 (2,000 repos): Full migration required (6-12x overall slowdown)
- **Key finding**: Non-linear performance degradation, especially in facet generation
- **Recommendation**: Phased approach starting with Redis caching before expensive infrastructure migration

## Summary

The stress tests revealed that:
1. **Current SQLite is great** for small deployments (Level 1)
2. **Redis caching is crucial** for medium deployments (Level 2) - this is the new issue
3. **External databases needed** for large deployments (Level 3) - this is issue #55

This creates a clear, cost-effective scaling path for hadiscover deployments.
