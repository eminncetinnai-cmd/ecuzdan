"""StrategyApplicationService."""
from application.base import ApplicationService


class StrategyApplicationService(ApplicationService):
    def __init__(self, strategy_service=None, **kwargs):
        super().__init__(**kwargs)
        self.strategy_service = strategy_service

    def page_context(self, user_id):
        return self.execute(lambda: self.strategy_service.page_context(user_id))

    def get_or_create_settings(self, user_id):
        return self.execute(
            lambda: self.strategy_service.get_or_create_settings(user_id)
        )

    def update_settings_from_form(self, user_id, form):
        return self.execute(
            lambda: self.strategy_service.update_settings_from_form(user_id, form)
        )

    def settings_payload(self, settings):
        return self.execute(lambda: self.strategy_service.settings_payload(settings))

    def rollback(self):
        if hasattr(self.strategy_service, 'rollback'):
            self.strategy_service.rollback()

