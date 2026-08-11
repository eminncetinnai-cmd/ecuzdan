"""ProfileApplicationService."""
from application.base import ApplicationService


class ProfileApplicationService(ApplicationService):
    def __init__(self, profile_service=None, **kwargs):
        super().__init__(**kwargs)
        self.profile_service = profile_service

    def index_context(self, tenant_id, user_id):
        return self.execute(
            lambda: self.profile_service.index_context(tenant_id, user_id)
        )

    def wizard_context(self):
        return self.execute(lambda: self.profile_service.wizard_context())

    def questions_payload(self):
        return self.execute(lambda: self.profile_service.questions_payload())

    def submit_answers(self, tenant_id, user_id, answers_data):
        return self.execute(
            lambda: self.profile_service.submit_answers(
                tenant_id, user_id, answers_data
            )
        )

    def result_context(self, profile_id, tenant_id):
        return self.execute(
            lambda: self.profile_service.result_context(profile_id, tenant_id)
        )

    def profile_payload(self, profile_id, tenant_id):
        return self.execute(
            lambda: self.profile_service.profile_payload(profile_id, tenant_id)
        )

    def history_payload(self, tenant_id, user_id):
        return self.execute(
            lambda: self.profile_service.history_payload(tenant_id, user_id)
        )

    def rollback(self):
        if hasattr(self.profile_service, 'rollback'):
            self.profile_service.rollback()

