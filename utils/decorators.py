"""
Common decorators for route protection and authentication.
"""

from functools import wraps

from flask import redirect, session, url_for


def login_required(f):
    """
    Decorator to ensure user is logged in before accessing a route.
    Redirects to login page if user is not authenticated.

    Args:
        f: The function to decorate

    Returns:
        Decorated function that checks for user authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
