"""Repository for User Reminder storage and queries."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from models import UserReminder
from repositories.base import TenantScopedRepository


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class ReminderRepository(TenantScopedRepository):
    """Repository handling persistence for user registered reminders and events."""

    def list_reminders(
        self,
        tenant_id: str,
        category: str | None = None,
        search: str | None = None,
        is_completed: bool | None = None,
    ) -> list[UserReminder]:
        """List all reminders for a given tenant with optional filters."""
        t_id = self.require_tenant_id(tenant_id)
        query = self.query(UserReminder).filter(UserReminder.tenant_id == t_id)

        if category:
            query = query.filter(UserReminder.category == category)

        if is_completed is not None:
            query = query.filter(UserReminder.is_completed == is_completed)

        if search:
            term = f"%{search.strip()}%"
            query = query.filter(
                (UserReminder.title.ilike(term))
                | (UserReminder.category.ilike(term))
                | (UserReminder.note.ilike(term))
            )

        items = query.order_by(
            UserReminder.is_completed.asc(),
            UserReminder.created_at.desc(),
        ).all()

        # Sort active reminders by days remaining (closest first)
        def _sort_key(item: UserReminder) -> tuple[int, int]:
            completed_flag = 1 if item.is_completed else 0
            days = item.to_dict()['days_remaining']
            # Put past-due first (negative days sorted ascending), then today/future
            return (completed_flag, days)

        return sorted(items, key=_sort_key)

    def get_reminder(self, reminder_id: int, tenant_id: str) -> UserReminder | None:
        """Fetch a single reminder record by ID ensuring strict tenant isolation."""
        t_id = self.require_tenant_id(tenant_id)
        return (
            self.query(UserReminder)
            .filter(UserReminder.id == reminder_id, UserReminder.tenant_id == t_id)
            .first()
        )

    def create_reminder(
        self,
        tenant_id: str,
        user_id: int | None,
        title: str,
        category: str = "Genel",
        frequency: str = "Aylık",
        due_day: int | None = None,
        due_month: int | None = None,
        due_date: str | None = None,
        amount: Decimal | float | None = None,
        note: str | None = None,
        document_url: str | None = None,
    ) -> UserReminder:
        """Create and persist a new user reminder."""
        t_id_check = self.require_tenant_id(tenant_id)
        from datetime import timedelta
        cutoff = _utcnow() - timedelta(seconds=5)
        existing = (
            self.query(UserReminder)
            .filter(
                UserReminder.tenant_id == t_id_check,
                UserReminder.user_id == user_id,
                UserReminder.title == title.strip(),
                UserReminder.created_at >= cutoff,
            )
            .order_by(UserReminder.id.desc())
            .first()
        )
        if existing:
            return existing
        t_id = self.require_tenant_id(tenant_id)
        record = UserReminder(
            tenant_id=t_id,
            user_id=user_id,
            title=title.strip(),
            category=category or "Genel",
            frequency=frequency or "Aylık",
            due_day=due_day,
            due_month=due_month,
            due_date=due_date.strip() if due_date else None,
            amount=Decimal(str(amount)) if amount is not None else None,
            note=note.strip() if note else None,
            document_url=document_url.strip() if document_url else None,
            is_completed=False,
            created_at=_utcnow(),
            updated_at=_utcnow(),
        )
        self.session.add(record)
        self.session.flush()
        return record

    def update_reminder(
        self,
        reminder_id: int,
        tenant_id: str,
        title: str | None = None,
        category: str | None = None,
        frequency: str | None = None,
        due_day: int | None = None,
        due_month: int | None = None,
        due_date: str | None = None,
        amount: Decimal | float | None = None,
        note: str | None = None,
        document_url: str | None = None,
        remove_document: bool = False,
        is_completed: bool | None = None,
    ) -> UserReminder | None:
        """Update fields on an existing reminder record."""
        record = self.get_reminder(reminder_id, tenant_id)
        if not record:
            return None

        if title is not None:
            record.title = title.strip()
        if category is not None:
            record.category = category
        if frequency is not None:
            record.frequency = frequency
        if due_day is not None:
            record.due_day = due_day
        if due_month is not None:
            record.due_month = due_month
        if due_date is not None:
            record.due_date = due_date.strip() if due_date else None
        if amount is not None:
            record.amount = Decimal(str(amount)) if amount != "" else None
        if note is not None:
            record.note = note.strip() if note else None
        if remove_document:
            record.document_url = None
        elif document_url is not None:
            record.document_url = document_url.strip() if document_url else None
        if is_completed is not None:
            record.is_completed = bool(is_completed)
            if record.is_completed:
                record.last_completed_at = _utcnow()

        record.updated_at = _utcnow()
        self.session.flush()
        return record

    def toggle_complete(self, reminder_id: int, tenant_id: str) -> UserReminder | None:
        """Toggle is_completed flag for a reminder."""
        record = self.get_reminder(reminder_id, tenant_id)
        if not record:
            return None

        record.is_completed = not record.is_completed
        if record.is_completed:
            record.last_completed_at = _utcnow()
        record.updated_at = _utcnow()
        self.session.flush()
        return record

    def delete_reminder(self, reminder_id: int, tenant_id: str) -> bool:
        """Permanently delete a reminder record."""
        record = self.get_reminder(reminder_id, tenant_id)
        if not record:
            return False

        self.session.delete(record)
        self.session.flush()
        return True
