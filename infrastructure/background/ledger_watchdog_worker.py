"""
infrastructure/background/ledger_watchdog_worker.py
===================================================
Background Worker for Continuous Ledger & Invariant Integrity Auditing.

Runs periodic, non-blocking watchdog scans across all tenants.
Logs structured security alerts and records audit trail events on violations.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import Optional

from domain.ledger.services.ledger_watchdog_service import RuntimeLedgerWatchdog, WatchdogAuditResult

logger = logging.getLogger("ledger_watchdog")


class LedgerWatchdogWorker:
    """Daemon thread executing periodic ledger and balance drift audits."""

    def __init__(self, flask_app=None, interval_seconds: int = 300):
        self._app = flask_app
        self._interval = max(interval_seconds, 10)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_result: Optional[WatchdogAuditResult] = None
        self._lock = threading.Lock()

    @property
    def last_result(self) -> Optional[WatchdogAuditResult]:
        with self._lock:
            return self._last_result

    def start(self) -> None:
        """Start the background watchdog thread."""
        if self._thread and self._thread.is_alive():
            logger.warning("LedgerWatchdogWorker is already running.")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="LedgerWatchdogWorker",
            daemon=True,
        )
        self._thread.start()
        logger.info("LedgerWatchdogWorker started (interval: %ds)", self._interval)

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the background watchdog gracefully."""
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=timeout)
            logger.info("LedgerWatchdogWorker stopped.")

    def run_once(self) -> WatchdogAuditResult:
        """Execute a single synchronous watchdog scan and alert if needed."""
        watchdog = RuntimeLedgerWatchdog()
        result = watchdog.audit_all_tenants()

        with self._lock:
            self._last_result = result

        if not result.healthy:
            self._handle_violations(result)
        else:
            logger.info(
                "LedgerWatchdog check PASSED cleanly for tenants %s (checked %d JEs, %d LLs)",
                result.checked_tenants,
                result.total_journal_entries,
                result.total_ledger_lines,
            )

        return result

    def _run_loop(self) -> None:
        """Background loop execution."""
        # Initial sleep to allow application startup
        if self._stop_event.wait(5.0):
            return

        while not self._stop_event.is_set():
            try:
                if self._app:
                    with self._app.app_context():
                        self.run_once()
                else:
                    self.run_once()
            except Exception as exc:
                try:
                    from shared.db import db
                    if self._app:
                        with self._app.app_context():
                            db.session.rollback()
                    else:
                        db.session.rollback()
                except Exception:
                    pass
                if "no such table" in str(exc).lower():
                    logger.debug("LedgerWatchdogWorker schema not ready yet: %s", exc)
                else:
                    logger.exception("Unexpected error in LedgerWatchdogWorker execution: %s", exc)

            # Wait for next interval or stop event
            if self._stop_event.wait(float(self._interval)):
                break

    def _handle_violations(self, result: WatchdogAuditResult) -> None:
        """Handle detected integrity violations: log, alert, and record audit trail."""
        logger.error(
            "[SECURITY_ALERT] [FINANCIAL_INTEGRITY] Ledger Watchdog detected %d violations across tenants %s!",
            result.error_count,
            result.checked_tenants,
        )

        for v in result.violations:
            logger.error(
                "  [%s] [%s] tenant=%s entity=%s#%s message='%s'",
                v.severity,
                v.code,
                v.tenant_id,
                v.entity_type,
                v.entity_id,
                v.message,
            )

        # Record to AuditLog if DB context is available
        try:
            from models import AuditLog
            from shared.db import db

            for v in result.violations:
                audit_entry = AuditLog(
                    tenant_id=v.tenant_id,
                    user_id=None,
                    username="SYSTEM_LEDGER_WATCHDOG",
                    action=f"ALERT_{v.code}",
                    entity_type=v.entity_type or "ledger",
                    entity_id=v.entity_id,
                    details=json.dumps(v.as_dict(), ensure_ascii=False),
                    ip_address="127.0.0.1",
                    user_agent="RuntimeLedgerWatchdog/25.2",
                )
                db.session.add(audit_entry)
            db.session.commit()
            logger.info("Recorded %d watchdog alert entries to AuditLog.", len(result.violations))
        except Exception as audit_err:
            logger.warning("Failed to persist watchdog alert to AuditLog: %s", audit_err)


_global_watchdog_worker: Optional[LedgerWatchdogWorker] = None
_worker_init_lock = threading.Lock()


def get_ledger_watchdog_worker(flask_app=None, interval_seconds: int = 300) -> LedgerWatchdogWorker:
    """Singleton accessor for LedgerWatchdogWorker."""
    global _global_watchdog_worker
    with _worker_init_lock:
        if _global_watchdog_worker is None:
            _global_watchdog_worker = LedgerWatchdogWorker(flask_app=flask_app, interval_seconds=interval_seconds)
        return _global_watchdog_worker
