"""Log-based alert monitor — checks error rates and triggers notifications."""

from __future__ import annotations

import logging
import os
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, Optional

logger = logging.getLogger(__name__)

LOG_LINE_PATTERN = re.compile(
    r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?\b(CRITICAL|ERROR|WARNING)\b'
)


class LogAlertMonitor:
    """Scan recent log lines and emit alerts when thresholds are exceeded."""

    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        self.error_log_file = os.path.join(self.log_dir, 'e_cuzdan_errors.log')
        self.main_log_file = os.path.join(self.log_dir, 'e_cuzdan.log')
        self.enabled = os.getenv('LOG_ALERTS_ENABLED', 'false').lower() in ('1', 'true', 'yes')
        self.error_threshold = int(os.getenv('LOG_ALERT_ERROR_THRESHOLD', '10'))
        self.critical_threshold = int(os.getenv('LOG_ALERT_CRITICAL_THRESHOLD', '1'))
        self.window_minutes = int(os.getenv('LOG_ALERT_WINDOW_MINUTES', '1'))
        self.cooldown_minutes = int(os.getenv('LOG_ALERT_COOLDOWN_MINUTES', '15'))
        self._last_alert_at: Dict[str, datetime] = {}

    def _can_alert(self, alert_key: str) -> bool:
        last_sent = self._last_alert_at.get(alert_key)
        if not last_sent:
            return True
        return datetime.now() - last_sent >= timedelta(minutes=self.cooldown_minutes)

    def _mark_alert_sent(self, alert_key: str) -> None:
        self._last_alert_at[alert_key] = datetime.now()

    def _read_recent_levels(self) -> Counter:
        counts: Counter = Counter()
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        files = [self.error_log_file, self.main_log_file]

        for file_path in files:
            if not os.path.exists(file_path):
                continue
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as handle:
                    for line in handle.readlines()[-2000:]:
                        match = LOG_LINE_PATTERN.search(line)
                        if not match:
                            continue
                        timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                        if timestamp >= cutoff:
                            counts[match.group(2)] += 1
            except Exception as exc:
                logger.debug('Log alert scan skipped for %s: %s', file_path, exc)

        return counts

    def _notify(self, subject: str, message: str, priority: str) -> None:
        try:
            from utils.email_alerts import get_email_alert_system

            email_system = get_email_alert_system()
            if priority == 'CRITICAL':
                email_system.send_critical_alert(subject, message)
            elif priority == 'HIGH':
                email_system.send_error_alert(subject, message)
            else:
                email_system.send_warning_alert(subject, message)
        except Exception as exc:
            logger.warning('Log alert notification failed: %s', exc)

    def evaluate(self) -> Dict:
        """Read recent log levels without sending notifications."""
        result = {
            'enabled': self.enabled,
            'checked_at': datetime.now().isoformat(),
            'counts': {},
            'thresholds': {
                'error': self.error_threshold,
                'critical': self.critical_threshold,
                'window_minutes': self.window_minutes,
            },
        }

        if not self.enabled:
            return result

        try:
            counts = self._read_recent_levels()
            result['counts'] = dict(counts)
            result['breached'] = {
                'critical': counts.get('CRITICAL', 0) >= self.critical_threshold,
                'error': counts.get('ERROR', 0) >= self.error_threshold,
            }
        except Exception as exc:
            result['error'] = str(exc)

        return result

    def check(self) -> Dict:
        """Run one alert evaluation cycle. Never raises."""
        result = self.evaluate()
        result['alerts_triggered'] = []

        if not self.enabled or result.get('error'):
            return result

        try:
            counts = result.get('counts', {})
            critical_count = counts.get('CRITICAL', 0)
            error_count = counts.get('ERROR', 0)

            if critical_count >= self.critical_threshold and self._can_alert('critical'):
                message = (
                    f'{critical_count} CRITICAL log(s) detected in the last '
                    f'{self.window_minutes} minute(s).'
                )
                self._notify('Critical log threshold exceeded', message, 'CRITICAL')
                self._mark_alert_sent('critical')
                result['alerts_triggered'].append('critical')

            if error_count >= self.error_threshold and self._can_alert('error'):
                message = (
                    f'{error_count} ERROR log(s) detected in the last '
                    f'{self.window_minutes} minute(s).'
                )
                self._notify('Error log threshold exceeded', message, 'HIGH')
                self._mark_alert_sent('error')
                result['alerts_triggered'].append('error')

        except Exception as exc:
            logger.debug('Log alert check failed: %s', exc)
            result['error'] = str(exc)

        return result


_monitor: Optional[LogAlertMonitor] = None


def get_log_alert_monitor() -> LogAlertMonitor:
    global _monitor
    if _monitor is None:
        _monitor = LogAlertMonitor()
    return _monitor
