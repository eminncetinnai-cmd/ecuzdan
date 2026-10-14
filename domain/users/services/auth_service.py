"""Authentication and registration service layer."""

import re
import secrets
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from werkzeug.security import check_password_hash, generate_password_hash

if TYPE_CHECKING:
    pass

class AuthService:
    def __init__(self, repository=None):
        self.repository = repository

    def authenticate(self, username, password):
        """Authenticate user by username or email

        Args:
            username: Username or email address
            password: Password to verify

        Returns:
            User object if authentication successful, None otherwise
        """
        # Try username first
        user = self.repository.find_user_by_username(username)
        if user and user.password and check_password_hash(user.password, password):
            return user

        # Try email if username not found
        user = self.repository.find_user_by_email(username)
        if user and user.password and check_password_hash(user.password, password):
            return user

        return None

    def authenticate_oauth(self, provider, oauth_id, email, avatar_url, email_verified):
        """Domain logic for handling an OAuth login attempt.
        1. Look for user by provider & oauth_id.
        2. If not found, look by email. If found, link account.
        3. If not found by email, create new user and tenant.
        """
        # 1. Existing OAuth user
        user = self.repository.find_user_by_oauth_id(provider, oauth_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.repository.commit()
            return user, False # False means not newly created

        # 2. Link existing local account
        user = self.repository.find_user_by_username(email)
        if user:
            user.auth_provider = provider
            user.oauth_id = oauth_id
            if avatar_url and not user.profile_image:
                user.profile_image = avatar_url
            user.email_verified = email_verified
            user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
            self.repository.commit()
            return user, False

        # 3. Create new user and tenant
        tenant_id = email.replace('@', '_').replace('.', '_')
        if self.repository.find_tenant(tenant_id):
            tenant_id = f"{tenant_id}_{secrets.token_hex(4)}"

        tenant = self.repository.add_tenant(id=tenant_id, name=email, status='active')
        self.repository.session.flush()

        user = self.repository.add_user(
            username=email,
            password=None,
            role='tenant_admin',
            tenant_id=tenant.id,
            language='tr',
            auth_provider=provider,
            oauth_id=oauth_id,
            avatar_url=avatar_url,
            email_verified=email_verified,
            created_via=provider.lower()
        )
        user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.repository.commit()
        return user, True # True means newly created

    def record_session(self, user, session_id):
        user.last_session_id = session_id
        self.repository.commit()

    def clear_session(self, user_id):
        user = self.repository.get_user(user_id)
        if user:
            user.last_session_id = None
            self.repository.commit()
        return user

    def set_language(self, user_id, language):
        user = self.repository.get_user(user_id)
        if user:
            user.language = language
            self.repository.commit()
        return user

    def register_user(self, full_name, email, password, confirm_password):
        self._validate_registration(full_name, email, password, confirm_password)
        if self.repository.username_exists(email):
            raise ValueError("Bu e-posta adresi zaten kullanımda.")
        if self.repository.email_exists(email):
            raise ValueError("Bu e-posta adresi zaten kullanımda.")

        tenant_id = email.replace('@', '_').replace('.', '_')
        if self.repository.find_tenant(tenant_id):
            tenant_id = f"{tenant_id}_{secrets.token_hex(4)}"

        tenant = self.repository.add_tenant(id=tenant_id, name=full_name, status='active')
        self.repository.session.flush()
        user = self.repository.add_user(
            username=email,
            email=email,
            password=generate_password_hash(password),
            role='tenant_admin',   # Her yeni kayıt kendi tenant'ının admini olur
            tenant_id=tenant.id,
            language='tr',
        )
        self.repository.commit()
        # Yeni tenant için varsayılan kategorileri ekle
        try:
            self._seed_default_categories()
        except Exception:
            pass  # Seed hatası kayıt akışını engellemesin
        return tenant_id, user

    def get_valid_invite(self, token):
        invite = self.repository.find_invite(token)
        return invite if invite and invite.is_valid else None

    def register_invited_user(self, invite, full_name, password, confirm_password):
        self._validate_registration(full_name, invite.email, password, confirm_password, require_email=False)
        if self.repository.username_exists(invite.email):
            raise ValueError("Bu e-posta adresi zaten kullanımda.")
        self.repository.add_user(
            username=invite.email,
            password=generate_password_hash(password),
            role=invite.role,
            tenant_id=invite.tenant_id,
            language='tr',
        )
        invite.used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        self.repository.commit()

    def rollback(self):
        self.repository.rollback()

    def _seed_default_categories(self):
        """
        Yeni tenant oluşturulduğunda sistem genelinde varsayılan kategorilerin
        var olduğunu garantiler. Kategoriler global (tenant_id yok); bu yeterli.
        Standart kategoriler silinemez (is_active=True ve tenant_id=None).
        """
        from models import Category, db

        # Standart kategoriler - GL kodları ile
        standard_categories = [
            # Gelir Kategorileri (GLR-6xxx - 600 Hesap Grubu)
            ('GLR-6001', 'Maaş / Ücret Geliri', 'Gelir', 1),
            ('GLR-6002', 'Avans', 'Gelir', 2),
            ('GLR-6003', 'Ek Gelir / Diğer Gelirler', 'Gelir', 3),
            ('GLR-6004', 'Faiz Geliri', 'Gelir', 4),
            ('GLR-6005', 'Kira Geliri', 'Gelir', 5),
            ('GLR-6006', 'Prim & İkramiye', 'Gelir', 6),
            ('GLR-6007', 'Yardım & Destek', 'Gelir', 7),
            ('GLR-6008', 'Yatırım Kazancı', 'Gelir', 8),

            # Gider Kategorileri (GDR-7xxx - 700 Hesap Grubu)
            ('GDR-7001', 'Kredi Kartı Ödemesi', 'Gider', 1),
            ('GDR-7002', 'Kredi Ödemeleri', 'Gider', 2),
            ('GDR-7003', 'Aylık Sabit Gider', 'Gider', 3),
            ('GDR-7004', 'Bağış & Yardım', 'Gider', 4),
            ('GDR-7005', 'Eğitim & Kurslar', 'Gider', 5),
            ('GDR-7006', 'Kira', 'Gider', 6),
            ('GDR-7007', 'Kişisel Bakım', 'Gider', 7),
            ('GDR-7008', 'Nafaka', 'Gider', 8),
            ('GDR-7009', 'Diğer Giderler', 'Gider', 9),

            # Yatırım Kategorileri (YTR-1xxx - 100 Varlık Hesabı)
            ('YTR-1001', 'Altın Alımı', 'Yatırım', 1),
            ('YTR-1002', 'Diğer Yatırımlar', 'Yatırım', 2),
            ('YTR-1003', 'Fon', 'Yatırım', 3),
            ('YTR-1004', 'Gayrimenkul', 'Yatırım', 4),
            ('YTR-1005', 'Hisse Senedi', 'Yatırım', 5),
            ('YTR-1006', 'Kripto', 'Yatırım', 6),
            ('YTR-1007', 'Nakit & Mevduat', 'Yatırım', 7),
        ]

        for code, name, type_, sort_order in standard_categories:
            # Kategori zaten var mı kontrol et (koda göre)
            existing = Category.query.filter_by(code=code).first()
            if not existing:
                # Kategori yoksa oluştur - tenant_id NULL ile (sistem genelinde)
                db.session.add(Category(
                    code=code,
                    name=name,
                    type=type_,
                    sort_order=sort_order,
                    is_active=True,
                    tenant_id=None,  # Sistem genelinde, silinemez
                    level=0,
                    path="/",
                    budget_limit=None  # Başlangıçta bütçe limiti yok
                ))
            else:
                # Kategori varsa aktif olduğundan emin ol
                existing.is_active = True
                existing.tenant_id = None  # Sistem genelinde olduğundan emin ol
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    def _validate_registration(self, full_name, email, password, confirm_password, require_email=True):
        if not full_name or not password or (require_email and not email):
            raise ValueError("Tüm alanlar gereklidir.")
        if password != confirm_password:
            raise ValueError("Şifreler eşleşmiyor.")

        # Password complexity validation
        if len(password) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır.")

        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            raise ValueError("Şifre en az bir büyük harf içermelidir.")

        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            raise ValueError("Şifre en az bir küçük harf içermelidir.")

        # Check for digit
        if not re.search(r'\d', password):
            raise ValueError("Şifre en az bir rakam içermelidir.")

        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            raise ValueError("Şifre en az bir özel karakter içermelidir (!@#$%^&*(),.?\":{}|<>).")

        # Check for common passwords (basic list)
        common_passwords = ['password', '12345678', 'qwerty', 'abc123', 'password123']
        if password.lower() in common_passwords:
            raise ValueError("Bu şifre çok yaygın kullanılmaktadır. Lütfen daha güçlü bir şifre seçin.")

