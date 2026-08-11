"""DTOs for financial request payloads."""

from dataclasses import dataclass
from typing import Optional
from decimal import Decimal


@dataclass(frozen=True)
class TransactionFormDTO:
    amount: Decimal
    category: str
    description: str
    status: str
    date: str
    note: str = ''


@dataclass(frozen=True)
class PlanFormDTO:
    action: str
    name: str
    category: str
    amount: Decimal
    installments: int
    payment_day: int
    note: Optional[str] = None
    plan_id: Optional[str] = None
    start_date: Optional[str] = None
    plan_type: Optional[str] = 'Taksit'
    frequency: Optional[str] = 'Aylık'
    end_date: Optional[str] = None
    target_asset_id: Optional[int] = None


@dataclass(frozen=True)
class PaymentFormDTO:
    plan_id: str
    amount: Decimal
    payment_date: str
    installment_number: int
    notes: Optional[str] = None


@dataclass(frozen=True)
class LogbookEntryDTO:
    title: str
    content: str
    entry_date: str
    category: str
    sentiment: str
    asset_id: Optional[str] = None
    transaction_id: Optional[str] = None

