"""
Bütçe Hesaplamaları Testleri
Bütçe oluşturma, takibi, analizi ve raporlama testleri
"""


import pytest

from database import get_monthly_balance
from models import Category, Tenant, Transaction, User, db


class TestBudgetCalculations:
    """Bütçe hesaplamaları test sınıfı"""

    @pytest.fixture(autouse=True)
    def setup(self, app):
        """Test öncesi kurulum"""
        with app.app_context():
            # Test tenant oluştur
            tenant = Tenant(id='test_budget', name='Test Budget Tenant')
            db.session.add(tenant)
            db.session.commit()

            # Test kullanıcı oluştur
            user = User(
                username='test_budget_user',
                password='test123',
                tenant_id=tenant.id
            )
            db.session.add(user)
            db.session.commit()

            # Test kategorileri oluştur
            categories = [
                ('Maaş / Ücret Geliri', 'Gelir'),
                ('Kira', 'Gider'),
                ('Diğer Giderler', 'Gider'),
                ('Aylık Sabit Gider', 'Gider')
            ]
            for name, type_ in categories:
                if not Category.query.filter_by(name=name).first():
                    cat = Category(name=name, type=type_)
                    db.session.add(cat)
            db.session.commit()

            self.tenant_id = tenant.id
            self.user_id = user.id

    def test_monthly_income_calculation(self, app):
        """Aylık gelir hesaplama testi"""
        with app.app_context():
            # Test işlemleri oluştur
            transactions = [
                Transaction(
                    date='2024-01-15',
                    category='Maaş / Ücret Geliri',
                    description='Ocak maaşı',
                    type='Gelir',
                    amount=10000.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                ),
                Transaction(
                    date='2024-01-20',
                    category='Kira',
                    description='Ocak kirası',
                    type='Gider',
                    amount=3000.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                )
            ]
            for tx in transactions:
                db.session.add(tx)
            db.session.commit()

            # Aylık bakiyeyi hesapla
            income, expense = get_monthly_balance(2024, 1, self.tenant_id)

            assert income == 10000.0, f"Beklenen gelir: 10000.0, Alınan: {income}"
            assert expense == 3000.0, f"Beklenen gider: 3000.0, Alınan: {expense}"

    def test_monthly_expense_calculation(self, app):
        """Aylık gider hesaplama testi"""
        with app.app_context():
            # Test işlemleri oluştur
            transactions = [
                Transaction(
                    date='2024-02-10',
                    category='Diğer Giderler',
                    description='Şubat yemek gideri',
                    type='Gider',
                    amount=2000.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                ),
                Transaction(
                    date='2024-02-15',
                    category='Aylık Sabit Gider',
                    description='Şubat ulaşım gideri',
                    type='Gider',
                    amount=500.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                )
            ]
            for tx in transactions:
                db.session.add(tx)
            db.session.commit()

            # Aylık bakiyeyi hesapla
            income, expense = get_monthly_balance(2024, 2, self.tenant_id)

            assert income == 0.0, f"Beklenen gelir: 0.0, Alınan: {income}"
            assert expense == 2500.0, f"Beklenen gider: 2500.0, Alınan: {expense}"

    def test_budget_balance_calculation(self, app):
        """Bütçe bakiyesi hesaplama testi"""
        with app.app_context():
            # Test işlemleri oluştur
            transactions = [
                Transaction(
                    date='2024-03-01',
                    category='Maaş / Ücret Geliri',
                    description='Mart maaşı',
                    type='Gelir',
                    amount=15000.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                ),
                Transaction(
                    date='2024-03-05',
                    category='Kira',
                    description='Mart kirası',
                    type='Gider',
                    amount=3000.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                ),
                Transaction(
                    date='2024-03-10',
                    category='Diğer Giderler',
                    description='Mart yemek gideri',
                    type='Gider',
                    amount=2000.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                )
            ]
            for tx in transactions:
                db.session.add(tx)
            db.session.commit()

            # Aylık bakiyeyi hesapla
            income, expense = get_monthly_balance(2024, 3, self.tenant_id)
            balance = income - expense

            assert income == 15000.0, f"Beklenen gelir: 15000.0, Alınan: {income}"
            assert expense == 5000.0, f"Beklenen gider: 5000.0, Alınan: {expense}"
            assert balance == 10000.0, f"Beklenen bakiye: 10000.0, Alınan: {balance}"

    def test_pending_transactions_included(self, app):
        """Bekleyen işlemlerin bütçe hesaplamasına dahil edilmesi testi"""
        with app.app_context():
            # Test işlemleri oluştur
            transactions = [
                Transaction(
                    date='2024-04-01',
                    category='Maaş / Ücret Geliri',
                    description='Nisan maaşı',
                    type='Gelir',
                    amount=10000.0,
                    status='Ödendi',
                    tenant_id=self.tenant_id
                ),
                Transaction(
                    date='2024-04-05',
                    category='Kira',
                    description='Nisan kirası',
                    type='Gider',
                    amount=3000.0,
                    status='Bekliyor',  # Bekliyor durumu
                    tenant_id=self.tenant_id
                )
            ]
            for tx in transactions:
                db.session.add(tx)
            db.session.commit()

            # Aylık bakiyeyi hesapla
            income, expense = get_monthly_balance(2024, 4, self.tenant_id)

            assert income == 10000.0, f"Beklenen gelir: 10000.0, Alınan: {income}"
            assert expense == 3000.0, f"Beklenen gider: 3000.0 (bekleyen işlem dahil edilir), Alınan: {expense}"

    def test_tenant_isolation(self, app):
        """Tenant bazlı bütçe izolasyonu testi"""
        with app.app_context():
            # İkinci tenant oluştur
            tenant2 = Tenant(id='test_budget_2', name='Test Budget Tenant 2')
            db.session.add(tenant2)
            db.session.commit()

            # Tenant 1 için işlem
            tx1 = Transaction(
                date='2024-05-01',
                category='Maaş',
                description='Mayıs maaşı (Tenant 1)',
                type='Gelir',
                amount=10000.0,
                status='Ödendi',
                tenant_id=self.tenant_id
            )
            db.session.add(tx1)

            # Tenant 2 için işlem
            tx2 = Transaction(
                date='2024-05-01',
                category='Maaş',
                description='Mayıs maaşı (Tenant 2)',
                type='Gelir',
                amount=20000.0,
                status='Ödendi',
                tenant_id=tenant2.id
            )
            db.session.add(tx2)
            db.session.commit()

            # Tenant 1 bakiyesi
            income1, expense1 = get_monthly_balance(2024, 5, self.tenant_id)

            # Tenant 2 bakiyesi
            income2, expense2 = get_monthly_balance(2024, 5, tenant2.id)

            assert income1 == 10000.0, f"Tenant 1 beklenen gelir: 10000.0, Alınan: {income1}"
            assert income2 == 20000.0, f"Tenant 2 beklenen gelir: 20000.0, Alınan: {income2}"
            assert income1 != income2, "Tenant bakiyeleri farklı olmalı"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
