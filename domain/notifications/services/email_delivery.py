"""
Email notification delivery service
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class EmailDeliveryService:
    """Service for delivering email notifications"""
    
    def __init__(self, smtp_server: str = None, smtp_port: int = None,
                 smtp_username: str = None, smtp_password: str = None,
                 from_email: str = None):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port or 587
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.from_email = from_email
    
    def send_email(self, to_emails: List[str], subject: str, body: str,
                  html_body: str = None) -> Dict[str, any]:
        """
        Send email notification
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            Dict with success status and message
        """
        if not self.smtp_server or not self.from_email:
            return {
                'success': False,
                'message': 'SMTP server not configured'
            }
        
        if not to_emails:
            return {
                'success': False,
                'message': 'No recipients specified'
            }
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Connect to SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure connection
                
                # Login if credentials provided
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                # Send email
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {len(to_emails)} recipients")
            return {
                'success': True,
                'message': f'Email sent to {len(to_emails)} recipients'
            }
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication error: {e}")
            return {
                'success': False,
                'message': 'SMTP authentication failed'
            }
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return {
                'success': False,
                'message': f'SMTP error: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Email sending error: {e}")
            return {
                'success': False,
                'message': f'Error sending email: {str(e)}'
            }
    
    def send_notification(self, notification: Dict, to_emails: List[str]) -> Dict[str, any]:
        """
        Send a notification as email
        
        Args:
            notification: Notification dict with title, body, severity, link
            to_emails: List of recipient email addresses
            
        Returns:
            Dict with success status and message
        """
        subject = f"[{notification.get('severity', 'INFO').upper()}] {notification.get('title', 'Notification')}"
        
        # Build plain text body
        body = f"""
{notification.get('title', 'Notification')}

{notification.get('body', '')}

Severity: {notification.get('severity', 'INFO')}
Link: {notification.get('link', '#')}
"""
        
        # Build HTML body
        html_body = f"""
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .notification {{ padding: 20px; border-left: 4px solid #333; }}
        .danger {{ border-color: #dc3545; background-color: #f8d7da; }}
        .warning {{ border-color: #ffc107; background-color: #fff3cd; }}
        .success {{ border-color: #28a745; background-color: #d4edda; }}
        .info {{ border-color: #17a2b8; background-color: #d1ecf1; }}
        .title {{ font-weight: bold; font-size: 18px; margin-bottom: 10px; }}
        .body {{ margin-bottom: 15px; }}
        .link {{ color: #007bff; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="notification {notification.get('severity', 'info')}">
        <div class="title">{notification.get('title', 'Notification')}</div>
        <div class="body">{notification.get('body', '')}</div>
        <div>
            <a href="{notification.get('link', '#')}" class="link">View Details</a>
        </div>
    </div>
</body>
</html>
"""
        
        return self.send_email(to_emails, subject, body, html_body)
    
    def test_connection(self) -> Dict[str, any]:
        """
        Test SMTP connection
        
        Returns:
            Dict with success status and message
        """
        if not self.smtp_server:
            return {
                'success': False,
                'message': 'SMTP server not configured'
            }
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.noop()  # Test connection
            
            return {
                'success': True,
                'message': 'SMTP connection successful'
            }
            
        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return {
                'success': False,
                'message': f'Connection test failed: {str(e)}'
            }


def create_email_service_from_config(config: Dict) -> EmailDeliveryService:
    """
    Create EmailDeliveryService from configuration dict
    
    Args:
        config: Dict with smtp_server, smtp_port, smtp_username, smtp_password, from_email
        
    Returns:
        EmailDeliveryService instance
    """
    return EmailDeliveryService(
        smtp_server=config.get('smtp_server'),
        smtp_port=config.get('smtp_port'),
        smtp_username=config.get('smtp_username'),
        smtp_password=config.get('smtp_password'),
        from_email=config.get('from_email')
    )
