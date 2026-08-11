"""Tenant administration service layer."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

class TenantService:
    def __init__(self, repository=None):
        self.repository = repository

    def users_context(self, current_user_id):
        current_user = self.repository.get_user(current_user_id)
        return {
            'users': self.repository.list_users_for_tenant(current_user.tenant_id) if current_user else [],
            'current_user': current_user,
        }

    def validate_target_user(self, current_user_id, target_user_id):
        current_user = self.repository.get_user(current_user_id)
        target_user = self.repository.get_user(target_user_id)
        if not current_user or not target_user or target_user.tenant_id != current_user.tenant_id:
            raise PermissionError("Bu kullanıcıyı yönetme yetkiniz yok.")
        if target_user.id == current_user.id:
            raise ValueError("Kendi hesabınızda bu işlemi yapamazsınız.")
        return current_user, target_user

    def change_user_role(self, current_user_id, target_user_id, new_role):
        current_user, target_user = self.validate_target_user(current_user_id, target_user_id)
        if new_role not in ['kullanici', 'tenant_admin']:
            raise ValueError("Geçersiz rol.")
        target_user.role = new_role
        self.repository.commit()
        return current_user, target_user

    def create_invite(self, current_user_id, email, role):
        if not email:
            raise ValueError("E-posta adresi gereklidir.")
        if '@' not in email or '.' not in email:
            raise ValueError("Geçersiz e-posta adresi.")

        current_user = self.repository.get_user(current_user_id)
        if self.repository.username_exists(email):
            raise ValueError("Bu e-posta adresi zaten kullanımda.")

        existing_invite = self.repository.find_active_invite(email, current_user.tenant_id)
        if existing_invite and existing_invite.is_valid:
            raise LookupError("Bu e-posta zaten davet edilmiş.")

        token = secrets.token_urlsafe(32)
        invite = self.repository.add_invite(
            token=token,
            email=email,
            tenant_id=current_user.tenant_id,
            invited_by=current_user.id,
            role=role,
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=24),
        )
        self.repository.commit()
        return invite

    def list_invites(self, current_user_id):
        current_user = self.repository.get_user(current_user_id)
        if not current_user:
            return []
        return self.repository.list_invites(current_user.tenant_id, current_user.id)

    def remove_user(self, current_user_id: int, target_user_id: int) -> tuple:
        """
        Tenant admin'in kendi tenant'ındaki bir kullanıcıyı siler.
        Kurallar:
          - Kendini silemezsin
          - Farklı tenant'tan kullanıcı silemezsin
          - super_admin silinemez
        """
        current_user, target_user = self.validate_target_user(current_user_id, target_user_id)
        if target_user.is_super_admin:
            raise PermissionError("Platform sahibi silinemez.")
        if target_user.role == 'sistem_yoneticisi':
            raise PermissionError("Sistem yöneticisi bu arayüzden silinemez.")
        self.repository.delete_user(target_user)
        self.repository.commit()
        return current_user, target_user

    def rollback(self):
        self.repository.rollback()

