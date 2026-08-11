"""Configuration loader for demo data generation."""

import logging
import os
import yaml
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DemoDataConfigLoader:
    """Loads and manages demo data configuration from YAML files."""

    def __init__(self, config_dir: Optional[str] = None) -> None:
        """
        Initialize the config loader.
        
        Args:
            config_dir: Path to config directory. If None, uses default.
        """
        if config_dir is None:
            # Default to config/demo_data relative to project root
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_dir = os.path.join(project_root, 'config', 'demo_data')
        
        self.config_dir: str = config_dir
        self._category_mappings: Optional[Dict[str, Any]] = None
        self._generation_rules: Optional[Dict[str, Any]] = None
        self._data_templates: Optional[Dict[str, Any]] = None

    def load_category_mappings(self) -> Dict[str, Any]:
        """Load category mappings from YAML."""
        if self._category_mappings is None:
            filepath = os.path.join(self.config_dir, 'category_mappings.yaml')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._category_mappings = yaml.safe_load(f)
                logger.debug(f"Loaded category mappings from {filepath}")
            except FileNotFoundError:
                logger.error(f"Category mappings file not found: {filepath}")
                raise
            except yaml.YAMLError as e:
                logger.error(f"Error parsing category mappings YAML: {e}")
                raise
        return self._category_mappings

    def load_generation_rules(self) -> Dict[str, Any]:
        """Load generation rules from YAML."""
        if self._generation_rules is None:
            filepath = os.path.join(self.config_dir, 'generation_rules.yaml')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._generation_rules = yaml.safe_load(f)
                logger.debug(f"Loaded generation rules from {filepath}")
            except FileNotFoundError:
                logger.error(f"Generation rules file not found: {filepath}")
                raise
            except yaml.YAMLError as e:
                logger.error(f"Error parsing generation rules YAML: {e}")
                raise
        return self._generation_rules

    def load_data_templates(self) -> Dict[str, Any]:
        """Load data templates from YAML."""
        if self._data_templates is None:
            filepath = os.path.join(self.config_dir, 'data_templates.yaml')
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self._data_templates = yaml.safe_load(f)
                logger.debug(f"Loaded data templates from {filepath}")
            except FileNotFoundError:
                logger.error(f"Data templates file not found: {filepath}")
                raise
            except yaml.YAMLError as e:
                logger.error(f"Error parsing data templates YAML: {e}")
                raise
        return self._data_templates

    def get_standard_category_name(self, logical_name: str, category_type: str) -> Optional[str]:
        """
        Get standard category name for a logical name.
        
        Args:
            logical_name: Logical/demo category name (e.g., 'salary')
            category_type: Category type ('income', 'expense', 'investment', 'transfer')
        
        Returns:
            Standard category name or None if not found
        """
        mappings = self.load_category_mappings()
        type_mappings = mappings.get(category_type, {})
        category_info = type_mappings.get(logical_name)
        
        if category_info:
            return category_info.get('standard_name')
        return None

    def get_generation_rule(self, rule_name: str, rule_type: str) -> Optional[Dict[str, Any]]:
        """
        Get generation rule by name and type.
        
        Args:
            rule_name: Rule name (e.g., 'salary', 'food')
            rule_type: Rule type ('income_rules', 'expense_rules', 'investment_rules')
        
        Returns:
            Rule configuration or None if not found
        """
        rules = self.load_generation_rules()
        type_rules = rules.get(rule_type, {})
        return type_rules.get(rule_name)

    def get_transaction_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction template by name.
        
        Args:
            template_name: Template name (e.g., 'monthly_salary')
        
        Returns:
            Template configuration or None if not found
        """
        templates = self.load_data_templates()
        transaction_templates = templates.get('transaction_templates', {})
        return transaction_templates.get(template_name)

    def get_recurring_plan_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get recurring plan template by name.
        
        Args:
            template_name: Template name (e.g., 'salary_plan')
        
        Returns:
            Template configuration or None if not found
        """
        templates = self.load_data_templates()
        plan_templates = templates.get('recurring_plan_templates', {})
        return plan_templates.get(template_name)

    def get_asset_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get asset template by name.
        
        Args:
            template_name: Template name (e.g., 'stock', 'gold')
        
        Returns:
            Template configuration or None if not found
        """
        templates = self.load_data_templates()
        asset_templates = templates.get('asset_templates', {})
        return asset_templates.get(template_name)

    def get_global_settings(self) -> Dict[str, Any]:
        """Get global generation settings."""
        rules = self.load_generation_rules()
        return rules.get('global_settings', {})

    def reload_configs(self) -> None:
        """Reload all configuration files."""
        self._category_mappings = None
        self._generation_rules = None
        self._data_templates = None
        logger.info("Configuration files reloaded")
