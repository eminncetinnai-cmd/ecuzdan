"""Production WSGI entry point for E-Cüzdan."""

from app import app

application = app

__all__ = ["app", "application"]
