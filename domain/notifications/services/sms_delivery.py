"""
SMS notification delivery service
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class SMSDeliveryService:
    """Service for delivering SMS notifications"""

    def __init__(self, api_key: str = None, api_secret: str = None,
                 sender_id: str = None, provider: str = 'twilio'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.sender_id = sender_id
        self.provider = provider  # 'twilio', 'nexmo', 'messagebird', etc.

    def send_sms(self, to_phone: str, message: str) -> Dict[str, any]:
        """
        Send SMS notification

        Args:
            to_phone: Recipient phone number (with country code, e.g., +905321234567)
            message: SMS message body

        Returns:
            Dict with success status and message
        """
        if not self.api_key or not self.api_secret:
            return {
                'success': False,
                'message': 'SMS API credentials not configured'
            }

        if not to_phone:
            return {
                'success': False,
                'message': 'No phone number specified'
            }

        if not message:
            return {
                'success': False,
                'message': 'No message specified'
            }

        try:
            if self.provider == 'twilio':
                return self._send_via_twilio(to_phone, message)
            elif self.provider == 'nexmo':
                return self._send_via_nexmo(to_phone, message)
            elif self.provider == 'messagebird':
                return self._send_via_messagebird(to_phone, message)
            else:
                return {
                    'success': False,
                    'message': f'Unsupported SMS provider: {self.provider}'
                }

        except Exception as e:
            logger.error(f"SMS sending error: {e}")
            return {
                'success': False,
                'message': f'Error sending SMS: {str(e)}'
            }

    def _send_via_twilio(self, to_phone: str, message: str) -> Dict[str, any]:
        """Send SMS via Twilio API"""
        try:
            from twilio.rest import Client

            client = Client(self.api_key, self.api_secret)

            sms = client.messages.create(
                body=message,
                from_=self.sender_id,
                to=to_phone
            )

            logger.info(f"SMS sent via Twilio: {sms.sid}")
            return {
                'success': True,
                'message': f'SMS sent via Twilio: {sms.sid}',
                'message_id': sms.sid
            }

        except ImportError:
            logger.warning("Twilio library not installed")
            return {
                'success': False,
                'message': 'Twilio library not installed'
            }
        except Exception as e:
            logger.error(f"Twilio SMS error: {e}")
            return {
                'success': False,
                'message': f'Twilio error: {str(e)}'
            }

    def _send_via_nexmo(self, to_phone: str, message: str) -> Dict[str, any]:
        """Send SMS via Nexmo (Vonage) API"""
        try:
            import vonage

            client = vonage.Client(key=self.api_key, secret=self.api_secret)

            response = client.sms.send_message({
                "from": self.sender_id,
                "to": to_phone,
                "text": message,
            })

            if response["messages"][0]["status"] == "0":
                logger.info(f"SMS sent via Nexmo: {response['messages'][0]['message-id']}")
                return {
                    'success': True,
                    'message': 'SMS sent via Nexmo',
                    'message_id': response['messages'][0]['message-id']
                }
            else:
                logger.error(f"Nexmo SMS error: {response['messages'][0]['error-text']}")
                return {
                    'success': False,
                    'message': response['messages'][0]['error-text']
                }

        except ImportError:
            logger.warning("Vonage/Nexmo library not installed")
            return {
                'success': False,
                'message': 'Vonage/Nexmo library not installed'
            }
        except Exception as e:
            logger.error(f"Nexmo SMS error: {e}")
            return {
                'success': False,
                'message': f'Nexmo error: {str(e)}'
            }

    def _send_via_messagebird(self, to_phone: str, message: str) -> Dict[str, any]:
        """Send SMS via MessageBird API"""
        try:
            from messagebird.client import Client

            client = Client(self.api_key, self.api_secret)

            message_obj = client.message_create(
                self.sender_id,
                to_phone,
                message
            )

            logger.info(f"SMS sent via MessageBird: {message_obj.id}")
            return {
                'success': True,
                'message': 'SMS sent via MessageBird',
                'message_id': message_obj.id
            }

        except ImportError:
            logger.warning("MessageBird library not installed")
            return {
                'success': False,
                'message': 'MessageBird library not installed'
            }
        except Exception as e:
            logger.error(f"MessageBird SMS error: {e}")
            return {
                'success': False,
                'message': f'MessageBird error: {str(e)}'
            }

    def send_notification(self, notification: Dict, to_phone: str) -> Dict[str, any]:
        """
        Send a notification as SMS

        Args:
            notification: Notification dict with title, body, severity, link
            to_phone: Recipient phone number

        Returns:
            Dict with success status and message
        """
        # Build SMS message (keep it short, SMS has 160 char limit)
        severity_emoji = {
            'danger': '🚨',
            'warning': '⚠️',
            'success': '✅',
            'info': 'ℹ️'
        }

        emoji = severity_emoji.get(notification.get('severity', 'info'), 'ℹ️')

        message = f"{emoji} {notification.get('title', 'Notification')}\n"
        message += f"{notification.get('body', '')}\n"

        # Truncate if too long
        if len(message) > 160:
            message = message[:157] + "..."

        return self.send_sms(to_phone, message)

    def test_connection(self) -> Dict[str, any]:
        """
        Test SMS API connection

        Returns:
            Dict with success status and message
        """
        if not self.api_key or not self.api_secret:
            return {
                'success': False,
                'message': 'SMS API credentials not configured'
            }

        # For SMS, we can't really test without sending a message
        # So we just validate the credentials format
        if len(self.api_key) < 10:
            return {
                'success': False,
                'message': 'Invalid API key format'
            }

        return {
            'success': True,
            'message': 'SMS API credentials appear valid (send test SMS to verify)'
        }


def create_sms_service_from_config(config: Dict) -> SMSDeliveryService:
    """
    Create SMSDeliveryService from configuration dict

    Args:
        config: Dict with api_key, api_secret, sender_id, provider

    Returns:
        SMSDeliveryService instance
    """
    return SMSDeliveryService(
        api_key=config.get('api_key'),
        api_secret=config.get('api_secret'),
        sender_id=config.get('sender_id'),
        provider=config.get('provider', 'twilio')
    )
