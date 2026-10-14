"""Repository for system monitoring and alert configurations."""

from typing import Any, Dict, Optional

from models import MonitoringAlertConfig

from .base import BaseRepository


class MonitoringRepository(BaseRepository):
    """System monitoring and alert configuration data access."""

    def get_alert_config(self, user_id: int, tenant_id: Optional[str] = None) -> Optional[MonitoringAlertConfig]:
        """Fetch alert configuration for a user and tenant."""
        return (
            self.session.query(MonitoringAlertConfig)
            .filter_by(user_id=user_id, tenant_id=tenant_id)
            .first()
        )

    def save_alert_config(self, user_id: int, tenant_id: Optional[str], data: Dict[str, Any]) -> MonitoringAlertConfig:
        """Create or update alert configuration."""
        config = self.get_alert_config(user_id, tenant_id)
        if not config:
            config = MonitoringAlertConfig(
                user_id=user_id,
                tenant_id=tenant_id,
                email_alerts_enabled=data.get('email_alerts_enabled', False),
                smtp_server=data.get('smtp_server'),
                smtp_port=data.get('smtp_port'),
                smtp_username=data.get('smtp_username'),
                smtp_password=data.get('smtp_password'),
                from_email=data.get('from_email'),
                to_emails=data.get('to_emails', []),
                alert_thresholds=data.get('alert_thresholds', {
                    'error_rate': 10,
                    'critical_rate': 1,
                    'disk_space_percent': 10,
                }),
            )
            self.session.add(config)
        else:
            config.email_alerts_enabled = data.get('email_alerts_enabled', config.email_alerts_enabled)
            config.smtp_server = data.get('smtp_server', config.smtp_server)
            config.smtp_port = data.get('smtp_port', config.smtp_port)
            config.smtp_username = data.get('smtp_username', config.smtp_username)
            if data.get('smtp_password'):
                config.smtp_password = data.get('smtp_password')
            config.from_email = data.get('from_email', config.from_email)
            config.to_emails = data.get('to_emails', config.to_emails)
            config.alert_thresholds = data.get('alert_thresholds', config.alert_thresholds)

        self.session.commit()
        return config
