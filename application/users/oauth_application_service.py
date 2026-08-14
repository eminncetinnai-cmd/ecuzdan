"""OAuth Application Service - Authentication Provider Framework (Phase 11)

This service orchestrates the OAuth login flow following CQRS principles:
- Handles use-case orchestration only
- Delegates provider-specific logic to OAuthProvider implementations
- Manages user creation, tenant isolation, and account linking
- Emits domain events for OAuth operations
"""

import logging
from datetime import datetime, timezone

from application.users.ports.oauth_provider import OAuthProvider, OAuthUserInfoDto
from domain.users.events import OAuthAccountLinkedEvent, UserLoggedInEvent
from models import Tenant, User
from shared.db import db

from utils.log_redaction import mask_email

logger = logging.getLogger(__name__)


class OAuthApplicationService:
    """Application service for OAuth authentication

    This service coordinates the OAuth login process:
    1. Verifies OAuth token via provider
    2. Finds or creates user with proper tenant isolation
    3. Links OAuth account to existing user if email matches
    4. Updates user metadata (last_login, avatar, etc.)
    5. Emits domain events
    6. Returns user for session creation
    """

    def __init__(self, oauth_provider: OAuthProvider, event_bus=None):
        """Initialize OAuth application service

        Args:
            oauth_provider: OAuth provider implementation (Google, Apple, etc.)
            event_bus: Optional event bus for emitting domain events
        """
        self.provider = oauth_provider
        self.event_bus = event_bus

    def verify_and_login(self, code: str, redirect_uri: str) -> User:
        """Verify OAuth code and login/create user

        This method implements the complete OAuth login flow:
        1. Exchange authorization code for access token
        2. Verify token and get user info from provider
        3. Find existing user by email or create new user
        4. Ensure tenant isolation (new users get new tenant)
        5. Link OAuth account to user
        6. Update user metadata

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Callback URL used in authorization

        Returns:
            User object (existing or newly created)

        Raises:
            ValueError: If OAuth verification fails or email not verified
        """
        # Step 1: Exchange code for token
        token_info = self.provider.exchange_code_for_token(code, redirect_uri)
        access_token = token_info.get('access_token')

        if not access_token:
            raise ValueError("OAuth token alınamadı.")

        # Step 2: Verify token and get user info
        user_info = self.provider.verify_token_and_get_user_info(access_token)

        logger.info(
            f"OAuth login attempt: provider={user_info.provider}, "
            f"email={user_info.email}, email_verified={user_info.email_verified}"
        )

        # Step 3: Find or create user
        user = self._find_or_create_user(user_info)

        # Step 4: Update user metadata
        self._update_user_metadata(user, user_info)

        # Step 5: Commit changes
        db.session.commit()

        # Emit user logged in event
        if self.event_bus:
            event = UserLoggedInEvent(
                user_id=user.id,
                session_id='',  # Session ID will be set by routes layer
                via_provider=user_info.provider.upper()
            )
            self.event_bus.publish(event)
            logger.info(f"Emitted UserLoggedInEvent: user_id={user.id}, provider={user_info.provider}")

        logger.info(f"OAuth login successful: user_id={user.id}, provider={user_info.provider}")

        return user

    def _find_or_create_user(self, user_info: OAuthUserInfoDto) -> User:
        """Find existing user by email or create new user

        This implements the account linking logic:
        - If user exists with same email, link OAuth account to them
        - If user doesn't exist, create new user with new tenant
        - Ensure tenant isolation (each user has their own tenant)

        Args:
            user_info: OAuth user information

        Returns:
            User object (existing or newly created)
        """
        # Try to find existing user by email
        existing_user = User.query.filter_by(username=user_info.email).first()

        if existing_user:
            # Link OAuth account to existing user
            logger.info(f"Linking OAuth account to existing user: user_id={existing_user.id}")

            # Update OAuth fields if not already set
            if not existing_user.oauth_id:
                existing_user.oauth_id = user_info.provider_id
            if not existing_user.auth_provider or existing_user.auth_provider == 'LOCAL':
                existing_user.auth_provider = user_info.provider.upper()

            # Emit OAuth account linked event
            if self.event_bus:
                event = OAuthAccountLinkedEvent(
                    user_id=existing_user.id,
                    provider=user_info.provider,
                    oauth_id=user_info.provider_id
                )
                self.event_bus.publish(event)
                logger.info(f"Emitted OAuthAccountLinkedEvent: user_id={existing_user.id}")

            return existing_user

        # Create new user with new tenant
        logger.info(f"Creating new user from OAuth: email={mask_email(user_info.email)}")

        # Create new tenant for user isolation
        tenant = self._create_tenant_for_user(user_info)

        # Create new user
        user = User(
            username=user_info.email,
            password=None,  # OAuth users don't have passwords
            auth_provider=user_info.provider.upper(),
            oauth_id=user_info.provider_id,
            avatar_url=user_info.avatar_url,
            email_verified=user_info.email_verified,
            created_via='oauth',
            role='kullanici',
            language='tr',
            tenant_id=tenant.id
        )

        db.session.add(user)
        return user

    def _create_tenant_for_user(self, user_info: OAuthUserInfoDto) -> Tenant:
        """Create a new tenant for OAuth user

        Each OAuth user gets their own isolated tenant to ensure
        data separation between users.

        Args:
            user_info: OAuth user information

        Returns:
            Newly created Tenant
        """
        tenant_id = f"tenant_{user_info.email.split('@')[0]}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        tenant = Tenant(
            id=tenant_id,
            name=f"{user_info.name}'s Tenant",
            base_currency='TRY',
            status='active'
        )
        db.session.add(tenant)
        return tenant

    def _update_user_metadata(self, user: User, user_info: OAuthUserInfoDto):
        """Update user metadata after successful OAuth login

        Updates:
        - last_login_at timestamp
        - avatar_url if provided
        - email_verified status

        Args:
            user: User object to update
            user_info: OAuth user information
        """
        user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)

        if user_info.avatar_url:
            user.avatar_url = user_info.avatar_url

        user.email_verified = user_info.email_verified
