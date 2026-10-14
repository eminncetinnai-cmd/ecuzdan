"""
shared/query_profiler.py
========================
SQLAlchemy SQL Query Profiler & N+1 Performance Analyzer.

Intercepts database queries via SQLAlchemy engine events to detect:
1. Total query counts per request/operation (Budget Enforcement).
2. Duplicate query templates (N+1 Query Pattern Detection).
3. Slow queries exceeding latency thresholds.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sqlalchemy import event


@dataclass
class QueryRecord:
    """Detailed record of a single intercepted SQL query."""
    statement: str
    normalized_statement: str
    parameters: Any
    duration_ms: float
    timestamp: float


@dataclass
class QueryStats:
    """Aggregated statistics for a profiling session."""
    total_queries: int
    total_duration_ms: float
    duplicate_patterns: Dict[str, int]
    slow_queries: List[QueryRecord]
    records: List[QueryRecord] = field(default_factory=list)

    @property
    def has_n_plus_one(self) -> bool:
        """True if any single query template was repeated 3 or more times."""
        return any(count >= 3 for count in self.duplicate_patterns.values())

    @property
    def max_duplicate_count(self) -> int:
        return max(self.duplicate_patterns.values(), default=0)


def normalize_sql(statement: str) -> str:
    """Normalize SQL whitespace and casing for reliable template grouping."""
    cleaned = re.sub(r"\s+", " ", statement).strip()
    return cleaned


class QueryProfiler:
    """
    Context manager that profiles all SQLAlchemy queries executed within its scope.

    Usage:
        with QueryProfiler(engine) as profiler:
            db.session.query(Transaction).all()

        assert profiler.stats.total_queries <= 10
        assert not profiler.stats.has_n_plus_one
    """

    def __init__(self, engine, slow_threshold_ms: float = 50.0):
        self.engine = engine
        self.slow_threshold_ms = slow_threshold_ms
        self._records: List[QueryRecord] = []
        self._start_time: Optional[float] = None
        self._query_start_times: Dict[Any, float] = {}
        self._active = False

    def __enter__(self) -> "QueryProfiler":
        self._records.clear()
        self._query_start_times.clear()
        self._start_time = time.perf_counter()
        self._active = True
        self._attach_listeners()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._active = False
        self._detach_listeners()

    def _attach_listeners(self) -> None:
        event.listen(self.engine, "before_cursor_execute", self._before_cursor_execute)
        event.listen(self.engine, "after_cursor_execute", self._after_cursor_execute)

    def _detach_listeners(self) -> None:
        try:
            event.remove(self.engine, "before_cursor_execute", self._before_cursor_execute)
            event.remove(self.engine, "after_cursor_execute", self._after_cursor_execute)
        except Exception:
            pass

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not self._active:
            return
        # Store start time keyed by connection cursor context or timestamp
        self._query_start_times[id(cursor)] = time.perf_counter()

    def _after_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if not self._active:
            return
        end_time = time.perf_counter()
        start_time = self._query_start_times.pop(id(cursor), end_time)
        duration_ms = (end_time - start_time) * 1000.0

        norm_sql = normalize_sql(statement)
        record = QueryRecord(
            statement=statement,
            normalized_statement=norm_sql,
            parameters=parameters,
            duration_ms=duration_ms,
            timestamp=end_time,
        )
        self._records.append(record)

    @property
    def stats(self) -> QueryStats:
        """Compute aggregated query statistics."""
        duplicates: Dict[str, int] = {}
        slow: List[QueryRecord] = []
        total_dur = 0.0

        for r in self._records:
            total_dur += r.duration_ms
            duplicates[r.normalized_statement] = duplicates.get(r.normalized_statement, 0) + 1
            if r.duration_ms >= self.slow_threshold_ms:
                slow.append(r)

        # Filter duplicates to only those appearing more than once
        repeated_patterns = {stmt: count for stmt, count in duplicates.items() if count > 1}

        return QueryStats(
            total_queries=len(self._records),
            total_duration_ms=round(total_dur, 2),
            duplicate_patterns=repeated_patterns,
            slow_queries=slow,
            records=list(self._records),
        )

    def assert_max_queries(self, limit: int) -> None:
        """Assert that total query count does not exceed limit."""
        actual = self.stats.total_queries
        if actual > limit:
            raise AssertionError(f"Query count budget exceeded: expected <= {limit}, got {actual}")

    def assert_no_n_plus_one(self, max_allowed_repeats: int = 2) -> None:
        """Assert that no single SQL statement template was repeated excessively."""
        repeated = {stmt: cnt for stmt, cnt in self.stats.duplicate_patterns.items() if cnt > max_allowed_repeats}
        if repeated:
            top_violator = max(repeated.items(), key=lambda x: x[1])
            raise AssertionError(
                f"N+1 Query pattern detected! Statement was executed {top_violator[1]} times:\n"
                f"{top_violator[0]}"
            )
