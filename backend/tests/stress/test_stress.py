"""
Comprehensive stress tests for hadiscover backend.

Tests database and API performance under 3 intensity levels:
- Level 1 (Light): 100 repos, 1000 automations
- Level 2 (Medium): 500 repos, 5000 automations  
- Level 3 (Heavy): 2000 repos, 20000 automations
"""

import logging
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import pytest
from app.models.database import Automation, Base, Repository
from app.services.search_service import SearchService
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


class StressTestMetrics:
    """Collect and report stress test metrics."""

    def __init__(self, level: str):
        self.level = level
        self.metrics: Dict[str, List[float]] = {}

    def record(self, operation: str, duration: float):
        """Record a timed operation."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(duration)

    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics or not self.metrics[operation]:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        durations = self.metrics[operation]
        return {
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / len(durations),
            "count": len(durations),
        }

    def print_report(self, recommendations: List[str]):
        """Print comprehensive performance report."""
        print(f"\n{'=' * 80}")
        print(f"STRESS TEST RESULTS - {self.level}")
        print(f"{'=' * 80}\n")

        for operation, durations in sorted(self.metrics.items()):
            stats = self.get_stats(operation)
            print(f"{operation}:")
            print(f"  Count: {stats['count']}")
            print(f"  Min: {stats['min']:.4f}s")
            print(f"  Max: {stats['max']:.4f}s")
            print(f"  Avg: {stats['avg']:.4f}s")
            print()

        print(f"\n{'=' * 80}")
        print(f"PERFORMANCE RECOMMENDATIONS - {self.level}")
        print(f"{'=' * 80}\n")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        print(f"\n{'=' * 80}\n")


def generate_test_data(
    num_repos: int, num_automations: int
) -> Tuple[List[Dict], List[Dict]]:
    """
    Generate test repository and automation data.

    Args:
        num_repos: Number of repositories to generate
        num_automations: Number of automations to generate (distributed across repos)

    Returns:
        Tuple of (repositories list, automations list)
    """
    repos = []
    automations = []

    # Common trigger types and action calls for realistic data
    trigger_types = [
        "state",
        "numeric_state",
        "time",
        "webhook",
        "event",
        "mqtt",
        "template",
        "sun",
        "zone",
        "device",
    ]

    action_calls = [
        "light.turn_on",
        "light.turn_off",
        "switch.turn_on",
        "switch.turn_off",
        "notify.mobile_app",
        "climate.set_temperature",
        "media_player.play_media",
        "media_player.volume_set",
        "script.execute",
        "automation.trigger",
        "scene.turn_on",
        "homeassistant.restart",
    ]

    # Generate repositories
    for i in range(num_repos):
        repos.append(
            {
                "name": f"home-assistant-config-{i}",
                "owner": f"user{i % 100}",  # Create some overlap in owners
                "description": f"Home Assistant configuration {i} with various automations",
                "url": f"https://github.com/user{i % 100}/home-assistant-config-{i}",
                "stars": (i * 7) % 500,  # Varied star counts
            }
        )

    # Generate automations distributed across repos
    automations_per_repo = num_automations // num_repos
    extra_automations = num_automations % num_repos

    auto_id = 0
    for repo_idx in range(num_repos):
        # Determine how many automations for this repo
        count = automations_per_repo + (1 if repo_idx < extra_automations else 0)

        for j in range(count):
            # Vary the number of triggers and actions (1-3 each)
            num_triggers = 1 + (auto_id % 3)
            num_actions = 1 + ((auto_id + 1) % 3)

            trigger_list = [
                trigger_types[(auto_id + k) % len(trigger_types)]
                for k in range(num_triggers)
            ]
            action_list = [
                action_calls[(auto_id + k) % len(action_calls)]
                for k in range(num_actions)
            ]

            # Some automations use blueprints
            blueprint = None
            if auto_id % 5 == 0:
                blueprint = f"blueprint/automation/motion_light_v{auto_id % 3 + 1}.yaml"

            automations.append(
                {
                    "alias": f"Automation {auto_id} - {trigger_list[0].replace('_', ' ').title()}",
                    "description": f"Test automation {auto_id} that handles {', '.join(trigger_list)} triggers and calls {', '.join(action_list)}",
                    "trigger_types": ",".join(trigger_list),
                    "action_calls": ",".join(action_list),
                    "blueprint_path": blueprint,
                    "source_file_path": "automations.yaml",
                    "github_url": f"https://github.com/user{repo_idx % 100}/home-assistant-config-{repo_idx}/blob/main/automations.yaml#L{auto_id * 10}",
                    "start_line": auto_id * 10,
                    "end_line": auto_id * 10 + 8,
                    "repository_idx": repo_idx,
                }
            )
            auto_id += 1

    return repos, automations


def populate_database(
    db: Session, num_repos: int, num_automations: int, metrics: StressTestMetrics
) -> Tuple[int, int]:
    """
    Populate database with test data.

    Args:
        db: Database session
        num_repos: Number of repositories
        num_automations: Number of automations
        metrics: Metrics collector

    Returns:
        Tuple of (actual repos created, actual automations created)
    """
    logger.info(
        f"Generating test data: {num_repos} repos, {num_automations} automations"
    )
    start = time.time()
    repos_data, automations_data = generate_test_data(num_repos, num_automations)
    metrics.record("data_generation", time.time() - start)

    # Batch insert repositories
    logger.info("Inserting repositories...")
    start = time.time()
    repo_objects = []
    for repo_data in repos_data:
        repo = Repository(**repo_data)
        repo_objects.append(repo)

    db.add_all(repo_objects)
    db.commit()
    metrics.record("insert_repositories", time.time() - start)

    # Batch insert automations (in chunks for memory efficiency)
    logger.info("Inserting automations...")
    chunk_size = 1000
    automation_count = 0

    for i in range(0, len(automations_data), chunk_size):
        chunk = automations_data[i : i + chunk_size]
        start = time.time()

        automation_objects = []
        for auto_data in chunk:
            repo_idx = auto_data.pop("repository_idx")
            auto_data["repository_id"] = repo_objects[repo_idx].id
            automation = Automation(**auto_data)
            automation_objects.append(automation)

        db.add_all(automation_objects)
        db.commit()
        automation_count += len(automation_objects)

        metrics.record(f"insert_automations_chunk_{i // chunk_size}", time.time() - start)
        if (i + chunk_size) % 5000 == 0:
            logger.info(f"Inserted {automation_count} automations...")

    logger.info(f"Database populated: {len(repo_objects)} repos, {automation_count} automations")
    return len(repo_objects), automation_count


def run_search_performance_tests(
    db: Session, metrics: StressTestMetrics
) -> Dict[str, any]:
    """
    Run various search performance tests.

    Args:
        db: Database session
        metrics: Metrics collector

    Returns:
        Dictionary with performance results
    """
    results = {}

    # Test 1: Simple text search
    test_queries = [
        "light",
        "temperature",
        "motion",
        "notification",
        "media_player",
    ]

    for query in test_queries:
        start = time.time()
        search_results, total = SearchService.search_automations(
            db, query, page=1, per_page=50
        )
        duration = time.time() - start
        metrics.record(f"search_text_{query}", duration)
        results[f"search_{query}"] = {"count": len(search_results), "total": total, "duration": duration}

    # Test 2: Empty query (recent automations)
    start = time.time()
    search_results, total = SearchService.search_automations(db, "", page=1, per_page=50)
    duration = time.time() - start
    metrics.record("search_empty_recent", duration)
    results["search_recent"] = {"count": len(search_results), "total": total, "duration": duration}

    # Test 3: Filtered search by trigger type
    start = time.time()
    search_results, total = SearchService.search_automations(
        db, "automation", trigger_filter="state", page=1, per_page=50
    )
    duration = time.time() - start
    metrics.record("search_filtered_trigger", duration)
    results["search_trigger_filter"] = {"count": len(search_results), "total": total, "duration": duration}

    # Test 4: Filtered search by action domain
    start = time.time()
    search_results, total = SearchService.search_automations(
        db, "", action_domain_filter="light", page=1, per_page=50
    )
    duration = time.time() - start
    metrics.record("search_filtered_action_domain", duration)
    results["search_action_domain_filter"] = {"count": len(search_results), "total": total, "duration": duration}

    # Test 5: Pagination (multiple pages)
    for page in [1, 2, 5, 10]:
        start = time.time()
        search_results, total = SearchService.search_automations(
            db, "automation", page=page, per_page=50
        )
        duration = time.time() - start
        metrics.record(f"search_pagination_page_{page}", duration)

    return results


def run_facet_performance_tests(db: Session, metrics: StressTestMetrics) -> Dict[str, any]:
    """
    Run facet generation performance tests.

    Args:
        db: Database session
        metrics: Metrics collector

    Returns:
        Dictionary with facet performance results
    """
    results = {}

    # Test 1: Get all facets without filters
    start = time.time()
    facets = SearchService.get_facets(db, query="")
    duration = time.time() - start
    metrics.record("facets_no_filter", duration)
    results["facets_all"] = {
        "duration": duration,
        "repo_count": len(facets.get("repositories", [])),
        "trigger_count": len(facets.get("triggers", [])),
        "action_domain_count": len(facets.get("action_domains", [])),
    }

    # Test 2: Get facets with search query
    start = time.time()
    facets = SearchService.get_facets(db, query="light")
    duration = time.time() - start
    metrics.record("facets_with_query", duration)
    results["facets_filtered"] = {
        "duration": duration,
        "repo_count": len(facets.get("repositories", [])),
    }

    # Test 3: Get facets with multiple filters
    start = time.time()
    facets = SearchService.get_facets(db, query="automation", trigger_filter="state")
    duration = time.time() - start
    metrics.record("facets_with_trigger_filter", duration)

    return results


def run_statistics_tests(db: Session, metrics: StressTestMetrics) -> Dict[str, any]:
    """
    Run statistics query performance tests.

    Args:
        db: Database session
        metrics: Metrics collector

    Returns:
        Dictionary with statistics results
    """
    start = time.time()
    stats = SearchService.get_statistics(db)
    duration = time.time() - start
    metrics.record("statistics_query", duration)

    return {
        "duration": duration,
        "total_repositories": stats["total_repositories"],
        "total_automations": stats["total_automations"],
    }


def run_concurrent_queries(
    db: Session, num_concurrent: int, metrics: StressTestMetrics
) -> Dict[str, any]:
    """
    Simulate concurrent query load.
    
    Note: Since we're using in-memory SQLite which has limitations with 
    concurrent access, this test simulates concurrency by running queries 
    sequentially but measuring the overhead and performance characteristics.
    In production with PostgreSQL, true concurrent access would be tested.

    Args:
        db: Database session
        num_concurrent: Number of concurrent operations to simulate
        metrics: Metrics collector

    Returns:
        Dictionary with concurrency test results
    """
    queries = ["light", "motion", "temperature", "notify", "media"]
    durations = []

    start = time.time()
    for i in range(num_concurrent):
        query = queries[i % len(queries)]
        
        query_start = time.time()
        SearchService.search_automations(db, query, page=1, per_page=20)
        duration = time.time() - query_start
        durations.append(duration)
        metrics.record("concurrent_query_individual", duration)

    total_duration = time.time() - start
    metrics.record("concurrent_queries_total", total_duration)

    return {
        "total_duration": total_duration,
        "num_queries": num_concurrent,
        "avg_individual": sum(durations) / len(durations) if durations else 0,
        "max_individual": max(durations) if durations else 0,
    }


def analyze_performance_and_recommend(
    level: str,
    num_repos: int,
    num_automations: int,
    metrics: StressTestMetrics,
    search_results: Dict,
    concurrent_results: Dict,
) -> List[str]:
    """
    Analyze performance metrics and generate recommendations.

    Args:
        level: Test level name
        num_repos: Number of repositories tested
        num_automations: Number of automations tested
        metrics: Collected metrics
        search_results: Search performance results
        concurrent_results: Concurrent query results

    Returns:
        List of recommendations
    """
    recommendations = []

    # Check database insert performance
    insert_stats = metrics.get_stats("insert_repositories")
    if insert_stats["avg"] > 5.0:
        recommendations.append(
            f"Repository insertion took {insert_stats['avg']:.2f}s. Consider using bulk insert optimizations or batching."
        )

    # Check search performance
    search_avg = metrics.get_stats("search_text_light")
    if search_avg["avg"] > 1.0:
        recommendations.append(
            f"Text search averaging {search_avg['avg']:.2f}s. Consider adding full-text search indexes or migrating to PostgreSQL with pg_trgm."
        )
    elif search_avg["avg"] > 0.5:
        recommendations.append(
            f"Text search averaging {search_avg['avg']:.2f}s. Performance acceptable but monitor as data grows."
        )

    # Check facet generation performance
    facet_stats = metrics.get_stats("facets_no_filter")
    if facet_stats["avg"] > 2.0:
        recommendations.append(
            f"Facet generation took {facet_stats['avg']:.2f}s. Consider implementing Redis caching for facets (TTL: 5-10 minutes)."
        )
    elif facet_stats["avg"] > 1.0:
        recommendations.append(
            f"Facet generation took {facet_stats['avg']:.2f}s. Consider caching facets or using materialized views."
        )

    # Check concurrent query performance
    if concurrent_results:
        max_individual = concurrent_results.get("max_individual", 0)
        if max_individual > 2.0:
            recommendations.append(
                f"Max concurrent query time was {max_individual:.2f}s. Database connection pooling may be needed."
            )

    # Level-specific recommendations
    if level == "LEVEL 1 (LIGHT)":
        recommendations.append(
            "Current performance is suitable for small deployments (<100 repos). SQLite is sufficient."
        )
    elif level == "LEVEL 2 (MEDIUM)":
        recommendations.append(
            "For medium scale (500+ repos), consider: 1) Connection pooling, 2) Query result caching, 3) API rate limiting"
        )
        if facet_stats["avg"] > 1.0:
            recommendations.append(
                "Implement Redis for caching facets, statistics, and recent searches."
            )
    elif level == "LEVEL 3 (HEAVY)":
        recommendations.append(
            "At this scale (2000+ repos), strongly consider: 1) Migration to PostgreSQL with proper indexes, "
            "2) Elasticsearch/OpenSearch for full-text search, 3) Redis for caching, 4) CDN for API responses"
        )
        recommendations.append(
            "Implement database read replicas for search queries to separate read/write load."
        )
        recommendations.append(
            "Consider implementing API pagination with cursor-based approach instead of offset-based."
        )
        if search_avg["avg"] > 0.5:
            recommendations.append(
                "Search performance degrading. Implement dedicated search engine (Elasticsearch/Meilisearch/Typesense)."
            )

    # Memory recommendations
    db_size_estimate = (num_repos * 1 + num_automations * 2) / 1024  # Rough MB estimate
    recommendations.append(
        f"Estimated database size: ~{db_size_estimate:.1f}MB for {num_repos} repos and {num_automations} automations."
    )

    # Database optimization recommendations
    recommendations.append(
        "Ensure indexes exist on: repositories.url, automations.alias, automations.repository_id, automations.blueprint_path"
    )

    return recommendations


@pytest.fixture
def stress_test_db():
    """Create an in-memory database for stress testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db, engine
    finally:
        db.close()
        engine.dispose()


def test_stress_level_1_light(stress_test_db):
    """
    Stress Test Level 1: Light Load
    - 100 repositories
    - 1000 automations (10 per repo average)
    """
    db, engine = stress_test_db
    metrics = StressTestMetrics("LEVEL 1 (LIGHT)")

    # Populate database
    num_repos = 100
    num_automations = 1000
    logger.info("=" * 80)
    logger.info(f"Starting Level 1 Stress Test: {num_repos} repos, {num_automations} automations")
    logger.info("=" * 80)

    repos_created, autos_created = populate_database(
        db, num_repos, num_automations, metrics
    )

    # Run search tests
    search_results = run_search_performance_tests(db, metrics)

    # Run facet tests
    facet_results = run_facet_performance_tests(db, metrics)

    # Run statistics tests
    stats_results = run_statistics_tests(db, metrics)

    # Run concurrent query test (10 concurrent)
    concurrent_results = run_concurrent_queries(db, 10, metrics)

    # Generate recommendations
    recommendations = analyze_performance_and_recommend(
        "LEVEL 1 (LIGHT)",
        repos_created,
        autos_created,
        metrics,
        search_results,
        concurrent_results,
    )

    # Print report
    metrics.print_report(recommendations)

    # Assertions
    assert repos_created == num_repos
    assert autos_created == num_automations
    assert stats_results["total_repositories"] == num_repos
    assert stats_results["total_automations"] == num_automations


def test_stress_level_2_medium(stress_test_db):
    """
    Stress Test Level 2: Medium Load
    - 500 repositories
    - 5000 automations (10 per repo average)
    """
    db, engine = stress_test_db
    metrics = StressTestMetrics("LEVEL 2 (MEDIUM)")

    # Populate database
    num_repos = 500
    num_automations = 5000
    logger.info("=" * 80)
    logger.info(f"Starting Level 2 Stress Test: {num_repos} repos, {num_automations} automations")
    logger.info("=" * 80)

    repos_created, autos_created = populate_database(
        db, num_repos, num_automations, metrics
    )

    # Run search tests
    search_results = run_search_performance_tests(db, metrics)

    # Run facet tests
    facet_results = run_facet_performance_tests(db, metrics)

    # Run statistics tests
    stats_results = run_statistics_tests(db, metrics)

    # Run concurrent query test (25 concurrent)
    concurrent_results = run_concurrent_queries(db, 25, metrics)

    # Generate recommendations
    recommendations = analyze_performance_and_recommend(
        "LEVEL 2 (MEDIUM)",
        repos_created,
        autos_created,
        metrics,
        search_results,
        concurrent_results,
    )

    # Print report
    metrics.print_report(recommendations)

    # Assertions
    assert repos_created == num_repos
    assert autos_created == num_automations
    assert stats_results["total_repositories"] == num_repos
    assert stats_results["total_automations"] == num_automations


def test_stress_level_3_heavy(stress_test_db):
    """
    Stress Test Level 3: Heavy Load
    - 2000 repositories
    - 20000 automations (10 per repo average)
    """
    db, engine = stress_test_db
    metrics = StressTestMetrics("LEVEL 3 (HEAVY)")

    # Populate database
    num_repos = 2000
    num_automations = 20000
    logger.info("=" * 80)
    logger.info(f"Starting Level 3 Stress Test: {num_repos} repos, {num_automations} automations")
    logger.info("=" * 80)

    repos_created, autos_created = populate_database(
        db, num_repos, num_automations, metrics
    )

    # Run search tests
    search_results = run_search_performance_tests(db, metrics)

    # Run facet tests
    facet_results = run_facet_performance_tests(db, metrics)

    # Run statistics tests
    stats_results = run_statistics_tests(db, metrics)

    # Run concurrent query test (50 concurrent)
    concurrent_results = run_concurrent_queries(db, 50, metrics)

    # Generate recommendations
    recommendations = analyze_performance_and_recommend(
        "LEVEL 3 (HEAVY)",
        repos_created,
        autos_created,
        metrics,
        search_results,
        concurrent_results,
    )

    # Print report
    metrics.print_report(recommendations)

    # Assertions
    assert repos_created == num_repos
    assert autos_created == num_automations
    assert stats_results["total_repositories"] == num_repos
    assert stats_results["total_automations"] == num_automations
