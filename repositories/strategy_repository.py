"""Repository for strategy settings."""

from models import StrategySettings

from .base import BaseRepository


class StrategyRepository(BaseRepository):
    def get_settings_for_user(self, user_id):
        return StrategySettings.query.filter_by(user_id=user_id).first()

    def create_settings_for_user(self, user_id):
        settings = StrategySettings(user_id=user_id)
        self.add(settings)
        self.commit()
        return settings

