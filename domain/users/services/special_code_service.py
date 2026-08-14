"""Special Code Service for Role Upgrades

This service manages special codes that can be used to upgrade user roles.
It provides a world-standard approach for invitation/promo code systems.
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any
import yaml

logger = logging.getLogger(__name__)


class SpecialCodeService:
    """Service for managing special codes and role upgrades."""

    def __init__(self):
        self._codes_config = None
        self._config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'config',
            'special_codes.yaml'
        )

    def _load_config(self) -> Dict[str, Any]:
        """Load special codes configuration from YAML file."""
        if self._codes_config is not None:
            return self._codes_config

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self._codes_config = config.get('codes', {})
                logger.info(f"Loaded {len(self._codes_config)} special codes from configuration")
                return self._codes_config
        except FileNotFoundError:
            logger.warning(f"Special codes configuration file not found: {self._config_path}")
            self._codes_config = {}
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing special codes configuration: {e}")
            self._codes_config = {}
            return {}

    def validate_code(self, code: str, user_id: int, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """Validate a special code and return its details if valid.

        Args:
            code: The special code to validate
            user_id: The user ID attempting to use the code
            tenant_id: The tenant ID (for tenant-specific codes)

        Returns:
            Dictionary with validation result:
            - valid: bool
            - role: str (if valid)
            - description: str (if valid)
            - error: str (if invalid)
        """
        codes = self._load_config()
        code_config = codes.get(code)

        if not code_config:
            return {
                'valid': False,
                'error': 'Geçersiz özel kod'
            }

        # Check expiration
        expires_at = code_config.get('expires_at')
        if expires_at:
            try:
                expiry_date = datetime.strptime(expires_at, '%Y-%m-%d')
                if datetime.now() > expiry_date:
                    return {
                        'valid': False,
                        'error': 'Bu kodun süresi dolmuş'
                    }
            except ValueError:
                logger.warning(f"Invalid expiration date format for code {code}")

        # Check tenant-specific requirement
        if code_config.get('tenant_specific') and not tenant_id:
            return {
                'valid': False,
                'error': 'Bu kod sadece belirli tenant\'lar için geçerli'
            }

        # Check max uses (would require database tracking in production)
        max_uses = code_config.get('max_uses')
        if max_uses and max_uses <= 0:
            return {
                'valid': False,
                'error': 'Bu kodun kullanım hakkı dolmuş'
            }

        return {
            'valid': True,
            'role': code_config.get('role'),
            'description': code_config.get('description'),
            'metadata': code_config.get('metadata', {})
        }

    def get_code_info(self, code: str) -> Optional[Dict[str, Any]]:
        """Get information about a special code without validation.

        Args:
            code: The special code to look up

        Returns:
            Dictionary with code information or None if not found
        """
        codes = self._load_config()
        return codes.get(code)

    def list_available_codes(self) -> Dict[str, Dict[str, Any]]:
        """List all available special codes (for admin purposes).

        Returns:
            Dictionary of all codes with their configurations
        """
        codes = self._load_config()
        return codes


# Singleton instance
_special_code_service = None


def get_special_code_service() -> SpecialCodeService:
    """Get the singleton instance of SpecialCodeService."""
    global _special_code_service
    if _special_code_service is None:
        _special_code_service = SpecialCodeService()
    return _special_code_service
