"""Application Service for OAuth login flows."""

from typing import Dict

from application.base import ApplicationService
from domain.users.events import UserCreatedEvent, UserLoggedInEvent
from domain.users.services import AuthService

from .ports.oauth_provider import OAuthProvider


class OAuthApplicationService(ApplicationService):
    def __init__(self, auth_domain_service: AuthService, providers: Dict[str, OAuthProvider], outbox):
        self._auth_service = auth_domain_service
        self._providers = providers
        self._outbox = outbox

    def get_login_url(self, provider_name: str, state: str, redirect_uri: str) -> str:
        provider = self._providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Unsupported OAuth provider: {provider_name}")
        return self.execute(lambda: provider.get_authorization_url(state, redirect_uri))

    def verify_and_login(self, provider_name: str, code: str, redirect_uri: str, session_id: str):
        provider = self._providers.get(provider_name.lower())
        if not provider:
            raise ValueError(f"Unsupported OAuth provider: {provider_name}")

        def _use_case():
            # 1. Fetch user info via port
            user_info = provider.verify_token_and_get_user(code, redirect_uri)

            if not user_info.email_verified:
                raise ValueError("E-posta adresi doğrulanmamış hesaplar kabul edilmemektedir.")

            # 2. Domain logic to authenticate or register/link
            user, is_new = self._auth_service.authenticate_oauth(
                provider=user_info.provider,
                oauth_id=user_info.oauth_id,
                email=user_info.email,
                avatar_url=user_info.avatar_url,
                email_verified=user_info.email_verified
            )

            # 3. Session logic
            self._auth_service.record_session(user, session_id)

            # 4. Events
            if is_new:
                # Newly created tenant & user
                self._outbox.save(UserCreatedEvent(
                    user_id=user.id,
                    username=user.username,
                    tenant_id=user.tenant_id
                ))
            else:
                # If they were just linked or already existing
                if user.auth_provider == user_info.provider and user.last_login_at == user.created_at:
                    # Account might be newly linked or just logging in, but wait, the domain service
                    # sets last_login_at in both cases.
                    # We can assume it's just a login, but we dispatch UserLoggedInEvent anyway.
                    pass

            self._outbox.save(UserLoggedInEvent(
                user_id=user.id,
                session_id=session_id,
                via_provider=user_info.provider
            ))

            return user

        return self.execute(_use_case)
