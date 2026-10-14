"""Outbox Port — application-layer interface for event persistence.

The application layer calls this port to persist events.  The actual
storage mechanism (SQLAlchemy, file, message queue) is provided by
an infrastructure adapter injected at composition time.
"""

import abc

from domain.common.events import DomainEvent


class OutboxPort(abc.ABC):
    """Port that application services use to persist domain events."""

    @abc.abstractmethod
    def save(self, event: DomainEvent) -> None:
        """Persist an event for later asynchronous dispatch.

        The implementation MUST participate in the current database
        transaction (no independent commit) so that event persistence
        is atomic with the domain state change.
        """
        pass
