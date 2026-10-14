"""Prospective Storage Health metadata migration plan.

This module renders and fingerprints DDL only. It never opens the active
financial database, runs migrations, creates tables, or inspects financial rows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from domain.storage_health.persistence_models import STORAGE_METADATA_TABLES, render_sqlite_ddl


class MigrationReadiness(StrEnum):
    DRY_RUN_ONLY = "dry_run_only"
    READY_FOR_REVIEW = "ready_for_review"
    APPROVED = "approved"


class SchemaDiffStatus(StrEnum):
    PROSPECTIVE_MANIFEST_ONLY = "prospective_manifest_only"
    ACTIVE_DB_NOT_INSPECTED = "active_db_not_inspected"
    ACTIVE_DB_MATCH = "active_db_match"
    ACTIVE_DB_MISMATCH = "active_db_mismatch"


@dataclass(frozen=True, slots=True)
class RollbackPrerequisites:
    backup_required: bool
    backup_verified: bool
    restore_tested: bool
    maintenance_window_required: bool
    process_ownership_verified: bool
    notes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.backup_required and self.backup_verified:
            raise ValueError("backup_verified cannot be true when backup is not required")
        if self.restore_tested and not self.backup_verified:
            raise ValueError("restore_tested requires backup_verified")
        if self.process_ownership_verified and not self.maintenance_window_required:
            raise ValueError("process ownership verification requires a maintenance window")

    def to_dict(self) -> dict:
        return {
            "backup_required": self.backup_required,
            "backup_verified": self.backup_verified,
            "restore_tested": self.restore_tested,
            "maintenance_window_required": self.maintenance_window_required,
            "process_ownership_verified": self.process_ownership_verified,
            "notes": list(self.notes),
        }


@dataclass(frozen=True, slots=True)
class MetadataMigrationPlan:
    plan_id: str
    ddl_sha256: str
    table_names: tuple[str, ...]
    index_names: tuple[str, ...]
    statement_count: int
    foreign_key_count: int
    schema_diff_status: SchemaDiffStatus
    schema_diff: tuple[str, ...]
    readiness: MigrationReadiness
    blocking_reasons: tuple[str, ...]
    rollback: RollbackPrerequisites
    active_db_inspected: bool = False
    migration_executed: bool = False
    financial_rows_read: bool = False

    def __post_init__(self) -> None:
        if len(self.plan_id) != 32 or any(char not in "0123456789abcdef" for char in self.plan_id):
            raise ValueError("plan_id must be a 32-character lowercase hex value")
        if len(self.ddl_sha256) != 64 or any(char not in "0123456789abcdef" for char in self.ddl_sha256):
            raise ValueError("ddl_sha256 must be a 64-character lowercase SHA-256 hex value")
        if self.statement_count != len(self.table_names) + len(self.index_names):
            raise ValueError("statement_count must equal table and index statement count")
        if self.foreign_key_count < 0:
            raise ValueError("foreign_key_count cannot be negative")
        if not self.schema_diff:
            raise ValueError("schema_diff must explain the prospective or inspected result")
        if not self.active_db_inspected and self.schema_diff_status in {
            SchemaDiffStatus.ACTIVE_DB_MATCH,
            SchemaDiffStatus.ACTIVE_DB_MISMATCH,
        }:
            raise ValueError("active DB diff status requires active_db_inspected")
        if self.active_db_inspected or self.migration_executed or self.financial_rows_read:
            raise ValueError("prospective migration plan cannot inspect or mutate active financial DB")
        if self.readiness is MigrationReadiness.APPROVED:
            raise ValueError("active approval is not representable by a dry-run plan")

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "ddl_sha256": self.ddl_sha256,
            "table_names": list(self.table_names),
            "index_names": list(self.index_names),
            "statement_count": self.statement_count,
            "foreign_key_count": self.foreign_key_count,
            "schema_diff_status": self.schema_diff_status.value,
            "schema_diff": list(self.schema_diff),
            "readiness": self.readiness.value,
            "blocking_reasons": list(self.blocking_reasons),
            "rollback": self.rollback.to_dict(),
            "active_db_inspected": self.active_db_inspected,
            "migration_executed": self.migration_executed,
            "financial_rows_read": self.financial_rows_read,
        }


def build_metadata_migration_plan() -> MetadataMigrationPlan:
    """Build a review-only plan from model metadata and compiled SQLite DDL."""
    ddl_statements = tuple(sorted(render_sqlite_ddl()))
    ddl_payload = json.dumps(
        ddl_statements,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    ddl_sha256 = hashlib.sha256(ddl_payload).hexdigest()

    table_names = tuple(sorted(table.name for table in STORAGE_METADATA_TABLES))
    index_names = tuple(
        sorted(
            index.name
            for table in STORAGE_METADATA_TABLES
            for index in table.indexes
            if index.name
        )
    )
    identity_payload = json.dumps(
        {
            "schema": "storage-health-metadata-migration-v1",
            "ddl_sha256": ddl_sha256,
            "tables": table_names,
            "indexes": index_names,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    plan_id = hashlib.sha256(identity_payload).hexdigest()[:32]

    rollback = RollbackPrerequisites(
        backup_required=True,
        backup_verified=False,
        restore_tested=False,
        maintenance_window_required=True,
        process_ownership_verified=False,
        notes=(
            "active_financial_db_backup_required",
            "restore_test_required_before_migration",
            "owner_approved_maintenance_window_required",
            "metadata_tables_have_no_financial_foreign_keys",
        ),
    )
    blockers = (
        "active_db_schema_diff_not_inspected",
        "migration_not_authorized",
        "backup_verification_required",
        "restore_test_required",
        "maintenance_window_required",
    )
    return MetadataMigrationPlan(
        plan_id=plan_id,
        ddl_sha256=ddl_sha256,
        table_names=table_names,
        index_names=index_names,
        statement_count=len(ddl_statements),
        foreign_key_count=sum(len(table.foreign_keys) for table in STORAGE_METADATA_TABLES),
        schema_diff_status=SchemaDiffStatus.PROSPECTIVE_MANIFEST_ONLY,
        schema_diff=(
            "active_db_schema_not_inspected",
            "prospective_tables_and_indexes_compiled",
            "financial_foreign_keys_expected:0",
        ),
        readiness=MigrationReadiness.DRY_RUN_ONLY,
        blocking_reasons=blockers,
        rollback=rollback,
    )
