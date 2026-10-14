"""
Log Action System - Log sınıflandırma ve otomatik aksiyon sistemi
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional


class LogSeverity(Enum):
    """Log önem seviyeleri"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogCategory(Enum):
    """Log kategorileri"""
    SECURITY = "SECURITY"
    DATABASE = "DATABASE"
    PERFORMANCE = "PERFORMANCE"
    BUSINESS = "BUSINESS"
    SYSTEM = "SYSTEM"


@dataclass
class LogAction:
    """Log aksiyon tanımı"""
    action_type: str
    priority: int  # 1-10, 1 en yüksek öncelik
    cooldown_minutes: int = 60  # Aynı aksiyon için bekleme süresi
    enabled: bool = True


class LogActionConfig:
    """Log aksiyon konfigürasyonu"""

    # Varsayılan aksiyon tanımları
    DEFAULT_ACTIONS = {
        LogSeverity.CRITICAL: [
            LogAction("email_alert", 1, 30),
            LogAction("log_to_db", 1, 0),
            LogAction("immediate_notification", 1, 15),
        ],
        LogSeverity.ERROR: [
            LogAction("log_to_db", 3, 0),
            LogAction("create_ticket", 5, 120),
        ],
        LogSeverity.WARNING: [
            LogAction("monitoring_dashboard", 7, 0),
        ],
        LogCategory.SECURITY: [
            LogAction("security_team_alert", 1, 0),
            LogAction("audit_log", 1, 0),
        ],
    }

    def __init__(self):
        self.actions = self.DEFAULT_ACTIONS.copy()
        self.action_history: Dict[str, datetime] = {}
        self.action_handlers: Dict[str, Callable] = {
            'email_alert': self._email_alert,
            'log_to_db': self._log_to_db,
            'immediate_notification': self._immediate_notification,
            'create_ticket': self._create_ticket,
            'monitoring_dashboard': self._monitoring_dashboard,
            'security_team_alert': self._security_team_alert,
            'audit_log': self._audit_log,
        }

    def get_actions_for_log(self, severity: LogSeverity, category: Optional[LogCategory] = None) -> List[LogAction]:
        """Log için applicable aksiyonları döndür"""
        actions = []

        if severity in self.actions:
            actions.extend(self.actions[severity])

        if category and category in self.actions:
            actions.extend(self.actions[category])

        # Öncelik sırasına göre sırala
        actions.sort(key=lambda x: x.priority)

        return [a for a in actions if a.enabled]

    def can_execute_action(self, action: LogAction) -> bool:
        """Aksiyon cooldown kontrolü"""
        action_key = f"{action.action_type}_{action.priority}"

        if action_key in self.action_history:
            last_execution = self.action_history[action_key]
            cooldown = timedelta(minutes=action.cooldown_minutes)

            if datetime.now() - last_execution < cooldown:
                return False

        return True

    def execute_action(self, action: LogAction, log_data: Dict):
        """Aksiyonu çalıştır"""
        if not self.can_execute_action(action):
            return

        handler = self.action_handlers.get(action.action_type)
        if handler:
            try:
                handler(log_data)

                # Action history güncelle
                action_key = f"{action.action_type}_{action.priority}"
                self.action_history[action_key] = datetime.now()

            except Exception as e:
                logging.getLogger(__name__).error(f"Action execution failed: {action.action_type} - {e}")

    # Aksiyon handler'ları
    def _email_alert(self, log_data: Dict):
        """Email uyarısı gönder"""
        try:
            from utils.email_alerts import get_email_alert_system
            email_system = get_email_alert_system()

            subject = f"{log_data.get('severity', 'INFO')} - {log_data.get('category', 'SYSTEM')}"
            message = f"""
            <strong>Log Message:</strong> {log_data.get('message', 'N/A')}<br>
            <strong>Severity:</strong> {log_data.get('severity', 'N/A')}<br>
            <strong>Category:</strong> {log_data.get('category', 'N/A')}<br>
            <strong>Timestamp:</strong> {log_data.get('timestamp', 'N/A')}<br>
            """

            if log_data.get('severity') == 'CRITICAL':
                email_system.send_critical_alert(subject, message)
            elif log_data.get('severity') == 'ERROR':
                email_system.send_error_alert(subject, message)
            else:
                email_system.send_warning_alert(subject, message)

        except ImportError:
            logging.getLogger(__name__).info(f"EMAIL ALERT (fallback): {log_data}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Email alert failed: {e}")

    def _log_to_db(self, log_data: Dict):
        """Log'u veritabanına kaydet"""
        # TODO: DB entegrasyonu
        logging.getLogger(__name__).info(f"LOG TO DB: {log_data}")

    def _immediate_notification(self, log_data: Dict):
        """Anlık bildirim gönder"""
        # TODO: Push notification entegrasyonu
        logging.getLogger(__name__).info(f"IMMEDIATE NOTIFICATION: {log_data}")

    def _create_ticket(self, log_data: Dict):
        """Destek bileti oluştur"""
        # TODO: Ticket sistemi entegrasyonu
        logging.getLogger(__name__).info(f"CREATE TICKET: {log_data}")

    def _monitoring_dashboard(self, log_data: Dict):
        """Monitoring dashboard'a gönder"""
        # TODO: Dashboard entegrasyonu
        logging.getLogger(__name__).info(f"MONITORING DASHBOARD: {log_data}")

    def _security_team_alert(self, log_data: Dict):
        """Güvenlik ekibi uyarısı"""
        # TODO: Security team entegrasyonu
        logging.getLogger(__name__).info(f"SECURITY TEAM ALERT: {log_data}")

    def _audit_log(self, log_data: Dict):
        """Denetim logu kaydet"""
        # TODO: Audit log sistemi
        logging.getLogger(__name__).info(f"AUDIT LOG: {log_data}")


class LogClassifier:
    """Log sınıflandırma sistemi"""

    # Log pattern'ları ve kategorileri
    PATTERNS = {
        LogCategory.SECURITY: [
            r'authentication.*failed',
            r'unauthorized.*access',
            r'sql.*injection',
            r'xss.*attack',
            r'brute.*force',
            r'session.*hijack',
        ],
        LogCategory.DATABASE: [
            r'database.*connection.*failed',
            r'sql.*error',
            r'timeout.*database',
            r'deadlock',
            r'foreign.*key.*violation',
        ],
        LogCategory.PERFORMANCE: [
            r'slow.*query',
            r'high.*memory',
            r'cpu.*usage',
            r'response.*time',
            r'latency',
        ],
        LogCategory.BUSINESS: [
            r'payment.*failed',
            r'transaction.*error',
            r'validation.*failed',
            r'business.*rule',
        ],
    }

    def __init__(self):
        self.action_config = LogActionConfig()

    def classify_log(self, log_message: str, level: str) -> tuple:
        """Log'u sınıflandır"""
        severity = LogSeverity(level.upper()) if level.upper() in LogSeverity.__members__ else LogSeverity.INFO
        category = self._detect_category(log_message)

        return severity, category

    def _detect_category(self, log_message: str) -> Optional[LogCategory]:
        """Log kategorisini tespit et"""
        import re

        for category, patterns in self.PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, log_message, re.IGNORECASE):
                    return category

        return LogCategory.SYSTEM

    def process_log(self, log_message: str, level: str, additional_data: Optional[Dict] = None):
        """Log'u işle ve aksiyonları tetikle"""
        severity, category = self.classify_log(log_message, level)

        actions = self.action_config.get_actions_for_log(severity, category)

        log_data = {
            'message': log_message,
            'severity': severity.value,
            'category': category.value if category else None,
            'timestamp': datetime.now().isoformat(),
            **(additional_data or {})
        }

        for action in actions:
            self.action_config.execute_action(action, log_data)


# Global instance
_log_classifier = None


def get_log_classifier() -> LogClassifier:
    """Global log classifier instance'ı al"""
    global _log_classifier
    if _log_classifier is None:
        _log_classifier = LogClassifier()
    return _log_classifier
