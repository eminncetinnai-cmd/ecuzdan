"""Common base for Application Services.

This module provides a lightweight ApplicationService base class that application
services can inherit from. It intentionally contains no business logic — only
standard hooks and placeholders for future cross-cutting integrations (audit,
logging, metrics, validation, tenant resolution, events, transaction manager).

The goal is to provide a consistent shape for all ApplicationService classes so
routes and dependency injection can rely on a predictable interface.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class ApplicationService:
    """Base Application Service.

    Intended responsibilities (orchestration-only):
    - define lifecycle hooks (before_execute / after_execute)
    - hold references to cross-cutting adapters (audit, metrics, tenant resolver)
    - accept dependencies via constructor (for DI readiness)

    No business logic belongs here; domain services implement rules.
    """

    def __init__(
        self,
        audit_adapter: Optional[object] = None,
        metrics_adapter: Optional[object] = None,
        tenant_resolver: Optional[object] = None,
        events_adapter: Optional[object] = None,
        transaction_manager: Optional[object] = None,
        logger_adapter: Optional[logging.Logger] = None,
    ):
        self.audit = audit_adapter
        self.metrics = metrics_adapter
        self.tenant = tenant_resolver
        self.events = events_adapter
        self.tx = transaction_manager
        self.logger = logger_adapter or logger

    # lifecycle hooks — no-op by default
    def before_execute(self, context: Optional[dict] = None):
        """Hook called before each public use-case execution.

        Implementations can override to perform validation, tenant resolution,
        permission checks, or start a transaction.
        """
        return None

    def after_execute(self, context: Optional[dict] = None, result: Optional[object] = None):
        """Hook called after each public use-case execution.

        Implementations can override to emit events, audit logs, metrics, or
        to commit/rollback transactions.
        """
        return None

    # helper to run a callable with hooks — application services may use this
    def execute(self, func, *args, **kwargs):
        # Build a human-readable span name from the class and caller
        span_name = f"application.{type(self).__name__}.execute"
        ctx = {'args': args, 'kwargs': kwargs}
        try:
            from opentelemetry import trace as otel_trace
            tracer = otel_trace.get_tracer("application.base")
            with tracer.start_as_current_span(span_name):
                self.before_execute(ctx)
                result = func(*args, **kwargs)
                self.after_execute(ctx, result)
                return result
        except ImportError:
            # OTel not installed — fallback to plain execution
            self.before_execute(ctx)
            result = func(*args, **kwargs)
            self.after_execute(ctx, result)
            return result
        except Exception:
            raise


class Command:
    """Marker class for a CQRS Command."""
    pass


class Query:
    """Marker class for a CQRS Query."""
    pass
