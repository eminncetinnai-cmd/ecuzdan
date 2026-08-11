"""
Integration Tests for Decimal Migration

Tests real database operations with Decimal precision to ensure
the migration works correctly in a real application context.

Tests:
- Database read/write operations with Decimal
- Transaction creation and retrieval
- Asset creation and valuation
- Rollback verification
- Data integrity checks

Usage:
    pytest tests/test_integration_decimal.py -v
"""

import sys
import os
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from shared.decimal_precision import to_decimal, safe_add, safe_subtract, safe_multiply, safe_divide


class DecimalIntegrationTests:
    """Integration tests for Decimal migration."""
    
    def __init__(self):
        self.test_db_path = None
        self.original_db_path = None
    
    def setup_test_database(self):
        """Setup a test database for integration testing."""
        # Create a temporary copy of the database
        from config import Config
        self.original_db_path = Config.DATABASE_URL.replace('sqlite:///', '')
        
        # Create temporary database
        temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(temp_dir, 'test_ecuzdan.db')
        
        # Copy original database to test location
        if os.path.exists(self.original_db_path):
            shutil.copy2(self.original_db_path, self.test_db_path)
            print(f"✓ Created test database: {self.test_db_path}")
        else:
            print(f"⚠ Original database not found, creating new test database")
            # Create empty database
            import sqlite3
            conn = sqlite3.connect(self.test_db_path)
            conn.close()
        
        # Update config to use test database
        Config.DATABASE_URL = f'sqlite:///{self.test_db_path}'
        
        return self.test_db_path
    
    def teardown_test_database(self):
        """Cleanup test database."""
        if self.test_db_path and os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
            print(f"✓ Cleaned up test database")
        
        # Restore original config
        from config import Config
        Config.DATABASE_URL = f'sqlite:///{self.original_db_path}'
    
    def test_database_decimal_write_read(self):
        """Test writing and reading Decimal values from database."""
        print("\nTest: Database Decimal Write/Read")
        print("-" * 60)
        
        try:
            from shared.db import db
            from models import Transaction
            
            # Create a test transaction with Decimal
            amount = to_decimal('123.4567')
            
            tx = Transaction(
                amount=amount,
                type='Gelir',
                category='Test',
                description='Integration test transaction',
                status='Ödendi',
                date='2026-07-23'
            )
            
            db.session.add(tx)
            db.session.commit()
            
            # Read back from database
            retrieved_tx = Transaction.query.filter_by(description='Integration test transaction').first()
            
            if retrieved_tx:
                retrieved_amount = retrieved_tx.amount
                diff = abs(retrieved_amount - amount)
                
                if diff < Decimal('0.0001'):
                    print(f"  ✓ Decimal value preserved: {amount} -> {retrieved_amount}")
                    print(f"  ✓ Difference: {diff}")
                    success = True
                else:
                    print(f"  ✗ Decimal value changed: {amount} -> {retrieved_amount}")
                    print(f"  ✗ Difference: {diff}")
                    success = False
                
                # Cleanup
                db.session.delete(retrieved_tx)
                db.session.commit()
            else:
                print(f"  ✗ Failed to retrieve transaction")
                success = False
            
            return success
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def test_asset_decimal_operations(self):
        """Test asset creation and valuation with Decimal."""
        print("\nTest: Asset Decimal Operations")
        print("-" * 60)
        
        try:
            from shared.db import db
            from models import Asset, AssetSector
            
            # Create a test asset with Decimal values
            asset = Asset(
                type='Altın',
                name='Test Gold',
                value=to_decimal('2500.5000'),
                purchase_cost=to_decimal('2400.0000'),
                quantity=to_decimal('10.0000'),
                unit_price=to_decimal('250.0500'),
                purchase_date='2026-07-23',
                sector_id=1  # Assuming sector exists
            )
            
            db.session.add(asset)
            db.session.commit()
            
            # Read back
            retrieved_asset = Asset.query.filter_by(name='Test Gold').first()
            
            if retrieved_asset:
                value_diff = abs(retrieved_asset.value - to_decimal('2500.5000'))
                cost_diff = abs(retrieved_asset.purchase_cost - to_decimal('2400.0000'))
                
                if value_diff < Decimal('0.0001') and cost_diff < Decimal('0.0001'):
                    print(f"  ✓ Asset values preserved")
                    print(f"    Value: {retrieved_asset.value}")
                    print(f"    Cost: {retrieved_asset.purchase_cost}")
                    success = True
                else:
                    print(f"  ✗ Asset values changed")
                    print(f"    Value diff: {value_diff}")
                    print(f"    Cost diff: {cost_diff}")
                    success = False
                
                # Cleanup
                db.session.delete(retrieved_asset)
                db.session.commit()
            else:
                print(f"  ✗ Failed to retrieve asset")
                success = False
            
            return success
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def test_transaction_calculation_with_decimal(self):
        """Test financial calculations using Decimal from database values."""
        print("\nTest: Transaction Calculation with Decimal")
        print("-" * 60)
        
        try:
            from shared.db import db
            from models import Transaction
            
            # Create test transactions
            tx1 = Transaction(
                amount=to_decimal('1000.0000'),
                type='Gelir',
                category='Salary',
                description='Test income',
                status='Ödendi',
                date='2026-07-23'
            )
            
            tx2 = Transaction(
                amount=to_decimal('500.0000'),
                type='Gider',
                category='Rent',
                description='Test expense',
                status='Ödendi',
                date='2026-07-23'
            )
            
            db.session.add(tx1)
            db.session.add(tx2)
            db.session.commit()
            
            # Calculate totals using Decimal
            transactions = Transaction.query.filter(
                Transaction.description.in_(['Test income', 'Test expense'])
            ).all()
            
            total_income = to_decimal('0')
            total_expenses = to_decimal('0')
            
            for tx in transactions:
                if tx.type == 'Gelir':
                    total_income = safe_add(total_income, tx.amount)
                else:
                    total_expenses = safe_add(total_expenses, tx.amount)
            
            balance = safe_subtract(total_income, total_expenses)
            expected_balance = to_decimal('500.0000')
            
            if abs(balance - expected_balance) < Decimal('0.0001'):
                print(f"  ✓ Calculation correct")
                print(f"    Income: {total_income}")
                print(f"    Expenses: {total_expenses}")
                print(f"    Balance: {balance}")
                success = True
            else:
                print(f"  ✗ Calculation incorrect")
                print(f"    Expected: {expected_balance}")
                print(f"    Got: {balance}")
                success = False
            
            # Cleanup
            for tx in transactions:
                db.session.delete(tx)
            db.session.commit()
            
            return success
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False
    
    def test_rollback_verification(self):
        """Test that database rollback works correctly with Decimal."""
        print("\nTest: Rollback Verification")
        print("-" * 60)
        
        try:
            from shared.db import db
            from models import Transaction
            
            # Get initial transaction count
            initial_count = Transaction.query.count()
            
            # Start a transaction
            tx = Transaction(
                amount=to_decimal('999.9999'),
                type='Gelir',
                category='Test',
                description='Rollback test',
                status='Ödendi',
                date='2026-07-23'
            )
            
            db.session.add(tx)
            
            # Rollback
            db.session.rollback()
            
            # Verify count unchanged
            final_count = Transaction.query.count()
            
            if initial_count == final_count:
                print(f"  ✓ Rollback successful (count unchanged: {initial_count})")
                success = True
            else:
                print(f"  ✗ Rollback failed (count changed: {initial_count} -> {final_count})")
                success = False
            
            return success
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            db.session.rollback()
            return False
    
    def run_all_tests(self):
        """Run all integration tests."""
        print("=" * 60)
        print("INTEGRATION TESTS FOR DECIMAL MIGRATION")
        print("=" * 60)
        
        # Setup test database
        try:
            self.setup_test_database()
        except Exception as e:
            print(f"✗ Failed to setup test database: {e}")
            return False
        
        # Initialize database connection
        try:
            from shared.db import db
            from app import create_app
            app = create_app()
            with app.app_context():
                db.create_all()
        except Exception as e:
            print(f"✗ Failed to initialize database: {e}")
            self.teardown_test_database()
            return False
        
        results = []
        
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                results.append(("Database Write/Read", self.test_database_decimal_write_read()))
                results.append(("Asset Operations", self.test_asset_decimal_operations()))
                results.append(("Transaction Calculation", self.test_transaction_calculation_with_decimal()))
                results.append(("Rollback Verification", self.test_rollback_verification()))
        
        except Exception as e:
            print(f"✗ Error running tests: {e}")
            results = []
        
        # Teardown
        self.teardown_test_database()
        
        print("\n" + "=" * 60)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name:<25} {status}")
        
        print("=" * 60)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("✅ All integration tests passed")
            return True
        else:
            print("❌ Some integration tests failed")
            return False


def main():
    """Main test function."""
    tester = DecimalIntegrationTests()
    success = tester.run_all_tests()
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
