"""Migration to fix email field for existing OAuth users.

This script updates the email field for users who registered via OAuth
but have their email stored in the username field instead of the email field.
"""

import logging
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


from models import User, db

logger = logging.getLogger(__name__)


def fix_oauth_users_email():
    """Update email field for OAuth users who have email in username."""

    # Find OAuth users with None email but email-like username
    oauth_users = User.query.filter(
        User.auth_provider != 'LOCAL',
        User.email.is_(None)
    ).all()

    if not oauth_users:
        logger.info("No OAuth users with missing email found.")
        return

    logger.info(f"Found {len(oauth_users)} OAuth users with missing email.")

    updated_count = 0
    for user in oauth_users:
        # Check if username looks like an email
        if '@' in user.username and '.' in user.username:
            user.email = user.username
            updated_count += 1
            logger.info(f"Updated email for user {user.id}: {user.username}")
        else:
            logger.warning(f"User {user.id} has username '{user.username}' which doesn't look like an email.")

    if updated_count > 0:
        db.session.commit()
        logger.info(f"Successfully updated email for {updated_count} OAuth users.")
    else:
        logger.info("No users were updated.")


if __name__ == '__main__':
    from app import app
    with app.app_context():
        fix_oauth_users_email()
