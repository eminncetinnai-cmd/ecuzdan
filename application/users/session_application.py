from domain.users.services import SessionService


class SessionApplicationService:
    """Application layer for session operations. Delegates to domain SessionService."""

    def __init__(self, domain_service: SessionService = None):
        self._svc = domain_service

    def get_current_user(self, user_id):
        return self._svc.get_current_user(user_id)

    def validate_user_session(self, user_id, session_id):
        return self._svc.validate_user_session(user_id, session_id)

    # Keep other thin pass-through helpers if needed by routes
    def require_login(self, *args, **kwargs):
        return self._svc.require_login(*args, **kwargs)
