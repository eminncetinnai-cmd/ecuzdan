"""Orchestrator for demo data generation using factories."""

import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

from domain.categories.services.category_service import CategoryService
from domain.demo.config_loader import DemoDataConfigLoader
from infrastructure.demo.factories.transaction_factory import TransactionFactory
from infrastructure.demo.factories.recurring_plan_factory import RecurringPlanFactory
from infrastructure.demo.factories.asset_factory import AssetFactory
from models import db, User

logger = logging.getLogger(__name__)


class DemoDataOrchestrator:
    """Orchestrator for generating demo data using factories and configuration."""

    def __init__(self, tenant_id: Optional[str] = None, user_id: Optional[str] = None):
        """
        Initialize the demo data orchestrator.
        
        Args:
            tenant_id: Tenant ID for tenant-scoped operations
            user_id: User ID for user-specific operations
        """
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.category_service = CategoryService()
        self.config_loader = DemoDataConfigLoader()
        
        # Initialize factories
        self.transaction_factory = TransactionFactory(tenant_id)
        self.recurring_plan_factory = RecurringPlanFactory(tenant_id)
        self.asset_factory = AssetFactory(tenant_id)

    def generate_comprehensive_demo_data(
        self,
        start_year: int = 2025,
        end_year: int = 2027,
        is_admin_generated: bool = False
    ) -> Dict[str, int]:
        """
        Generate comprehensive demo data for a date range.
        
        Args:
            start_year: Start year
            end_year: End year
            is_admin_generated: Whether data is admin-generated
        
        Returns:
            Dictionary with generation statistics
        """
        stats = {
            'transactions': 0,
            'recurring_plans': 0,
            'assets': 0,
            'asset_valuations': 0
        }
        
        try:
            logger.info(f"=== {start_year}-{end_year} Demo Data Generation ===")
            
            # Validate categories before generation
            self._validate_categories()
            
            # Generate transactions
            tx_count = self._generate_transactions(start_year, end_year, is_admin_generated)
            stats['transactions'] = tx_count
            logger.info(f"Generated {tx_count} transactions")
            
            # Generate recurring plans
            plan_count = self._generate_recurring_plans(start_year, end_year, is_admin_generated)
            stats['recurring_plans'] = plan_count
            logger.info(f"Generated {plan_count} recurring plans")
            
            # Generate assets
            asset_count, valuation_count = self._generate_assets(start_year, end_year, is_admin_generated)
            stats['assets'] = asset_count
            stats['asset_valuations'] = valuation_count
            logger.info(f"Generated {asset_count} assets with {valuation_count} valuations")
            
            # Commit all changes
            db.session.commit()
            
            logger.info("=== Demo Data Generation Complete ===")
            return stats
            
        except Exception as e:
            logger.error(f"Error during demo data generation: {e}")
            logger.exception("Full exception traceback:")
            db.session.rollback()
            raise

    def _validate_categories(self):
        """Validate that all required categories exist and are standard."""
        try:
            standard_categories = self.category_service.get_standard_categories()
            logger.info(f"Found {len(standard_categories)} standard categories")
            
            if not standard_categories:
                logger.error("No standard categories found in database!")
                raise ValueError("Standard categories must be seeded before demo data generation")
            
            # Validate category mappings
            mappings = self.config_loader.load_category_mappings()
            invalid_categories = []
            
            for category_type, type_mappings in mappings.items():
                for logical_name, category_info in type_mappings.items():
                    standard_name = category_info.get('standard_name')
                    if not standard_name:
                        logger.warning(f"No standard_name defined for {category_type}.{logical_name}")
                        continue
                    
                    # Check if category exists in standard categories (tenant_id=None)
                    is_valid = self.category_service.is_valid_category(standard_name, None)
                    if not is_valid:
                        invalid_categories.append(standard_name)
                        logger.error(f"Invalid category '{standard_name}' for logical name '{logical_name}'")
            
            if invalid_categories:
                error_msg = f"Invalid categories found: {invalid_categories}. These must be standard categories (tenant_id=None)."
                logger.error(error_msg)
                raise ValueError(error_msg)
            else:
                logger.info("All category mappings validated successfully")
                
        except Exception as e:
            logger.error(f"Category validation failed: {e}")
            raise

    def _generate_transactions(
        self,
        start_year: int,
        end_year: int,
        is_admin_generated: bool
    ) -> int:
        """Generate transactions for the date range."""
        count = 0
        
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                # Monthly salary
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_salary', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
                
                # Monthly rent income
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_rent_income', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
                
                # Quarterly dividend
                if month in [3, 6, 9, 12]:
                    tx = self.transaction_factory.create_transaction_from_template(
                        'quarterly_dividend', year, month, is_admin_generated=is_admin_generated
                    )
                    if tx and not self._transaction_exists(tx):
                        db.session.add(tx)
                        count += 1
                
                # Extra income (bi-monthly)
                if month % 2 == 0:
                    tx = self.transaction_factory.create_transaction_from_template(
                        'extra_income', year, month, is_admin_generated=is_admin_generated
                    )
                    if tx and not self._transaction_exists(tx):
                        db.session.add(tx)
                        count += 1
                
                # Monthly rent expense
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_rent_expense', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
                
                # Weekly food (4 weeks per month)
                for week in range(1, 5):
                    tx = self.transaction_factory.create_transaction_from_template(
                        'weekly_food', year, month, week=week, is_admin_generated=is_admin_generated
                    )
                    if tx and not self._transaction_exists(tx):
                        db.session.add(tx)
                        count += 1
                
                # Credit card payment
                tx = self.transaction_factory.create_transaction_from_template(
                    'credit_card_payment', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
                
                # Tax payment
                tx = self.transaction_factory.create_transaction_from_template(
                    'tax_payment', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
                
                # Credit payment
                tx = self.transaction_factory.create_transaction_from_template(
                    'credit_payment', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
                
                # Transport expense
                tx = self.transaction_factory.create_transaction_from_template(
                    'transport_expense', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
                
                # Monthly investment
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_investment', year, month, is_admin_generated=is_admin_generated
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1
        
        return count

    def _generate_recurring_plans(
        self,
        start_year: int,
        end_year: int,
        is_admin_generated: bool
    ) -> int:
        """Generate recurring plans for the date range."""
        count = 0
        
        templates = [
            'salary_plan',
            'rent_income_plan',
            'rent_expense_plan',
            'credit_plan',
            'credit_card_plan',
            'internet_plan',
            'investment_plan'
        ]
        
        for year in range(start_year, end_year + 1):
            for template_name in templates:
                plan = self.recurring_plan_factory.create_recurring_plan_from_template(
                    template_name, year, is_admin_generated=is_admin_generated
                )
                if plan and not self._recurring_plan_exists(plan):
                    db.session.add(plan)
                    count += 1
        
        return count

    def _generate_assets(
        self,
        start_year: int,
        end_year: int,
        is_admin_generated: bool
    ) -> tuple:
        """Generate assets and valuations for the date range."""
        asset_count = 0
        valuation_count = 0
        
        # Asset samples with sectors
        asset_samples = [
            ('stock', 'Türk Hava Yolları', 'THYAO', 'Teknoloji'),
            ('stock', 'Garanti BBVA', 'GARAN', 'Bankacılık'),
            ('gold', 'Gram Altın', 'XAU', 'Emtia & Hammadde'),
            ('forex', 'Döviz Rezervi', 'USD', 'Finansal Sistem'),
            ('fund', 'BIST 100 Fonu', 'BIST100', 'Finansal Sistem'),
        ]
        
        for template_name, name, symbol, sector_name in asset_samples:
            # Check if asset already exists
            from models import Asset
            if Asset.query.filter_by(name=name).first():
                continue
            
            # Get or create sector
            sector = self.asset_factory.get_or_create_sector(sector_name)
            
            # Create asset
            purchase_date = f"{start_year}-01-15"
            asset = self.asset_factory.create_asset_from_template(
                template_name, name, symbol, purchase_date, is_admin_generated=is_admin_generated
            )
            
            if asset:
                asset.sector_id = sector.id
                db.session.add(asset)
                asset_count += 1
                
                # Create valuations (quarterly)
                valuations = self._generate_asset_valuations(
                    asset.id, start_year, purchase_date, is_admin_generated
                )
                valuation_count += valuations
        
        return asset_count, valuation_count

    def _generate_asset_valuations(
        self,
        asset_id: int,
        start_year: int,
        purchase_date: str,
        is_admin_generated: bool
    ) -> int:
        """Generate quarterly asset valuations."""
        count = 0
        growth_steps = [1.0, 1.04, 1.09, 1.12]
        
        purchase_month = int(purchase_date.split('-')[1])
        
        for i, mult in enumerate(growth_steps[1:], start=1):
            month = ((purchase_month - 1 + i * 3) % 12) + 1
            year = start_year + ((purchase_month - 1 + i * 3) // 12)
            
            valuation_date = f"{year}-{month:02d}-28"
            
            # Get asset for current values
            from models import Asset
            asset = Asset.query.get(asset_id)
            if not asset:
                continue
            
            old_val = float(asset.purchase_cost) * growth_steps[i - 1]
            new_val = float(asset.purchase_cost) * mult
            old_price = float(asset.unit_price) * growth_steps[i - 1]
            new_price = float(asset.unit_price) * mult
            
            valuation_data = self.asset_factory.create_asset_valuation(
                asset_id=asset_id,
                old_value=old_val,
                new_value=new_val,
                old_unit_price=old_price,
                new_unit_price=new_price,
                update_type='manual',
                notes="Demo data valuation",
                updated_at=valuation_date
            )
            
            from models import AssetUpdate
            db.session.add(AssetUpdate(**valuation_data))
            count += 1
        
        # Update final asset value
        asset = Asset.query.get(asset_id)
        if asset:
            asset.value = float(asset.purchase_cost) * growth_steps[-1]
            asset.unit_price = float(asset.unit_price) * growth_steps[-1]
            asset.last_updated = datetime.now().strftime('%Y-%m-%d')
        
        return count

    def _transaction_exists(self, transaction) -> bool:
        """Check if transaction already exists."""
        from models import Transaction
        return Transaction.query.filter_by(
            date=transaction.date,
            category=transaction.category,
            description=transaction.description,
            type=transaction.type
        ).first() is not None

    def _recurring_plan_exists(self, plan) -> bool:
        """Check if recurring plan already exists."""
        from models import RecurringPlan
        return RecurringPlan.query.filter_by(name=plan.name).first() is not None


def generate_advanced_demo_data(user_id: Optional[str] = None, start_year: int = 2025, end_year: int = 2027) -> Dict[str, int]:
    """
    Generate comprehensive demo data using the orchestrator.
    
    This is the main entry point for demo data generation from the settings page.
    
    Args:
        user_id: User ID for tenant-scoped data generation
        start_year: Start year for data generation (default: 2025)
        end_year: End year for data generation (default: 2027)
    
    Returns:
        Dictionary with generation statistics (transactions, recurring_plans, assets, asset_valuations)
    """
    # Get tenant_id from user if provided
    tenant_id = None
    if user_id:
        user = User.query.get(user_id)
        if user:
            tenant_id = user.tenant_id
    
    # Create orchestrator and generate data
    orchestrator = DemoDataOrchestrator(tenant_id=tenant_id, user_id=user_id)
    stats = orchestrator.generate_comprehensive_demo_data(
        start_year=start_year,
        end_year=end_year,
        is_admin_generated=True
    )
    
    return stats
