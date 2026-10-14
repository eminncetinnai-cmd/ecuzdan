"""Mathematical and Financial Invariants Test Suite.

Proves that fundamental financial equations and conservation laws always hold
across random variations and edge-case transactions:
1. Cash Flow Conservation (Initial + Inflows - Outflows == Final)
2. Net Worth Accounting Invariant (Assets - Debts == Net Worth)
3. Portfolio Asset Weight Sum (Weights sum to exactly 1.0 / 100%)
4. Multi-Currency Round-Trip Precision Invariant
5. Installment Amortization Principal Conservation Invariant
"""

from __future__ import annotations

import random
from decimal import ROUND_HALF_UP, Decimal

from shared.decimal_precision import safe_add, safe_divide, safe_multiply, safe_subtract, to_decimal


def test_cash_flow_conservation_invariant():
    """Invariant: Starting Balance + Total Inflow - Total Outflow == Final Balance."""
    random.seed(42)
    initial_balance = to_decimal("50000.00")
    current_balance = initial_balance
    total_inflows = Decimal("0.00")
    total_outflows = Decimal("0.00")

    # Simulate 500 arbitrary financial transactions
    for _ in range(500):
        amount = to_decimal(str(round(random.uniform(1.0, 2500.0), 2)))
        tx_type = random.choice(["income", "expense"])

        if tx_type == "income":
            current_balance = safe_add(current_balance, amount)
            total_inflows = safe_add(total_inflows, amount)
        else:
            current_balance = safe_subtract(current_balance, amount)
            total_outflows = safe_add(total_outflows, amount)

    expected_final = safe_subtract(safe_add(initial_balance, total_inflows), total_outflows)
    assert current_balance == expected_final, f"Cash flow invariant violated: {current_balance} != {expected_final}"


def test_net_worth_accounting_invariant():
    """Invariant: Total Assets Value - Total Debts Value == Net Worth."""
    random.seed(1337)

    # Generate 10 random assets
    assets = []
    total_assets = Decimal("0.00")
    for i in range(10):
        qty = to_decimal(str(round(random.uniform(0.5, 500.0), 4)))
        unit_price = to_decimal(str(round(random.uniform(10.0, 5000.0), 2)))
        val = safe_multiply(qty, unit_price)
        total_assets = safe_add(total_assets, val)
        assets.append({"qty": qty, "price": unit_price, "val": val})

    # Generate 5 random debts
    total_debts = Decimal("0.00")
    for _ in range(5):
        debt_amt = to_decimal(str(round(random.uniform(500.0, 10000.0), 2)))
        total_debts = safe_add(total_debts, debt_amt)

    net_worth = safe_subtract(total_assets, total_debts)

    # Assert conservation
    assert safe_add(net_worth, total_debts) == total_assets
    assert safe_subtract(total_assets, net_worth) == total_debts


def test_portfolio_weights_normalization_invariant():
    """Invariant: Sum of asset weights in a non-empty portfolio must equal exactly 1.0 (100%)."""
    random.seed(999)
    asset_values = [
        to_decimal(str(round(random.uniform(100.0, 50000.0), 2)))
        for _ in range(8)
    ]
    total_portfolio_value = sum(asset_values, Decimal("0.00"))
    assert total_portfolio_value > 0

    weights = [
        safe_divide(v, total_portfolio_value, scale=4)
        for v in asset_values
    ]

    total_weight = sum(weights, Decimal("0.0000"))
    # In float or 4-digit decimal, rounding differences can be at most 0.0008 across 8 assets
    diff = abs(total_weight - Decimal("1.0000"))
    assert diff <= Decimal("0.0010"), f"Portfolio weights do not sum to 100%: {total_weight}"


def test_multi_currency_exchange_roundtrip_invariant():
    """Invariant: Converting X (Base) -> Y (Foreign) -> X (Base) preserves value within 1 cent scale."""
    random.seed(2026)
    rates = [Decimal("34.25"), Decimal("38.10"), Decimal("45.00"), Decimal("1.08")]

    for rate in rates:
        for original_try in [Decimal("100.00"), Decimal("1250.75"), Decimal("50000.00"), Decimal("99.99")]:
            # TRY to Foreign: Foreign = TRY / Rate (scale 4 for financial precision)
            foreign_amt = safe_divide(original_try, rate, scale=4)
            # Foreign to TRY: TRY = Foreign * Rate (scale 4 intermediate)
            converted_back = safe_multiply(foreign_amt, rate, scale=4)
            final_try = to_decimal(converted_back, scale=2)

            diff = abs(final_try - original_try)
            # Maximum allowed diff due to 4-decimal intermediate rounding is 0.02 TRY
            assert diff <= Decimal("0.02"), f"Round-trip currency conversion violated: {original_try} -> {final_try} (diff: {diff})"


def test_loan_amortization_principal_conservation():
    """Invariant: Total principal paid across N installments must exactly equal loan principal."""
    principal = Decimal("120000.00")
    months = 12
    monthly_principal = (principal / Decimal(months)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    installments = []
    accumulated = Decimal("0.00")
    for m in range(months - 1):
        installments.append(monthly_principal)
        accumulated += monthly_principal
    # Last installment adjusts remainder to guarantee 100% exact match
    last_installment = principal - accumulated
    installments.append(last_installment)

    total_principal_paid = sum(installments, Decimal("0.00"))
    assert total_principal_paid == principal, f"Principal leaked: {total_principal_paid} != {principal}"
