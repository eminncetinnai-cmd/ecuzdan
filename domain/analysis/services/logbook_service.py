"""Logbook application service."""



from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

class LogbookService:
    def __init__(self, repository=None):
        self.repository = repository

    def list_entries(self, tenant_id, filters=None):
        return self.repository.list_entries(tenant_id, filters)

    def create_entry(self, dto, tenant_id, user_id):
        # Prevent rapid duplicate submissions (e.g. repeated user clicks while waiting)
        if hasattr(self.repository, 'find_recent_duplicate'):
            existing = self.repository.find_recent_duplicate(
                tenant_id=tenant_id,
                user_id=user_id,
                title=dto.title,
                content=dto.content,
                seconds=5,
            )
            if existing:
                return existing
        asset_id, transaction_id = self._validated_relation_ids(dto, tenant_id)
        entry = self.repository.add_entry(
            tenant_id=tenant_id,
            user_id=user_id,
            title=dto.title,
            content=dto.content,
            entry_date=dto.entry_date,
            category=dto.category,
            sentiment=dto.sentiment,
            asset_id=asset_id,
            transaction_id=transaction_id,
        )
        self.repository.commit()
        return entry

    def detail_payload(self, entry_id, tenant_id):
        entry = self.repository.get_entry(entry_id, tenant_id)
        if not entry:
            return None
        data = {
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'entry_date': entry.entry_date,
            'category': entry.category,
            'sentiment': entry.sentiment,
        }
        if entry.asset:
            data['asset'] = {
                'id': entry.asset.id,
                'name': entry.asset.name,
                'symbol': entry.asset.symbol,
            }
        if entry.transaction:
            data['transaction'] = {
                'id': entry.transaction.id,
                'description': entry.transaction.description,
                'amount': entry.transaction.amount,
            }
        return data

    def update_entry(self, entry_id, dto, tenant_id):
        entry = self.repository.get_entry(entry_id, tenant_id)
        if not entry:
            raise ValueError("Kayıt bulunamadı veya yetkiniz yok.")
        asset_id, transaction_id = self._validated_relation_ids(dto, tenant_id)
        entry.title = dto.title
        entry.content = dto.content
        entry.entry_date = dto.entry_date
        entry.category = dto.category
        entry.sentiment = dto.sentiment
        entry.asset_id = asset_id
        entry.transaction_id = transaction_id
        self.repository.commit()
        return entry

    def delete_entry(self, entry_id, tenant_id):
        entry = self.repository.get_entry(entry_id, tenant_id)
        if not entry:
            raise ValueError("Kayıt bulunamadı veya yetkiniz yok.")
        self.repository.delete(entry)
        self.repository.commit()

    def entries_api_payload(self, tenant_id, filters, page=1, per_page=20):
        pagination = self.repository.paginate_entries(tenant_id, filters, page, per_page)
        return {
            'success': True,
            'entries': [self._entry_api_payload(entry) for entry in pagination.items],
            'pagination': {
                'page': pagination.page,
                'pages': pagination.pages,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
            },
        }

    def calendar_events(self, tenant_id, filters, color_resolver):
        events = []
        for entry in self.repository.list_entries(tenant_id, filters, ascending=True):
            color = color_resolver(entry.category)
            events.append({
                'id': entry.id,
                'title': f"{entry.category_emoji} {entry.title}",
                'start': entry.entry_date,
                'allDay': True,
                'backgroundColor': color,
                'borderColor': color,
                'extendedProps': {
                    'category': entry.category,
                    'sentiment': entry.sentiment,
                    'sentiment_emoji': entry.sentiment_emoji,
                    'content_preview': entry.content_preview,
                },
            })
        return events

    def assets_api_payload(self, tenant_id):
        return {
            'success': True,
            'assets': [
                {
                    'id': asset.id,
                    'name': asset.name,
                    'symbol': asset.symbol,
                    'asset_type': asset.type,
                }
                for asset in self.repository.list_assets(tenant_id)
            ],
        }

    def transactions_api_payload(self, tenant_id):
        return {
            'success': True,
            'transactions': [
                {
                    'id': tx.id,
                    'description': tx.description,
                    'amount': tx.amount,
                    'type': tx.type,
                    'date': tx.date,
                }
                for tx in self.repository.list_transactions(tenant_id)
            ],
        }

    def _validated_relation_ids(self, dto, tenant_id):
        asset_id = None
        if dto.asset_id:
            asset = self.repository.get_asset(dto.asset_id, tenant_id)
            if not asset:
                raise ValueError("Geçersiz varlık seçimi.")
            asset_id = asset.id

        transaction_id = None
        if dto.transaction_id:
            transaction = self.repository.get_transaction(dto.transaction_id, tenant_id)
            if not transaction:
                raise ValueError("Geçersiz işlem seçimi.")
            transaction_id = transaction.id
        return asset_id, transaction_id

    def _entry_api_payload(self, entry):
        data = {
            'id': entry.id,
            'title': entry.title,
            'content': entry.content,
            'content_preview': entry.content_preview,
            'entry_date': entry.entry_date,
            'category': entry.category,
            'category_emoji': entry.category_emoji,
            'sentiment': entry.sentiment,
            'sentiment_emoji': entry.sentiment_emoji,
            'created_at': entry.created_at.isoformat() if entry.created_at else None,
            'updated_at': entry.updated_at.isoformat() if entry.updated_at else None,
        }
        if entry.asset:
            data['asset'] = {
                'id': entry.asset.id,
                'name': entry.asset.name,
                'symbol': entry.asset.symbol,
            }
        if entry.transaction:
            data['transaction'] = {
                'id': entry.transaction.id,
                'description': entry.transaction.description,
                'amount': entry.transaction.amount,
            }
        return data

