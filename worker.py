"""Dedicated production process for background and outbox workers."""

from __future__ import annotations

import logging
import signal
from threading import Event

from app import _start_background_workers, app

logger = logging.getLogger(__name__)
_stop_event = Event()


def _request_shutdown(signum, _frame):
    logger.info("Background worker shutdown requested by signal %s", signum)
    _stop_event.set()


def main() -> None:
    signal.signal(signal.SIGTERM, _request_shutdown)
    signal.signal(signal.SIGINT, _request_shutdown)
    with app.app_context():
        _start_background_workers(owner='worker')
    if not _stop_event.is_set():
        logger.info("Dedicated background worker is running.")
    _stop_event.wait()
    logger.info("Dedicated background worker stopped.")


if __name__ == "__main__":
    main()
