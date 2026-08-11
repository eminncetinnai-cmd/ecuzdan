"""Factory for creating demo transactions."""

import logging
import random
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional

from domain.categories.services.category_service import CategoryService
from domain.demo.config_loader import DemoDataConfigLoader
from models import Transaction
from shared.decimal_precision import to_decimal

logger = logging.getLogger(__name__)


class TransactionFactory:
    """Factory for creating demo transactions with category validation."""

    def __init__(self, tenant_id: Optional[str] = None) -> None:
        """
        Initialize the transaction factory.
        
        Args:
            tenant_id: Tenant ID for tenant-scoped operations
        """
        self.tenant_id: Optional[str] = tenant_id
        self.category_service: CategoryService = CategoryService()
        self.config_loader: DemoDataConfigLoader = DemoDataConfigLoader()

    def create_transaction(
        self,
        date: str,
        logical_category: str,
        category_type: str,
        description: str,
        amount: float,
        status: Optional[str] = None,
        is_admin_generated: bool = False
    ) -> Optional[Transaction]:
        """
        Create a transaction with category validation.
        
        Args:
            date: Transaction date (YYYY-MM-DD format)
            logical_category: Logical/demo category name (e.g., 'salary')
            category_type: Category type ('income', 'expense', 'investment', 'transfer')
            description: Transaction description
            amount: Transaction amount
            status: Transaction status (optional)
            is_admin_generated: Whether this is admin-generated data
        
        Returns:
            Transaction object or None if category is invalid
        """
        try:
            # Get standard category name
            standard_category = self.config_loader.get_standard_category_name(
                logical_category, category_type
            )
            
            if not standard_category:
                # Fallback: try to use logical category directly
                standard_category = logical_category
                logger.warning(f"Category mapping not found for '{logical_category}', using fallback")
            
            # Validate category exists - must be standard category (tenant_id=None)
            if not self.category_service.is_valid_category(standard_category, None):
                logger.warning(f"Invalid category '{standard_category}' - not a standard category")
                return None
            
            # Determine status if not provided
            if status is None:
                status = self._determine_status(category_type, standard_category)
            
            # Create transaction
            transaction = Transaction(
                date=date,
                category=standard_category,
                description=description,
                type=self._map_category_type_to_transaction_type(category_type),
                status=status,
                amount=to_decimal(amount),
                source_type=None,
                source_id=None,
                is_admin_generated=is_admin_generated,
                tenant_id=self.tenant_id
            )
            
            logger.debug(f"Created transaction: {description} - {amount} - {standard_category}")
            return transaction
            
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            return None

    def create_transaction_from_template(
        self,
        template_name: str,
        year: int,
        month: int,
        day: Optional[int] = None,
        week: Optional[int] = None,
        variation_percent: float = 0.0,
        is_admin_generated: bool = False
    ) -> Optional[Transaction]:
        """
        Create a transaction from a predefined template.
        
        Args:
            template_name: Template name (e.g., 'monthly_salary')
            year: Year
            month: Month
            day: Day (optional, uses template default if not provided)
            week: Week number (for weekly transactions)
            variation_percent: Amount variation percentage
            is_admin_generated: Whether this is admin-generated data
        
        Returns:
            Transaction object or None if template/invalid
        """
        template = self.config_loader.get_transaction_template(template_name)
        if not template:
            return None
        
        # Get generation rule
        rule_name = template.get('amount_rule')
        rule_type = self._map_transaction_type_to_rule_type(template['type'])
        rule = self.config_loader.get_generation_rule(rule_name, rule_type)
        
        # Handle inline amount_rule (for templates with embedded rules)
        if not rule and isinstance(rule_name, dict):
            rule = rule_name
        
        # Calculate amount with variation
        base_amount = rule.get('base_amount', 0) if rule else 0
        
        # Log warning if base_amount is 0
        if base_amount == 0:
            logger.warning(f"Base amount is 0 for template '{template_name}' with rule '{rule_name}'")
        
        amount = base_amount * (1 + random.uniform(-variation_percent, variation_percent))
        
        # Determine day
        if day is None:
            day = template.get('day', 1)
            if 'day_range' in template:
                day = random.randint(template['day_range'][0], template['day_range'][1])
        
        # Format description
        description = template.get('description_template', '').format(
            year=year, month=month, day=day, week=week
        )
        
        # Format date
        date_str = f"{year}-{month:02d}-{day:02d}"
        
        # Get logical category name from template
        logical_category = template.get('category_mapping')
        category_type = self._map_transaction_type_to_category_type(template['type'])
        
        return self.create_transaction(
            date=date_str,
            logical_category=logical_category,
            category_type=category_type,
            description=description,
            amount=amount,
            is_admin_generated=is_admin_generated
        )

    def _determine_status(self, category_type: str, category_name: str) -> str:
        """Determine appropriate status based on category type and name."""
        # Get generation rule for status distribution
        rule_name = self._map_category_name_to_rule_name(category_name)
        rule_type = f"{category_type}_rules"
        rule = self.config_loader.get_generation_rule(rule_name, rule_type)
        
        if rule and 'status_distribution' in rule:
            status_dist = rule['status_distribution']
            return random.choices(
                list(status_dist.keys()),
                weights=list(status_dist.values())
            )[0]
        
        # Default status based on category type
        if category_type == 'income':
            return random.choice(['Ödendi', 'Ödendi', 'Ödendi', 'Bekliyor'])
        elif category_type == 'expense':
            return random.choice(['Ödendi', 'Ödendi', 'Bekliyor', 'Gecikti', 'İptal'])
        elif category_type == 'investment':
            return random.choice(['Ödendi', 'Ödendi', 'Bekliyor', 'İptal'])
        
        return 'Ödendi'

    def _map_category_type_to_transaction_type(self, category_type: str) -> str:
        """Map category type to transaction type."""
        mapping = {
            'income': 'Gelir',
            'expense': 'Gider',
            'investment': 'Yatırım',
            'transfer': 'Transfer'
        }
        return mapping.get(category_type, 'Gider')

    def _map_transaction_type_to_category_type(self, transaction_type: str) -> str:
        """Map transaction type to category type."""
        mapping = {
            'Gelir': 'income',
            'Gider': 'expense',
            'Yatırım': 'investment',
            'Transfer': 'transfer'
        }
        return mapping.get(transaction_type, 'expense')
    
    def _map_transaction_type_to_rule_type(self, transaction_type: str) -> str:
        """Map transaction type to rule type for generation rules."""
        mapping = {
            'Gelir': 'income_rules',
            'Gider': 'expense_rules',
            'Yatırım': 'investment_rules',
            'Transfer': 'transfer_rules'
        }
        return mapping.get(transaction_type, 'expense_rules')

    def _map_category_name_to_rule_name(self, category_name: str) -> str:
        """Map category name to rule name."""
        # Simple mapping based on common patterns
        mappings = {
            'Maaş / Ücret Geliri': 'salary',
            'Ek Gelir / Yan İş': 'extra_income',
            'Kira Geliri': 'rent_income',
            'Faiz Geliri': 'interest_income',
            'Konut & Kira': 'monthly_fixed',
            'Market & Gıda': 'food',
            'Kredi Kartı': 'credit_card',
            'Vergi': 'tax',
            'Kredi': 'credit',
            'Ulaşım & Yakıt': 'transport',
            'Hisse Senedi Alımı': 'monthly_investment',
            # Legacy mappings for backward compatibility
            'Maaş': 'salary',
            'Ek Gelir': 'extra_income',
            'Kira': 'rent_income',
            'Aylık Sabit Gider': 'monthly_fixed',
            'Gıda': 'food',
            'Ulaşım': 'transport',
            'Hisse Senedi': 'monthly_investment',
        }
        return mappings.get(category_name, category_name.lower())
