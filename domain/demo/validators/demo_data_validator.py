"""Validation layer for demo data generation."""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from domain.categories.services.category_service import CategoryService
from domain.demo.config_loader import DemoDataConfigLoader


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, message: str):
        """Add an error message."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message."""
        self.warnings.append(message)


class DemoDataValidator:
    """Validator for demo data configuration and generation."""

    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize the validator.
        
        Args:
            tenant_id: Tenant ID for tenant-scoped validation
        """
        self.tenant_id = tenant_id
        self.category_service = CategoryService()
        self.config_loader = DemoDataConfigLoader()

    def validate_category_mappings(self) -> ValidationResult:
        """
        Validate all category mappings in configuration.
        
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        mappings = self.config_loader.load_category_mappings()
        
        for category_type, type_mappings in mappings.items():
            for logical_name, category_info in type_mappings.items():
                standard_name = category_info.get('standard_name')
                category_type_from_config = category_info.get('category_type')
                
                # Validate standard category exists
                if not self.category_service.is_valid_category(standard_name, self.tenant_id):
                    result.add_error(
                        f"Invalid standard category '{standard_name}' for logical name '{logical_name}'"
                    )
                
                # Validate category type matches
                category = self.category_service.get_category_by_name(standard_name, self.tenant_id)
                if category and category.type != category_type_from_config:
                    result.add_error(
                        f"Category type mismatch for '{standard_name}': "
                        f"config says '{category_type_from_config}', actual is '{category.type}'"
                    )
        
        return result

    def validate_generation_rules(self) -> ValidationResult:
        """
        Validate generation rules configuration.
        
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        rules = self.config_loader.load_generation_rules()
        
        # Check required rule types
        required_rule_types = ['income_rules', 'expense_rules', 'investment_rules']
        for rule_type in required_rule_types:
            if rule_type not in rules:
                result.add_error(f"Missing required rule type: {rule_type}")
        
        # Validate individual rules
        for rule_type in rules.keys():
            if rule_type == 'global_settings':
                continue
                
            for rule_name, rule_config in rules[rule_type].items():
                # Skip validation for configuration-only rules
                if rule_name in ['investment_direction', 'asset_types']:
                    continue
                
                # Validate required fields for transaction-generating rules
                required_fields = ['base_amount', 'amount_range']
                for field in required_fields:
                    if field not in rule_config:
                        result.add_error(
                            f"Missing required field '{field}' in rule '{rule_name}' of type '{rule_type}'"
                        )
                
                # Validate amount range
                if 'amount_range' in rule_config:
                    amount_range = rule_config['amount_range']
                    if 'min' not in amount_range or 'max' not in amount_range:
                        result.add_error(
                            f"Invalid amount_range in rule '{rule_name}': must have 'min' and 'max'"
                        )
                    elif amount_range['min'] > amount_range['max']:
                        result.add_error(
                            f"Invalid amount_range in rule '{rule_name}': min > max"
                        )
                
                # Validate status distribution
                if 'status_distribution' in rule_config:
                    status_dist = rule_config['status_distribution']
                    total = sum(status_dist.values())
                    if abs(total - 1.0) > 0.01:  # Allow small floating point errors
                        result.add_warning(
                            f"Status distribution in rule '{rule_name}' does not sum to 1.0 (sum: {total})"
                        )
        
        return result

    def validate_data_templates(self) -> ValidationResult:
        """
        Validate data templates configuration.
        
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        templates = self.config_loader.load_data_templates()
        
        # Validate transaction templates
        if 'transaction_templates' in templates:
            for template_name, template_config in templates['transaction_templates'].items():
                # Validate required fields
                required_fields = ['category_mapping', 'description_template', 'amount_rule', 'type']
                for field in required_fields:
                    if field not in template_config:
                        result.add_error(
                            f"Missing required field '{field}' in transaction template '{template_name}'"
                        )
                
                # Validate category mapping exists
                logical_category = template_config.get('category_mapping')
                category_type = self._map_transaction_type_to_category_type(template_config.get('type'))
                standard_name = self.config_loader.get_standard_category_name(logical_category, category_type)
                
                if not standard_name:
                    result.add_error(
                        f"Invalid category mapping '{logical_category}' in transaction template '{template_name}'"
                    )
        
        # Validate recurring plan templates
        if 'recurring_plan_templates' in templates:
            for template_name, template_config in templates['recurring_plan_templates'].items():
                # Validate required fields
                required_fields = ['category_mapping', 'amount_rule', 'type', 'installments', 'payment_day']
                for field in required_fields:
                    if field not in template_config:
                        result.add_error(
                            f"Missing required field '{field}' in recurring plan template '{template_name}'"
                        )
        
        # Validate asset templates
        if 'asset_templates' in templates:
            for template_name, template_config in templates['asset_templates'].items():
                # Validate required fields
                required_fields = ['type', 'category_mapping', 'base_quantity', 'base_price', 'currency']
                for field in required_fields:
                    if field not in template_config:
                        result.add_error(
                            f"Missing required field '{field}' in asset template '{template_name}'"
                        )
        
        return result

    def validate_all_configurations(self) -> ValidationResult:
        """
        Validate all demo data configurations.
        
        Returns:
            ValidationResult with combined validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate category mappings
        category_result = self.validate_category_mappings()
        result.errors.extend(category_result.errors)
        result.warnings.extend(category_result.warnings)
        
        # Validate generation rules
        rules_result = self.validate_generation_rules()
        result.errors.extend(rules_result.errors)
        result.warnings.extend(rules_result.warnings)
        
        # Validate data templates
        templates_result = self.validate_data_templates()
        result.errors.extend(templates_result.errors)
        result.warnings.extend(templates_result.warnings)
        
        result.is_valid = len(result.errors) == 0
        
        return result

    def validate_transaction_data(
        self,
        category: str,
        amount: float,
        transaction_type: str
    ) -> ValidationResult:
        """
        Validate transaction data before creation.
        
        Args:
            category: Category name
            amount: Transaction amount
            transaction_type: Transaction type
        
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate category exists
        if not self.category_service.is_valid_category(category, self.tenant_id):
            result.add_error(f"Invalid category: {category}")
        
        # Validate amount
        if amount <= 0:
            result.add_error(f"Amount must be positive: {amount}")
        
        # Validate transaction type
        valid_types = ['Gelir', 'Gider', 'Yatırım', 'Transfer']
        if transaction_type not in valid_types:
            result.add_error(f"Invalid transaction type: {transaction_type}")
        
        return result

    def validate_recurring_plan_data(
        self,
        category: str,
        amount: float,
        installments: int,
        payment_day: int
    ) -> ValidationResult:
        """
        Validate recurring plan data before creation.
        
        Args:
            category: Category name
            amount: Plan amount
            installments: Number of installments
            payment_day: Payment day of month
        
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate category exists
        if not self.category_service.is_valid_category(category, self.tenant_id):
            result.add_error(f"Invalid category: {category}")
        
        # Validate amount
        if amount <= 0:
            result.add_error(f"Amount must be positive: {amount}")
        
        # Validate installments
        if installments <= 0:
            result.add_error(f"Installments must be positive: {installments}")
        
        # Validate payment day
        if payment_day < 1 or payment_day > 31:
            result.add_error(f"Payment day must be between 1 and 31: {payment_day}")
        
        return result

    def _map_transaction_type_to_category_type(self, transaction_type: str) -> str:
        """Map transaction type to category type."""
        mapping = {
            'Gelir': 'income',
            'Gider': 'expense',
            'Yatırım': 'investment',
            'Transfer': 'transfer'
        }
        return mapping.get(transaction_type, 'expense')
