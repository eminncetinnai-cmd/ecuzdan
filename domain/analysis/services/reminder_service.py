"""Domain service for calculating reminder deadlines, statuses, and validation.

Strictly follows domain purity: no Flask, routes, or database imports.
"""

from __future__ import annotations

import calendar
from datetime import date, datetime
from typing import Any


class ReminderService:
    """Pure domain service for user reminders calculation and formatting."""

    VALID_FREQUENCIES = ('Aylık', 'Yıllık', 'Tek Seferlik')
    VALID_CATEGORIES = ('Ödeme', 'Doğum Günü', 'Fatura', 'Sigorta / Vergi', 'Genel')

    @classmethod
    def calculate_due_status(
        cls,
        frequency: str,
        due_day: int | None = None,
        due_month: int | None = None,
        due_date: str | None = None,
        is_completed: bool = False,
        reference_date: date | None = None,
    ) -> dict[str, Any]:
        """Calculates days remaining, next target date, badge text, color, and urgency."""
        today = reference_date or date.today()

        if is_completed:
            return {
                'days_remaining': 999,
                'target_date': None,
                'badge_text': 'Tamamlandı ✓',
                'badge_color': 'emerald',
                'is_urgent': False,
            }

        days_remaining = None
        target_date = None

        if frequency == 'Tek Seferlik':
            if due_date:
                try:
                    target_date = datetime.strptime(due_date, "%Y-%m-%d").date()
                    days_remaining = (target_date - today).days
                except (ValueError, TypeError):
                    days_remaining = None
        elif frequency == 'Aylık':
            day = max(1, min(due_day or 1, 31))
            # Current month target
            max_day_this_month = calendar.monthrange(today.year, today.month)[1]
            actual_day = min(day, max_day_this_month)
            this_month_target = date(today.year, today.month, actual_day)

            if this_month_target >= today:
                target_date = this_month_target
                days_remaining = (this_month_target - today).days
            else:
                # Next month target
                next_month = today.month + 1 if today.month < 12 else 1
                next_year = today.year if today.month < 12 else today.year + 1
                max_day_next_month = calendar.monthrange(next_year, next_month)[1]
                target_date = date(next_year, next_month, min(day, max_day_next_month))
                days_remaining = (target_date - today).days
        elif frequency == 'Yıllık':
            day = max(1, min(due_day or 1, 31))
            month = max(1, min(due_month or today.month, 12))

            max_day_this_year = calendar.monthrange(today.year, month)[1]
            this_year_target = date(today.year, month, min(day, max_day_this_year))

            if this_year_target >= today:
                target_date = this_year_target
                days_remaining = (this_year_target - today).days
            else:
                max_day_next_year = calendar.monthrange(today.year + 1, month)[1]
                target_date = date(today.year + 1, month, min(day, max_day_next_year))
                days_remaining = (target_date - today).days

        if days_remaining is None:
            return {
                'days_remaining': 0,
                'target_date': None,
                'badge_text': 'Tarih Belirtilmedi',
                'badge_color': 'slate',
                'is_urgent': False,
            }

        if days_remaining < 0:
            return {
                'days_remaining': days_remaining,
                'target_date': target_date,
                'badge_text': f"{abs(days_remaining)} gün gecikti!",
                'badge_color': 'rose',
                'is_urgent': True,
            }
        elif days_remaining == 0:
            return {
                'days_remaining': 0,
                'target_date': target_date,
                'badge_text': 'Bugün!',
                'badge_color': 'rose',
                'is_urgent': True,
            }
        elif days_remaining == 1:
            return {
                'days_remaining': 1,
                'target_date': target_date,
                'badge_text': 'Yarın',
                'badge_color': 'amber',
                'is_urgent': True,
            }
        elif days_remaining <= 7:
            return {
                'days_remaining': days_remaining,
                'target_date': target_date,
                'badge_text': f"{days_remaining} gün kaldı",
                'badge_color': 'indigo',
                'is_urgent': False,
            }
        elif days_remaining <= 30:
            return {
                'days_remaining': days_remaining,
                'target_date': target_date,
                'badge_text': f"{days_remaining} gün kaldı",
                'badge_color': 'sky',
                'is_urgent': False,
            }
        else:
            return {
                'days_remaining': days_remaining,
                'target_date': target_date,
                'badge_text': f"{days_remaining} gün kaldı",
                'badge_color': 'slate',
                'is_urgent': False,
            }

    @classmethod
    def validate_reminder(
        cls,
        title: str | None,
        frequency: str | None,
        due_day: int | None = None,
        due_month: int | None = None,
        due_date: str | None = None,
    ) -> tuple[bool, str | None]:
        """Validates reminder form fields."""
        if not title or not title.strip():
            return False, "Hatırlatıcı başlığı zorunludur."

        if frequency not in cls.VALID_FREQUENCIES:
            return False, f"Geçersiz sıklık: {frequency}. Seçenekler: {', '.join(cls.VALID_FREQUENCIES)}"

        if frequency == 'Aylık':
            if due_day is None or not (1 <= due_day <= 31):
                return False, "Aylık hatırlatıcı için 1-31 arasında bir ödeme/hatırlatma günü seçilmelidir."
        elif frequency == 'Yıllık':
            if due_day is None or not (1 <= due_day <= 31):
                return False, "Yıllık hatırlatıcı için 1-31 arasında bir gün seçilmelidir."
            if due_month is None or not (1 <= due_month <= 12):
                return False, "Yıllık hatırlatıcı için 1-12 arasında bir ay seçilmelidir."
        elif frequency == 'Tek Seferlik':
            if not due_date or not due_date.strip():
                return False, "Tek seferlik hatırlatıcı için bir tarih seçilmelidir."
            try:
                datetime.strptime(due_date.strip(), "%Y-%m-%d")
            except ValueError:
                return False, "Geçersiz tarih formatı. YYYY-MM-DD bekleniyor."

        return True, None
