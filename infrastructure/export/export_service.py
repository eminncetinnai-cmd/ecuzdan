"""Export service layer."""

import calendar
from datetime import datetime, timedelta

from infrastructure.database.management import export_database_to_json, import_database_from_json
from repositories.financial_repository import FinancialRepository
from repositories.user_repository import UserRepository


class ExportService:
    def __init__(self, financial_repository=None, user_repository=None):
        self.financial_repository = financial_repository or FinancialRepository()
        self.user_repository = user_repository or UserRepository()

    # ------------------------------------------------------------------
    # Tenant-scoped PDF rapor context
    # ------------------------------------------------------------------
    def pdf_report_context(self, period, now_dt=None, tenant_id=None, user_id=None):
        """
        PDF raporu için veri hazırlar.
        tenant_id veya user_id üzerinden tenant çözümlenir.
        Tüm sorgular tenant-scope çalışır.
        """
        now_dt = now_dt or datetime.now()
        today = now_dt.strftime("%Y-%m-%d")

        # tenant_id çözümleme: önce direkt parametre, sonra user_id, sonra g
        if not tenant_id and user_id:
            user = self.user_repository.get_user(user_id)
            if user:
                tenant_id = user.tenant_id
        if not tenant_id:
            try:
                from flask import g
                tenant_id = g.get('tenant_id')
            except RuntimeError:
                pass
        if not tenant_id:
            raise RuntimeError("PDF raporu için tenant_id gereklidir.")

        if period == "week":
            title = "Haftalık Bekleyen Ödemeler Raporu"
            end_date = (now_dt + timedelta(days=7)).strftime("%Y-%m-%d")
            transactions = self.financial_repository.pending_transactions_between(
                today, end_date, tenant_id=tenant_id
            )
        elif period == "month":
            title = "Aylık Bekleyen Ödemeler Raporu"
            end_date = f"{now_dt.year}-{now_dt.month:02d}-{calendar.monthrange(now_dt.year, now_dt.month)[1]:02d}"
            transactions = self.financial_repository.pending_transactions_between(
                today, end_date, tenant_id=tenant_id
            )
        else:
            title = "Nakit Akış Hareketleri Raporu"
            transactions = self.financial_repository.list_transactions(tenant_id=tenant_id)

        return title, transactions, today

    # ------------------------------------------------------------------
    # Yetki kontrolü
    # ------------------------------------------------------------------
    def require_admin(self, user_id):
        user = self.user_repository.get_user(user_id)
        if not user or not user.has_admin_access:
            raise PermissionError("Bu işlem için yönetici yetkisi gereklidir.")
        return user

    def require_platform_owner(self, user_id):
        """Yalnızca sistem_yoneticisi tam DB export/import yapabilir."""
        user = self.user_repository.get_user(user_id)
        if not user or not user.is_super_admin:
            raise PermissionError(
                "Tam veritabanı yedekleme/geri yükleme yalnızca platform sahibine açıktır."
            )
        return user

    # ------------------------------------------------------------------
    # Tenant-scoped JSON export
    # ------------------------------------------------------------------
    def export_tenant_json(self, user_id: int, encrypt: bool = False, password: str = None):
        """
        Yalnızca kullanıcının kendi tenant'ına ait veriyi export eder.

        Veri taşınabilirliği temel bir son kullanıcı hakkıdır ve bu işlem
        salt-okunur olup tenant sınırının dışına çıkmaz; bu yüzden yönetici
        yetkisi aranmaz. Platform geneli export için require_platform_owner
        kullanan export_db_json'a bakınız.
        """
        user = self.user_repository.get_user(user_id)
        if not user:
            raise PermissionError("Oturum bulunamadı.")
        tenant_id = user.tenant_id

        from models import Transaction, RecurringPlan
        from domain.portfolio.models.portfolio_models import Asset, AssetUpdate

        data = {
            "export_type": "tenant",
            "tenant_id": tenant_id,
            "exported_at": datetime.now().isoformat(),
            "transactions": [
                {c.name: str(getattr(t, c.name)) for c in t.__table__.columns}
                for t in Transaction.query.filter_by(tenant_id=tenant_id).all()
            ],
            "recurring_plans": [
                {c.name: str(getattr(p, c.name)) for c in p.__table__.columns}
                for p in RecurringPlan.query.filter_by(tenant_id=tenant_id).all()
            ],
            "assets": [
                {c.name: str(getattr(a, c.name)) for c in a.__table__.columns}
                for a in Asset.query.filter_by(tenant_id=tenant_id).all()
            ],
        }

        import json
        raw = json.dumps(data, ensure_ascii=False, default=str)

        if encrypt and password:
            try:
                from infrastructure.database.management import _encrypt_content
                return _encrypt_content(raw, password)
            except Exception:
                pass  # şifreleme desteklenmiyorsa düz döndür

        return raw

    # ------------------------------------------------------------------
    # Platform-scope full DB export/import (sadece sistem_yoneticisi)
    # ------------------------------------------------------------------
    def export_database_json(self, user_id: int, encrypt: bool = False, password: str = None):
        """
        TAM veritabanı yedeği — yalnızca platform owner.
        """
        self.require_platform_owner(user_id)
        return export_database_to_json(encrypt=encrypt, password=password)

    def import_database_json(self, user_id: int, content, password: str = None):
        """
        TAM veritabanı geri yükleme — yalnızca platform owner.
        """
        self.require_platform_owner(user_id)
        return import_database_from_json(content, password=password)

