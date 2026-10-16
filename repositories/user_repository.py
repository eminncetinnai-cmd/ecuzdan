"""Repository for users, tenants and invites."""

from typing import Any

from sqlalchemy.orm import joinedload

from models import (
    Account,
    Asset,
    AssetTransaction,
    AssetUpdate,
    BankAccount,
    BankStatementSnapshot,
    JournalEntry,
    LedgerAdjustment,
    LedgerAuditEvent,
    LedgerLine,
    LogbookEntry,
    Payment,
    PlanOccurrence,
    RecurringPlan,
    Tenant,
    TenantInvite,
    Transaction,
    User,
    UserPreference,
)

from .base import BaseRepository


class UserRepository(BaseRepository):
    """Kullanıcı, Tenant ve Davetiye erişim katmanı."""

    def get_user(self, user_id: int) -> User | None:
        return self.get(User, user_id)

    def list_users(self) -> list[User]:
        """Platform-scope: tüm kullanıcılar. Yalnızca sistem_yoneticisi kullanmalı."""
        return User.query.all()

    def list_users_for_tenant(self, tenant_id: str) -> list[User]:
        """Tenant-scope: yalnızca o tenant'a ait kullanıcılar."""
        return User.query.filter_by(tenant_id=tenant_id).order_by(User.id).all()

    def count_users_for_tenant(self, tenant_id: str) -> int:
        """Tenant-scope: kullanıcı sayısını getirin."""
        return User.query.filter_by(tenant_id=tenant_id).count()

    def find_user_by_username(self, username: str) -> User | None:
        return User.query.filter_by(username=username).first()

    def find_user_by_email(self, email: str) -> User | None:
        return User.query.filter_by(email=email).first()

    def find_user_by_oauth_id(self, provider: str, oauth_id: str) -> User | None:
        return User.query.filter_by(auth_provider=provider, oauth_id=oauth_id).first()

    def username_exists(self, username: str) -> bool:
        return self.find_user_by_username(username) is not None

    def email_exists(self, email: str) -> bool:
        return self.find_user_by_email(email) is not None

    def add_user(self, **fields: Any) -> User:
        return self.add(User(**fields))

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self.get(Tenant, tenant_id)

    def find_tenant(self, tenant_id: str) -> Tenant | None:
        return Tenant.query.filter_by(id=tenant_id).first()

    def get_user_with_preference(self, user_id: int) -> User | None:
        return (
            self.session.query(User)
            .options(
                joinedload(User.preference),
                joinedload(User.tenant),      # type: ignore[arg-type]
            )
            .filter(User.id == user_id)
            .first()
        )

    def add_tenant(self, **fields: Any) -> Tenant:
        return self.add(Tenant(**fields))

    def find_invite(self, token: str) -> TenantInvite | None:
        return TenantInvite.query.filter_by(token=token).first()

    def find_active_invite(self, email: str, tenant_id: str) -> TenantInvite | None:
        return TenantInvite.query.filter_by(email=email, tenant_id=tenant_id, used_at=None).first()

    def list_invites(self, tenant_id: str, invited_by: int | None = None) -> list[TenantInvite]:
        q = TenantInvite.query.filter_by(tenant_id=tenant_id)
        if invited_by is not None:
            q = q.filter_by(invited_by=invited_by)
        return q.order_by(TenantInvite.created_at.desc()).all()

    def add_invite(self, **fields: Any) -> TenantInvite:
        return self.add(TenantInvite(**fields))

    def delete_user(self, user: User) -> None:
        self.delete(user)

    # ------------------------------------------------------------------
    # Kullanıcı tercihleri (Faz 18)
    # ------------------------------------------------------------------
    def find_preference(self, user_id: int) -> UserPreference | None:
        """Tercih satırını döndürür; yoksa None (satır tembel oluşturulur)."""
        return UserPreference.query.filter_by(user_id=user_id).first()

    def add_preference(self, **fields: Any) -> UserPreference:
        return self.add(UserPreference(**fields))

    # ------------------------------------------------------------------
    # Tenant-scoped financial data reset (güvenli)
    # ------------------------------------------------------------------
    def reset_financial_data_for_tenant(self, tenant_id: str) -> None:
        """
        Yalnızca belirtilen tenant'a ait finansal verileri siler.
        tenant_id zorunludur; boş geçilemez.
        Foreign key kısıtlarına uyumlu olarak önce bağımlı (çocuk) kayıtlar silinir.
        """
        if not tenant_id:
            raise ValueError("reset_financial_data_for_tenant: tenant_id boş olamaz.")

        # 1. Transaction bağımlıları
        self.session.query(LogbookEntry).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        self.session.query(LedgerAuditEvent).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        self.session.query(LedgerAdjustment).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)

        # 2. General Ledger bağımlıları
        je_ids = self.session.query(JournalEntry.id).filter_by(tenant_id=tenant_id)
        self.session.query(LedgerLine).filter(LedgerLine.journal_entry_id.in_(je_ids)).delete(synchronize_session=False)
        self.session.query(JournalEntry).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        self.session.query(Account).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)

        # 3. Plan bağımlıları (Transaction'a da referans verebilir)
        self.session.query(Payment).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        self.session.query(PlanOccurrence).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)

        # 4. Ana işlemler ve planlar
        self.session.query(Transaction).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        self.session.query(RecurringPlan).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)

        # 5. Banka hesapları ve ekstre mutabakatları
        self.session.query(BankStatementSnapshot).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        self.session.query(BankAccount).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)

        # 6. Varlıklar ve alt kayıtları
        asset_ids = self.session.query(Asset.id).filter_by(tenant_id=tenant_id)
        self.session.query(AssetUpdate).filter(AssetUpdate.asset_id.in_(asset_ids)).delete(synchronize_session=False)
        self.session.query(AssetTransaction).filter(AssetTransaction.asset_id.in_(asset_ids)).delete(synchronize_session=False)
        self.session.query(Asset).filter_by(tenant_id=tenant_id).delete(synchronize_session=False)

    def reset_financial_data(self) -> None:
        """
        Platform-scope GLOBAL silme — yalnızca platform owner (sistem_yoneticisi)
        kullanmalı. Hiçbir kullanıcı-facing UI bu metodu çağırmamalı.
        """
        self.session.query(LogbookEntry).delete(synchronize_session=False)
        self.session.query(LedgerAuditEvent).delete(synchronize_session=False)
        self.session.query(LedgerAdjustment).delete(synchronize_session=False)
        self.session.query(LedgerLine).delete(synchronize_session=False)
        self.session.query(JournalEntry).delete(synchronize_session=False)
        self.session.query(Account).delete(synchronize_session=False)
        self.session.query(Payment).delete(synchronize_session=False)
        self.session.query(PlanOccurrence).delete(synchronize_session=False)
        self.session.query(Transaction).delete(synchronize_session=False)
        self.session.query(RecurringPlan).delete(synchronize_session=False)
        self.session.query(BankStatementSnapshot).delete(synchronize_session=False)
        self.session.query(BankAccount).delete(synchronize_session=False)
        self.session.query(AssetUpdate).delete(synchronize_session=False)
        self.session.query(AssetTransaction).delete(synchronize_session=False)
        self.session.query(Asset).delete(synchronize_session=False)
