"""AuthApplicationService."""
from application.base import ApplicationService


class AuthApplicationService(ApplicationService):
    def __init__(self, auth_service=None, outbox=None, **kwargs):
        super().__init__(**kwargs)
        self.auth_service = auth_service
        self._outbox = outbox

    def authenticate(self, username, password):
        user = self.execute(lambda: self.auth_service.authenticate(username, password))
        if user and self._outbox:
            # We don't have session_id here, session creation is separate.
            # Usually record_session is called right after.
            pass
        return user

    def record_session(self, user, session_id):
        result = self.execute(lambda: self.auth_service.record_session(user, session_id))
        from domain.users.events import UserLoggedInEvent
        if self._outbox:
            self._outbox.save(UserLoggedInEvent(user_id=user.id, session_id=session_id))
        return result

    def clear_session(self, user_id):
        return self.execute(lambda: self.auth_service.clear_session(user_id))

    def set_language(self, user_id, language):
        result = self.execute(lambda: self.auth_service.set_language(user_id, language))
        from domain.users.events import UserLanguageChangedEvent
        if self._outbox:
            self._outbox.save(UserLanguageChangedEvent(user_id=user_id, language=language))
        return result

    def register_user(self, full_name, email, password, confirm_password):
        tenant_id, user = self.execute(
            lambda: self.auth_service.register_user(
                full_name, email, password, confirm_password
            )
        )
        from domain.users.events import UserCreatedEvent
        from domain.tenant.events import TenantCreatedEvent
        if self._outbox:
            self._outbox.save(TenantCreatedEvent(tenant_id=tenant_id, name=full_name))
            self._outbox.save(UserCreatedEvent(user_id=user.id, username=user.username, tenant_id=tenant_id))
        return tenant_id

    def get_valid_invite(self, token):
        return self.execute(lambda: self.auth_service.get_valid_invite(token))

    def register_invited_user(self, invite, full_name, password, confirm_password):
        return self.execute(
            lambda: self.auth_service.register_invited_user(
                invite, full_name, password, confirm_password
            )
        )

    def rollback(self):
        if hasattr(self.auth_service, 'rollback'):
            self.auth_service.rollback()

