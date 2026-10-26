"""Deterministic occurrence generation for canonical plans."""

from __future__ import annotations

import calendar
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from domain.planning.models.plan_contracts import CanonicalPlan, PlanOccurrence


class OccurrenceCalculator:
    """Generate expected plan periods without backfilling before the anchor."""

    MAX_OCCURRENCES = 360

    @classmethod
    def generate(
        cls,
        plan: CanonicalPlan,
        *,
        count: int | None = None,
        anchor_today: bool = False,
        today: date | None = None,
        until_date: date | None = None,
        horizon_months: int = 3,
    ) -> list[PlanOccurrence]:
        ref_today = today or date.today()
        is_indefinite = plan.occurrence_limit is None and count is None and plan.end_date is None

        if count is not None:
            if count <= 0:
                return []
            target_count = min(count, cls.MAX_OCCURRENCES)
        elif plan.occurrence_limit is not None:
            if plan.occurrence_limit <= 0:
                return []
            target_count = min(plan.occurrence_limit, cls.MAX_OCCURRENCES)
        else:
            target_count = cls.MAX_OCCURRENCES

        anchor = plan.start_date or ref_today
        if anchor_today:
            anchor = max(anchor, ref_today)
        current = cls._first_occurrence(plan, anchor)
        occurrences: list[PlanOccurrence] = []

        if is_indefinite:
            default_horizon = ref_today + relativedelta(months=horizon_months)
            horizon = max(default_horizon, until_date) if until_date else default_horizon
        else:
            horizon = None

        index = 0
        is_finite = plan.occurrence_limit is not None and plan.occurrence_limit > 0 and not is_indefinite
        while index < target_count:
            if is_indefinite and index >= 3 and current > horizon:
                break
            if plan.end_date and current > plan.end_date and not is_finite:
                break
            occurrences.append(
                PlanOccurrence(
                    plan_id=plan.id,
                    occurrence_number=index + 1,
                    scheduled_date=current,
                )
            )
            current = cls._next_occurrence(plan, current)
            index += 1
        return occurrences

    @classmethod
    def _first_occurrence(cls, plan: CanonicalPlan, anchor: date) -> date:
        if plan.frequency == "Haftalık":
            return anchor

        candidate = anchor.replace(day=cls._payment_day(plan, anchor.year, anchor.month))
        if candidate < anchor:
            candidate = cls._add_interval(plan, anchor)
            candidate = candidate.replace(day=cls._payment_day(plan, candidate.year, candidate.month))
        return candidate

    @classmethod
    def _next_occurrence(cls, plan: CanonicalPlan, current: date) -> date:
        candidate = cls._add_interval(plan, current)
        if plan.frequency != "Haftalık":
            candidate = candidate.replace(day=cls._payment_day(plan, candidate.year, candidate.month))
        return candidate

    @staticmethod
    def _payment_day(plan: CanonicalPlan, year: int, month: int) -> int:
        return min(max(plan.payment_day, 1), calendar.monthrange(year, month)[1])

    @staticmethod
    def _add_interval(plan: CanonicalPlan, current: date) -> date:
        if plan.frequency == "Haftalık":
            return current + timedelta(days=7)
        if plan.frequency == "3-Aylık":
            return current + relativedelta(months=3)
        if plan.frequency == "Yıllık":
            return current + relativedelta(months=12)
        return current + relativedelta(months=1)


class OccurrenceLifecycleService:
    """Application-facing occurrence lifecycle facade.

    The calculator remains pure and deterministic; persistence and tenant
    enforcement stay behind ``OccurrenceRepository``. This split keeps schedule
    generation testable and prevents route code from mutating ORM rows directly.
    """

    def __init__(self, repository=None):
        if repository is None:
            from domain.planning.services.occurrence_repository import OccurrenceRepository

            repository = OccurrenceRepository()
        self.repository = repository

    def sync_plan(self, plan, tenant_id=None, count=None, until_date=None, horizon_months=3):
        return self.repository.get_or_create_occurrences(
            plan, tenant_id, count=count, until_date=until_date, horizon_months=horizon_months
        )

    def mark_paid(self, occurrence_id, transaction_id, tenant_id=None):
        return self.repository.mark_paid(occurrence_id, transaction_id, tenant_id)

    def mark_skipped(self, occurrence_id, tenant_id=None, reason=None):
        return self.repository.mark_skipped(occurrence_id, tenant_id, reason=reason)

    def mark_cancelled(self, occurrence_id, tenant_id=None, reason=None):
        return self.repository.mark_cancelled(occurrence_id, tenant_id, reason=reason)

    def list_pending(self, plan_id, tenant_id=None):
        return self.repository.list_pending(plan_id, tenant_id)
