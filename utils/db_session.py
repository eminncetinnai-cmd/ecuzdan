"""Database session utilities for route error handling."""

from models import db


def rollback_session():
    db.session.rollback()


def remove_session():
    db.session.remove()
