"""
Repository Layer — repositories/__init__.py

Veritabanı erişimi (SQLAlchemy sorguları) ve veri kalıcılığı katmanı.

Temel Kurallar:
  - İş mantığı İÇERMEZ (iş mantığı domain/ katmanındadır).
  - Her sorguda 'tenant_id' filtresi zorunludur (BaseRepository / TenantScopedRepository).
  - Flask HTTP nesneleri (request, response) doğrudan kullanılmamalıdır.

Ana Repository Sınıfları:
  - BaseRepository, TenantScopedRepository (repositories.base)
  - FinancialRepository (repositories.financial_repository)
  - UserRepository (repositories.user_repository)
  - CategoryRepository, TenantCategoryRepository (repositories.category_repository)
  - PortfolioRepository (repositories.portfolio_repository)
  - NotificationRepository (repositories.notification_repository)
"""

from .base import BaseRepository, TenantScopedRepository
from .category_repository import CategoryRepository, TenantCategoryRepository
from .financial_education_repository import FinancialEducationRepository
from .financial_repository import FinancialRepository
from .monitoring_repository import MonitoringRepository
from .notification_repository import NotificationRepository
from .portfolio_repository import PortfolioRepository
from .recurring_plan_repository import RecurringPlanRepository
from .transaction_repository import TransactionRepository
from .user_repository import UserRepository

__all__ = [
    "BaseRepository",
    "TenantScopedRepository",
    "CategoryRepository",
    "TenantCategoryRepository",
    "FinancialEducationRepository",
    "FinancialRepository",
    "MonitoringRepository",
    "NotificationRepository",
    "PortfolioRepository",
    "RecurringPlanRepository",
    "TransactionRepository",
    "UserRepository",
]
