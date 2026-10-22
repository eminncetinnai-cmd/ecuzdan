# ruff: noqa: E402
"""Models facade module for backwards compatibility.

All SQLAlchemy ORM models have been modularized into their respective domain packages:
  - domain.tenant.models (Tenant)
  - domain.users.models (User, TenantInvite, StrategySettings, UserPreference, ProfileQuestion, InvestorProfile, InvestorProfileAnswer)
  - domain.catalog.models (Category, AssetType, AssetSector, CategoryAssetTypeMapping, Tag, EntityTag)
  - domain.portfolio.models (Asset, AssetTransaction, AssetUpdate)
  - domain.ledger.models (Account, JournalEntry, LedgerLine)
  - domain.transactions.models (Transaction, RecurringPlan, Payment, PlanOccurrence, LedgerAdjustment, LedgerAuditEvent, LogbookEntry)
  - domain.reconciliation.models (BankAccount, BankStatementSnapshot)
  - domain.notifications.models (Notification)
  - domain.admin.models (QuizQuestion, QuizAttempt, UserProgress, UserAchievement, BackupMetadata, AuditLog, MonitoringAlertConfig)
  - infrastructure.database.models.outbox_model (OutboxMessageModel)

This facade re-exports all models and helpers to ensure complete backwards compatibility.
"""
from datetime import datetime, timezone

from shared.db import db


def utcnow_naive():
    """UTC zamanı naive datetime olarak döndürür."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# Domain models
from domain.admin.models.audit_models import AuditLog, BackupMetadata, MonitoringAlertConfig
from domain.admin.models.education_models import QuizAttempt, QuizQuestion, UserAchievement, UserProgress
from domain.catalog.models.catalog_models import AssetSector, AssetType, Category
from domain.catalog.models.tag_models import CategoryAssetTypeMapping, EntityTag, Tag
from domain.ledger.models.ledger_models import Account, JournalEntry, LedgerLine
from domain.notifications.models.notification_models import Notification
from domain.portfolio.models.portfolio_models import Asset, AssetTransaction, AssetUpdate
from domain.reconciliation.models.bank_models import BankAccount, BankStatementSnapshot
from domain.tenant.models.tenant_models import Tenant
from domain.transactions.models.transaction_models import (
    LedgerAdjustment,
    LedgerAuditEvent,
    LogbookEntry,
    Payment,
    PlanOccurrence,
    RecurringPlan,
    Transaction,
    UserIban,
)
from domain.users.models.profile_models import InvestorProfile, InvestorProfileAnswer, ProfileQuestion
from domain.users.models.user_models import StrategySettings, TenantInvite, User, UserPreference
from infrastructure.database.models.outbox_model import OutboxMessageModel

__all__ = [
    # Database instance & helpers
    'db',
    'utcnow_naive',
    # Tenant
    'Tenant',
    # Users & Auth
    'User',
    'TenantInvite',
    'StrategySettings',
    'UserPreference',
    'InvestorProfile',
    'InvestorProfileAnswer',
    'ProfileQuestion',
    # Catalog
    'Category',
    'AssetType',
    'AssetSector',
    'CategoryAssetTypeMapping',
    'Tag',
    'EntityTag',
    # Portfolio
    'Asset',
    'AssetTransaction',
    'AssetUpdate',
    # Ledger
    'Account',
    'JournalEntry',
    'LedgerLine',
    # Transactions & Planning
    'Transaction',
    'RecurringPlan',
    'Payment',
    'PlanOccurrence',
    'LedgerAdjustment',
    'LedgerAuditEvent',
    'LogbookEntry',
    'UserIban',
    # Banking & Reconciliation
    'BankAccount',
    'BankStatementSnapshot',
    # Notifications
    'Notification',
    # Education & Gamification
    'QuizQuestion',
    'QuizAttempt',
    'UserProgress',
    'UserAchievement',
    # Audit & Monitoring
    'BackupMetadata',
    'AuditLog',
    'MonitoringAlertConfig',
    'OutboxMessageModel',
]
