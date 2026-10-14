"""Startup validation for demo data configuration."""

import logging
from typing import Optional

from domain.demo.config_loader import DemoDataConfigLoader
from domain.demo.validators.demo_data_validator import DemoDataValidator

logger = logging.getLogger(__name__)


class DemoDataStartupValidator:
    """Validates demo data configuration on application startup."""

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """
        Initialize the startup validator.

        Args:
            config_dir: Path to config directory. If None, uses default.
        """
        self.config_loader = DemoDataConfigLoader(config_dir)
        self.validator = DemoDataValidator()

    def validate_all(self) -> bool:
        """
        Validate all demo data configurations.

        Returns:
            bool: True if all validations pass, False otherwise
        """
        logger.debug("Starting demo data configuration validation...")

        try:
            # Validate category mappings
            category_result = self.validator.validate_category_mappings()
            if not category_result.is_valid:
                logger.error("Category mappings validation failed:")
                for error in category_result.errors:
                    logger.error(f"  - {error}")
            else:
                logger.debug("✓ Category mappings validation passed")

            # Validate generation rules
            rules_result = self.validator.validate_generation_rules()
            if not rules_result.is_valid:
                logger.error("Generation rules validation failed:")
                for error in rules_result.errors:
                    logger.error(f"  - {error}")
            else:
                logger.debug("✓ Generation rules validation passed")

            # Validate data templates
            templates_result = self.validator.validate_data_templates()
            if not templates_result.is_valid:
                logger.error("Data templates validation failed:")
                for error in templates_result.errors:
                    logger.error(f"  - {error}")
            else:
                logger.debug("✓ Data templates validation passed")

            # Log warnings
            all_warnings = category_result.warnings + rules_result.warnings + templates_result.warnings
            if all_warnings:
                logger.warning("Configuration validation warnings:")
                for warning in all_warnings:
                    logger.warning(f"  - {warning}")

            # Overall result
            is_valid = (
                category_result.is_valid and
                rules_result.is_valid and
                templates_result.is_valid
            )

            if is_valid:
                logger.debug("✓ All demo data configuration validations passed")
            else:
                logger.error("✗ Demo data configuration validation failed")

            return is_valid

        except Exception as e:
            logger.error(f"Error during configuration validation: {e}")
            logger.exception("Full exception traceback:")
            return False

    def validate_with_tenant(self, tenant_id: str) -> bool:
        """
        Validate configurations for a specific tenant.

        Args:
            tenant_id: Tenant ID to validate against

        Returns:
            bool: True if all validations pass, False otherwise
        """
        logger.info(f"Starting demo data configuration validation for tenant '{tenant_id}'...")

        # Update validator with tenant context
        self.validator.tenant_id = tenant_id

        return self.validate_all()


def validate_demo_data_config(config_dir: Optional[str] = None) -> bool:
    """
    Convenience function to validate demo data configuration.

    Args:
        config_dir: Path to config directory. If None, uses default.

    Returns:
        bool: True if all validations pass, False otherwise
    """
    validator = DemoDataStartupValidator(config_dir)
    return validator.validate_all()
