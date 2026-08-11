"""Factory for creating demo recurring plans."""

import random
from decimal import Decimal
from typing import Dict, Any, Optional

from domain.categories.services.category_service import CategoryService
from domain.demo.config_loader import DemoDataConfigLoader
from models import RecurringPlan
from shared.decimal_precision import to_decimal


class RecurringPlanFactory:
    """Factory for creating demo recurring plans with category validation."""

    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize the recurring plan factory.
        
        Args:
            tenant_id: Tenant ID for tenant-scoped operations
        """
        self.tenant_id = tenant_id
        self.category_service = CategoryService()
        self.config_loader = DemoDataConfigLoader()

    def create_recurring_plan(
        self,
        name: str,
        logical_category: str,
        category_type: str,
        amount: float,
        installments: int,
        payment_day: int,
        note: Optional[str] = None,
        is_admin_generated: bool = False
    ) -> Optional[RecurringPlan]:
        """
        Create a recurring plan with category validation.
        
        Args:
            name: Plan name
            logical_category: Logical/demo category name (e.g., 'salary')
            category_type: Category type ('income', 'expense', 'investment')
            amount: Plan amount
            installments: Number of installments
            payment_day: Payment day of month
            note: Optional note
            is_admin_generated: Whether this is admin-generated data
        
        Returns:
            RecurringPlan object or None if category is invalid
        """
        # Get standard category name
        standard_category = self.config_loader.get_standard_category_name(
            logical_category, category_type
        )
        
        if not standard_category:
            # Fallback: try to use logical category directly
            standard_category = logical_category
        
        # Validate category exists - must be standard category (tenant_id=None)
        if not self.category_service.is_valid_category(standard_category, None):
            logger.warning(f"Invalid category '{standard_category}' - not a standard category")
            return None
        
        # Create recurring plan
        plan = RecurringPlan(
            name=name,
            category=standard_category,
            flow_type=self._map_category_type_to_flow_type(category_type),
            amount=to_decimal(amount),
            installments=installments,
            payment_day=payment_day,
            note=note,
            tenant_id=self.tenant_id
        )
        
        return plan

    def create_recurring_plan_from_template(
        self,
        template_name: str,
        year: int,
        variation_percent: float = 0.0,
        is_admin_generated: bool = False
    ) -> Optional[RecurringPlan]:
        """
        Create a recurring plan from a predefined template.
        
        Args:
            template_name: Template name (e.g., 'salary_plan')
            year: Year for note formatting
            variation_percent: Amount variation percentage
            is_admin_generated: Whether this is admin-generated data
        
        Returns:
            RecurringPlan object or None if template/invalid
        """
        template = self.config_loader.get_recurring_plan_template(template_name)
        if not template:
            return None
        
        # Get generation rule
        rule_name = template.get('amount_rule')
        
        # Handle inline amount rule (dict) vs reference (string)
        if isinstance(rule_name, dict):
            # Inline rule - use directly
            inline_rule = rule_name
            rule = None
        else:
            # Reference to generation rules
            rule_type = self._map_flow_type_to_rule_type(template['type'])
            rule = self.config_loader.get_generation_rule(rule_name, rule_type)
            inline_rule = None
        
        # Calculate amount with variation
        if rule:
            base_amount = rule.get('base_amount', 0)
            amount = base_amount * (1 + random.uniform(-variation_percent, variation_percent))
        elif inline_rule:
            base_amount = inline_rule.get('base_amount', 0)
            amount = base_amount * (1 + random.uniform(-variation_percent, variation_percent))
        else:
            amount = 0
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No amount rule found for template '{template_name}'")
        
        # Format name and note
        name = template.get('name', '').format(year=year)
        note = template.get('note_template', '').format(year=year)
        
        # Get logical category name from template
        logical_category = template.get('category_mapping')
        category_type = self._map_flow_type_to_category_type(template['type'])
        
        return self.create_recurring_plan(
            name=name,
            logical_category=logical_category,
            category_type=category_type,
            amount=amount,
            installments=template.get('installments', 12),
            payment_day=template.get('payment_day', 1),
            note=note,
            is_admin_generated=is_admin_generated
        )

    def _map_category_type_to_flow_type(self, category_type: str) -> str:
        """Map category type to flow type."""
        mapping = {
            'income': 'Gelir',
            'expense': 'Gider',
            'investment': 'Yatırım'
        }
        return mapping.get(category_type, 'Gider')

    def _map_flow_type_to_category_type(self, flow_type: str) -> str:
        """Map flow type to category type."""
        mapping = {
            'Gelir': 'income',
            'Gider': 'expense',
            'Yatırım': 'investment'
        }
        return mapping.get(flow_type, 'expense')
    
    def _map_flow_type_to_rule_type(self, flow_type: str) -> str:
        """Map flow type to rule type for generation rules."""
        mapping = {
            'Gelir': 'income_rules',
            'Gider': 'expense_rules',
            'Yatırım': 'investment_rules'
        }
        return mapping.get(flow_type, 'expense_rules')
