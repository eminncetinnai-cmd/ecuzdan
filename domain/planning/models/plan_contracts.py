"""Canonical planning contracts shared by the planning service and UI.

The persistence model still keeps the legacy ``plan_type`` and ``installments``
columns. These immutable value objects translate those columns into a smaller,
explicit domain vocabulary without changing the database schema.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any

from dateutil.relativedelta import relativedelta


class PlanFlow(str, Enum):
    INCOME = "Gelir"
    EXPENSE = "Gider"
    INVESTMENT = "Yatırım"


class PlanLifecycle(str, Enum):
    INDEFINITE = "Süresiz"
    INSTALLMENT = "Taksitli"
    END_DATED = "Bitiş Tarihli"


class PlanStatus(str, Enum):
    ACTIVE = "Aktif"
    PAUSED = "Duraklatıldı"
    COMPLETED = "Tamamlandı"
    CANCELLED = "İptal"


class OccurrenceStatus(str, Enum):
    """Stable persistence/API values for the occurrence lifecycle."""

    SCHEDULED = "scheduled"
    PAID = "paid"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class CanonicalPlan:
    """Stable domain representation of a persisted recurring plan."""

    id: int
    tenant_id: str
    name: str
    category: str
    flow: PlanFlow
    amount: Decimal
    frequency: str
    lifecycle: PlanLifecycle
    start_date: date | None
    end_date: date | None
    occurrence_limit: int | None
    payment_day: int
    status: PlanStatus
    note: str | None = None
    target_asset_id: int | None = None
    legacy_plan_type: str | None = None
    paid_occurrences_count: int | None = None
    version: int = 1

    @property
    def is_investment(self) -> bool:
        return self.flow is PlanFlow.INVESTMENT or self.legacy_plan_type == "DCA"

    @property
    def is_cashflow(self) -> bool:
        return not self.is_investment

    @property
    def is_indefinite(self) -> bool:
        return self.lifecycle is PlanLifecycle.INDEFINITE

    @property
    def is_active(self) -> bool:
        """Planın şu an aktif olup olmadığı."""
        return self.status is PlanStatus.ACTIVE

    @property
    def months_remaining(self) -> int | None:
        """Kalan ay/dönem sayısını döner.

        - Tamamlandı / İptal / Duraklatıldı → 0
        - Süresiz yaşam döngüsü (Abonelik, DCA sonsuz) → None (∞)
        - paid_occurrences_count ve occurrence_limit varsa → occurrence_limit - paid_occurrences_count (en az 0)
        - end_date varsa:
            - Haftalık → hafta farkı (en az 0)
            - Diğer → ay farkı (en az 0)
        - occurrence_limit varsa:
            - start_date varsa → geçen süreyi düşerek kalan taksit/dönem sayısını hesaplar
            - yoksa → occurrence_limit
        - Diğer → None
        """
        if self.status in (PlanStatus.COMPLETED, PlanStatus.CANCELLED, PlanStatus.PAUSED):
            return 0
        if self.lifecycle is PlanLifecycle.INDEFINITE:
            return None
        today = date.today()
        if self.paid_occurrences_count is not None and self.occurrence_limit is not None and self.occurrence_limit > 0:
            return max(0, self.occurrence_limit - self.paid_occurrences_count)
        if self.end_date is not None:
            if self.frequency == "Haftalık":
                return max(0, (self.end_date - today).days // 7)
            delta = (self.end_date.year - today.year) * 12 + (self.end_date.month - today.month)
            return max(0, delta)
        if self.occurrence_limit is not None and self.occurrence_limit > 0:
            if self.start_date is not None:
                if today < self.start_date:
                    elapsed = 0
                else:
                    elapsed_months = (today.year - self.start_date.year) * 12 + (today.month - self.start_date.month)
                    if self.frequency == "Yıllık":
                        elapsed = max(0, elapsed_months // 12)
                    elif self.frequency == "3-Aylık":
                        elapsed = max(0, elapsed_months // 3)
                    elif self.frequency == "Haftalık":
                        elapsed = max(0, (today - self.start_date).days // 7)
                    else:
                        elapsed = max(0, elapsed_months)
                return max(0, self.occurrence_limit - elapsed)
            return self.occurrence_limit
        return None

    @property
    def remaining_total_amount(self) -> Decimal | None:
        """Kalan toplam tutar/borç (kalan dönem sayısı * dönem tutarı).
        Süresiz planlar için None döner."""
        if self.months_remaining is None:
            return None
        return Decimal(self.months_remaining) * self.amount

    @property
    def is_completed(self) -> bool:
        """Planın tamamlanıp tamamlanmadığı (durum 'Tamamlandı' veya tüm taksitleri ödenmiş)."""
        if self.status is PlanStatus.COMPLETED:
            return True
        if self.occurrence_limit is not None and self.occurrence_limit > 0:
            if self.paid_occurrences_count is not None and self.paid_occurrences_count >= self.occurrence_limit:
                return True
        if self.end_date is not None:
            if date.today() >= self.end_date:
                if self.occurrence_limit is None or (self.paid_occurrences_count is not None and self.paid_occurrences_count >= self.occurrence_limit):
                    return True
        return False

    @property
    def progress_pct(self) -> int:
        """Taksitli veya vadeli planlar için tamamlanma yüzdesi (0-100)."""
        if self.is_completed:
            return 100
        if not self.occurrence_limit or self.occurrence_limit <= 0:
            return 0
        paid = self.paid_occurrences_count or 0
        return min(100, max(0, int((paid / self.occurrence_limit) * 100)))

    @property
    def estimated_end_date_display(self) -> str | None:
        """Tahmini veya kesin bitiş ayı/yılı."""
        months_tr = [
            '', 'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
            'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
        ]
        if self.end_date:
            m_name = months_tr[self.end_date.month] if 1 <= self.end_date.month <= 12 else ''
            return f"{m_name} {self.end_date.year}"
        if self.months_remaining is not None and self.months_remaining > 0:
            today = date.today()
            m = today.month + self.months_remaining
            y = today.year + (m - 1) // 12
            m = (m - 1) % 12 + 1
            m_name = months_tr[m] if 1 <= m <= 12 else ''
            return f"{m_name} {y}"
        return None

    @property
    def payment_countdown(self) -> dict[str, Any] | None:
        """Bugünün gününe göre bir sonraki ödeme gününe kalan gün bilgisi ve badge_class döner."""
        if self.status in (PlanStatus.COMPLETED, PlanStatus.CANCELLED):
            return None
        if self.is_completed:
            return None
        if self.status is PlanStatus.PAUSED:
            return {
                'label': 'Duraklatıldı',
                'tone': 'paused',
                'days': 0,
                'badge_class': 'bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400',
            }

        today = date.today()
        if self.frequency == "Haftalık":
            anchor = self.start_date or today
            if today <= anchor:
                candidate = anchor
            else:
                days_since = (today - anchor).days
                weeks = (days_since + 6) // 7
                candidate = anchor + timedelta(days=weeks * 7)
                if candidate < today:
                    candidate += timedelta(days=7)
        else:
            month_max = calendar.monthrange(today.year, today.month)[1]
            clamped_day = min(max(self.payment_day, 1), month_max)
            if today.day <= clamped_day:
                candidate = date(today.year, today.month, clamped_day)
            else:
                next_month = today.replace(day=1) + relativedelta(months=1)
                next_max = calendar.monthrange(next_month.year, next_month.month)[1]
                next_clamped = min(max(self.payment_day, 1), next_max)
                candidate = date(next_month.year, next_month.month, next_clamped)

        if self.end_date and candidate > self.end_date:
            return None

        diff = (candidate - today).days
        if diff == 0:
            return {
                'label': 'Bugün',
                'tone': 'today',
                'days': 0,
                'badge_class': 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300',
            }
        if diff == 1:
            return {
                'label': 'Yarın',
                'tone': 'warning',
                'days': 1,
                'badge_class': 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
            }
        if 2 <= diff <= 5:
            return {
                'label': f'{diff} gün kaldı',
                'tone': 'warning',
                'days': diff,
                'badge_class': 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300',
            }
        return {
            'label': f'{diff} gün sonra',
            'tone': 'normal',
            'days': diff,
            'badge_class': 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
        }

    @classmethod
    def from_model(cls, model: Any, flow_hint: str | None = None) -> "CanonicalPlan":
        """Adapt the current ``RecurringPlan`` model without changing storage."""
        plan_type = _as_string(getattr(model, "plan_type", ""), "")
        installments = _as_int(getattr(model, "installments", 0), 0)
        flow_value = _as_string(getattr(model, "flow_type", flow_hint or PlanFlow.EXPENSE.value), flow_hint or PlanFlow.EXPENSE.value)
        flow = PlanFlow(flow_value) if flow_value in PlanFlow._value2member_map_ else PlanFlow.EXPENSE

        start_d = _parse_date(getattr(model, "start_date", None))
        end_d = _parse_date(getattr(model, "end_date", None))
        frequency = _as_string(getattr(model, "frequency", "Aylık"), "Aylık")

        if plan_type == "Abonelik" or (plan_type == "DCA" and installments in (0, 9999)):
            lifecycle = PlanLifecycle.INDEFINITE
        elif end_d and (installments in (0, 9999) or plan_type in ("Dönemsel", "Bitiş Tarihli")):
            lifecycle = PlanLifecycle.END_DATED
        elif plan_type == "Taksit":
            lifecycle = PlanLifecycle.INSTALLMENT
        elif end_d:
            lifecycle = PlanLifecycle.END_DATED
        elif installments in (0, 9999):
            lifecycle = PlanLifecycle.INDEFINITE
        else:
            lifecycle = PlanLifecycle.INSTALLMENT

        if installments in (0, 9999) and end_d and start_d:
            occurrence_limit = _calc_installments_from_dates(start_d, end_d, frequency)
        else:
            occurrence_limit = None if installments in (0, 9999) else installments

        paid_count = _optional_int(getattr(model, "paid_occurrences_count", None))
        if paid_count is None and hasattr(model, "paid_count"):
            paid_count = _optional_int(getattr(model, "paid_count", None))
        if paid_count is None and hasattr(model, "payments"):
            payments = getattr(model, "payments", None)
            if isinstance(payments, (list, tuple)):
                paid_count = len(payments)
        if paid_count is None or paid_count == 0:
            occurrences = getattr(model, "occurrences", None)
            if occurrences and isinstance(occurrences, (list, tuple)):
                occ_paid = len([o for o in occurrences if getattr(o, "status", None) == "paid"])
                if occ_paid > (paid_count or 0):
                    paid_count = occ_paid

        return cls(
            id=_as_int(getattr(model, "id", 0), 0),
            tenant_id=_as_string(getattr(model, "tenant_id", "default"), "default"),
            name=_as_string(getattr(model, "name", "Plansız"), "Plansız"),
            category=_as_string(getattr(model, "category", "Genel"), "Genel"),
            flow=flow,
            amount=_as_decimal(getattr(model, "amount", 0)),
            frequency=frequency,
            lifecycle=lifecycle,
            start_date=start_d,
            end_date=end_d,
            occurrence_limit=occurrence_limit,
            payment_day=_as_int(getattr(model, "payment_day", 1), 1),
            status=_status_value(getattr(model, "status", PlanStatus.ACTIVE.value)),
            note=(_as_string(getattr(model, "note", ""), "").strip() or None),
            target_asset_id=_optional_int(getattr(model, "target_asset_id", None)),
            legacy_plan_type=plan_type or None,
            paid_occurrences_count=paid_count,
            version=_as_int(getattr(model, "version", 1), 1),
        )


def _calc_installments_from_dates(start_date: date, end_date: date, frequency: str = "Aylık") -> int:
    if end_date < start_date:
        return 1
    if frequency == "Haftalık":
        return max(1, (end_date - start_date).days // 7 + 1)
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    if end_date.day >= start_date.day:
        months += 1
    if frequency == "3-Aylık":
        return max(1, (months + 2) // 3)
    if frequency == "Yıllık":
        return max(1, (months + 11) // 12)
    return max(1, months)


def _as_string(value: Any, default: str) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    parsed = _as_int(value, -1)
    return parsed if parsed >= 0 else None


def _as_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except (TypeError, ValueError):
        return Decimal("0")


def _parse_date(value: Any) -> date | None:
    if value in (None, "") or not isinstance(value, (str, date, datetime)):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _status_value(value: Any) -> PlanStatus:
    value = _as_string(value, PlanStatus.ACTIVE.value)
    return PlanStatus(value) if value in PlanStatus._value2member_map_ else PlanStatus.ACTIVE


@dataclass(frozen=True, slots=True)
class PlanOccurrence:
    """A deterministic expected period generated from a canonical plan."""

    plan_id: int
    occurrence_number: int
    scheduled_date: date
    status: OccurrenceStatus = OccurrenceStatus.SCHEDULED


@dataclass(frozen=True, slots=True)
class PlanFilters:
    """User-facing filters for the unified Plans view."""

    flow: PlanFlow | None = None
    lifecycle: PlanLifecycle | None = None
    status: PlanStatus | None = None
    search: str = ""
    investment_only: bool = False

    def matches(self, plan: CanonicalPlan) -> bool:
        search = self.search.casefold().strip()
        if self.flow and plan.flow is not self.flow:
            return False
        if self.lifecycle and plan.lifecycle is not self.lifecycle:
            return False
        if self.status and plan.status is not self.status:
            return False
        if self.investment_only and not plan.is_investment:
            return False
        if search and search not in f"{plan.name} {plan.category} {plan.note or ''}".casefold():
            return False
        return True
