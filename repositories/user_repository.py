"""Repository for users, tenants and invites."""

from models import (
    Asset,
    AssetTransaction,
    AssetUpdate,
    RecurringPlan,
    Tenant,
    TenantInvite,
    Transaction,
    User,
    UserPreference,
)
from sqlalchemy.orm import joinedload

from .base import BaseRepository


class UserRepository(BaseRepository):
    def get_user(self, user_id):
        return self.get(User, user_id)

    def list_users(self):
        """Platform-scope: tüm kullanıcılar. Yalnızca sistem_yoneticisi kullanmalı."""
        return User.query.all()

    def list_users_for_tenant(self, tenant_id):
        """Tenant-scope: yalnızca o tenant'a ait kullanıcılar."""
        return User.query.filter_by(tenant_id=tenant_id).order_by(User.id).all()

    def count_users_for_tenant(self, tenant_id):
        """Tenant-scope: kullanıcı sayısını getirin."""
        return User.query.filter_by(tenant_id=tenant_id).count()

    def find_user_by_username(self, username):
        return User.query.filter_by(username=username).first()

    def find_user_by_email(self, email):
        return User.query.filter_by(email=email).first()

    def find_user_by_oauth_id(self, provider, oauth_id):
        return User.query.filter_by(auth_provider=provider, oauth_id=oauth_id).first()

    def username_exists(self, username):
        return self.find_user_by_username(username) is not None

    def email_exists(self, email):
        return self.find_user_by_email(email) is not None

    def add_user(self, **fields):
        return self.add(User(**fields))

    def get_tenant(self, tenant_id):
        return self.get(Tenant, tenant_id)

    def find_tenant(self, tenant_id):
        return Tenant.query.filter_by(id=tenant_id).first()

    def get_user_with_preference(self, user_id):
        return (
            self.session.query(User)
            .options(
                joinedload(User.preference),
                joinedload(User.tenant),
            )
            .filter(User.id == user_id)
            .first()
        )

    def add_tenant(self, **fields):
        return self.add(Tenant(**fields))

    def find_invite(self, token):
        return TenantInvite.query.filter_by(token=token).first()

    def find_active_invite(self, email, tenant_id):
        return TenantInvite.query.filter_by(email=email, tenant_id=tenant_id, used_at=None).first()

    def list_invites(self, tenant_id, invited_by=None):
        q = TenantInvite.query.filter_by(tenant_id=tenant_id)
        if invited_by is not None:
            q = q.filter_by(invited_by=invited_by)
        return q.order_by(TenantInvite.created_at.desc()).all()

    def add_invite(self, **fields):
        return self.add(TenantInvite(**fields))

    def delete_user(self, user):
        self.delete(user)

    # ------------------------------------------------------------------
    # Kullanıcı tercihleri (Faz 18)
    # ------------------------------------------------------------------
    def find_preference(self, user_id):
        """Tercih satırını döndürür; yoksa None (satır tembel oluşturulur)."""
        return UserPreference.query.filter_by(user_id=user_id).first()

    def add_preference(self, **fields):
        return self.add(UserPreference(**fields))

    # ------------------------------------------------------------------
    # Tenant-scoped financial data reset (güvenli)
    # ------------------------------------------------------------------
    def reset_financial_data_for_tenant(self, tenant_id: str):
        """
        Yalnızca belirtilen tenant'a ait finansal verileri siler.
        tenant_id zorunludur; boş geçilemez.
        """
        if not tenant_id:
            raise ValueError("reset_financial_data_for_tenant: tenant_id boş olamaz.")
        Transaction.query.filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        RecurringPlan.query.filter_by(tenant_id=tenant_id).delete(synchronize_session=False)
        asset_ids = self.session.query(Asset.id).filter_by(tenant_id=tenant_id)
        AssetUpdate.query.filter(AssetUpdate.asset_id.in_(asset_ids)).delete(synchronize_session=False)
        AssetTransaction.query.filter(AssetTransaction.asset_id.in_(asset_ids)).delete(synchronize_session=False)
        Asset.query.filter_by(tenant_id=tenant_id).delete(synchronize_session=False)

    def reset_financial_data(self):
        """
        Platform-scope GLOBAL silme — yalnızca platform owner (sistem_yoneticisi)
        kullanmalı. Hiçbir kullanıcı-facing UI bu metodu çağırmamalı.
        """
        Transaction.query.delete()
        RecurringPlan.query.delete()
        Asset.query.delete()
        AssetUpdate.query.delete()
