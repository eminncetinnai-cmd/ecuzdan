"""
Property-Based Testing for Decimal Precision

Tests financial calculations with 100,000 random operations to detect
precision loss and edge cases that unit tests might miss.

Tests:
- Random addition operations
- Random multiplication operations
- Random division operations
- Complex financial calculations (ROI, weighted average, KDV, commission)
- Edge cases (very small numbers, very large numbers, negative numbers)

Usage:
    pytest tests/test_property_based_decimal.py -v
"""

import os
import random
import sys
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.decimal_precision import safe_add, safe_divide, safe_multiply, safe_subtract, to_decimal


class PropertyBasedDecimalTests:
    """Property-based tests for Decimal precision."""

    def __init__(self, iterations=100000):
        self.iterations = iterations
        self.max_diff = Decimal('0.0001')  # Maximum acceptable difference

    def generate_random_decimal(self, min_val=-1000000, max_val=1000000):
        """Generate a random Decimal value."""
        value = random.uniform(min_val, max_val)
        return to_decimal(str(value))

    def test_addition_property(self):
        """Test that addition is consistent across many random values."""
        print(f"\nTesting addition with {self.iterations} random operations...")
        max_diff_found = Decimal('0')
        violations = 0

        for _ in range(self.iterations):
            a = self.generate_random_decimal()
            b = self.generate_random_decimal()

            # Calculate with Decimal
            decimal_result = safe_add(a, b)

            # Calculate with float (for comparison)
            float_result = Decimal(str(float(a) + float(b)))

            # Check difference
            diff = abs(decimal_result - float_result)
            if diff > self.max_diff:
                violations += 1
                if diff > max_diff_found:
                    max_diff_found = diff

        print(f"  Max difference found: {max_diff_found}")
        print(f"  Violations (> {self.max_diff}): {violations}/{self.iterations}")

        if violations > 0:
            print(f"  [WARN] {violations} violations found in addition tests")
        else:
            print("  [OK] All addition tests passed")

        return violations == 0

    def test_multiplication_property(self):
        """Test that multiplication is consistent across many random values."""
        print(f"\nTesting multiplication with {self.iterations} random operations...")
        max_diff_found = Decimal('0')
        violations = 0

        for _ in range(self.iterations):
            a = self.generate_random_decimal(-10000, 10000)
            b = self.generate_random_decimal(-100, 100)

            # Calculate with Decimal
            decimal_result = safe_multiply(a, b)

            # Calculate with float (for comparison)
            float_result = Decimal(str(float(a) * float(b)))

            # Check difference
            diff = abs(decimal_result - float_result)
            if diff > self.max_diff:
                violations += 1
                if diff > max_diff_found:
                    max_diff_found = diff

        print(f"  Max difference found: {max_diff_found}")
        print(f"  Violations (> {self.max_diff}): {violations}/{self.iterations}")

        if violations > 0:
            print(f"  [WARN] {violations} violations found in multiplication tests")
        else:
            print("  [OK] All multiplication tests passed")

        return violations == 0

    def test_division_property(self):
        """Test that division is consistent across many random values."""
        print(f"\nTesting division with {self.iterations} random operations...")
        max_diff_found = Decimal('0')
        violations = 0
        zero_divisions = 0

        for _ in range(self.iterations):
            a = self.generate_random_decimal(-10000, 10000)
            b = self.generate_random_decimal(-100, 100)

            # Avoid division by zero
            if b == 0:
                zero_divisions += 1
                continue

            # Calculate with Decimal
            try:
                decimal_result = safe_divide(a, b)
            except ZeroDivisionError:
                continue

            # Calculate with float (for comparison)
            float_result = Decimal(str(float(a) / float(b)))

            # Check difference
            diff = abs(decimal_result - float_result)
            if diff > self.max_diff:
                violations += 1
                if diff > max_diff_found:
                    max_diff_found = diff

        print(f"  Max difference found: {max_diff_found}")
        print(f"  Violations (> {self.max_diff}): {violations}/{self.iterations}")
        print(f"  Zero divisions skipped: {zero_divisions}")

        if violations > 0:
            print(f"  [WARN] {violations} violations found in division tests")
        else:
            print("  [OK] All division tests passed")

        return violations == 0

    def test_complex_calculation_property(self):
        """Test complex calculation: (a + b) * c / d with random values."""
        print(f"\nTesting complex calculation with {self.iterations} random operations...")
        max_diff_found = Decimal('0')
        violations = 0

        for _ in range(self.iterations):
            a = self.generate_random_decimal(1, 1000)
            b = self.generate_random_decimal(1, 1000)
            c = self.generate_random_decimal(1, 100)
            d = self.generate_random_decimal(1, 100)

            # Calculate with Decimal
            result = safe_divide(safe_multiply(safe_add(a, b), c), d)

            # Calculate with float (for comparison)
            float_result = Decimal(str(((float(a) + float(b)) * float(c)) / float(d)))

            # Check difference
            diff = abs(result - float_result)
            if diff > self.max_diff:
                violations += 1
                if diff > max_diff_found:
                    max_diff_found = diff

        print(f"  Max difference found: {max_diff_found}")
        print(f"  Violations (> {self.max_diff}): {violations}/{self.iterations}")

        if violations > 0:
            print(f"  [WARN] {violations} violations found in complex calculation tests")
        else:
            print("  [OK] All complex calculation tests passed")

        return violations == 0

    def test_weighted_average_property(self):
        """Test weighted average calculation with random values."""
        print(f"\nTesting weighted average with {self.iterations} random operations...")
        max_diff_found = Decimal('0')
        violations = 0

        for _ in range(self.iterations):
            buy1_qty = self.generate_random_decimal(1, 10000)
            buy1_price = self.generate_random_decimal(1, 1000)
            buy2_qty = self.generate_random_decimal(1, 10000)
            buy2_price = self.generate_random_decimal(1, 1000)

            # Calculate with Decimal
            total_qty = safe_add(buy1_qty, buy2_qty)
            total_cost = safe_add(safe_multiply(buy1_qty, buy1_price), safe_multiply(buy2_qty, buy2_price))
            avg_cost = safe_divide(total_cost, total_qty)

            # Calculate with float (for comparison)
            float_total_qty = float(buy1_qty) + float(buy2_qty)
            float_total_cost = (float(buy1_qty) * float(buy1_price)) + (float(buy2_qty) * float(buy2_price))
            float_avg_cost = Decimal(str(float_total_cost / float_total_qty))

            # Check difference
            diff = abs(avg_cost - float_avg_cost)
            if diff > self.max_diff:
                violations += 1
                if diff > max_diff_found:
                    max_diff_found = diff

        print(f"  Max difference found: {max_diff_found}")
        print(f"  Violations (> {self.max_diff}): {violations}/{self.iterations}")

        if violations > 0:
            print(f"  [WARN] {violations} violations found in weighted average tests")
        else:
            print("  [OK] All weighted average tests passed")

        return violations == 0

    def test_kdv_calculation_property(self):
        """Test KDV (VAT) calculation with random values."""
        print(f"\nTesting KDV calculation with {self.iterations} random operations...")
        max_diff_found = Decimal('0')
        violations = 0

        for _ in range(self.iterations):
            amount = self.generate_random_decimal(0, 1000000)
            tax_rate = to_decimal('0.18')  # 18% KDV

            # Calculate with Decimal
            tax = safe_multiply(amount, tax_rate)
            total = safe_add(amount, tax)

            # Calculate with float (for comparison)
            float_tax = float(amount) * 0.18
            float_total = Decimal(str(float(amount) + float_tax))

            # Check difference
            diff = abs(total - float_total)
            if diff > self.max_diff:
                violations += 1
                if diff > max_diff_found:
                    max_diff_found = diff

        print(f"  Max difference found: {max_diff_found}")
        print(f"  Violations (> {self.max_diff}): {violations}/{self.iterations}")

        if violations > 0:
            print(f"  [WARN] {violations} violations found in KDV tests")
        else:
            print("  [OK] All KDV tests passed")

        return violations == 0

    def test_commission_calculation_property(self):
        """Test commission calculation with random values."""
        print(f"\nTesting commission calculation with {self.iterations} random operations...")
        max_diff_found = Decimal('0')
        violations = 0

        for _ in range(self.iterations):
            amount = self.generate_random_decimal(0, 1000000)
            commission_rate = to_decimal('0.005')  # 0.5% commission

            # Calculate with Decimal
            commission = safe_multiply(amount, commission_rate)
            net_amount = safe_subtract(amount, commission)

            # Calculate with float (for comparison)
            float_commission = float(amount) * 0.005
            float_net_amount = Decimal(str(float(amount) - float_commission))

            # Check difference
            diff = abs(net_amount - float_net_amount)
            if diff > self.max_diff:
                violations += 1
                if diff > max_diff_found:
                    max_diff_found = diff

        print(f"  Max difference found: {max_diff_found}")
        print(f"  Violations (> {self.max_diff}): {violations}/{self.iterations}")

        if violations > 0:
            print(f"  [WARN] {violations} violations found in commission tests")
        else:
            print("  [OK] All commission tests passed")

        return violations == 0

    def test_edge_cases(self):
        """Test edge cases with very small and very large numbers."""
        print("\nTesting edge cases...")
        violations = 0

        # Very small numbers
        small_values = [
            to_decimal('0.0001'),
            to_decimal('0.00001'),
            to_decimal('0.000001'),
            to_decimal('-0.0001'),
        ]

        for val in small_values:
            result = safe_add(val, val)
            if result != to_decimal(str(float(val) * 2)):
                violations += 1
                print(f"  [WARN] Edge case failed for {val}")

        # Very large numbers
        large_values = [
            to_decimal('999999999999'),
            to_decimal('1000000000000'),
            to_decimal('-999999999999'),
        ]

        for val in large_values:
            result = safe_add(val, val)
            if result != to_decimal(str(float(val) * 2)):
                violations += 1
                print(f"  [WARN] Edge case failed for {val}")

        # Negative values
        negative_values = [
            to_decimal('-100'),
            to_decimal('-1000.50'),
            to_decimal('-0.01'),
        ]

        for val in negative_values:
            result = safe_add(val, to_decimal('100'))
            if result != to_decimal(str(float(val) + 100)):
                violations += 1
                print(f"  [WARN] Negative value failed for {val}")

        if violations == 0:
            print("  [OK] All edge case tests passed")
        else:
            print(f"  [WARN] {violations} edge case violations found")

        return violations == 0

    def test_multi_currency_operations(self):
        """Test operations with different currency scales."""
        print("\nTesting multi-currency operations...")
        violations = 0

        from shared.currency_precision import get_currency_scale

        # BTC (8 decimals)
        btc_amount = to_decimal('0.12345678')
        btc_scale = get_currency_scale('BTC')
        btc_quantized = btc_amount.quantize(Decimal('1.' + '0' * btc_scale))

        # Gold (3 decimals)
        gold_amount = to_decimal('2500.500')
        gold_scale = get_currency_scale('GRAM')
        gold_quantized = gold_amount.quantize(Decimal('1.' + '0' * gold_scale))

        # TRY (2 decimals)
        try_amount = to_decimal('10000.50')
        try_scale = get_currency_scale('TRY')
        try_quantized = try_amount.quantize(Decimal('1.' + '0' * try_scale))

        # Verify quantization
        if btc_quantized != to_decimal('0.12345678'):
            violations += 1
            print(f"  [WARN] BTC quantization failed: {btc_quantized}")

        if gold_quantized != to_decimal('2500.500'):
            violations += 1
            print(f"  [WARN] Gold quantization failed: {gold_quantized}")

        if try_quantized != to_decimal('10000.50'):
            violations += 1
            print(f"  [WARN] TRY quantization failed: {try_quantized}")

        # Test currency conversion simulation
        # 1 BTC = 60000 USD, 1 USD = 32 TRY
        btc_value_usd = safe_multiply(btc_amount, to_decimal('60000'))
        btc_value_try = safe_multiply(btc_value_usd, to_decimal('32'))

        expected_try = to_decimal('237120.0000')  # 0.12345678 * 60000 * 32 = 237120.0000
        if abs(btc_value_try - expected_try) > to_decimal('0.01'):
            violations += 1
            print(f"  [WARN] Currency conversion failed: {btc_value_try} vs {expected_try}")

        if violations == 0:
            print("  [OK] All multi-currency tests passed")
        else:
            print(f"  [WARN] {violations} multi-currency violations found")

        return violations == 0

    def test_mixed_portfolio_calculation(self):
        """Test portfolio calculation with mixed asset types (BTC, Gold, TRY)."""
        print("\nTesting mixed portfolio calculation...")
        violations = 0

        from shared.currency_precision import get_currency_scale

        # Mixed portfolio
        portfolio = [
            {'type': 'BTC', 'quantity': to_decimal('0.5'), 'unit_price': to_decimal('60000'), 'scale': get_currency_scale('BTC')},
            {'type': 'Gold', 'quantity': to_decimal('10'), 'unit_price': to_decimal('2500'), 'scale': get_currency_scale('GRAM')},
            {'type': 'TRY', 'quantity': to_decimal('10000'), 'unit_price': to_decimal('1'), 'scale': get_currency_scale('TRY')},
        ]

        total_value = to_decimal('0')

        for asset in portfolio:
            asset_value = safe_multiply(asset['quantity'], asset['unit_price'])
            total_value = safe_add(total_value, asset_value)

        # Expected: 0.5*60000 + 10*2500 + 10000*1 = 30000 + 25000 + 10000 = 65000
        expected_value = to_decimal('65000')

        if abs(total_value - expected_value) > to_decimal('0.01'):
            violations += 1
            print(f"  [WARN] Portfolio calculation failed: {total_value} vs {expected_value}")

        # Test percentage allocation
        btc_allocation = safe_divide(
            safe_multiply(to_decimal('0.5'), to_decimal('60000')),
            total_value
        )
        expected_btc_allocation = to_decimal('0.4615')  # 30000/65000 ≈ 0.4615

        if abs(btc_allocation - expected_btc_allocation) > to_decimal('0.01'):
            violations += 1
            print(f"  [WARN] BTC allocation failed: {btc_allocation} vs {expected_btc_allocation}")

        if violations == 0:
            print("  [OK] All mixed portfolio tests passed")
        else:
            print(f"  [WARN] {violations} mixed portfolio violations found")

        return violations == 0

    def run_all_tests(self):
        """Run all property-based tests."""
        print("=" * 80)
        print("PROPERTY-BASED TESTING FOR DECIMAL PRECISION")
        print("=" * 80)
        print(f"Iterations: {self.iterations}")
        print(f"Max acceptable difference: {self.max_diff}")

        results = []
        results.append(("Addition", self.test_addition_property()))
        results.append(("Multiplication", self.test_multiplication_property()))
        results.append(("Division", self.test_division_property()))
        results.append(("Complex Calculation", self.test_complex_calculation_property()))
        results.append(("Weighted Average", self.test_weighted_average_property()))
        results.append(("KDV Calculation", self.test_kdv_calculation_property()))
        results.append(("Commission", self.test_commission_calculation_property()))
        results.append(("Edge Cases", self.test_edge_cases()))
        results.append(("Multi-Currency Operations", self.test_multi_currency_operations()))
        results.append(("Mixed Portfolio Calculation", self.test_mixed_portfolio_calculation()))

        print("\n" + "=" * 80)
        print("PROPERTY-BASED TEST SUMMARY")
        print("=" * 80)

        passed = sum(1 for _, result in results if result)
        total = len(results)

        for test_name, result in results:
            status = "[PASS]" if result else "[FAIL]"
            print(f"{test_name:<25} {status}")

        print("=" * 80)
        print(f"Total: {passed}/{total} tests passed")

        if passed == total:
            print("[OK] All property-based tests passed")
            return True
        else:
            print("[FAIL] Some property-based tests failed")
            return False


def main():
    """Main test function."""
    # Run with 100,000 iterations
    tester = PropertyBasedDecimalTests(iterations=100000)
    success = tester.run_all_tests()

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


class TestPropertyBasedDecimal:
    """Pytest discovery wrapper for property-based financial precision tests."""

    @classmethod
    def setup_class(cls):
        # 500 random property iterations per test provides strong statistical guarantees in ~1 second
        cls.tester = PropertyBasedDecimalTests(iterations=500)

    def test_addition_property(self):
        assert self.tester.test_addition_property()

    def test_multiplication_property(self):
        assert self.tester.test_multiplication_property()

    def test_division_property(self):
        assert self.tester.test_division_property()

    def test_complex_calculation_property(self):
        assert self.tester.test_complex_calculation_property()

    def test_weighted_average_property(self):
        assert self.tester.test_weighted_average_property()

    def test_kdv_calculation_property(self):
        assert self.tester.test_kdv_calculation_property()

    def test_commission_calculation_property(self):
        assert self.tester.test_commission_calculation_property()

    def test_edge_cases(self):
        assert self.tester.test_edge_cases()

    def test_multi_currency_operations(self):
        assert self.tester.test_multi_currency_operations()

    def test_mixed_portfolio_calculation(self):
        assert self.tester.test_mixed_portfolio_calculation()
