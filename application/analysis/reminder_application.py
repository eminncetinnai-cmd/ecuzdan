"""Reminder Application Service for coordinating domain validation and repository persistence."""

from __future__ import annotations

from typing import Any

from application.base import ApplicationService
from domain.analysis.services.reminder_service import ReminderService
from repositories.reminder_repository import ReminderRepository


class ReminderApplicationService(ApplicationService):
    """Application use case orchestrator for User Reminders."""

    def __init__(
        self,
        reminder_repository: ReminderRepository | None = None,
        reminder_domain_service: ReminderService | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.reminder_repository = reminder_repository or ReminderRepository()
        self.reminder_domain_service = reminder_domain_service or ReminderService()

    def list_reminders(
        self,
        tenant_id: str,
        category: str | None = None,
        search: str | None = None,
        is_completed: bool | None = None,
    ) -> list[Any]:
        """List reminder records for tenant."""
        return self.execute(
            lambda: self.reminder_repository.list_reminders(
                tenant_id, category=category, search=search, is_completed=is_completed
            )
        )

    def get_reminder(self, reminder_id: int, tenant_id: str) -> Any | None:
        """Get single reminder record."""
        return self.execute(
            lambda: self.reminder_repository.get_reminder(reminder_id, tenant_id)
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
        amount: Any | None = None,
        note: str | None = None,
        document_url: str | None = None,
    ) -> Any:
        """Validate and create a new reminder record."""
        def _action() -> Any:
            is_valid, error = self.reminder_domain_service.validate_reminder(
                title=title,
                frequency=frequency,
                due_day=due_day,
                due_month=due_month,
                due_date=due_date,
            )
            if not is_valid:
                raise ValueError(error or "Geçersiz hatırlatıcı bilgisi.")

            parsed_amount = None
            if amount is not None and str(amount).strip():
                try:
                    cleaned_amt = str(amount).replace(" ", "").replace(",", ".")
                    parsed_amount = float(cleaned_amt)
                except ValueError:
                    raise ValueError("Geçersiz tutar formatı.")

            return self.reminder_repository.create_reminder(
                tenant_id=tenant_id,
                user_id=user_id,
                title=title,
                category=category,
                frequency=frequency,
                due_day=due_day,
                due_month=due_month,
                due_date=due_date,
                amount=parsed_amount,
                note=note,
                document_url=document_url,
            )

        return self.execute(_action)

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
        amount: Any | None = None,
        note: str | None = None,
        document_url: str | None = None,
        remove_document: bool = False,
        is_completed: bool | None = None,
    ) -> Any | None:
        """Validate and update an existing reminder record."""
        def _action() -> Any:
            if title is not None or frequency is not None:
                existing = self.reminder_repository.get_reminder(reminder_id, tenant_id)
                if not existing:
                    raise ValueError("Hatırlatıcı kaydı bulunamadı.")
                check_title = title if title is not None else existing.title
                check_freq = frequency if frequency is not None else existing.frequency
                check_day = due_day if due_day is not None else existing.due_day
                check_month = due_month if due_month is not None else existing.due_month
                check_date = due_date if due_date is not None else existing.due_date

                is_valid, error = self.reminder_domain_service.validate_reminder(
                    title=check_title,
                    frequency=check_freq,
                    due_day=check_day,
                    due_month=check_month,
                    due_date=check_date,
                )
                if not is_valid:
                    raise ValueError(error or "Geçersiz hatırlatıcı bilgisi.")

            parsed_amount = None
            if amount is not None and str(amount).strip():
                try:
                    cleaned_amt = str(amount).replace(" ", "").replace(",", ".")
                    parsed_amount = float(cleaned_amt)
                except ValueError:
                    raise ValueError("Geçersiz tutar formatı.")

            return self.reminder_repository.update_reminder(
                reminder_id=reminder_id,
                tenant_id=tenant_id,
                title=title,
                category=category,
                frequency=frequency,
                due_day=due_day,
                due_month=due_month,
                due_date=due_date,
                amount=parsed_amount,
                note=note,
                document_url=document_url,
                remove_document=remove_document,
                is_completed=is_completed,
            )

        return self.execute(_action)

    def toggle_complete(self, reminder_id: int, tenant_id: str) -> Any | None:
        """Toggle is_completed for a reminder record."""
        return self.execute(
            lambda: self.reminder_repository.toggle_complete(reminder_id, tenant_id)
        )

    def delete_reminder(self, reminder_id: int, tenant_id: str) -> bool:
        """Delete reminder record."""
        return bool(
            self.execute(
                lambda: self.reminder_repository.delete_reminder(reminder_id, tenant_id)
            )
        )
