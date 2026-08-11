"""Request/session support service."""



from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

class SessionService:
    def __init__(self, repository=None):
        self.repository = repository

    def get_current_user(self, user_id):
        return self.repository.get_user(user_id) if user_id else None

    def validate_user_session(self, user_id, session_id):
        user = self.get_current_user(user_id)
        if not user:
            return None, 'missing_user'
        if user.last_session_id and session_id != user.last_session_id:
            return user, 'session_replaced'
        return user, None

