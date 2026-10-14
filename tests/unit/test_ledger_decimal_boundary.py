from decimal import Decimal

from domain.ledger.services.ledger_service import LedgerService


def test_calculate_hash_canonicalizes_equivalent_money_values():
    decimal_hash = LedgerService.calculate_hash("2026-08-15", "test", Decimal("0.30"), Decimal("0.30"), "prev")
    float_hash = LedgerService.calculate_hash("2026-08-15", "test", 0.1 + 0.2, 0.3, "prev")
    assert float_hash == decimal_hash
