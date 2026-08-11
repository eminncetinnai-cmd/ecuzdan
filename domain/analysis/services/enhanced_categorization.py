"""
Enhanced Categorization Service
===============================
Detailed financial transaction categorization for accurate reporting
Phase 4: Enhanced cash flow categorization (debt, tax, commission, dividend, etc.)
"""

import logging
from typing import Dict, List

from models import Category, Transaction, db

logger = logging.getLogger(__name__)


class EnhancedCategorization:
    """Enhanced financial transaction categorization system"""

    # Standard category types (Phase 4)
    CATEGORY_TYPES = {
        'Gelir': 'Income',
        'Gider': 'Expense',
        'Yatırım': 'Investment',
        'Transfer': 'Transfer',
        'Borç': 'Debt',
        'Vergi': 'Tax',
        'Komisyon': 'Commission',
        'Temettü': 'Dividend',
        'Faiz': 'Interest',
        'Kur Farkı': 'FX Gain/Loss',
        'Alacak': 'Receivable',
        'Kredi': 'Credit',
    }

    # Standard subcategories by type
    STANDARD_SUBCATEGORIES = {
        'Gelir': ['Maaş', 'Bonus', 'Kira Geliri', 'Temettü', 'Faiz', 'Diğer'],
        'Gider': ['Kira', 'Fatura', 'Gıda', 'Ulaşım', 'Eğlence', 'Sağlık', 'Eğitim', 'Diğer'],
        'Yatırım': ['Hisse', 'Fon', 'Altın', 'Döviz', ' kripto', 'Gayrimenkul', 'Diğer'],
        'Transfer': ['Hesap Arası', 'Nakit Transfer', 'Yatırım Transfer', 'Diğer'],
        'Borç': ['Kredi Kartı', 'İhtiyaç Kredisi', 'Konut Kredisi', 'Araç Kredisi', 'Diğer'],
        'Vergi': ['Gelir Vergisi', 'KDV', 'Stopaj', 'Damga Vergisi', 'Diğer'],
        'Komisyon': ['Borsa Komisyonu', 'Banka Komisyonu', 'Broker Komisyonu', 'Diğer'],
        'Temettü': ['Hisse Temettü', 'Fon Temettü', 'ETF Temettü', 'Diğer'],
        'Faiz': ['Mevduat Faizi', 'Tahvil Faizi', 'Kredi Faizi', 'Diğer'],
        'Kur Farkı': ['Döviz Alış', 'Döviz Satış', 'Varlık Kur Farkı', 'Diğer'],
        'Alacak': ['Müşteri Alacağı', 'Borç Alacağı', 'Diğer'],
        'Kredi': ['Verilen Kredi', 'Kredi Kartı Borçlanma', 'Diğer'],
    }

    @staticmethod
    def create_standard_categories(tenant_id: str = None) -> List[Category]:
        """
        Create standard system categories

        Args:
            tenant_id: If provided, creates tenant-specific categories
                      If None, creates global system categories

        Returns:
            List of created categories
        """
        created_categories = []

        for category_type, subcategories in EnhancedCategorization.STANDARD_SUBCATEGORIES.items():
            for subcategory in subcategories:
                # Check if category already exists
                existing = Category.query.filter_by(
                    name=subcategory,
                    type=category_type,
                    subcategory=subcategory,
                    tenant_id=tenant_id
                ).first()

                if not existing:
                    category = Category(
                        name=subcategory,
                        type=category_type,
                        subcategory=subcategory,
                        tenant_id=tenant_id
                    )
                    db.session.add(category)
                    created_categories.append(category)

        db.session.commit()
        logger.info(f"Created {len(created_categories)} standard categories for tenant: {tenant_id or 'global'}")

        return created_categories

    @staticmethod
    def get_category_hierarchy(tenant_id: str = None) -> Dict:
        """
        Get category hierarchy organized by type and subcategory

        Args:
            tenant_id: Filter by tenant

        Returns:
            Dict with category hierarchy
        """
        query = Category.query
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        categories = query.all()

        hierarchy = {}

        for category in categories:
            category_type = category.type
            if category_type not in hierarchy:
                hierarchy[category_type] = {
                    'name': EnhancedCategorization.CATEGORY_TYPES.get(category_type, category_type),
                    'subcategories': []
                }

            hierarchy[category_type]['subcategories'].append({
                'id': category.id,
                'name': category.name,
                'subcategory': category.subcategory,
                'is_global': category.tenant_id is None
            })

        return hierarchy

    @staticmethod
    def categorize_transaction(
        transaction: Transaction,
        category_type: str,
        subcategory: str = None,
        auto_create: bool = True
    ) -> Category:
        """
        Categorize a transaction with enhanced category system

        Args:
            transaction: Transaction instance
            category_type: Main category type
            subcategory: Subcategory name
            auto_create: Auto-create category if not exists

        Returns:
            Category instance
        """
        # Find existing category
        category = Category.query.filter_by(
            type=category_type,
            subcategory=subcategory,
            tenant_id=transaction.tenant_id
        ).first()

        if not category and auto_create:
            # Try global category
            category = Category.query.filter_by(
                type=category_type,
                subcategory=subcategory,
                tenant_id=None
            ).first()

        if not category and auto_create:
            # Create new category
            category = Category(
                name=subcategory or category_type,
                type=category_type,
                subcategory=subcategory,
                tenant_id=transaction.tenant_id
            )
            db.session.add(category)
            db.session.commit()
            logger.info(f"Auto-created category: {category_type} - {subcategory}")

        if category:
            transaction.category = category.name
            transaction.type = category_type
            db.session.commit()

        return category

    @staticmethod
    def get_category_statistics(tenant_id: str = None, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get statistics by category type and subcategory

        Args:
            tenant_id: Filter by tenant
            start_date: Start date
            end_date: End date

        Returns:
            Dict with category statistics
        """
        query = Transaction.query.filter_by(is_deleted=False)

        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)
        if start_date:
            query = query.filter(Transaction.date >= start_date)
        if end_date:
            query = query.filter(Transaction.date <= end_date)

        transactions = query.all()

        statistics = {}

        for tx in transactions:
            category_type = tx.type
            if category_type not in statistics:
                statistics[category_type] = {
                    'total_amount': 0,
                    'count': 0,
                    'subcategories': {}
                }

            statistics[category_type]['total_amount'] += tx.amount
            statistics[category_type]['count'] += 1

            subcategory = tx.category
            if subcategory not in statistics[category_type]['subcategories']:
                statistics[category_type]['subcategories'][subcategory] = {
                    'total_amount': 0,
                    'count': 0
                }

            statistics[category_type]['subcategories'][subcategory]['total_amount'] += tx.amount
            statistics[category_type]['subcategories'][subcategory]['count'] += 1

        return statistics

    @staticmethod
    def detect_category_type(transaction: Transaction) -> str:
        """
        Auto-detect category type based on transaction attributes

        Args:
            transaction: Transaction instance

        Returns:
            Detected category type
        """
        # Check transfer
        if transaction.type == 'Transfer':
            return 'Transfer'

        # Check investment-related
        if transaction.source_type in ['asset', 'asset_sale']:
            if transaction.type == 'Gelir':
                return 'Temettü'  # Dividend from asset sale
            return 'Yatırım'

        # Check description keywords
        description = transaction.description.lower() if transaction.description else ''
        note = transaction.note.lower() if transaction.note else ''
        combined = description + ' ' + note

        if any(keyword in combined for keyword in ['temettü', 'dividend', 'kâr payı']):
            return 'Temettü'
        elif any(keyword in combined for keyword in ['faiz', 'interest', 'getiri']):
            return 'Faiz'
        elif any(keyword in combined for keyword in ['komisyon', 'commission', 'borsa ücret']):
            return 'Komisyon'
        elif any(keyword in combined for keyword in ['vergi', 'tax', 'stopaj', 'kdv']):
            return 'Vergi'
        elif any(keyword in combined for keyword in ['kur', 'döviz', 'fx', 'exchange']):
            return 'Kur Farkı'
        elif any(keyword in combined for keyword in ['borç', 'kredi', 'loan', 'debt']):
            return 'Borç'
        elif any(keyword in combined for keyword in ['alacak', 'receivable']):
            return 'Alacak'

        # Default to existing type
        return transaction.type

    @staticmethod
    def reclassify_transactions(tenant_id: str = None, dry_run: bool = True) -> Dict:
        """
        Reclassify transactions using enhanced categorization

        Args:
            tenant_id: Filter by tenant
            dry_run: If True, only report changes without applying

        Returns:
            Dict with reclassification results
        """
        query = Transaction.query.filter_by(is_deleted=False)
        if tenant_id:
            query = query.filter_by(tenant_id=tenant_id)

        transactions = query.all()

        reclassifications = []

        for tx in transactions:
            detected_type = EnhancedCategorization.detect_category_type(tx)

            if detected_type != tx.type:
                reclassifications.append({
                    'transaction_id': tx.id,
                    'date': tx.date,
                    'amount': tx.amount,
                    'old_type': tx.type,
                    'new_type': detected_type,
                    'description': tx.description
                })

                if not dry_run:
                    tx.type = detected_type
                    # Auto-categorize
                    EnhancedCategorization.categorize_transaction(
                        tx,
                        detected_type,
                        detected_type  # Use type as subcategory for simplicity
                    )

        if not dry_run:
            db.session.commit()
            logger.info(f"Reclassified {len(reclassifications)} transactions")

        return {
            'total_transactions': len(transactions),
            'reclassifications': len(reclassifications),
            'changes': reclassifications,
            'dry_run': dry_run
        }
