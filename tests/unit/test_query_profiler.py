"""
tests/unit/test_query_profiler.py
=================================
Unit tests for SQLAlchemy QueryProfiler and N+1 detection.
"""

from sqlalchemy import create_engine, text

from shared.query_profiler import QueryProfiler, normalize_sql


def test_normalize_sql():
    raw = "  SELECT   id,   name \n FROM users \n  WHERE id = ?   "
    expected = "SELECT id, name FROM users WHERE id = ?"
    assert normalize_sql(raw) == expected


def test_query_profiler_counts_queries():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test_items (id INTEGER PRIMARY KEY, name TEXT)"))
        conn.commit()

    with QueryProfiler(engine) as profiler:
        with engine.connect() as conn:
            conn.execute(text("INSERT INTO test_items (name) VALUES ('Item 1')"))
            conn.execute(text("INSERT INTO test_items (name) VALUES ('Item 2')"))
            conn.execute(text("SELECT * FROM test_items"))

    stats = profiler.stats
    assert stats.total_queries == 3
    assert len(stats.records) == 3
    assert stats.total_duration_ms >= 0.0


def test_query_profiler_detects_n_plus_one():
    engine = create_engine("sqlite:///:memory:")
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE test_data (id INTEGER PRIMARY KEY, val TEXT)"))
        for i in range(5):
            conn.execute(text(f"INSERT INTO test_data (val) VALUES ('val_{i}')"))
        conn.commit()

    with QueryProfiler(engine) as profiler:
        with engine.connect() as conn:
            for i in range(1, 5):
                conn.execute(text("SELECT * FROM test_data WHERE id = :id"), {"id": i})

    stats = profiler.stats
    assert stats.total_queries == 4
    assert stats.has_n_plus_one is True
    assert stats.max_duplicate_count == 4


def test_query_profiler_slow_query_threshold():
    engine = create_engine("sqlite:///:memory:")
    # Set threshold very low so any query is caught or 0.0 threshold
    with QueryProfiler(engine, slow_threshold_ms=0.0) as profiler:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    stats = profiler.stats
    assert len(stats.slow_queries) >= 1
    assert stats.slow_queries[0].normalized_statement == "SELECT 1"


def test_query_profiler_detaches_after_exit():
    engine = create_engine("sqlite:///:memory:")
    with QueryProfiler(engine) as profiler:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    assert profiler.stats.total_queries == 1

    # Executing query outside the context manager should not be recorded
    with engine.connect() as conn:
        conn.execute(text("SELECT 2"))

    assert profiler.stats.total_queries == 1
