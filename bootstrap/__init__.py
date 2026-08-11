"""Bootstrap package for Composition Root / DI provider scaffolding.

This package provides a minimal, non-invasive container intended for Phase 7 preparation.

It purposely does not change any runtime wiring. All providers are opt-in: code must explicitly use them.
"""

__all__ = ["container", "get_container", "reset_container"]

from .container import container, get_container, reset_container
