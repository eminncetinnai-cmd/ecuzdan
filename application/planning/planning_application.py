"""PlanningApplicationService.

Orchestration for recurring plans and payment calendars.
"""

from application.base import ApplicationService


class PlanningApplicationService(ApplicationService):
    def __init__(self, plan_service=None, **kwargs):
        super().__init__(**kwargs)
        self.plan_service = plan_service

    @property
    def financial_repository(self):
        # Expose the repository from plan_service since routes/plans.py uses it for check-delete
        return self.plan_service.financial_repository

    def save_plan(self, form_data):
        return self.execute(lambda: self.plan_service.save_plan(form_data))

    def plans_context(self, tenant_id=None):
        return self.execute(lambda: self.plan_service.plans_context(tenant_id))

    def payment_calendar_context(self):
        return self.execute(lambda: self.plan_service.payment_calendar_context())

    def month_data(self, year, month, tenant_id=None):
        return self.execute(lambda: self.plan_service.month_data(year, month, tenant_id))

    def daily_balance(self, year, month):
        return self.execute(lambda: self.plan_service.daily_balance(year, month))

    def add_payment(self, form_data, tenant_id=None):
        return self.execute(lambda: self.plan_service.add_payment(form_data, tenant_id))
