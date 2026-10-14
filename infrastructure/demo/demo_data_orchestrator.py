"""Orchestrator for demo data generation using factories."""

import logging
from datetime import date, datetime
from typing import Dict, Optional, Tuple

from domain.categories.services.category_service import CategoryService
from domain.demo.config_loader import DemoDataConfigLoader
from domain.planning.models.plan_contracts import OccurrenceStatus
from domain.transactions.services import (
    create_adjustment_transaction,
    create_reversal_transaction,
    sell_asset_position,
)
from infrastructure.demo.factories.asset_factory import AssetFactory
from infrastructure.demo.factories.recurring_plan_factory import RecurringPlanFactory
from infrastructure.demo.factories.transaction_factory import TransactionFactory
from models import (
    Asset,
    AssetUpdate,
    BankAccount,
    BankStatementSnapshot,
    LedgerAdjustment,
    PlanOccurrence,
    RecurringPlan,
    Transaction,
    User,
    db,
)
from shared.decimal_precision import to_decimal

logger = logging.getLogger(__name__)


def _has_active_context() -> bool:
    """Check if Flask application context is available."""
    try:
        from flask import has_app_context
        return bool(has_app_context())
    except Exception:
        return False


class DemoDataOrchestrator:
    """Orchestrator for generating comprehensive demo data using factories and domain services."""

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
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        is_admin_generated: bool = False
    ) -> Dict[str, int]:
        """
        Generate comprehensive demo data for a dynamic 3-year timeline.

        Default timeline anchors dynamically around datetime.now().year:
        - 1 year past (historical paid records)
        - Current year (current month mixed, past months paid/overdue)
        - 1 year future (scheduled plans & pending occurrences)

        Args:
            start_year: Optional start year (defaults to current_year - 1)
            end_year: Optional end year (defaults to current_year + 1)
            is_admin_generated: Whether data is admin-generated

        Returns:
            Dictionary with generation statistics
        """
        current_year = datetime.now().year
        if start_year is None:
            start_year = current_year - 1
        if end_year is None:
            end_year = current_year + 1

        stats = {
            'transactions': 0,
            'recurring_plans': 0,
            'plan_occurrences': 0,
            'assets': 0,
            'asset_valuations': 0,
            'bank_accounts': 0,
            'reversals': 0,
            'adjustments': 0,
        }

        try:
            logger.info(f"=== {start_year}-{end_year} Demo Data Generation Started ===")

            # Validate categories before generation
            self._validate_categories()

            active_ctx = _has_active_context()
            initial_tx_count = Transaction.query.filter_by(tenant_id=self.tenant_id).count() if active_ctx else 0

            # Ensure bank accounts and reconciliation snapshot exist
            accounts = self._ensure_bank_accounts() if active_ctx else {}
            stats['bank_accounts'] = len(accounts)

            # Generate transactions
            tx_count = self._generate_transactions(start_year, end_year, is_admin_generated, accounts)

            # Generate recurring plans & occurrences
            plan_res = self._generate_recurring_plans(start_year, end_year, is_admin_generated)
            if isinstance(plan_res, tuple):
                plan_count, occurrence_count = plan_res
            else:
                plan_count, occurrence_count = plan_res, 0
            stats['recurring_plans'] = plan_count
            stats['plan_occurrences'] = occurrence_count
            logger.info(f"Generated {plan_count} recurring plans and {occurrence_count} occurrences")

            # Generate assets with valuations & cash synchronization
            asset_res = self._generate_assets(start_year, end_year, is_admin_generated, accounts)
            if isinstance(asset_res, tuple):
                asset_count, valuation_count = asset_res
            else:
                asset_count, valuation_count = asset_res, 0
            stats['assets'] = asset_count
            stats['asset_valuations'] = valuation_count
            logger.info(f"Generated {asset_count} assets with {valuation_count} valuations")

            # Commit changes so far so adjustment and reversal services can operate on persisted IDs
            db.session.commit()

            # Generate ledger reversals and adjustments (Ters Kayıt & Düzeltmeler)
            if active_ctx:
                rev_count, adj_count = self._generate_reversals_and_adjustments()
                final_tx_count = Transaction.query.filter_by(tenant_id=self.tenant_id).count()
                stats['transactions'] = final_tx_count - initial_tx_count
            else:
                rev_count, adj_count = 0, 0
                stats['transactions'] = tx_count

            stats['reversals'] = rev_count
            stats['adjustments'] = adj_count
            logger.info(f"Generated {rev_count} reversals and {adj_count} adjustments")
            logger.info(f"Total net transactions created in run: {stats['transactions']}")

            logger.info("=== Demo Data Generation Complete ===")
            return stats

        except Exception as e:
            logger.error(f"Error during demo data generation: {e}")
            logger.exception("Full exception traceback:")
            db.session.rollback()
            raise

    def _ensure_bank_accounts(self) -> Dict[str, BankAccount]:
        """Ensure sample demo bank accounts and initial statement exist for the tenant."""
        accounts = {}
        definitions = [
            ('checking', 'İş Bankası Vadesiz TL (Demo)', 'İş Bankası (Demo)', 'checking', 'TRY'),
            ('credit_card', 'Garanti BBVA Bonus (Demo)', 'Garanti BBVA (Demo)', 'credit_card', 'TRY'),
            ('investment', 'Midas Yatırım Hesabı (Demo)', 'Midas (Demo)', 'investment', 'TRY'),
            ('cash', 'Kasa / Nakit Cüzdan (Demo)', 'Nakit Kasa (Demo)', 'cash', 'TRY'),
        ]

        for key, name, inst, acct_type, cur in definitions:
            acct = BankAccount.query.filter_by(name=name, tenant_id=self.tenant_id).first()
            if not acct:
                acct = BankAccount(
                    name=name,
                    institution=inst,
                    account_type=acct_type,
                    currency=cur,
                    is_active=True,
                    created_by=self.user_id,
                    tenant_id=self.tenant_id,
                )
                db.session.add(acct)
                db.session.flush()
            accounts[key] = acct

        # Add initial statement snapshot for checking account
        checking_acct = accounts.get('checking')
        if checking_acct:
            snapshot = BankStatementSnapshot.query.filter_by(
                bank_account_id=checking_acct.id,
                tenant_id=self.tenant_id,
            ).first()
            if not snapshot:
                current_year = datetime.now().year
                snapshot = BankStatementSnapshot(
                    bank_account_id=checking_acct.id,
                    as_of=f"{current_year}-01-01",
                    balance=25000.0,
                    currency='TRY',
                    source='manual',
                    note='Demo açılış hesap ekstresi mutabakatı',
                    created_by=self.user_id,
                    tenant_id=self.tenant_id,
                )
                db.session.add(snapshot)
                db.session.flush()

        return accounts

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
        is_admin_generated: bool,
        accounts: Dict[str, BankAccount]
    ) -> int:
        """Generate transactions covering all payment types, statuses, transfers, and accounts."""
        count = 0
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        today_str = now.strftime('%Y-%m-%d')

        checking_id = accounts.get('checking').id if accounts.get('checking') else None
        credit_card_id = accounts.get('credit_card').id if accounts.get('credit_card') else None
        investment_id = accounts.get('investment').id if accounts.get('investment') else None
        cash_id = accounts.get('cash').id if accounts.get('cash') else None

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                # Monthly salary -> checking
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_salary', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=checking_id
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1

                # Monthly rent income -> checking
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_rent_income', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=checking_id
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1

                # Quarterly dividend -> investment
                if month in [3, 6, 9, 12]:
                    tx = self.transaction_factory.create_transaction_from_template(
                        'quarterly_dividend', year, month, is_admin_generated=is_admin_generated,
                        bank_account_id=investment_id
                    )
                    if tx and not self._transaction_exists(tx):
                        db.session.add(tx)
                        count += 1

                # Extra income (bi-monthly) -> cash
                if month % 2 == 0:
                    tx = self.transaction_factory.create_transaction_from_template(
                        'extra_income', year, month, is_admin_generated=is_admin_generated,
                        bank_account_id=cash_id
                    )
                    if tx and not self._transaction_exists(tx):
                        db.session.add(tx)
                        count += 1

                # Monthly rent expense -> checking
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_rent_expense', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=checking_id
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1

                # Weekly food (4 weeks per month) -> alternating credit card and cash
                for week in range(1, 5):
                    card_for_week = credit_card_id if week in (1, 3) else cash_id
                    tx = self.transaction_factory.create_transaction_from_template(
                        'weekly_food', year, month, week=week, is_admin_generated=is_admin_generated,
                        bank_account_id=card_for_week
                    )
                    if tx and not self._transaction_exists(tx):
                        db.session.add(tx)
                        count += 1

                # Credit card payment -> checking
                tx = self.transaction_factory.create_transaction_from_template(
                    'credit_card_payment', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=checking_id
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1

                # Tax payment -> checking (with one realistic overdue case)
                tx = self.transaction_factory.create_transaction_from_template(
                    'tax_payment', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=checking_id
                )
                if tx:
                    # Realistic overdue test: mark previous month tax as overdue if in current year
                    if year == current_year and month == max(1, current_month - 1) and current_month > 1:
                        tx.status = 'Gecikti'
                    if not self._transaction_exists(tx):
                        db.session.add(tx)
                        count += 1

                # Credit payment -> checking
                tx = self.transaction_factory.create_transaction_from_template(
                    'credit_payment', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=checking_id
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1

                # Transport expense -> credit card
                tx = self.transaction_factory.create_transaction_from_template(
                    'transport_expense', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=credit_card_id
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1

                # Monthly investment -> checking
                tx = self.transaction_factory.create_transaction_from_template(
                    'monthly_investment', year, month, is_admin_generated=is_admin_generated,
                    bank_account_id=checking_id
                )
                if tx and not self._transaction_exists(tx):
                    db.session.add(tx)
                    count += 1

                # Monthly virman / transfer between accounts (checking -> investment)
                transfer_date = f"{year}-{month:02d}-16"
                transfer_status = 'Bekliyor' if transfer_date > today_str else 'Ödendi'
                transfer_tx = Transaction(
                    date=transfer_date,
                    category='Nakit & Mevduat',
                    description='Vadesiz Hesaptan Yatırım Hesabına Aylık Birikim Aktarımı',
                    note='Hesaplar arası otomatik virman işlemi',
                    type='Transfer',
                    status=transfer_status,
                    amount=5000.0,
                    bank_account_id=checking_id,
                    transfer_from=accounts.get('checking').name if accounts.get('checking') else 'Vadesiz TL',
                    transfer_to=accounts.get('investment').name if accounts.get('investment') else 'Yatırım Hesabı',
                    tenant_id=self.tenant_id,
                    is_admin_generated=is_admin_generated,
                )
                if not self._transaction_exists(transfer_tx):
                    db.session.add(transfer_tx)
                    count += 1

        # Add 1 soft-deleted transaction to test deleted transaction filters
        soft_del_tx = Transaction(
            date=f"{current_year}-01-22",
            category='Diğer Giderler',
            description='İptal Edilen Sipariş (Demo Soft Delete Örneği)',
            note='Kullanıcı tarafından silinmiş demo işlem kaydı',
            type='Gider',
            status='Ödendi',
            amount=1450.0,
            bank_account_id=credit_card_id,
            tenant_id=self.tenant_id,
            is_admin_generated=is_admin_generated,
            is_deleted=True,
            deleted_at=datetime.now(),
            deleted_by=self.user_id,
        )
        if not self._transaction_exists(soft_del_tx):
            db.session.add(soft_del_tx)
            count += 1

        return count

    def _generate_recurring_plans(
        self,
        start_year: int,
        end_year: int,
        is_admin_generated: bool
    ) -> Tuple[int, int]:
        """Generate recurring plans and their timeline occurrences."""
        plan_count = 0
        occurrence_count = 0
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        today_date = date.today()

        templates = [
            'salary_plan',
            'rent_income_plan',
            'rent_expense_plan',
            'credit_plan',
            'credit_card_plan',
            'investment_plan'
        ]

        created_plans = []
        for year in range(start_year, end_year + 1):
            for template_name in templates:
                plan = self.recurring_plan_factory.create_recurring_plan_from_template(
                    template_name, year, is_admin_generated=is_admin_generated
                )
                if plan and not self._recurring_plan_exists(plan):
                    db.session.add(plan)
                    db.session.flush()
                    created_plans.append(plan)
                    plan_count += 1

        plans_to_schedule = created_plans or RecurringPlan.query.filter_by(tenant_id=self.tenant_id).all()

        # Generate occurrences across the 3-year timeline for newly created plans
        for plan in plans_to_schedule:
            payment_day = plan.payment_day or 15
            for occ_year in range(start_year, end_year + 1):
                for occ_month in range(1, 13):
                    occ_day = min(payment_day, 28)
                    occ_date = date(occ_year, occ_month, occ_day)
                    occ_date_str = occ_date.strftime('%Y-%m-%d')

                    # Determine status: skipped (selective test), paid (past), scheduled (future)
                    if occ_year == current_year and occ_month == current_month and plans_to_schedule and plan == plans_to_schedule[0]:
                        # One skipped occurrence in current period to test skipped state
                        occ_status = OccurrenceStatus.SKIPPED.value
                        paid_at = None
                        note = "Demo atlanan periyot simülasyonu"
                    elif occ_date < today_date:
                        occ_status = OccurrenceStatus.PAID.value
                        paid_at = datetime(occ_year, occ_month, occ_day, 9, 30)
                        note = "Demo tamamlanmış plan ödemesi"
                    else:
                        occ_status = OccurrenceStatus.SCHEDULED.value
                        paid_at = None
                        note = "Demo planlanan yaklaşan ödeme"

                    # Check existence
                    existing_occ = PlanOccurrence.query.filter_by(
                        plan_id=plan.id,
                        scheduled_date=occ_date_str,
                        tenant_id=self.tenant_id,
                    ).first()
                    if not existing_occ:
                        occurrence = PlanOccurrence(
                            plan_id=plan.id,
                            occurrence_number=(occ_year - start_year) * 12 + occ_month,
                            scheduled_date=occ_date_str,
                            status=occ_status,
                            amount=plan.amount,
                            paid_at=paid_at,
                            notes=note,
                            tenant_id=self.tenant_id,
                        )
                        db.session.add(occurrence)
                        occurrence_count += 1

        return plan_count, occurrence_count

    def _generate_assets(
        self,
        start_year: int,
        end_year: int,
        is_admin_generated: bool,
        accounts: Dict[str, BankAccount]
    ) -> Tuple[int, int]:
        """Generate assets, valuations, ledger synchronization, and completed sales."""
        asset_count = 0
        valuation_count = 0

        # Asset samples with diverse sectors and one to be sold/closed
        asset_samples = [
            ('stock', 'Türk Hava Yolları', 'THYAO', 'Havacılık & Ulaşım'),
            ('stock', 'Garanti BBVA', 'GARAN', 'Bankacılık'),
            ('gold', 'Gram Altın', 'XAU', 'Emtia & Hammadde'),
            ('forex', 'Döviz Rezervi', 'USD', 'Finansal Sistem'),
            ('fund', 'BIST 100 Fonu', 'BIST100', 'Fon & Portföy'),
            ('fund', 'Para Piyasası Fonu', 'PPF', 'Fon & Portföy'),  # Position to be sold & closed
        ]

        investment_acct_id = accounts.get('investment').id if accounts.get('investment') else None
        created_assets = {}

        for template_name, name, symbol, sector_name in asset_samples:
            # Check if asset already exists for this tenant
            existing_asset = Asset.query.filter_by(name=name, tenant_id=self.tenant_id).first()
            if existing_asset:
                created_assets[name] = existing_asset
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
                asset.tenant_id = self.tenant_id
                db.session.add(asset)
                db.session.flush()
                asset_count += 1
                created_assets[name] = asset

                category_mapping = {
                    'stock': 'Hisse Senedi',
                    'gold': 'Altın Alımı',
                    'fund': 'Fon',
                    'forex': 'Nakit & Mevduat',
                }
                asset_cat = category_mapping.get(template_name, 'Diğer Yatırımlar')

                # Synchronize with cash ledger: create initial purchase transaction
                purchase_tx = Transaction(
                    date=purchase_date,
                    category=asset_cat,
                    description=f"Varlık Portföy Alımı — {asset.name} ({asset.symbol})",
                    note="Demo varlık alım işlemi nakit çıkışı",
                    type='Yatırım',
                    status='Ödendi',
                    amount=float(asset.purchase_cost),
                    source_type='asset',
                    source_id=asset.id,
                    bank_account_id=investment_acct_id,
                    tenant_id=self.tenant_id,
                    is_admin_generated=is_admin_generated,
                )
                if not self._transaction_exists(purchase_tx):
                    db.session.add(purchase_tx)

                # Create valuations (quarterly)
                valuations = self._generate_asset_valuations(
                    asset.id, start_year, purchase_date, is_admin_generated
                )
                valuation_count += valuations

        # Execute a full sale & closure on 'Para Piyasası Fonu' to test closed asset flows
        ppf_asset = created_assets.get('Para Piyasası Fonu')
        if ppf_asset and not ppf_asset.is_closed:
            sale_date = f"{datetime.now().year}-02-25"
            try:
                sale_qty = to_decimal(ppf_asset.quantity)
                sale_price = to_decimal(ppf_asset.unit_price) * to_decimal('1.25')
                sell_asset_position(
                    asset_id=ppf_asset.id,
                    quantity=sale_qty,
                    sale_unit_price=sale_price,
                    sale_date=sale_date,
                    note="Demo varlık tam satış ve pozisyon kapatma testi",
                    user_id=self.user_id,
                    tenant_id=self.tenant_id,
                )
                logger.info(f"Successfully sold and closed demo asset {ppf_asset.name}")
            except Exception as e:
                logger.warning(f"Demo asset sale execution fallback: {e}")

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

            asset = db.session.get(Asset, asset_id)
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
                notes="Demo periyodik değerleme güncellemesi",
                updated_at=valuation_date
            )

            db.session.add(AssetUpdate(**valuation_data))
            count += 1

        # Update final asset value
        asset = db.session.get(Asset, asset_id)
        if asset:
            asset.value = float(asset.purchase_cost) * growth_steps[-1]
            asset.unit_price = float(asset.unit_price) * growth_steps[-1]
            asset.last_updated = datetime.now().strftime('%Y-%m-%d')

        return count

    def _generate_reversals_and_adjustments(self) -> Tuple[int, int]:
        """Generate demo ledger reversal and adjustment compensating records."""
        reversal_count = 0
        adjustment_count = 0

        # Prevent duplicate adjustments/reversals on repeat runs
        existing_adj_count = LedgerAdjustment.query.filter_by(tenant_id=self.tenant_id).count()
        if existing_adj_count >= 2:
            return 0, 0

        # Find a suitable paid transaction to reverse (Ters Kayıt)
        rev_candidate = Transaction.query.filter(
            Transaction.tenant_id == self.tenant_id,
            Transaction.status == 'Ödendi',
            Transaction.is_deleted.is_(False),
            Transaction.source_type.is_(None),
            Transaction.type.in_(['Gider', 'Gelir']),
        ).order_by(Transaction.id.desc()).first()

        if rev_candidate:
            existing_adj = LedgerAdjustment.query.filter_by(
                original_transaction_id=rev_candidate.id,
                tenant_id=self.tenant_id,
            ).first()
            if not existing_adj:
                try:
                    create_reversal_transaction(
                        original_tx_id=rev_candidate.id,
                        reason="Demo ters kayıt testi — mükerrer kayıt iptali",
                        tenant_id=self.tenant_id,
                    )
                    reversal_count += 1
                except Exception as e:
                    logger.warning(f"Reversal demo generation failed: {e}")

        # Find another paid transaction to adjust (Düzeltme)
        adj_candidate = Transaction.query.filter(
            Transaction.tenant_id == self.tenant_id,
            Transaction.status == 'Ödendi',
            Transaction.is_deleted.is_(False),
            Transaction.source_type.is_(None),
            Transaction.type.in_(['Gider', 'Gelir']),
            Transaction.id != (rev_candidate.id if rev_candidate else -1),
        ).order_by(Transaction.id.asc()).first()

        if adj_candidate:
            existing_adj = LedgerAdjustment.query.filter_by(
                original_transaction_id=adj_candidate.id,
                tenant_id=self.tenant_id,
            ).first()
            if not existing_adj:
                try:
                    delta = -150.0 if float(adj_candidate.amount) > 150 else -10.0
                    create_adjustment_transaction(
                        original_tx_id=adj_candidate.id,
                        amount_delta=delta,
                        reason="Demo düzeltme testi — kısmi indirim / iade düzeltmesi",
                        tenant_id=self.tenant_id,
                    )
                    adjustment_count += 1
                except Exception as e:
                    logger.warning(f"Adjustment demo generation failed: {e}")

        return reversal_count, adjustment_count

    def _transaction_exists(self, transaction) -> bool:
        """Check if transaction already exists for this tenant."""
        return Transaction.query.filter_by(
            date=transaction.date,
            category=transaction.category,
            description=transaction.description,
            type=transaction.type,
            tenant_id=self.tenant_id,
        ).first() is not None

    def _recurring_plan_exists(self, plan) -> bool:
        """Check if recurring plan already exists for this tenant."""
        return RecurringPlan.query.filter_by(
            name=plan.name,
            tenant_id=self.tenant_id,
        ).first() is not None


def generate_advanced_demo_data(
    user_id: Optional[str] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
) -> Dict[str, int]:
    """
    Generate comprehensive demo data using the orchestrator.

    This is the main entry point for demo data generation from the settings page.

    Args:
        user_id: User ID for tenant-scoped data generation
        start_year: Start year for data generation (default: dynamic current_year - 1)
        end_year: End year for data generation (default: dynamic current_year + 1)

    Returns:
        Dictionary with generation statistics
    """
    tenant_id = None
    if user_id:
        user = db.session.get(User, user_id)
        if user:
            tenant_id = user.tenant_id

    orchestrator = DemoDataOrchestrator(tenant_id=tenant_id, user_id=user_id)
    stats = orchestrator.generate_comprehensive_demo_data(
        start_year=start_year,
        end_year=end_year,
        is_admin_generated=True
    )

    return stats
