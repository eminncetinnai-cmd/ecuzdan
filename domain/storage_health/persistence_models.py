"""SQLAlchemy metadata models for a future, separately approved migration.

This module is intentionally not imported by the application bootstrap in this
phase. The tables contain only Storage Health metadata and have no foreign keys
or relationships to financial models, tenants, users, transactions, ledgers,
credentials, or file contents.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import declarative_base

metadata = MetaData()
Base = declarative_base(metadata=metadata)


class StorageScanHistoryMetadata(Base):
    """One complete project-scope metadata snapshot."""

    __tablename__ = "storage_scan_history"
    __table_args__ = (
        UniqueConstraint("scope", "snapshot_id", name="uq_storage_history_scope_snapshot"),
        Index("idx_storage_history_scanned_at", "scanned_at_epoch"),
        Index("idx_storage_history_scope_time", "scope", "scanned_at_epoch"),
    )

    history_id = Column(String(32), primary_key=True)
    scope = Column(String(32), nullable=False)
    snapshot_id = Column(String(64), nullable=False)
    scanned_at_epoch = Column(Float, nullable=False)
    total_bytes = Column(BigInteger, nullable=False)
    category_bytes = Column(JSON, nullable=False)
    policy_bytes = Column(JSON, nullable=False)
    protected_bytes = Column(BigInteger, nullable=False)
    candidate_bytes = Column(BigInteger, nullable=False)
    safe_reclaimable_bytes = Column(BigInteger, nullable=False)
    files_scanned = Column(Integer, nullable=False)
    directories_scanned = Column(Integer, nullable=False)
    symlinks_skipped = Column(Integer, nullable=False)
    errors_count = Column(Integer, nullable=False)
    truncated = Column(Boolean, nullable=False)
    schema_version = Column(Integer, nullable=False, default=1)


class StorageCleanupAuditMetadata(Base):
    """Append-only recommendation/cleanup audit metadata without file paths."""

    __tablename__ = "storage_cleanup_audit"
    __table_args__ = (
        Index("idx_storage_audit_candidate", "candidate_id"),
        Index("idx_storage_audit_snapshot", "scan_snapshot_id"),
        Index("idx_storage_audit_created_at", "created_at_epoch"),
    )

    audit_id = Column(String(32), primary_key=True)
    candidate_id = Column(String(24), nullable=False)
    scan_snapshot_id = Column(String(64), nullable=False)
    action = Column(String(40), nullable=False)
    status = Column(String(24), nullable=False)
    risk_level = Column(String(16), nullable=False)
    rollback_strategy = Column(String(32), nullable=False)
    reclaimable_bytes = Column(BigInteger, nullable=False)
    mutation_performed = Column(Boolean, nullable=False, default=False)
    created_at_epoch = Column(Float, nullable=False)
    schema_version = Column(Integer, nullable=False, default=1)


STORAGE_METADATA_TABLES = (
    StorageScanHistoryMetadata.__table__,
    StorageCleanupAuditMetadata.__table__,
)


def render_sqlite_ddl() -> tuple[str, ...]:
    """Render prospective SQLite DDL without connecting to or mutating a DB."""
    from sqlalchemy.dialects.sqlite import dialect
    from sqlalchemy.schema import CreateIndex, CreateTable

    sqlite_dialect = dialect()
    statements: list[str] = []
    for table in STORAGE_METADATA_TABLES:
        statements.append(str(CreateTable(table).compile(dialect=sqlite_dialect)))
        for index in sorted(table.indexes, key=lambda item: item.name or ""):
            statements.append(str(CreateIndex(index).compile(dialect=sqlite_dialect)))
    return tuple(statements)
