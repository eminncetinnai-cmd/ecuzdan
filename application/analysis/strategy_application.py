"""StrategyApplicationService."""
from application.base import ApplicationService


class StrategyApplicationService(ApplicationService):
    def __init__(self, strategy_service=None, **kwargs):
        super().__init__(**kwargs)
        self.strategy_service = strategy_service

    def page_context(self, user_id):
        return self.execute(lambda: self.strategy_service.page_context(user_id))

    def fund_nowcast_payload(self, user_id):
        return self.execute(lambda: self.strategy_service.fund_nowcast_payload(user_id))

    def fund_market_data_payload(
        self,
        user_id,
        *,
        limit=200,
        current_snapshot=False,
        include_performance=False,
        portfolio_funds=None,
    ):
        return self.execute(
            lambda: self.strategy_service.fund_market_data_payload(
                user_id,
                limit=limit,
                current_snapshot=current_snapshot,
                include_performance=include_performance,
                portfolio_funds=portfolio_funds,
            )
        )

    def get_fund_observation(self, user_id, fund_code):
        return self.execute(lambda: self.strategy_service.get_fund_observation(user_id, fund_code))

    def fund_history_payload(
        self,
        user_id,
        fund_code,
        *,
        fund_type=None,
        from_date=None,
        to_date=None,
        compare_code=None,
        compare_type=None,
    ):
        return self.execute(
            lambda: self.strategy_service.fund_history_payload(
                user_id,
                fund_code,
                fund_type=fund_type,
                from_date=from_date,
                to_date=to_date,
                compare_code=compare_code,
                compare_type=compare_type,
            )
        )

    def import_fund_market_file(self, user_id, file_obj, filename):
        return self.execute(
            lambda: self.strategy_service.import_fund_market_file(
                user_id,
                file_obj,
                filename,
            )
        )

    def sync_fund_market_data(self, user_id, fund_type='YAT', fund_code=None, lookback_days=7):
        return self.execute(
            lambda: self.strategy_service.sync_fund_market_data(
                user_id,
                fund_type=fund_type,
                fund_code=fund_code,
                lookback_days=lookback_days,
            )
        )

    def sync_fund_history(
        self,
        user_id,
        fund_code,
        *,
        fund_type=None,
        history_days=365,
    ):
        return self.execute(
            lambda: self.strategy_service.sync_fund_history(
                user_id,
                fund_code,
                fund_type=fund_type,
                history_days=history_days,
            )
        )

    def preview_fund_nowcast(self, user_id, payload):
        return self.execute(
            lambda: self.strategy_service.preview_fund_nowcast(user_id, payload)
        )

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

