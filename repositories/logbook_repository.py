"""Repository for logbook entries and related dropdown data."""

from models import Asset, LogbookEntry, Transaction

from .base import BaseRepository


class LogbookRepository(BaseRepository):
    def query_entries(self, tenant_id, filters=None):
        filters = filters or {}
        query = LogbookEntry.query.filter_by(tenant_id=tenant_id)
        if filters.get('category'):
            query = query.filter_by(category=filters['category'])
        if filters.get('sentiment'):
            query = query.filter_by(sentiment=filters['sentiment'])
        if filters.get('date_from'):
            query = query.filter(LogbookEntry.entry_date >= filters['date_from'])
        if filters.get('date_to'):
            query = query.filter(LogbookEntry.entry_date <= filters['date_to'])
        return query

    def list_entries(self, tenant_id, filters=None, ascending=False):
        order = LogbookEntry.entry_date.asc() if ascending else LogbookEntry.entry_date.desc()
        return self.query_entries(tenant_id, filters).order_by(order).all()

    def paginate_entries(self, tenant_id, filters=None, page=1, per_page=20):
        return self.query_entries(tenant_id, filters).order_by(LogbookEntry.entry_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

    def get_entry(self, entry_id, tenant_id):
        return LogbookEntry.query.filter_by(id=entry_id, tenant_id=tenant_id).first()

    def find_recent_duplicate(self, tenant_id, user_id, title, content, seconds=5):
        """Find an existing entry created within the last N seconds to prevent double-submit."""
        from datetime import datetime, timezone, timedelta
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=seconds)
        return (
            LogbookEntry.query.filter_by(tenant_id=tenant_id, user_id=user_id, title=title)
            .filter(LogbookEntry.content == content)
            .filter(LogbookEntry.created_at >= cutoff)
            .order_by(LogbookEntry.id.desc())
            .first()
        )

    def add_entry(self, **fields):
        return self.add(LogbookEntry(**fields))

    def get_asset(self, asset_id, tenant_id):
        return Asset.query.filter_by(id=asset_id, tenant_id=tenant_id).first()

    def get_transaction(self, transaction_id, tenant_id):
        return Transaction.query.filter_by(id=transaction_id, tenant_id=tenant_id).first()

    def list_assets(self, tenant_id):
        return Asset.query.filter_by(tenant_id=tenant_id).order_by(Asset.name).all()

    def list_transactions(self, tenant_id, limit=100):
        return Transaction.query.filter_by(tenant_id=tenant_id).order_by(Transaction.date.desc()).limit(limit).all()

