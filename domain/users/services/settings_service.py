"""Settings service layer."""

from datetime import datetime
from typing import TYPE_CHECKING

from werkzeug.security import check_password_hash, generate_password_hash

from shared.decimal_precision import to_decimal

if TYPE_CHECKING:
    pass

class SettingsService:
    def __init__(self, repository=None):
        self.repository = repository

    def page_context(self, user_id):
        """
        Ayarlar sayfası için context.

        Kullanıcı listesi buradan kaldırıldı: /settings artık kullanıcı
        yönetmiyor (kanonik yer /admin/users ve /tenant/users).
        """
        user = self.repository.get_user_with_preference(user_id)
        return {
            'current_user': user,
            'preferences': getattr(user, 'preference', None) if user else None,
        }

    def update_profile_image(self, user_id, image_path):
        user = self.repository.get_user(user_id)
        if user:
            user.profile_image = image_path
            self.repository.commit()
        return user

    def change_password(self, user_id, new_password, current_password=None):
        if len(new_password) < 8:
            raise ValueError("Şifre en az 8 karakter olmalıdır.")
        user = self.repository.get_user(user_id)
        if not user:
            raise LookupError("Kullanıcı bulunamadı.")
        if current_password is not None:
            if not user.password or not check_password_hash(user.password, current_password):
                raise ValueError("Mevcut şifre hatalı.")
        user.password = generate_password_hash(new_password)
        user.password_changed_at = datetime.now()
        self.repository.commit()
        return user

    def change_language(self, user_id, language, allowed_languages=None):
        if allowed_languages and language not in allowed_languages:
            raise ValueError(f"Language '{language}' is not supported.")
        user = self.repository.get_user(user_id)
        user.language = language
        self.repository.commit()
        return user

    # ------------------------------------------------------------------
    # Finansal tercihler (Faz 18)
    # ------------------------------------------------------------------
    def get_preferences(self, user_id):
        """Kullanıcının tercih satırı; henüz oluşturulmadıysa None."""
        return self.repository.find_preference(user_id)

    def pin_session(self, user_id, session_id):
        """
        Kullanıcının geçerli oturumunu verilen session_id'ye sabitler.

        Tek-oturum kontrolü last_session_id üzerinden yapıldığı için, bu
        alanı mevcut oturuma yazmak diğer tüm oturumları geçersiz kılar.
        """
        if not session_id:
            raise ValueError("Oturum kimliği bulunamadı.")
        user = self.repository.get_user(user_id)
        if not user:
            raise LookupError("Kullanıcı bulunamadı.")
        user.last_session_id = session_id
        self.repository.commit()
        return user

    def update_notification_preferences(self, user_id, notify_budget, notify_payments, reminder_days):
        """Bildirim tercihlerini günceller."""
        if reminder_days is not None and not (0 <= int(reminder_days) <= 30):
            raise ValueError("Hatırlatma günü 0 ile 30 arasında olmalıdır.")
        if not self.repository.get_user(user_id):
            raise LookupError("Kullanıcı bulunamadı.")
        preference = self.repository.find_preference(user_id)
        if preference is None:
            preference = self.repository.add_preference(user_id=user_id)
        preference.notify_budget = bool(notify_budget)
        preference.notify_payments = bool(notify_payments)
        preference.payment_reminder_days = 3 if reminder_days is None else int(reminder_days)
        self.repository.commit()
        return preference

    def set_privacy_mode(self, user_id, enabled):
        """Gizlilik modunu açar/kapatır (ekrandaki tutarları bulanıklaştırır)."""
        if not self.repository.get_user(user_id):
            raise LookupError("Kullanıcı bulunamadı.")
        preference = self.repository.find_preference(user_id)
        if preference is None:
            preference = self.repository.add_preference(user_id=user_id)
        preference.privacy_mode = bool(enabled)
        self.repository.commit()
        return preference

    def change_theme(self, user_id, theme):
        """Görünüm temasını günceller ('light' | 'dark' | 'system')."""
        from models import UserPreference

        if theme not in UserPreference.THEMES:
            raise ValueError(f"'{theme}' geçerli bir tema değil.")
        if not self.repository.get_user(user_id):
            raise LookupError("Kullanıcı bulunamadı.")

        preference = self.repository.find_preference(user_id)
        if preference is None:
            preference = self.repository.add_preference(user_id=user_id)
        preference.theme = theme
        self.repository.commit()
        return preference

    def update_preferences(self, user_id, values):
        """
        Finansal hedefleri ve analiz varsayımlarını günceller.

        `values` yalnızca doğrulanmış alanları içermelidir; None gönderilen
        alanlar 'ayarlanmadı' anlamına gelir ve motorlar varsayılana düşer.
        """
        user = self.repository.get_user(user_id)
        if not user:
            raise LookupError("Kullanıcı bulunamadı.")

        preference = self.repository.find_preference(user_id)
        if preference is None:
            preference = self.repository.add_preference(user_id=user_id)

        birth_year = values.get('birth_year')
        if birth_year is not None and not (1900 <= birth_year <= datetime.now().year):
            raise ValueError("Doğum yılı 1900 ile bu yıl arasında olmalıdır.")

        retirement_age = values.get('target_retirement_age')
        if retirement_age is not None and not (18 <= retirement_age <= 100):
            raise ValueError("Hedef emeklilik yaşı 18 ile 100 arasında olmalıdır.")

        passive_income = values.get('target_monthly_passive_income')
        if passive_income is not None and passive_income < 0:
            raise ValueError("Hedef aylık pasif gelir negatif olamaz.")

        emergency_months = values.get('emergency_fund_target_months')
        if emergency_months is not None and not (1 <= emergency_months <= 60):
            raise ValueError("Acil durum fonu hedefi 1 ile 60 ay arasında olmalıdır.")

        swr = values.get('safe_withdrawal_rate')
        if swr is not None:
            from models import UserPreference
            swr = to_decimal(swr, scale=4)
            low = to_decimal(UserPreference.MIN_SAFE_WITHDRAWAL_RATE, scale=4)
            high = to_decimal(UserPreference.MAX_SAFE_WITHDRAWAL_RATE, scale=4)
            if not (low <= swr <= high):
                raise ValueError("Güvenli çekim oranı %2 ile %10 arasında olmalıdır.")

        mode = values.get('risk_free_rate_mode', 'auto')
        if mode not in ('auto', 'manual'):
            raise ValueError("Risksiz faiz modu 'auto' veya 'manual' olmalıdır.")
        manual_rate = values.get('risk_free_rate_manual')
        if mode == 'manual':
            if manual_rate is None:
                raise ValueError("Manuel mod için risksiz faiz oranı girilmelidir.")
            manual_rate = to_decimal(manual_rate, scale=4)
            if not (to_decimal(0, scale=4) <= manual_rate <= to_decimal(2, scale=4)):
                raise ValueError("Risksiz faiz oranı %0 ile %200 arasında olmalıdır.")

        preference.birth_year = birth_year
        preference.target_retirement_age = retirement_age
        preference.target_monthly_passive_income = passive_income
        preference.emergency_fund_target_months = emergency_months
        preference.safe_withdrawal_rate = swr
        preference.risk_free_rate_mode = mode
        preference.risk_free_rate_manual = manual_rate if mode == 'manual' else None

        self.repository.commit()
        return preference

    def change_base_currency(self, user_id, currency, allowed_currencies=None):
        """Kullanıcının raporlama (baz) para birimini günceller."""
        currency = (currency or '').strip().upper()
        if allowed_currencies and currency not in allowed_currencies:
            raise ValueError(f"'{currency}' desteklenen bir para birimi değil.")
        user = self.repository.get_user(user_id)
        if not user:
            raise LookupError("Kullanıcı bulunamadı.")
        user.base_currency = currency
        self.repository.commit()
        return user

    def can_reset_data(self, user):
        """
        Workspace sıfırlama yetkisi.

        Sıfırlama TENANT genelindedir; paylaşımlı bir workspace'te sıradan bir
        üyenin eşinin verisini de silebilmesi kabul edilemez. Bu yüzden:
          - yönetici yetkisi olanlar sıfırlayabilir,
          - yöneticisi olmayan kullanıcı yalnızca workspace'in TEK üyesiyse
            sıfırlayabilir (B2C bireysel hesap durumu).
        """
        if not user:
            return False
        if user.has_admin_access or user.is_super_admin:
            return True
        members_count = self.repository.count_users_for_tenant(user.tenant_id)
        return members_count <= 1

    def reset_data(self, current_user_id, password):
        """
        Finansal veri sıfırlama.
        - Yöneticiler ve tek kişilik workspace sahipleri kendi tenant'ını sıfırlar.
        Global platform reset, bu metot üzerinden MÜMKÜN DEĞİL.
        """
        import logging
        logger = logging.getLogger(__name__)

        current_user = self.repository.get_user(current_user_id)
        if not current_user:
            raise PermissionError("Yetkilendirme Başarısız!")

        logger.info(
            "Reset data attempt for user %s, has_password_set=%s",
            current_user.username,
            bool(current_user.password),
        )

        if not current_user.password:
            # OAuth hesaplarında lokal parola yoktur; şifreyle onay alınamaz.
            raise PermissionError("Bu işlem şifre onayı gerektirir; OAuth hesapları için kullanılamaz.")

        if not check_password_hash(current_user.password, password):
            logger.warning(f"Password mismatch for user {current_user.username}")
            raise PermissionError("Yetkilendirme Başarısız! İşlemi onaylamak için şifrenizi doğru girmelisiniz.")

        if not self.can_reset_data(current_user):
            raise PermissionError(
                "Paylaşımlı bir workspace'i yalnızca yöneticisi sıfırlayabilir. "
                "Kendi verinizi dışa aktarabilir veya workspace yöneticisiyle iletişime geçebilirsiniz."
            )
        # Tenant-scoped reset — global silme yok
        # NOT: Commit çağıran route seviyesinde yapılır (transaction bütünlüğü için)
        self.repository.reset_financial_data_for_tenant(current_user.tenant_id)
        return current_user

    def apply_special_code(self, user_id, new_role, code_fingerprint):
        """Kullanıcının özel kodla rolünü yükseltir ve kullanım kaydını düşer."""
        user = self.repository.get_user(user_id)
        if not user:
            raise LookupError("Kullanıcı bulunamadı.")
        user.role = new_role
        user.special_code = code_fingerprint
        user.special_code_used_at = datetime.now()
        self.repository.commit()
        return user

    def commit(self):
        """Veritabanı oturumundaki bekleyen değişiklikleri onaylar."""
        self.repository.commit()


    def rollback(self):
        self.repository.rollback()

