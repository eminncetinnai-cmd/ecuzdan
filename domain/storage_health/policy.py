"""Canonical Storage Health policy vocabulary.

Policy labels are deliberately independent from execution. Observe mode only
classifies resources; it does not delete or move anything.
"""

from __future__ import annotations

from enum import StrEnum


class PolicyClass(StrEnum):
    SAFE_AUTO = "SAFE_AUTO"
    SAFE_WITH_CONFIRMATION = "SAFE_WITH_CONFIRMATION"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    PROTECTED = "PROTECTED"
    MAINTENANCE_WINDOW_REQUIRED = "MAINTENANCE_WINDOW_REQUIRED"


CATEGORY_NAMES = (
    "database",
    "runtime",
    "backups",
    "logs",
    "reports",
    "cache",
    "test_artifacts",
    "source",
    "configuration",
    "archives",
    "build_artifacts",
    "unknown",
)

PROTECTED_NAMES = (
    ".git",
    ".venv",
    ".env",
    "client_secret",
    "credentials",
    "e_cuzdan_v15.db",
    "e_cuzdan_v15.db-wal",
    "e_cuzdan_v15.db-shm",
    "app.py",
    "config.py",
    "wsgi.py",
    "configuration",
    "domain",
    "routes",
    "infrastructure",
    "templates",
    "static",
    "translations",
    "tests",
)
