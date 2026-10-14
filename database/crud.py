"""
Database CRUD - CRUD işlemleri
Transaction, Asset, RecurringPlan ve diğer CRUD operasyonları
"""

from repositories.reporting_repository import ReportingRepository

# --- Query Functions ---

def get_monthly_balance(year, month, tenant_id=None):
    return ReportingRepository().get_monthly_balance(year, month, tenant_id=tenant_id)


def get_actual_cash(tenant_id=None):
    return ReportingRepository().get_actual_cash(tenant_id=tenant_id)


def get_total_assets(tenant_id=None):
    return ReportingRepository().get_total_assets(tenant_id=tenant_id)


def get_total_debts(tenant_id=None):
    return ReportingRepository().get_total_debts(tenant_id=tenant_id)


def get_transactions_by_date_range(start_date, end_date, tenant_id=None):
    return ReportingRepository().get_transactions_by_date_range(start_date, end_date, tenant_id=tenant_id)


def get_calendar_month_data(year, month, tenant_id=None):
    return ReportingRepository().get_calendar_month_data(year, month, tenant_id=tenant_id)


def get_pending_payments(start_date, end_date, tenant_id=None):
    return ReportingRepository().get_pending_payments(start_date, end_date, tenant_id=tenant_id)

# --- Transaction CRUD ---

def add_transaction(
    date,
    category,
    description,
    type_,
    amount,
    status,
    note=None,
    source_id=None,
    source_type=None,
    installment_number=None,
    tenant_id=None,
    idempotency_key=None,
    bank_account_id=None,
):
    """
    UYARI: Bu fonksiyon çift-kayıt mantığını bypass eder, sadece sistem içi kullanım (seeding vb.) içindir. Route'lardan çağrılmamalıdır. Defter işlemleri için financial_ledger.py kullanın.
    """
    from repositories.financial_repository import FinancialRepository

    return FinancialRepository().add_transaction(
        date,
        category,
        description,
        type_,
        amount,
        status,
        note=note,
        source_id=source_id,
        source_type=source_type,
        installment_number=installment_number,
        idempotency_key=idempotency_key,
        tenant_id=tenant_id,
        bank_account_id=bank_account_id,
    )


def update_transaction(transaction_id, date, category, description, amount, status, note=None):
    """İşlem günceller"""
    from repositories.financial_repository import FinancialRepository

    return FinancialRepository().update_transaction(
        transaction_id,
        date,
        category,
        description,
        amount,
        status,
        note=note,
    )


def delete_transaction(transaction_id):
    """İşlem siler"""
    from repositories.financial_repository import FinancialRepository

    return FinancialRepository().delete_transaction(transaction_id)


# --- Asset CRUD ---

def add_asset(type_, name, value, description, purchase_date=None, purchase_cost=0.0,
               quantity=1.0, unit_price=0.0, currency='TRY', symbol=None,
               risk_level='Orta', liquidity='Likit', sector_id=None, notes=None, tenant_id=None):
    """
    UYARI: Bu fonksiyon çift-kayıt mantığını bypass eder, sadece sistem içi kullanım (seeding vb.) içindir. Route'lardan çağrılmamalıdır. Defter işlemleri için financial_ledger.py kullanın.
    """
    from repositories.portfolio_repository import PortfolioRepository
    return PortfolioRepository().add_asset(
        type_,
        name,
        value,
        description,
        purchase_date=purchase_date,
        purchase_cost=purchase_cost,
        quantity=quantity,
        unit_price=unit_price,
        currency=currency,
        symbol=symbol,
        risk_level=risk_level,
        liquidity=liquidity,
        sector_id=sector_id,
        notes=notes,
        tenant_id=tenant_id,
    )


def update_asset(asset_id, type_, name, value, description, purchase_date=None, purchase_cost=0.0,
               quantity=1.0, unit_price=0.0, currency='TRY', symbol=None,
               risk_level='Orta', liquidity='Likit', sector_id=None, notes=None):
    """Varlık günceller - profesyonel alanlarla"""
    from repositories.portfolio_repository import PortfolioRepository
    return PortfolioRepository().update_asset(
        asset_id,
        type_,
        name,
        value,
        description,
        purchase_date=purchase_date,
        purchase_cost=purchase_cost,
        quantity=quantity,
        unit_price=unit_price,
        currency=currency,
        symbol=symbol,
        risk_level=risk_level,
        liquidity=liquidity,
        sector_id=sector_id,
        notes=notes,
    )


def delete_asset(asset_id):
    """Varlık siler (defter servisi üzerinden)."""
    from repositories.portfolio_repository import PortfolioRepository
    return PortfolioRepository().delete_asset(asset_id)


def delete_with_transactions(model_class, item_id, source_type):
    """Kaydı ve bağlı işlemleri siler"""
    from models import Transaction, db

    item = db.get_or_404(model_class, item_id)
    Transaction.query.filter_by(source_id=item_id, source_type=source_type).delete()
    db.session.delete(item)
    db.session.commit()


# --- Asset Update Logging ---
def log_asset_update(asset_id, old_value, new_value, old_unit_price=None, new_unit_price=None, update_type='manual', update_source=None, notes=None, user_id=None, auto_commit=True):
    """Varlık güncelleme geçmişini kaydeder"""
    from repositories.portfolio_repository import PortfolioRepository
    return PortfolioRepository().log_asset_update(
        asset_id,
        old_value,
        new_value,
        old_unit_price=old_unit_price,
        new_unit_price=new_unit_price,
        update_type=update_type,
        update_source=update_source,
        notes=notes,
        user_id=user_id,
        auto_commit=auto_commit,
    )


def get_asset_update_history(asset_id, limit=50):
    """Varlık güncelleme geçmişini getirir"""
    from repositories.portfolio_repository import PortfolioRepository
    return PortfolioRepository().get_asset_update_history(asset_id, limit=limit)


def bulk_update_assets(asset_ids, new_unit_prices, user_id=None, notes=None):
    """Toplu varlık güncelleme — TEK commit ile"""
    from repositories.portfolio_repository import PortfolioRepository
    return PortfolioRepository().bulk_update_assets(asset_ids, new_unit_prices, user_id=user_id, notes=notes)

# --- Category CRUD ---

def update_category(category_id, new_name, new_type, tenant_id=None):
    from repositories.catalog_repository import CatalogRepository
    return CatalogRepository().update_category(category_id, new_name, new_type, tenant_id=tenant_id)

def delete_category(category_id, tenant_id=None):
    from repositories.catalog_repository import CatalogRepository
    return CatalogRepository().delete_category(category_id, tenant_id=tenant_id)


# --- Asset Type CRUD ---

def update_asset_type(asset_type_id, new_name):
    from repositories.catalog_repository import CatalogRepository
    return CatalogRepository().update_asset_type(asset_type_id, new_name)

def delete_asset_type(asset_type_id):
    from repositories.catalog_repository import CatalogRepository
    return CatalogRepository().delete_asset_type(asset_type_id)


# --- Asset Sector CRUD ---

def update_asset_sector(asset_sector_id, new_name):
    from repositories.catalog_repository import CatalogRepository
    return CatalogRepository().update_asset_sector(asset_sector_id, new_name)

def delete_asset_sector(asset_sector_id):
    from repositories.catalog_repository import CatalogRepository
    return CatalogRepository().delete_asset_sector(asset_sector_id)
