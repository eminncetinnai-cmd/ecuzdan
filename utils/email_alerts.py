"""
Email Alert System - Log uyarıları için email gönderme sistemi
"""

import logging
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional


class EmailAlertConfig:
    """Email uyarı konfigürasyonu"""

    def __init__(self):
        self.smtp_server = None
        self.smtp_port = 587
        self.smtp_username = None
        self.smtp_password = None
        self.from_email = None
        self.to_emails: List[str] = []
        self.enabled = False

    def load_from_config(self, config_dict: dict):
        """Konfigürasyonu yükle"""
        self.smtp_server = config_dict.get('SMTP_SERVER')
        self.smtp_port = config_dict.get('SMTP_PORT', 587)
        self.smtp_username = config_dict.get('SMTP_USERNAME')
        self.smtp_password = config_dict.get('SMTP_PASSWORD')
        self.from_email = config_dict.get('FROM_EMAIL')
        self.to_emails = config_dict.get('TO_EMAILS', [])
        self.enabled = config_dict.get('EMAIL_ALERTS_ENABLED', False)


class EmailAlertSystem:
    """Email uyarı sistemi"""

    def __init__(self, config: Optional[EmailAlertConfig] = None):
        self.config = config or EmailAlertConfig()
        self.logger = logging.getLogger(__name__)

    def send_alert(self, subject: str, message: str, priority: str = 'HIGH'):
        """
        Email uyarısı gönder

        Args:
            subject: Email konusu
            message: Email içeriği
            priority: Öncelik seviyesi (LOW, MEDIUM, HIGH, CRITICAL)
        """
        if not self.config.enabled or not self.config.to_emails:
            self.logger.warning("Email alerts disabled or no recipients configured")
            return

        try:
            # Email oluştur
            msg = MIMEMultipart()
            msg['From'] = self.config.from_email
            msg['To'] = ', '.join(self.config.to_emails)
            msg['Subject'] = f"[{priority}] E-Cüzdan Alert: {subject}"

            # Email body
            body = f"""
            <html>
            <body>
                <h2>E-Cüzdan System Alert</h2>
                <p><strong>Priority:</strong> {priority}</p>
                <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <hr>
                <p>{message}</p>
                <hr>
                <p><em>This is an automated alert from E-Cüzdan monitoring system.</em></p>
            </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            # Email gönder
            context = ssl.create_default_context()

            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)

            self.logger.info(f"Email alert sent successfully: {subject}")

        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")

    def send_critical_alert(self, subject: str, message: str):
        """Kritik uyarı gönder"""
        self.send_alert(subject, message, 'CRITICAL')

    def send_error_alert(self, subject: str, message: str):
        """Hata uyarısı gönder"""
        self.send_alert(subject, message, 'HIGH')

    def send_warning_alert(self, subject: str, message: str):
        """Uyarı gönder"""
        self.send_alert(subject, message, 'MEDIUM')

    def send_info_alert(self, subject: str, message: str):
        """Bilgi uyarısı gönder"""
        self.send_alert(subject, message, 'LOW')


# Global instance
_email_alert_system = None


def get_email_alert_system() -> EmailAlertSystem:
    """Global email alert system instance'ı al"""
    global _email_alert_system
    if _email_alert_system is None:
        _email_alert_system = EmailAlertSystem()
    return _email_alert_system


def setup_email_alerts(config_dict: dict):
    """Email uyarı sistemini konfigüre et"""
    config = EmailAlertConfig()
    config.load_from_config(config_dict)

    global _email_alert_system
    _email_alert_system = EmailAlertSystem(config)

    return _email_alert_system
