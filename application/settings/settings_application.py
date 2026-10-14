"""Settings application service."""

from application.base import ApplicationService


class SettingsApplicationService(ApplicationService):
    def __init__(self, settings_service=None):
        super().__init__()
        self.settings_service = settings_service

    def page_context(self, user_id):
        return self.execute(lambda: self.settings_service.page_context(user_id))

    def update_profile_image(self, user_id, image_path):
        return self.execute(lambda: self.settings_service.update_profile_image(user_id, image_path))

    def change_password(self, user_id, new_password, current_password=None):
        return self.execute(
            lambda: self.settings_service.change_password(user_id, new_password, current_password=current_password)
        )

    def change_language(self, user_id, language):
        from infrastructure.i18n import i18n  # utility — lives in application layer, not domain
        return self.execute(
            lambda: self.settings_service.change_language(
                user_id, language, allowed_languages=list(i18n.translations.keys())
            )
        )

    def change_base_currency(self, user_id, currency):
        # CurrencyManager altyapı/analiz katmanında yaşar; domain'e izinli liste
        # olarak enjekte edilir (change_language ile aynı desen).
        from domain.analysis.services import CurrencyManager
        return self.execute(
            lambda: self.settings_service.change_base_currency(
                user_id, currency, allowed_currencies=list(CurrencyManager.SUPPORTED_CURRENCIES.keys())
            )
        )

    def can_reset_data(self, user):
        return self.execute(lambda: self.settings_service.can_reset_data(user))

    def get_preferences(self, user_id):
        return self.execute(lambda: self.settings_service.get_preferences(user_id))

    def update_preferences(self, user_id, values):
        return self.execute(lambda: self.settings_service.update_preferences(user_id, values))

    def change_theme(self, user_id, theme):
        return self.execute(lambda: self.settings_service.change_theme(user_id, theme))

    def pin_session(self, user_id, session_id):
        return self.execute(lambda: self.settings_service.pin_session(user_id, session_id))

    def update_notification_preferences(self, user_id, notify_budget, notify_payments, reminder_days):
        return self.execute(lambda: self.settings_service.update_notification_preferences(
            user_id, notify_budget, notify_payments, reminder_days
        ))

    def set_privacy_mode(self, user_id, enabled):
        return self.execute(lambda: self.settings_service.set_privacy_mode(user_id, enabled))

    def reset_data(self, current_user_id, password):
        return self.execute(lambda: self.settings_service.reset_data(current_user_id, password))

    def apply_special_code(self, user_id, new_role, code_fingerprint):
        return self.execute(
            lambda: self.settings_service.apply_special_code(user_id, new_role, code_fingerprint)
        )

    def commit(self):
        return self.execute(lambda: self.settings_service.commit())

